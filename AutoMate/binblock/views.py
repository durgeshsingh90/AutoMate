import os
import string
import logging
import threading
import subprocess
import json
import time
from django.shortcuts import render
from django.conf import settings

# Get the logger for the binblock app
logger = logging.getLogger('binblock')

# Define the output directory
OUTPUT_DIR = os.path.join(settings.BASE_DIR, 'binblock', 'output')

def run_sqlplus_command(command, query, output_file, server_name):
    """Run SQL*Plus command and capture the output."""
    logger.debug(f"Running SQL*Plus command on {server_name} with query: {query}")
    
    start_time = time.time()  # Start timing
    
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate(input=query.encode())
    
    end_time = time.time()  # End timing
    
    # Calculate time taken
    elapsed_time = end_time - start_time
    logger.info(f"SQL*Plus command on {server_name} completed in {elapsed_time:.2f} seconds.")

    if process.returncode != 0:
        logger.error(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")
        raise Exception(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")

    output_lines = [line for line in stdout.decode().splitlines() if line.strip()]
    with open(output_file, "w") as file:
        file.write("\n".join(output_lines) + "\n")
    
    logger.debug(f"SQL*Plus command completed on {server_name}. Output written to {output_file}")

def clean_file(file_path):
    """Clean the output file by removing unnecessary lines."""
    logger.debug(f"Starting clean_file for {file_path}")
    cleaned_lines = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Filter lines: remove those with control characters or unnecessary content
        for line in lines:
            if line.strip() and 'rows selected' not in line.lower():
                cleaned_lines.append(line.strip())

        # Write cleaned lines back to the file
        with open(file_path, 'w') as file:
            file.write("\n".join(cleaned_lines) + "\n")

        logger.info(f"Successfully cleaned output file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning file {file_path}: {e}")
    return cleaned_lines

def clean_distinct_file(file_path):
    """Clean the distinct output file and return as a list."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
    end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

    return [
        ''.join(char for char in line if char in string.printable).strip()
        for line in lines[start_index:end_index]
        if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'DESCRIPTION'
    ]

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

def combine_json_data(file_paths):
    """Combine JSON data from multiple files."""
    logger.debug(f"Starting combine_json_data for files: {file_paths}")
    combined_data = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                combined_data.extend(data)
        except Exception as e:
            logger.error(f"Error loading JSON data from {file_path}: {e}")
    logger.debug(f"Completed combine_json_data for files: {file_paths}")
    return combined_data

def remove_control_characters(s):
    """Remove control characters from strings."""
    logger.debug("Starting remove_control_characters")
    result = ''.join(ch for ch in s if ch.isprintable())
    logger.debug("Completed remove_control_characters")
    return result

def remove_null_values(d):
    """Remove null values from a dictionary."""
    logger.debug("Starting remove_null_values")
    cleaned_data = {k: v for k, v in d.items() if v is not None}
    logger.debug("Completed remove_null_values")
    return cleaned_data

def clean_json_data(json_list):
    """Clean JSON data by removing control characters and null values."""
    logger.debug("Starting clean_json_data")
    cleaned_data = []
    for entry in json_list:
        entry = {k: remove_control_characters(v) if isinstance(v, str) else v for k, v in entry.items()}
        entry = remove_null_values(entry)
        cleaned_data.append(entry)
    logger.debug("Completed clean_json_data")
    return cleaned_data

def apply_length_checks(data, length_constraints):
    """Apply length checks to JSON data based on constraints."""
    logger.debug("Starting apply_length_checks")
    checked_data = []
    for entry in data:
        for key, max_length in length_constraints.items():
            if key in entry and len(str(entry[key])) > max_length:
                logger.warning(f"Truncating {key} to {max_length} characters.")
                entry[key] = str(entry[key])[:max_length]
        checked_data.append(entry)
    logger.debug("Completed apply_length_checks")
    return checked_data

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
    logger.debug("Starting convert_to_sql_insert_statements")
    statements = [json_to_sql_insert(entry, table_name) for entry in cleaned_json_list]
    logger.debug("Completed convert_to_sql_insert_statements")
    return statements

def save_sql_statements_to_file(statements, file_path):
    """Save SQL INSERT statements to a file."""
    logger.debug(f"Starting save_sql_statements_to_file for {file_path}")
    try:
        with open(file_path, 'w') as file:
            file.write("\n".join(statements))
        logger.info(f"SQL statements saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving SQL statements to file {file_path}: {e}")
    logger.debug(f"Completed save_sql_statements_to_file for {file_path}")

def run_background_queries():
    """Run prod and uat queries in the background, clean the output files, and perform further processing."""
    logger.debug("Starting background queries for prod and uat")

    def run_query_and_process(command, query, output_file, server_name):
        try:
            logger.debug(f"Running query for {server_name}")
            run_sqlplus_command(command, query, output_file, server_name)
            
            cleaned_data = clean_file(output_file)
            logger.info(f"Cleaned data from {server_name}: {cleaned_data}")

            combined_data = combine_json_data([output_file])
            cleaned_combined_data = clean_json_data(combined_data)

            length_constraints = {'field1': 50, 'field2': 100}  # Example constraints
            checked_data = apply_length_checks(cleaned_combined_data, length_constraints)

            sql_statements = convert_to_sql_insert_statements(checked_data, 'your_table_name')
            sql_file_path = os.path.join(OUTPUT_DIR, f"{server_name.lower()}_insert_statements.sql")
            save_sql_statements_to_file(sql_statements, sql_file_path)

        except Exception as e:
            logger.error(f"Error running SQL query or processing data on {server_name}: {e}")

    prod_command = "sqlplus oasis77/ist0py@istu2_equ"
    uat_command = "sqlplus oasis77/ist0py@istu2_uat"
    query = "SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 4;"
    prod_output_file = os.path.join(OUTPUT_DIR, 'prod_output.json')
    uat_output_file = os.path.join(OUTPUT_DIR, 'uat_output.json')

    threading.Thread(target=run_query_and_process, args=(prod_command, query, prod_output_file, "Prod")).start()
    threading.Thread(target=run_query_and_process, args=(uat_command, query, uat_output_file, "UAT")).start()

def bin_blocking_editor(request):
    logger.info("Bin blocking editor view accessed")
    result = None
    log_with_delays = None
    prod_distinct_list = []

    try:
        distinct_command = "sqlplus oasis77/ist0py@istu2_equ"
        distinct_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"
        distinct_output_file = os.path.join(OUTPUT_DIR, 'prod_distinct_output.txt')
        run_sqlplus_command(distinct_command, distinct_query, distinct_output_file, "Distinct")

        prod_distinct_list = clean_file(distinct_output_file)
        categorized_list, _ = categorize_and_expand_items(prod_distinct_list)

        run_background_queries()

    except Exception as e:
        logger.error(f"Error running distinct query: {e}")
        categorized_list = []

    if request.method == 'POST':
        blocked_item = request.POST.get('blocked_item')
        search_items = request.POST.getlist('search_items')

        _, expanded_search_items = categorize_and_expand_items(prod_distinct_list, search_items)
        logger.info(f"User selected blocked item: {blocked_item} and expanded search items: {expanded_search_items}")

    context = {
        'result': result,
        'log_with_delays': log_with_delays,
        'prod_distinct_list': categorized_list
    }
    logger.info("Rendering binblocker.html with context data")
    return render(request, 'binblock/binblocker.html', context)
