import subprocess
import logging
import os
import tempfile
import json
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render

# Get an instance of a logger
logger = logging.getLogger('sql_db')

def get_table_names_from_db():
    script_content = """
SET PAGESIZE 999
SET LINESIZE 200
SET FEEDBACK OFF
SET VERIFY OFF
COLUMN table_name FORMAT A30
SELECT table_name FROM user_tables;
EXIT;
    """
    tables = []

    try:
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sql') as temp_script:
            script_path = temp_script.name
            temp_script.write(script_content)
        
        logger.debug(f"Temporary script created at: {script_path}")

        sql_command = f"sqlplus -S oasis77/ist0py@istu2_equ @{script_path}"
        logger.debug(f"Running SQL command: {sql_command}")

        result = subprocess.run(sql_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        logger.debug(f"SQL command stdout: {stdout}")
        logger.error(f"SQL command stderr: {stderr}")

        if stderr:
            raise subprocess.CalledProcessError(1, sql_command, stderr)

        for line in stdout.splitlines():
            if line.strip() and not line.startswith("TABLE_NAME") and not line.startswith("---"):
                tables.append(line.strip())

        logger.debug(f"Extracted table names: {tables}")

    except subprocess.CalledProcessError as e:
        logger.error(f"SQL command failed: {str(e)}")
    finally:
        os.remove(script_path)
        logger.debug(f"Temporary script removed: {script_path}")

    return sorted(tables)  # Ensure the table names are sorted alphabetically

def load_table_names():
    json_file_path = Path('C:/Durgesh/Office/Automation/AutoMate/AutoMate/sql_db/db/table_names.json')

    # Ensure the directory exists
    json_file_path.parent.mkdir(parents=True, exist_ok=True)

    if json_file_path.is_file() and json_file_path.stat().st_size > 0:
        with json_file_path.open('r') as json_file:
            table_data = json.load(json_file)
        logger.debug(f"Loaded table names from file: {table_data}")
    else:
        table_data = get_table_names_from_db()
        with json_file_path.open('w') as json_file:
            json.dump(table_data, json_file)
        logger.debug(f"Saved table names to file: {table_data}")

    return sorted(table_data)  # Ensure the table names are sorted alphabetically

def save_updated_table_names(new_table_names):
    json_file_path = Path('C:/Durgesh/Office/Automation/AutoMate/AutoMate/sql_db/db/table_names.json')

    # Ensure the directory exists
    json_file_path.parent.mkdir(parents=True, exist_ok=True)

    if json_file_path.is_file() and json_file_path.stat().st_size > 0:
        with json_file_path.open('r') as json_file:
            existing_table_data = json.load(json_file)
    else:
        existing_table_data = []

    updated_table_data = list(set(existing_table_data + new_table_names))
    updated_table_data.sort()  # Ensure the table names are sorted alphabetically
    
    with json_file_path.open('w') as json_file:
        json.dump(updated_table_data, json_file)

    logger.debug(f"Updated table names saved to file: {updated_table_data}")
    return updated_table_data

def run_sql_commands(request):
    table_names = load_table_names()
    data_dir_path = Path('C:/Durgesh/Office/Automation/AutoMate/AutoMate/sql_db/db/data')
    fetched_tables = [f.stem for f in data_dir_path.glob("*.json")]

    context = {
        'table_names': table_names,
        'fetched_tables': fetched_tables,
        'unfetched_tables': [t for t in table_names if t not in fetched_tables]
    }
    return render(request, 'sql_db/index.html', context)

def update_table_names(request):
    new_table_names = get_table_names_from_db()
    updated_table_data = save_updated_table_names(new_table_names)
    return JsonResponse({'table_names': updated_table_data})

def fetch_table_data(request, table_name):
    sql_query = f"""
SET PAGESIZE 999
SET LINESIZE 200
SET FEEDBACK OFF
SET VERIFY OFF
COLUMN json_output FORMAT A1000
SELECT json_arrayagg(
         json_object(
           'TXNSRC' VALUE TXNSRC,
           'TXNDEST' VALUE TXNDEST,
           'ISS_ENTITY_ID' VALUE ISS_ENTITY_ID,
           'MSGTYPE' VALUE MSGTYPE,
           'EXTERNALID' VALUE EXTERNALID,
           'EXT_ID_DESC' VALUE EXT_ID_DESC,
           'MEMBER_ID' VALUE MEMBER_ID,
           'F_ID' VALUE F_ID,
           'INST_ID' VALUE INST_ID,
           'USERBIN_ID' VALUE USERBIN_ID,
           'KEYPARAM' VALUE KEYPARAM,
           'SITE_ID' VALUE SITE_ID,
           'BINROUTE_GROUP' VALUE BINROUTE_GROUP
         )
       ) AS json_output
FROM (
  SELECT TXNSRC, TXNDEST, ISS_ENTITY_ID, MSGTYPE, EXTERNALID, EXT_ID_DESC, MEMBER_ID, F_ID, INST_ID, USERBIN_ID, KEYPARAM, SITE_ID, BINROUTE_GROUP
  FROM OASIS77.{table_name}
  WHERE ROWNUM <= 20
)
    """

    data_dir = Path('C:/Durgesh/Office/Automation/AutoMate/AutoMate/sql_db/db/data')
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file_path = data_dir / f"{table_name}.json"

    try:
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sql') as temp_script:
            script_path = temp_script.name
            temp_script.write(sql_query)

        sql_command = f"sqlplus -S oasis77/ist0py@istu2_equ @{script_path}"
        logger.debug(f"Running SQL command: {sql_command}")

        result = subprocess.run(sql_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        logger.debug(f"SQL command stdout: {stdout}")
        logger.error(f"SQL command stderr: {stderr}")

        if stderr:
            raise subprocess.CalledProcessError(1, sql_command, stderr)

        # Parsing JSON output from SQL command
        json_output = stdout.split("JSON_OUTPUT")[1].strip()
        json_output = json.loads(json_output)

        with data_file_path.open('w') as data_file:
            json.dump(json_output, data_file)

    except subprocess.CalledProcessError as e:
        logger.error(f"SQL command failed: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        os.remove(script_path)
        logger.debug(f"Temporary script removed: {script_path}")

    return JsonResponse({'table_name': table_name, 'data': json_output})

def delete_table_data(request, table_name):
    data_file_path = Path(f'C:/Durgesh/Office/Automation/AutoMate/AutoMate/sql_db/db/data/{table_name}.json')
    try:
        if data_file_path.is_file():
            os.remove(data_file_path)
        else:
            return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'table_name': table_name})
