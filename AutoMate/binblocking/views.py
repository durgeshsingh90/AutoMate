from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .db_utils import run_sqlplus_query
from .models import DatabaseConnection
from django.http import HttpResponseRedirect
import mysql.connector  # Import MySQL connector
import logging
import json
from datetime import date
import re
# Get an instance of a logger
logger = logging.getLogger(__name__)

@csrf_exempt
def process_bins(request):
    #logger.info("Started processing bins")
    if request.method == 'POST':
        bins = request.POST.get('bins', '')
        bin_list = bins.splitlines()
        total_values = len(bin_list)
        
        
        #logger.info(f"Total input values: {total_values}")
        
        # Remove duplicates
        bin_set = set(bin_list)
        duplicates_removed = total_values - len(bin_set)
        #logger.info(f"Duplicates removed: {duplicates_removed}")
        
        # Sort bins
        sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
        
        # Remove subsets
        final_bins = []
        for bin in sorted_bins:
            if not any(bin.startswith(existing_bin) for existing_bin in final_bins):
                final_bins.append(bin)
        
        unique_values = len(final_bins)
        #logger.info(f"Unique values after removing subsets: {unique_values}")
        
        # Combine consecutive numbers
        combined_bins, consecutive_count = combine_consecutives(final_bins)
        #logger.info(f"Consecutive values combined: {consecutive_count}")
        
        # Store the processed data in session
        processed_bins = '\n'.join(combined_bins)
        request.session['processed_bins'] = processed_bins
        #logger.info("Processed bins stored in session")
        
        # Call query_view to continue processing
        return query_view(request)

    else:
        #logger.info("Received a non-POST request")
        return render(request, 'binblocking/binblocker.html')

def display_processed_bins(request):
    processed_bins = request.session.get('processed_bins', '')
    sorted_production_rows_copy = request.session.get('sorted_production_rows_copy', '')  # Assuming you have this data in the session

    return render(request, 'binblocking/binblocker_output.html', {
        'processed_bins': processed_bins
    })

def combine_consecutives(bins):
    #logger.info("Combining consecutive bins")
    combined = []
    consecutive_count = 0
    i = 0
    while i < len(bins):
        current_bin = bins[i]
        start_bin = current_bin
        end_bin = current_bin
        while i + 1 < len(bins) and is_consecutive(current_bin, bins[i + 1]):
            end_bin = bins[i + 1]
            current_bin = bins[i + 1]
            i += 1
            consecutive_count += 1
        combined.append(f"{start_bin}-{end_bin}" if start_bin != end_bin else start_bin)
        i += 1
    #logger.info(f"Total consecutive bins combined: {consecutive_count}")
    return combined, consecutive_count

def is_consecutive(bin1, bin2):
    return len(bin1) == len(bin2) and int(bin2) == int(bin1) + 1


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()  # Convert date to a string in ISO format (YYYY-MM-DD)
        return super().default(obj)


from datetime import datetime

def print_processed_data(processed_bins, production_data):
    """Print processed_bins and production_data to the console, and check for matches."""
    print("Processed Bins:")
    print(processed_bins)
    
    # Convert production_data into a list of rows
    production_rows = production_data.splitlines()

    # Create a copy of production_rows
    production_rows_copy = production_rows.copy()

    # Split processed_bins into a list
    processed_bin_list = processed_bins.splitlines()
    
    # Initialize variables to store the new Russian entry details
    russian_lowbin = None
    russian_highbin = None
    modified_row_1 = None

    # Get today's date in the format YYYY-MM-DD
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Loop through each bin or range in processed_bins and check against production_data
    for bin_range in processed_bin_list:
        bin_range = bin_range.strip()  # Clean up any extra spaces
        found = False

        # Check if the processed_bin is a range
        if '-' in bin_range:
            start_bin, end_bin = bin_range.split('-')
            start_bin = start_bin.strip()
            end_bin = end_bin.strip()
        else:
            start_bin = end_bin = bin_range.strip()

        for i, row in enumerate(production_rows):
            try:
                # Extract the LOWBIN and HIGHBIN from the row (assuming fixed format as in your example)
                values_part = row.split('VALUES (')[1]
                lowbin = values_part.split(',')[0].strip()
                highbin = values_part.split(',')[1].strip()

                # First Modified Row based on the start_bin
                modified_highbin = (start_bin + '0' * (len(highbin) - len(start_bin)))
                modified_highbin = str(int(modified_highbin) - 1).zfill(len(highbin))
                modified_row = row.replace(f"{highbin}", f"{modified_highbin}")
                production_rows_copy[i]=modified_row

                # Modified Row 1 with LOWBIN as (end_bin + 1) and keeping original HIGHBIN
                incremented_end_bin = str(int(end_bin) + 1)
                modified_lowbin_1 = incremented_end_bin + '0' * (len(lowbin) - len(incremented_end_bin))
                modified_row_1 = row.replace(f"{lowbin}", f"{modified_lowbin_1}")
                production_rows_copy.append(modified_row_1)
                print(f"Bin range {start_bin} - {end_bin} found in row {i + 1}:")
                print(f"Original row: {row}")
                print(f"Modified Row: {modified_row}")
                found = True
                break
            except (IndexError, ValueError) as e:
                print(f"Error processing row {i + 1}: {e}")
                continue
            
        if not found:
            print(f"Bin range {start_bin} - {end_bin} not found in production data.")
        
        # Store the processed number for the Russian entry creation based on the end_bin
        if not russian_lowbin and not russian_highbin:
            # Calculate the required length of the BIN (assuming it's the same as the existing lowbin length)
            required_length = len(lowbin)

            # Create the lowbin by appending zeros to the end of the start_bin
            russian_lowbin = start_bin + '0' * (required_length - len(start_bin))
            
            # Create the highbin by appending nines to the end of the end_bin
            russian_highbin = end_bin + '9' * (required_length - len(end_bin))

    # After processing, add the new Russian entry if we have valid data
    if russian_lowbin and russian_highbin:
        russian_insert_statement = f"INSERT INTO PROD_SHCEXTBINDB (LOWBIN, HIGHBIN, DESCRIPTION, BIN_LENGTH, CARDPRODUCT, COUNTRY_CODE, DESTINATION, ENTITY_ID, FILE_DATE, FILE_NAME, FILE_VERSION, NETWORK_CONFIG, NETWORK_DATA, LEVEL, STATUS) VALUES ({russian_lowbin}, {russian_highbin}, 'Russian', None, 'Russian', None, '500', None, {today_date}, 'EUFILE', '1.10', None, None, 0, 'B');"
        print("New Russian Entry:")
        print(russian_insert_statement)
        production_rows_copy.append(russian_insert_statement)
    
    print ('production_rows_copy')
    for i in production_rows_copy:
        print (i)

    # Extract LOWBIN and sort the SQL statements
    sorted_production_rows_copy = sorted(production_rows_copy, key=lambda x: int(re.search(r"VALUES \((\d+),", x).group(1)))

    print ('sorted_production_rows_copy')
    # Display the sorted SQL statements
    for i in sorted_production_rows_copy:
        print(i)

