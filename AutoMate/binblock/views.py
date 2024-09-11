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

def clean_distinct_file(file_path):
    """Clean the distinct output file and return as a list."""
    logger.debug(f"Cleaning output file: {file_path}")
    with open(file_path, 'r') as file:
        lines = file.readlines()

    start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
    end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

    cleaned_list = [
        ''.join(char for char in line if char in string.printable).strip()
        for line in lines[start_index:end_index]
        if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'DESCRIPTION'
    ]

    logger.debug(f"Cleaned output file: {file_path} with {len(cleaned_list)} entries")
    return cleaned_list

def run_sql_queries_in_threads():
    """Run SQL queries using multithreading."""
    logger.debug("Starting SQL queries in multiple threads")
    prod_command = "sqlplus oasis77/ist0py@istu2_equ"
    distinct_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"
    output_file = 'prod_distinct_output.txt'

    threads = [
        threading.Thread(target=run_sqlplus_command, args=(prod_command, distinct_query, output_file, "Prod"))
    ]

    for thread in threads:
        thread.start()
        logger.debug(f"Started thread {thread.name} for SQL*Plus command")

    for thread in threads:
        thread.join()
        logger.debug(f"Completed thread {thread.name} for SQL*Plus command")

def bin_blocking_editor(request):
    logger.info("Bin blocking editor view accessed")
    result = None
    log_with_delays = None
    prod_distinct_list = []

    try:
        # Run SQL queries in threads and process the output
        run_sql_queries_in_threads()
        prod_distinct_list = clean_distinct_file('prod_distinct_output.txt')
    except Exception as e:
        logger.error(f"Error running SQL queries: {e}")

    # Handle user selections
    if request.method == 'POST':
        blocked_item = request.POST.get('blocked_item')
        search_items = request.POST.getlist('search_items')
        logger.info(f"User selected blocked item: {blocked_item} and search items: {search_items}")

        # Further processing with blocked_item and search_items
        # (e.g., filter results, modify SQL statements, etc.)

    context = {
        'result': result,
        'log_with_delays': log_with_delays,
        'prod_distinct_list': prod_distinct_list
    }
    logger.info("Rendering binblocker.html with context data")
    return render(request, 'binblock/binblocker.html', context)
