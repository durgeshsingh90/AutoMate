import os
import string
import logging
import threading
import subprocess
from django.shortcuts import render
from django.conf import settings
import json
import re
# Get the logger for the binblock app
logger = logging.getLogger('binblock')

# Define the output directory
OUTPUT_DIR = os.path.join(settings.BASE_DIR, 'binblock', 'output')

def run_background_queries():
    """Run prod and uat queries in the background, clean the output files, and perform further processing."""
    logger.debug("Starting background queries for prod and uat")

    def run_query_and_process(command, query, output_file, server_name):
        try:
            # Run the SQL query and generate the output file
            run_sqlplus_command(command, query, output_file, server_name)
            
            # Clean the output file after running the query
            cleaned_data = clean_file(output_file)
            logger.info(f"Cleaned data from {server_name}: {cleaned_data}")

            # After cleaning, continue with further processing of the data
            # Load cleaned data from JSON
            combined_data = combine_json_data([output_file])
            cleaned_combined_data = clean_json_data(combined_data)

            # Apply length checks (define length constraints for your fields)
            length_constraints = {'field1': 50, 'field2': 100}  # Example constraints
            checked_data = apply_length_checks(cleaned_combined_data, length_constraints)

            # Convert cleaned JSON data to SQL insert statements
            sql_statements = json_to_sql_insert(checked_data, 'your_table_name')
            sql_file_path = os.path.join(OUTPUT_DIR, f"{server_name.lower()}_insert_statements.sql")

            # Save the SQL statements to a file
            save_sql_statements_to_file(sql_statements, sql_file_path)

        except Exception as e:
            logger.error(f"Error running SQL query or processing data on {server_name}: {e}")

    prod_command = "sqlplus oasis77/ist0py@istu2_equ"
    uat_command = "sqlplus oasis77/ist0py@istu2_uat"
    query = "SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 4;"
    prod_output_file = os.path.join(OUTPUT_DIR, 'prod_output.json')
    uat_output_file = os.path.join(OUTPUT_DIR, 'uat_output.json')

    # Start threads for prod and uat queries and subsequent processing
    threading.Thread(target=run_query_and_process, args=(prod_command, query, prod_output_file, "Prod")).start()
    threading.Thread(target=run_query_and_process, args=(uat_command, query, uat_output_file, "UAT")).start()

def bin_blocking_editor(request):
    logger.info("Bin blocking editor view accessed")
    result = None
    log_with_delays = None
    prod_distinct_list = []

    try:
        # Run the distinct query first
        distinct_command = "sqlplus oasis77/ist0py@istu2"
        distinct_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"
        distinct_output_file = os.path.join(OUTPUT_DIR, 'prod_distinct_output.txt')
        run_sqlplus_command(distinct_command, distinct_query, distinct_output_file, "Distinct")

        # Clean the distinct output file to create prod_distinct_list
        prod_distinct_list = clean_distinct_file(distinct_output_file)  # Now prod_distinct_list will be a list
        categorized_list, _ = categorize_and_expand_items(prod_distinct_list)

        # Run prod and uat queries in the background
        run_background_queries()

    except Exception as e:
        logger.error(f"Error running distinct query: {e}")
        categorized_list = []

    if request.method == 'POST':
        blocked_item = request.POST.get('blocked_item')
        search_items = request.POST.getlist('search_items')

        # Expand the selected search items
        _, expanded_search_items = categorize_and_expand_items(prod_distinct_list, search_items)
        logger.info(f"User selected blocked item: {blocked_item} and expanded search items: {expanded_search_items}")

    context = {
        'result': result,
        'log_with_delays': log_with_delays,
        'prod_distinct_list': categorized_list
    }
    logger.info("Rendering binblocker.html with context data")
    return render(request, 'binblock/binblocker.html', context)

