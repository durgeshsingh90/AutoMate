import subprocess
import os
import filecmp
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Define database connection strings
DB_CONNECTIONS = {
    'uat_novate': 'novate/nov1234@istu2',
    'uat_oasis77': 'oasis77/ist0py@istu2_equ',
    'prod_f94gdos': 'f94gdos/Pune24!@A5PCDO8001.EQU.IST',
}

OUTPUT_DIR = r"C:\Durgesh\Office\Automation\AutoMate\AutoMate\sql_db\db\data"

def run_sqlplus_command(command, db_key, filename, include_db_info=False):
    try:
        db_credentials = DB_CONNECTIONS.get(db_key)
        if not db_credentials:
            logger.error(f"Invalid database key provided: {db_key}")
            return None, "Invalid database key provided."

        # Create the subdirectory for the database if it doesn't exist
        db_directory = os.path.join(OUTPUT_DIR, db_key)
        os.makedirs(db_directory, exist_ok=True)

        filepath = os.path.join(db_directory, filename)

        # SQLPlus configuration settings
        sqlplus_config = """
        SET TERMOUT OFF
        SET PAGESIZE 9999
        SET LINESIZE 2000
        SET FEEDBACK OFF
        SET VERIFY OFF
        SET ECHO OFF
        """

        # Include server info in the output if requested
        server_info = ""
        if include_db_info:
            server_info = f"Prompt {db_key} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Creating the SQL command script directly in a string
        sql_command = f"""
        {sqlplus_config}
        {server_info}
        spool {filepath}
        {command}
        spool off
        exit
        """

        # Write the script to a file in the same database directory
        sql_script_path = os.path.join(db_directory, f"{db_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql")
        with open(sql_script_path, 'w') as sql_file:
            sql_file.write(sql_command)

        # Set the custom environment for the SQL*Plus command
        env = os.environ.copy()
        env["NLS_LANG"] = ".AL32UTF8"

        # Execute the SQL script using SQL*Plus
        sqlplus_command = f"sqlplus {db_credentials} @{sql_script_path}"

        result = subprocess.run(
            sqlplus_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env  # Set the custom environment
        )

        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            logger.debug(f"SQL*Plus Output: {result.stdout}")
            return None, result.stderr

        logger.info(f"Command executed successfully: {filename}")
        logger.debug(f"SQL*Plus Output: {result.stdout}")

        # Clean up the temporary SQL script file
        os.remove(sql_script_path)

        # Clean up any unintended profile log files
        profile_log_path = os.path.join(db_directory, 'INST_PROFILE.log')
        if os.path.exists(profile_log_path):
            os.remove(profile_log_path)

        # Check for existing files with the same data
        existing_files = sorted(
            [f for f in os.listdir(db_directory) if f.endswith('.log') and f != filename], reverse=True)

        for existing_file in existing_files:
            existing_filepath = os.path.join(db_directory, existing_file)
            if filecmp.cmp(filepath, existing_filepath, shallow=False):
                logger.info(f"New file {filename} has the same content as existing file {existing_file}. Deleting the new file.")
                os.remove(filepath)
                return existing_filepath, None

        return filepath, None
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        return None, str(e)

def index(request):
    return render(request, 'sql_db/index.html')

def list_tables(request):
    db_key = request.GET.get('db_key')
    if not db_key:
        return JsonResponse({'error': 'Database key is required'})

    command = 'SELECT table_name FROM user_tables;'
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"tablelist_{timestamp}.log"
    filepath, error = run_sqlplus_command(command, db_key, filename, include_db_info=True)
    
    if error:
        return JsonResponse({'error': error})
    
    tables = []
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith(("TABLE_NAME", "---------")):
                tables.append(line)

    # Sort the table names alphabetically
    tables.sort()

    return JsonResponse({'tables': tables})

def select_all_from_table(request, table_name):
    db_key = request.GET.get('db_key')
    if not db_key:
        return JsonResponse({'error': 'Database key is required'})

    # Create a timestamped filename
    command = f'SELECT * FROM OASIS77.{table_name};'
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{table_name}_{timestamp}.log"
    filepath, error = run_sqlplus_command(command, db_key, filename)
    
    if error:
        return JsonResponse({'error': error})
    
    with open(filepath, 'rb') as file:
        response = HttpResponse(file.read(), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
