from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import DatabaseConnection
from datetime import datetime
import subprocess  
import logging
import re
import json
# Get an instance of a logger
logger = logging.getLogger(__name__)

@csrf_exempt
def process_bins(request):
    """
    Process the bins from the request, remove duplicates and subsets, and combine consecutive ranges.
    """
    logger.info("Processing bins request started.")
    
    if request.method == 'POST':
        # Extract bins from POST request
        bins = request.POST.get('bins', '')
        bin_list = bins.splitlines()
        logger.debug(f"Received bins input: {bins}")
        
        # Remove duplicates and subsets
        unique_bins = remove_duplicates_and_subsets(bin_list)
        logger.info(f"Total unique bins after removing duplicates and subsets: {len(unique_bins)}")
        
        # Combine consecutive bins
        combined_bins, consecutive_count = combine_consecutives(unique_bins)
        logger.info(f"Total consecutive bins combined: {consecutive_count}")
        
        # Store processed bins in session
        request.session['processed_bins'] = '\n'.join(combined_bins)
        logger.info("Processed bins stored in session successfully.")
        
        # Redirect to the next view for further processing
        return query_view(request)
    else:
        logger.warning("Received a non-POST request for processing bins.")
        return render(request, 'binblocking/binblocker.html')

def remove_duplicates_and_subsets(bin_list):
    """
    Remove duplicate and subset bins from the list.
    """
    logger.debug("Removing duplicates and subsets from the bins.")
    
    # Convert list to a set to remove duplicates
    bin_set = set(bin_list)
    
    # Sort bins first by length and then lexicographically
    sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
    final_bins = []
    
    # Remove bins that are subsets of any other bin
    for bin in sorted_bins:
        if not any(bin.startswith(existing_bin) for existing_bin in final_bins):
            final_bins.append(bin)
    logger.info(f"Duplicates and subsets removed. Unique bins count: {len(final_bins)}")
    return final_bins

def display_processed_bins(request):
    """
    Display the processed bins stored in session.
    """
    processed_bins = request.session.get('processed_bins', '')
    logger.debug("Displaying processed bins.")
    return render(request, 'binblocking/binblocker_output.html', {
        'processed_bins': processed_bins
    })

def combine_consecutives(bins):
    """
    Combine consecutive bin ranges into single ranges.
    """
    logger.info("Combining consecutive bins.")
    combined = []
    consecutive_count = 0
    i = 0
    while i < len(bins):
        current_bin = bins[i]
        start_bin = current_bin
        end_bin = current_bin
        
        # Check for consecutive bins
        while i + 1 < len(bins) and is_consecutive(current_bin, bins[i + 1]):
            end_bin = bins[i + 1]
            current_bin = bins[i + 1]
            i += 1
            consecutive_count += 1
        
        # Append combined bin range or single bin
        combined.append(f"{start_bin}-{end_bin}" if start_bin != end_bin else start_bin)
        i += 1
    logger.info(f"Total consecutive bins combined: {consecutive_count}")
    return combined, consecutive_count

def is_consecutive(bin1, bin2):
    """
    Check if two bins are consecutive.
    """
    logger.debug(f"Checking if {bin1} and {bin2} are consecutive.")
    return len(bin1) == len(bin2) and int(bin2) == int(bin1) + 1

