# AutoMate/sql_db/views.py

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
import subprocess
import os
import filecmp
from datetime import datetime
import logging
import glob

# Set up logging
logger = logging.getLogger(__name__)

# Define database connection strings
DB_CONNECTIONS = {
    'uat_novate': 'novate/nov1234@istu2',
    'uat_oasis77': 'oasis77/ist0py@istu2',
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'sql_db', 'db', 'data')

def index(request):
    logger.debug("Rendering index page.")
    return render(request, 'sql_db/index.html')

def get_db_connections(request):
    logger.debug("Fetching database connections.")
    return JsonResponse(list(DB_CONNECTIONS.keys()), safe=False)

def list_tables(request):
    db_key = request.GET.get('db_key')
    if not db_key:
        logger.error("No database key provided.")
        return JsonResponse({'error': 'Database key is required'})

    try:
        logger.debug(f"Listing tables for database key: {db_key}")
        search_pattern = os.path.join(OUTPUT_DIR, db_key, 'tablelist_*.log')
        files = glob.glob(search_pattern, recursive=True)
        tables = []
        for file in files:
            with open(file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(("TABLE_NAME", "---------")):
                        tables.append(line)

        tables.sort()
        logger.info(f"Tables listed for {db_key}: {tables}")
        return JsonResponse({'tables': tables})
    except Exception as e:
        logger.exception("Error listing tables.")
        return JsonResponse({'error': str(e)}, status=500)

def refresh_list_tables(request):
    db_key = request.GET.get('db_key')
    if not db_key:
        logger.error("No database key provided.")
        return JsonResponse({'error': 'Database key is required'})

    command = 'SELECT table_name FROM user_tables;'
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"tablelist_{timestamp}.log"
    filepath, error = run_sqlplus_command(command, db_key, filename, include_db_info=True)

    if error:
        logger.error(f"Error refreshing table list for {db_key}: {error}")
        return JsonResponse({'error': error})

    try:
        tables = []
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith(("TABLE_NAME", "---------")):
                    tables.append(line)

        tables.sort()
        logger.info(f"Refreshed tables for {db_key}: {tables}")
        return JsonResponse({'tables': tables})
    except Exception as e:
        logger.exception(f"Error reading refreshed table list for {db_key}.")
        return JsonResponse({'error': str(e)}, status=500)

def refresh_select_all_from_table(request, table_name):
    db_key = request.GET.get('db_key')
    if not db_key:
        logger.error("No database key provided.")
        return JsonResponse({'error': 'Database key is required'}, status=400)

    command = f'SELECT * FROM {table_name};'
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{table_name}_{timestamp}.log"
    filepath, error = run_sqlplus_command(command, db_key, filename)

    if error:
        logger.error(f"Error refreshing table {table_name} in {db_key}: {error}")
        return JsonResponse({'error': error}, status=500)

    if not os.path.exists(filepath):
        logger.error(f"File creation failed or file not found for table {table_name} in {db_key}.")
        return JsonResponse({'error': 'File creation failed or file not found.'}, status=500)

    logger.info(f"Table {table_name} refreshed successfully for {db_key}.")
    return JsonResponse({
        'message': f'Table "{table_name}" refreshed successfully.',
        'filename': filename
    })

def select_all_from_table(request, table_name):
    try:
        db_key = request.GET.get('db_key')
        logger.debug(f"Selecting all from table {table_name} for database key: {db_key}")

        search_pattern = os.path.join(OUTPUT_DIR, db_key, f'{table_name}_*.log')
        related_files = glob.glob(search_pattern, recursive=True)

        if not related_files:
            logger.warning(f"No files found for table {table_name} in {db_key}.")
            return JsonResponse({'files': []})

        related_files.sort(key=os.path.getmtime, reverse=True)
        file_names = [os.path.basename(file_path) for file_path in related_files]

        logger.info(f"Files found for table {table_name} in {db_key}: {file_names}")
        return JsonResponse({'files': file_names})
    except Exception as e:
        logger.exception(f"Error selecting all from table {table_name}.")
        return JsonResponse({'error': str(e)})

def run_sqlplus_command(command, db_key, filename, include_db_info=False):
    try:
        db_credentials = DB_CONNECTIONS.get(db_key)
        if not db_credentials:
            logger.error(f"Invalid database key provided: {db_key}")
            return None, "Invalid database key provided."

        db_directory = os.path.join(OUTPUT_DIR, db_key)
        os.makedirs(db_directory, exist_ok=True)

        filepath = os.path.join(db_directory, filename)
        logger.debug(f"Generating SQL*Plus script file for {db_key} at {filepath}")

        sqlplus_config = """
        SET TERMOUT OFF
        SET PAGESIZE 9999
        SET LINESIZE 2000
        SET FEEDBACK OFF
        SET VERIFY OFF
        SET ECHO OFF
        """

        server_info = ""
        if include_db_info:
            server_info = f"Prompt {db_key} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        command_block = f"{server_info}{sqlplus_config}\n{command}\nEXIT\n"
        sql_script_path = os.path.join(db_directory, 'script.sql')
        with open(sql_script_path, 'w') as f:
            f.write(command_block)

        result = subprocess.run(
            ['sqlplus', db_credentials + " @script.sql"],
            cwd=db_directory,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"SQL*Plus command failed for {db_key}: {result.stderr}")
            return None, result.stderr

        os.remove(sql_script_path)

        profile_log_path = os.path.join(db_directory, 'INST_PROFILE.log')
        if os.path.exists(profile_log_path):
            os.remove(profile_log_path)

        existing_files = sorted(
            [f for f in os.listdir(db_directory) if f.endswith('.log') and f != filename], reverse=True)

        for existing_file in existing_files:
            existing_filepath = os.path.join(db_directory, existing_file)
            if filecmp.cmp(filepath, existing_filepath, shallow=False):
                logger.info(f"New file {filename} has the same content as existing file {existing_file}. Deleting the new file.")
                os.remove(filepath)
                return existing_filepath, None

        logger.debug(f"SQL*Plus command executed successfully for {db_key}. File created at {filepath}")
        return filepath, None
    except Exception as e:
        logger.exception(f"Error running SQL*Plus command for {db_key}.")
        return None, str(e)
