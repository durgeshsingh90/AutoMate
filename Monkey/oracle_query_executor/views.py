import oracledb
import logging
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
import base64
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# Set up logging
logger = logging.getLogger(__name__)

# File path for storing query history
HISTORY_FILE_PATH = os.path.join(settings.BASE_DIR, 'media/oracledb/query_history/query_history.json')

# Directory for saving and loading scripts
SCRIPT_DIR = os.path.join(settings.BASE_DIR, 'media/oracledb/querybook')

# Ensure the required directories exist
os.makedirs(os.path.dirname(HISTORY_FILE_PATH), exist_ok=True)
os.makedirs(SCRIPT_DIR, exist_ok=True)

# Custom JSON encoder for handling specific data types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(CustomJSONEncoder, self).default(obj)

def initialize_connection(db_config):
    try:
        oracledb.init_oracle_client(lib_dir=db_config['client_path'])
        logger.info(f"Oracle client initialized from {db_config['client_path']}")
        connection = oracledb.connect(user=db_config['USER'], 
                                     password=db_config['PASSWORD'], 
                                     dsn=db_config['NAME'])
        logger.info("Successfully connected to the database")
        return connection
    except oracledb.DatabaseError as e:
        logger.error(f"Database connection error: {e}")
        return None

def generate_insert_statement(schema, table_name, columns, row):
    columns_str = ', '.join(columns)
    values_str = ', '.join(f"'{value}'" if value is not None else 'NULL' for value in row)
    insert_statement = f"INSERT INTO {schema}.{table_name} ({columns_str}) VALUES ({values_str});"
    return insert_statement

def execute_query(query, db_config):
    query_result = {"query": query, "result": None, "error": None, "execution_time": None}
    connection = initialize_connection(db_config)
    if connection is None:
        query_result["error"] = "Unable to establish database connection"
        return query_result

    start_time = time.time()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query.rstrip(';'))
            logger.info(f"Executed query: {query}")

            rows = cursor.fetchall()
            metadata = cursor.description
            columns = [col[0] for col in metadata]

            result = []
            insert_statements = []
            if "SELECT COUNT(*)" in query.upper():
                for row in rows:
                    result.append({"COUNT(*)": row[0]})
            else:
                schema, table_name = query.split()[3].split('.')
                for row in rows:
                    row_dict = {columns[idx]: value for idx, value in enumerate(row)}
                    result.append(row_dict)
                    insert_statements.append(generate_insert_statement(schema, table_name, columns, row))
            
            query_result["result"] = {
                "data": result,
                "insert_statements": insert_statements
            }

        finally:
            cursor.close()
            connection.close()

    except oracledb.DatabaseError as e:
        error = e.args[0]
        logger.error(f"An error occurred: {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        query_result["error"] = str(e)

    end_time = time.time()
    query_result["execution_time"] = end_time - start_time

    return query_result

def save_query_result_to_file(result, query, output_types, db_key):
    table_name = query.split()[3].split('.')[1]
    output_dir = os.path.join(settings.BASE_DIR, 'media', 'oracledb', db_key)
    os.makedirs(output_dir, exist_ok=True)

    if 'json' in output_types:
        output_filename_json = os.path.join(output_dir, f"{table_name}.json")
        with open(output_filename_json, 'w') as output_file:
            json.dump(result["result"]["data"], output_file, cls=CustomJSONEncoder, indent=4)

    if 'sql' in output_types:
        output_filename_sql = os.path.join(output_dir, f"{table_name}.sql")
        with open(output_filename_sql, 'w') as sql_file:
            for statement in result["result"]["insert_statements"]:
                sql_file.write(statement + '\n')

def file_writer(queue, output_types, db_key):
    while True:
        item = queue.get()
        if item is None:
            break
        result, query = item
        save_query_result_to_file(result, query, output_types, db_key)
        queue.task_done()

def execute_queries_with_new_connection(queries, output_types, result_queue, db_config, db_key):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {executor.submit(execute_query, query, db_config): query for query in queries}
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Query completed: {query} (Time taken: {result['execution_time']} seconds)")

                result_queue.put((result, query))

            except Exception as exc:
                logger.error(f"Query {query} generated an exception: {exc}")
                results.append({"query": query, "result": None, "error": str(exc), "execution_time": None})

    return results

def execute_multiple_query_sets(query_sets, output_types, db_config, db_key):
    all_results = []
    result_queue = Queue()

    num_writer_threads = 5
    writer_threads = []
    for _ in range(num_writer_threads):
        t = threading.Thread(target=file_writer, args=(result_queue, output_types, db_key,))
        t.start()
        writer_threads.append(t)

    with ThreadPoolExecutor(max_workers=len(query_sets)) as executor:
        future_to_query_set = {executor.submit(execute_queries_with_new_connection, query_set, output_types, result_queue, db_config, db_key): query_set for query_set in query_sets}
        for future in as_completed(future_to_query_set):
            query_set = future_to_query_set[future]
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as exc:
                logger.error(f"Query set {query_set} generated an exception: {exc}")
                all_results.append({"query_set": query_set, "result": None, "error": str(exc), "execution_time": None})

    for _ in range(num_writer_threads):
        result_queue.put(None)
    for t in writer_threads:
        t.join()

    return all_results

def save_query_history(query_text, format):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "format": format,
        "query": query_text
    }

    if os.path.exists(HISTORY_FILE_PATH):
        with open(HISTORY_FILE_PATH, 'r') as history_file:
            history = json.load(history_file)
    else:
        history = []

    if len(history) >= 5000:
        history = history[1:]

    history.append(entry)
    with open(HISTORY_FILE_PATH, 'w') as history_file:
        json.dump(history, history_file, indent=4)

@csrf_exempt
@require_POST
def execute_queries_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON data")

    db_key = data.get('db_key', 'default')
    db_config = settings.DATABASES.get(db_key)

    if not db_config:
        return JsonResponse({"error": "Invalid database configuration key provided."}, status=400)

    query_sets = data.get('query_sets')
    if not query_sets:
        return HttpResponseBadRequest("No query sets provided")

    output_types = data.get('output_types', ['json', 'sql'])

    results = execute_multiple_query_sets(query_sets, output_types, db_config, db_key)

    response_data = {
        "results": results
    }

    save_query_history(data.get('query_sets_text', ''), data.get('format', ''))

    return JsonResponse(response_data, encoder=CustomJSONEncoder, safe=False)

@csrf_exempt
@require_POST
def save_script_view(request):
    data = json.loads(request.body)
    name = data.get("name")
    description = data.get("description")
    content = data.get("content")
    format = data.get("format")

    if not name or not content:
        return HttpResponseBadRequest("Name and content are required")

    script = save_script(name, description, content, format)
    return JsonResponse(script)

def load_scripts_view(request):
    scripts = load_scripts()
    return JsonResponse(scripts, safe=False)

def save_script(name, description, content, format):
    script = {
        "name": name,
        "description": description,
        "content": content,
        "format": format,
        "timestamp": datetime.now().isoformat()
    }
    file_path = os.path.join(SCRIPT_DIR, f"{name}.json")
    with open(file_path, 'w') as f:
        json.dump(script, f, indent=4)
    return script

def load_scripts():
    scripts = []
    for filename in os.listdir(SCRIPT_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(SCRIPT_DIR, filename), 'r') as f:
                script = json.load(f)
                scripts.append(script)
    return scripts

def index(request):
    return render(request, 'oracle_query_executor/index.html')