def print_processed_data(processed_bins, production_data):
    # Convert production data into a list of rows
    production_rows = production_data.splitlines()
    production_rows_copy = production_rows.copy()

    # Split processed_bins into a list
    processed_bin_list = processed_bins.splitlines()
    modified_row_1 = None
    modified = False  # Flag to indicate if any modification has been made

    # Initialize lowbin to handle cases where it might not be set inside the loop
    lowbin = None

    # Get today's date in the format YYYY-MM-DD
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Loop through each bin or range in processed_bins and check against production_data
    for bin_range in processed_bin_list:
        bin_range = bin_range.strip()  # Clean up any extra spaces

        # Check if the processed_bin is a range
        if '-' in bin_range:
            start_bin, end_bin = bin_range.split('-')
            start_bin = start_bin.strip()
            start_bin = start_bin.ljust(15, '0')
            end_bin = end_bin.strip()
            end_bin = end_bin.ljust(15, '9')

        else:
            start_bin = end_bin = bin_range.strip()
            start_bin = start_bin.ljust(15, '0')
            end_bin = end_bin.ljust(15, '9')
        
        logger.debug(f"bin_range: {bin_range}")
        logger.debug(f"start_bin: {start_bin}, end_bin: {end_bin}")
        # Process production rows and modify as required
        for i, row in enumerate(production_rows):
            # Ensure the row contains 'VALUES ('
            if 'VALUES (' not in row:
                continue
            
            # Extract the LOWBIN and HIGHBIN from the row
            values_part = row.split('VALUES (')[1]
            try:
                lowbin = values_part.split(',')[0].strip()
                highbin = values_part.split(',')[1].strip()
                logger.debug(f"Starting debug")
                logger.debug(f"lowbin: {lowbin}")
                logger.debug(f"highbin: {highbin}")
                logger.debug(f"Comparing start_bin: {start_bin} with lowbin: {lowbin} and highbin: {highbin}")
                logger.debug(f"Entering the loop for row {i}")
                logger.debug(f"Type start_bin: {type(int(start_bin))}")
                logger.debug(f"Type lowbin: {type(int(lowbin))}")
                logger.debug(f"Type highbin: {type(int(highbin))}")

                logger.debug(f"int(start_bin): {int(start_bin)}, int(lowbin): {int(lowbin)}, int(highbin): {int(highbin)}")
                if int(start_bin) >= int(lowbin) and int(start_bin) <= int(highbin):
                # if int(lowbin) <= int(start_bin) <= int(highbin):

                    logger.debug(f"Condition met for start_bin: {start_bin}")
                    logger.debug(f"Working")
                    modified_highbin = (start_bin + '0' * (len(highbin) - len(start_bin)))
                    modified_highbin = str(int(modified_highbin) - 1).zfill(len(highbin))
                    modified_row = row.replace(f"{highbin}", f"{modified_highbin}")
                    production_rows_copy[i] = modified_row

                    # Modify lowbin for end_bin range
                    incremented_end_bin = str(int(end_bin) + 1)
                    modified_lowbin_1 = incremented_end_bin + '0' * (len(lowbin) - len(incremented_end_bin))
                    modified_row_1 = row.replace(f"{lowbin}", f"{modified_lowbin_1}")
                    production_rows_copy.append(modified_row_1)
                    logger.debug(f"modified_row: {modified_row}, modified_row_1: {modified_row_1}")
                    logger.debug(f"production_rows_copy: {production_rows_copy}")
                    modified = True  # Set the flag to true since modification was done
                    break
                
            except (IndexError, ValueError) as e:
                # Handle potential parsing or conversion errors gracefully
                print(f"Error processing row {i + 1}: {e}")
                continue

    # After processing, add the new Russian entry if we have valid data and modifications were made
    if modified and start_bin and end_bin:
        russian_insert_statement = (
            f"INSERT INTO oasis77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, NETWORK_DATA, FILE_NAME, FILE_VERSION, FILE_DATE, COUNTRY_CODE, NETWORK_CONFIG, BIN_LENGTH) "
            f"VALUES ('{start_bin}', '{end_bin}', '0', 'A', 'RUSSIAN-                                          ', '500', '*', 'RUSSIAN-            ', NULL, 'EUFILE    ', '1.10    ', '{today_date}', NULL, NULL, NULL);"
        )
        production_rows_copy.append(russian_insert_statement)

    # Sort the SQL statements by LOWBIN
    sorted_production_rows_copy = sorted(production_rows_copy, key=lambda x: int(re.search(r"VALUES \((\d+),", x).group(1)) if re.search(r"VALUES \((\d+),", x) else float('inf'))

    return sorted_production_rows_copy


def query_view(request):
    """
    View function to handle database queries and generate insert statements.
    """
    logger.info('Query view execution started.')
    
    prod_insert_statements = []
    uat_insert_statements = []

    try:
        # Fetch PROD and UAT database connection details
        prod_connection = DatabaseConnection.objects.get(environment='PROD')
        uat_connection = DatabaseConnection.objects.get(environment='UAT')
        logger.info(f"Fetched database connections for PROD: {prod_connection.name}, UAT: {uat_connection.name}")

        # Run queries and generate insert statements for both PROD and UAT
        prod_insert_statements = connect_to_oracle_sqlplus(prod_connection)
        uat_insert_statements = connect_to_oracle_sqlplus(uat_connection)

    except DatabaseConnection.DoesNotExist as e:
        logger.error(f"No connection details found for environment: {str(e)}")
        return render(request, 'binblocking/binblocker_output.html', {
            'error': f"No connection details found for environment: {str(e)}",
            'processed_bins': request.session.get('processed_bins', '')
        })

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return render(request, 'binblocking/binblocker_output.html', {
            'error': str(e),
            'processed_bins': request.session.get('processed_bins', '')
        })

    # Get processed bins from session
    processed_bins = request.session.get('processed_bins', '')

    # Print processed bins and production data to console
    sorted_production_rows_copy = print_processed_data(processed_bins, '\n'.join(prod_insert_statements))

    logger.info('Query view executed successfully.')
    # Include both processed bins and SQL insert statements in the rendering context
    return render(request, 'binblocking/binblocker_output.html', {
        'production_data': '\n'.join(prod_insert_statements),
        'uat_data': '\n'.join(uat_insert_statements),
        'processed_bins': processed_bins,
        'insert_statement': '\n'.join(sorted_production_rows_copy),
    })



