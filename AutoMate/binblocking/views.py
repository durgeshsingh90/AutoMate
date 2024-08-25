from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .db_utils import run_sqlplus_query
from .models import DatabaseConnection
from django.http import HttpResponseRedirect
import mysql.connector  # Import MySQL connector
import logging
import json
from datetime import date

# Get an instance of a logger
logger = logging.getLogger(__name__)

@csrf_exempt
def process_bins(request):
    logger.info("Started processing bins")
    if request.method == 'POST':
        bins = request.POST.get('bins', '')
        bin_list = bins.splitlines()
        total_values = len(bin_list)
        
        logger.info(f"Total input values: {total_values}")
        
        # Remove duplicates
        bin_set = set(bin_list)
        duplicates_removed = total_values - len(bin_set)
        logger.info(f"Duplicates removed: {duplicates_removed}")
        
        # Sort bins
        sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
        
        # Remove subsets
        final_bins = []
        for bin in sorted_bins:
            if not any(bin.startswith(existing_bin) for existing_bin in final_bins):
                final_bins.append(bin)
        
        unique_values = len(final_bins)
        logger.info(f"Unique values after removing subsets: {unique_values}")
        
        # Combine consecutive numbers
        combined_bins, consecutive_count = combine_consecutives(final_bins)
        logger.info(f"Consecutive values combined: {consecutive_count}")
        
        # Store the processed data in session
        processed_bins = '\n'.join(combined_bins)
        request.session['processed_bins'] = processed_bins
        logger.info("Processed bins stored in session")
        
        # Call query_view to continue processing
        return query_view(request)

    else:
        logger.info("Received a non-POST request")
        return render(request, 'binblocking/binblocker.html')

def display_processed_bins(request):
    processed_bins = request.session.get('processed_bins', '')
    return render(request, 'binblocking/binblocker_output.html', {
        'processed_bins': processed_bins
    })

def combine_consecutives(bins):
    logger.info("Combining consecutive bins")
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
    logger.info(f"Total consecutive bins combined: {consecutive_count}")
    return combined, consecutive_count

def is_consecutive(bin1, bin2):
    return len(bin1) == len(bin2) and int(bin2) == int(bin1) + 1


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()  # Convert date to a string in ISO format (YYYY-MM-DD)
        return super().default(obj)


def query_view(request):
    logger.info('Attempting to fetch PROD and UAT database connection details')
    
    prod_insert_statements = []
    uat_insert_statements = []

    try:
        # Fetch PROD and UAT database connection details
        prod_connection = DatabaseConnection.objects.get(environment='PROD')
        uat_connection = DatabaseConnection.objects.get(environment='UAT')
        logger.info(f"Fetched database connections for PROD: {prod_connection.name}, UAT: {uat_connection.name}")

        # Run queries and generate insert statements for both PROD and UAT
        prod_insert_statements = generate_insert_statements(prod_connection)
        uat_insert_statements = generate_insert_statements(uat_connection)

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

        logger.debug(f"Generated insert statements for {connection.environment}: {insert_statements}")
        return insert_statements

    except mysql.connector.Error as err:
        logger.error(f"Database error for {connection.environment}: {err}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error for {connection.environment}: {e}")
        return []
