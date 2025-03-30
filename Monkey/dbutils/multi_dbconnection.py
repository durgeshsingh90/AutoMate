import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO)

# Oracle connection details
username = 'oasis77'
password = 'ist0py'
dsn_alias = 'ISTU2_EQU'  # Alias defined in TNSNAMES.ORA

# Path to the Oracle Instant Client
oracle_client_path = r"C:\Oracle\Ora12c_64\BIN"

# Initialize Oracle client only once
try:
    oracledb.init_oracle_client(lib_dir=oracle_client_path)
    logging.info(f"Oracle client initialized from {oracle_client_path}")
except Exception as e:
    logging.warning(f"Oracle client may already be initialized: {e}")

# Custom JSON encoder for datetime and bytes
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(CustomJSONEncoder, self).default(obj)

def execute_query(query):
    try:
        connection = oracledb.connect(user=username, password=password, dsn=dsn_alias)
        cursor = connection.cursor()

        cursor.execute(query.rstrip(';'))
        rows = cursor.fetchall()
        metadata = cursor.description
        columns = [(col[0], col[1]) for col in metadata]

        result = []
        for row in rows:
            row_dict = {}
            for idx, value in enumerate(row):
                col_name, col_type = columns[idx]
                if col_type in (oracledb.DB_TYPE_TIMESTAMP, oracledb.DB_TYPE_DATE):
                    if value is not None:
                        value = value.isoformat()
                elif col_type == oracledb.DB_TYPE_RAW:
                    if value is not None:
                        value = base64.b64encode(value).decode('utf-8')
                row_dict[col_name] = value
            result.append(row_dict)

        cursor.close()
        connection.close()

        return {
            "query": query,
            "success": True,
            "data": result
        }

    except oracledb.DatabaseError as e:
        error, = e.args
        return {
            "query": query,
            "success": False,
            "error": f"{error.code}: {error.message}",
            "recoverable": error.isrecoverable,
            "context": error.context
        }
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e)
        }

def run_multiple_queries(queries):
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_query = {executor.submit(execute_query, q): q for q in queries}
        for future in as_completed(future_to_query):
            results.append(future.result())
    return results

def run_query_as_json(query):
    result = execute_query(query)
    if result["success"]:
        return json.dumps(result["data"], indent=2, cls=CustomJSONEncoder)
    else:
        return json.dumps(result, indent=2)