def connect_to_oracle_sqlplus(connection):
    """
    Generate SQL INSERT statements for the data retrieved from the Oracle database using SQL*Plus.
"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Ensure debug messages are shown
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info(f"Generating SQL insert statements for environment: {connection.environment}")
    
    try:
        # Construct the SQL*Plus connection string
        conn_str = f"{connection.username}/{connection.password}@{connection.DatabaseTNS}"
        logger.debug(f"Connection string: {conn_str}")

        # Construct the query to fetch data
        query = f"SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 2;"
        logger.debug(f"SQL query: {query}")

        # Command to execute using SQL*Plus
        sqlplus_command = f"sqlplus {conn_str}"
        logger.debug(f"SQL*Plus command: {sqlplus_command}")

        # Run the SQL query using subprocess
        result = subprocess.run(sqlplus_command, input=query, text=True, capture_output=True, shell=True)
        logger.debug(f"SQL*Plus result: {result}")

        # Log the query used for login
        logger.info(f"Login query: {sqlplus_command}")

        # Check for errors in SQL*Plus execution
        if result.returncode != 0 or "ORA-" in result.stderr:
            logger.error(f"SQL*Plus error for {connection.environment}: {result.stderr}")
            logger.info("Login failed")
            return []

        # Log the output from SQL*Plus
        output = result.stdout.strip().splitlines()
        logger.debug(f"Output from SQL*Plus: {output}")

        # Combine lines to form complete JSON objects
        json_lines = []
        current_json = ""
        inside_json = False
        for line in output:
            if line.startswith('{'):
                inside_json = True
                current_json = line
            elif inside_json:
                current_json += line
                if line.endswith('}'):
                    json_lines.append(current_json)
                    inside_json = False
        logger.debug(f"Combined JSON lines: {json_lines}")

        # Clean control characters from JSON lines
        cleaned_json_lines = [re.sub(r'[\x00-\x1F\x7F]', '', line) for line in json_lines]
        logger.debug(f"Cleaned JSON lines: {cleaned_json_lines}")

        # Define the length and data type for each column
        column_definitions = {
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

        # Convert the output to SQL INSERT statements
        insert_statements = []
        for line in cleaned_json_lines:
            logger.debug(f"Processing line: {line}")
            try:
                # Parse each line as JSON
                data = json.loads(line)
                logger.debug(f"Parsed JSON data: {data}")

                # Log the final JSON data
                logger.info(f"Final JSON data: {json.dumps(data, indent=2)}")

                # Extract columns and values, treating all values as strings
                columns = ', '.join(data.keys())
                values = []
                for key, value in data.items():
                    col_def = column_definitions.get(key, {"type": "CHAR", "length": 255})
                    if col_def["type"] == "CHAR" and value is not None:
                        value = str(value).ljust(col_def["length"])
                    elif col_def["type"] == "NUMBER" and value is not None:
                        value = str(value).rjust(col_def["length"], '0')
                    elif col_def["type"] == "DATE" and value is not None:
                        value = f"TO_DATE('{value}', 'YYYY-MM-DD\"T\"HH24:MI:SS')"
                    else:
                        value = 'NULL'
                    values.append(f"'{value}'" if value != 'NULL' else value)

                values_str = ', '.join(values)

                # Construct the SQL INSERT statement
                insert_statement = f"INSERT INTO {connection.table_name} ({columns}) VALUES ({values_str});"
                insert_statements.append(insert_statement)
                logger.debug(f"Generated SQL INSERT statement: {insert_statement}")
                logger.info(f"Generated SQL INSERT statement: {insert_statement}")

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                logger.error(f"Problematic line: {line}")
                continue

        logger.info("Generated SQL INSERT Statements:")
        for statement in insert_statements:
            logger.info(statement)

        return insert_statements

    except Exception as e:
        logger.error(f"Error while connecting to Oracle using SQL*Plus for {connection.environment}: {e}")
        return []