def run_sqlplus_command(command, query, output_file, server_name):
    """Run SQL*Plus command and capture the output."""
    logger.debug(f"Running SQL*Plus command on {server_name} with query: {query}")
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate(input=query.encode())
    if process.returncode != 0:
        logger.error(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")
        raise Exception(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")

    output_lines = [line for line in stdout.decode().splitlines() if line.strip()]
    with open(output_file, "w") as file:
        file.write("\n".join(output_lines) + "\n")
    logger.debug(f"SQL*Plus command completed on {server_name}. Output written to {output_file}")

def clean_file(file_path):
    """Clean the output file by removing unnecessary lines."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find indexes for relevant content
    start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
    end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

    # Clean lines between indexes
    cleaned_lines = [
        ''.join(char for char in line if char in string.printable).strip()
        for line in lines[start_index:end_index]
        if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'JSON_DATA'
    ]

    with open(file_path, 'w') as file:
        file.write("\n".join(cleaned_lines) + "\n")
       
def clean_distinct_file(file_path):
    """Clean the distinct output file and return as a list of cleaned items."""
    logger.debug(f"Cleaning output file for distinct query: {file_path}")
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
        end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

        cleaned_list = [
            ''.join(char for char in line if char in string.printable).strip()
            for line in lines[start_index:end_index]
            if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'DESCRIPTION'
        ]

        logger.info(f"Successfully cleaned distinct output file: {file_path} with {len(cleaned_list)} entries")
        return cleaned_list  # Return the cleaned lines as a list

    except Exception as e:
        logger.error(f"Error cleaning distinct output file {file_path}: {e}")
        return []  # Return an empty list in case of an error



def categorize_and_expand_items(distinct_list, search_items=None):
    """
    Categorize 'RUSSIAN' and 'SYRIA' variations into single categories for blocking 
    and expand them for search items if needed.
    """
    categorized_list = []
    expanded_items = []

    for item in distinct_list:
        if item.startswith("RUSSIAN"):
            if "RUSSIAN" not in categorized_list:
                categorized_list.append("RUSSIAN")
        elif item.startswith("SYRIA"):
            if "SYRIA" not in categorized_list:
                categorized_list.append("SYRIA")
        else:
            categorized_list.append(item)

    # If search_items is provided, expand "RUSSIAN" and "SYRIA" into their variations
    if search_items:
        for item in search_items:
            if item in ["RUSSIAN", "SYRIA"]:
                expanded_items.extend([i for i in distinct_list if i.startswith(item)])
            else:
                expanded_items.append(item)

    # Return categorized list for display and expanded items for search
    return categorized_list, expanded_items



def combine_json_data(file_path):
    """Read file and combine all JSON data into a single line."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    combined_data, current_json, in_json = [], [], False
    for line in lines:
        if '{' in line:
            in_json = True
            current_json.append(line.strip())
        elif '}' in line and in_json:
            in_json = False
            current_json.append(line.strip())
            combined_data.append(''.join(current_json))
            current_json = []
        elif in_json:
            current_json.append(line.strip())

    return combined_data

def remove_control_characters(s):
    """Remove control characters from a string."""
    return re.sub(r'[\x00-\x1F\x7F]', '', s)

def remove_null_values(d):
    """Recursively remove null values from a dictionary or list."""
    if isinstance(d, dict):
        return {k: remove_null_values(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        return [remove_null_values(item) for item in d if item is not None]
    return d

def clean_json_data(json_list):
    """Clean JSON data by removing control characters and null values."""
    cleaned_data = []
    for json_str in json_list:
        json_str = remove_control_characters(json_str)
        try:
            json_obj = json.loads(json_str)
            cleaned_json_obj = apply_length_checks(remove_null_values(json_obj))
            cleaned_data.append(json.dumps(cleaned_json_obj))
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {json_str}")
    return cleaned_data

def apply_length_checks(json_obj):
    """Apply length checks to JSON fields based on configuration."""
    length_config = {
        "LOWBIN": {"type": "CHAR", "length": 15},
        "HIGHBIN": {"type": "CHAR", "length": 15},
        "O_LEVEL": {"type": "NUMBER", "length": 1},
        "STATUS": {"type": "CHAR", "length": 1},
        "DESCRIPTION": {"type": "CHAR", "length": 50},
        "DESTINATION": {"type": "CHAR", "length": 3},
        "ENTITY_ID": {"type": "CHAR", "length": 1},
        "CARDPRODUCT": {"type": "CHAR", "length": 20},
        "NETWORK_DATA": {"type": "CHAR", "length": 10},
        "FILE_NAME": {"type": "CHAR", "length": 10},
        "FILE_VERSION": {"type": "CHAR", "length": 5},
        "FILE_DATE": {"type": "DATE", "length": None},
        "COUNTRY_CODE": {"type": "CHAR", "length": 3},
        "NETWORK_CONFIG": {"type": "CHAR", "length": 10},
        "BIN_LENGTH": {"type": "NUMBER", "length": 2}
    }

    for key, value in json_obj.items():
        if key in length_config:
            config = length_config[key]
            if config["type"] == "CHAR" and config["length"] is not None:
                json_obj[key] = str(value).ljust(config["length"])[:config["length"]]
            elif config["type"] == "NUMBER" and config["length"] is not None:
                json_obj[key] = str(value).zfill(config["length"])[:config["length"]]
    return json_obj

def json_to_sql_insert(json_obj, table_name):
    """Convert a JSON object to an SQL INSERT statement for a specified table."""
    keys = list(json_obj.keys())
    values = [
        f"TO_DATE('{value.strip()}', 'DD/MM/YYYY')" if key == "FILE_DATE" and value else 
        str(value) if key == "O_LEVEL" else 
        f"'{value}'" if isinstance(value, str) else str(value) 
        for key, value in json_obj.items()
    ]
    return f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({', '.join(values)});"

def convert_to_sql_insert_statements(cleaned_json_list, table_name):
    """Convert a list of cleaned JSON objects to SQL INSERT statements."""
    return [json_to_sql_insert(json.loads(json_str), table_name) for json_str in cleaned_json_list]

def save_sql_statements_to_file(statements, file_path):
    """Save SQL statements to a file."""
    with open(file_path, 'w') as file:
        file.write("\n".join(statements) + "\n")