def query_view(request):
    #logger.info('Attempting to fetch PROD and UAT database connection details')
    
    prod_insert_statements = []
    uat_insert_statements = []

    try:
        # Fetch PROD and UAT database connection details
        prod_connection = DatabaseConnection.objects.get(environment='PROD')
        uat_connection = DatabaseConnection.objects.get(environment='UAT')
        #logger.info(f"Fetched database connections for PROD: {prod_connection.name}, UAT: {uat_connection.name}")

        # Run queries and generate insert statements for both PROD and UAT
        prod_insert_statements = generate_insert_statements(prod_connection)
        uat_insert_statements = generate_insert_statements(uat_connection)

    except DatabaseConnection.DoesNotExist as e:
        #logger.error(f"No connection details found for environment: {str(e)}")
        return render(request, 'binblocking/binblocker_output.html', {
            'error': f"No connection details found for environment: {str(e)}",
            'processed_bins': request.session.get('processed_bins', '')
        })

    except Exception as e:
        #logger.error(f"Unexpected error: {e}")
        return render(request, 'binblocking/binblocker_output.html', {
            'error': str(e),
            'processed_bins': request.session.get('processed_bins', '')
        })
   # Get processed bins from session
    processed_bins = request.session.get('processed_bins', '')

    # Print processed_bins and production_data to console
    print_processed_data(processed_bins, '\n'.join(prod_insert_statements))
    # Include both processed bins and SQL insert statements in the rendering context
    return render(request, 'binblocking/binblocker_output.html', {
        'production_data': '\n'.join(prod_insert_statements),
        'uat_data': '\n'.join(uat_insert_statements),
        'processed_bins': request.session.get('processed_bins', '')
    })

def generate_insert_statements(connection):
    """Generate SQL INSERT statements for the data retrieved from the database."""
    try:
        conn = mysql.connector.connect(
            host=connection.DatabaseTNS,
            user=connection.username,
            password=connection.password,
            database=connection.environment.lower()
        )
        query = f"SELECT * FROM {connection.table_name} ORDER BY LOWBIN"
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        insert_statements = []
        for row in data:
            # Reorder the columns
            ordered_columns = ['LOWBIN', 'HIGHBIN', 'DESCRIPTION']
            remaining_columns = [col for col in row.keys() if col not in ordered_columns]
            final_columns = ordered_columns + remaining_columns

            columns = ', '.join(final_columns)
            values = ', '.join(
                [f"'{str(row[col]).replace('\'', '\'\'')}'" if isinstance(row[col], str) else str(row[col]) for col in final_columns]
            )
            insert_statement = f"INSERT INTO {connection.table_name} ({columns}) VALUES ({values});"
            insert_statements.append(insert_statement)

        #logger.debug(f"Generated insert statements for {connection.environment}: {insert_statements}")
        return insert_statements

    except mysql.connector.Error as err:
        #logger.error(f"Database error for {connection.environment}: {err}")
        return []

    except Exception as e:
        #logger.error(f"Unexpected error for {connection.environment}: {e}")
        return []

