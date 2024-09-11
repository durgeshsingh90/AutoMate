import string
import logging
import threading
import subprocess
from django.shortcuts import render

# Get the logger for the binblock app
logger = logging.getLogger('binblock')

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
    """Clean the output JSON file and return the cleaned list of lines."""
    logger.debug(f"Cleaning output file: {file_path}")
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        cleaned_lines = [line.strip() for line in lines if line.strip() and 'rows selected' not in line.lower()]

        with open(file_path, 'w') as file:
            file.write("\n".join(cleaned_lines) + "\n")

        logger.info(f"Successfully cleaned output file: {file_path}")
        return cleaned_lines  # Return the cleaned lines as a list

    except Exception as e:
        logger.error(f"Error cleaning file {file_path}: {e}")
        return []  # Return an empty list in case of an error

def categorize_and_expand_items(distinct_list, search_items=None):
    """Categorize 'RUSSIAN' and 'SYRIA' variations into single categories for blocking 
       and expand them for search items if needed."""
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

def run_background_queries():
    """Run prod and uat queries in the background and clean the output files."""
    logger.debug("Starting background queries for prod and uat")

    def run_query_and_clean(command, query, output_file, server_name):
        try:
            run_sqlplus_command(command, query, output_file, server_name)
            clean_file(output_file)  # Clean the output file after running the query
        except Exception as e:
            logger.error(f"Error running SQL query or cleaning file on {server_name}: {e}")

    prod_command = "sqlplus oasis77/ist0py@istu2_equ"
    uat_command = "sqlplus oasis77/ist0py@istu2_uat"
    query = "SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 4;"
    prod_output_file = 'prod_output.json'
    uat_output_file = 'uat_output.json'

    # Start threads for prod and uat queries
    threading.Thread(target=run_query_and_clean, args=(prod_command, query, prod_output_file, "Prod")).start()
    threading.Thread(target=run_query_and_clean, args=(uat_command, query, uat_output_file, "UAT")).start()

def bin_blocking_editor(request):
    logger.info("Bin blocking editor view accessed")
    result = None
    log_with_delays = None
    prod_distinct_list = []

    try:
        # Run the distinct query first
        distinct_command = "sqlplus oasis77/ist0py@istu2_equ"
        distinct_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"
        distinct_output_file = 'prod_distinct_output.txt'
        run_sqlplus_command(distinct_command, distinct_query, distinct_output_file, "Distinct")

        # Clean the output file to create prod_distinct_list
        prod_distinct_list = clean_file(distinct_output_file)  # Now prod_distinct_list will be a list
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

        # Further processing with blocked_item and expanded_search_items
        # (e.g., filter results, modify SQL statements, etc.)

    context = {
        'result': result,
        'log_with_delays': log_with_delays,
        'prod_distinct_list': categorized_list
    }
    logger.info("Rendering binblocker.html with context data")
    return render(request, 'binblock/binblocker.html', context)
    