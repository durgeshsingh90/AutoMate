import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time  # Import time module

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Oracle connection details
username = 'oasis77'
password = 'ist0py'
dsn_alias = 'ISTU2_EQU'  # Alias defined in TNSNAMES.ORA

# Provide the path to the Oracle Instant Client libraries
oracle_client_path = r"C:\Oracle\Ora12c_64\BIN"  # Your Oracle Instant Client path

# Custom JSON encoder for handling specific data types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(CustomJSONEncoder, self).default(obj)

def initialize_connection():
    try:
        # Initialize the Oracle client with the provided library path
        oracledb.init_oracle_client(lib_dir=oracle_client_path)
        logging.info(f"Oracle client initialized from {oracle_client_path}")

        # Create a single connection using the TNS alias
        connection = oracledb.connect(user=username, password=password, dsn=dsn_alias)
        logging.info("Successfully connected to the database")
        return connection
    except oracledb.DatabaseError as e:
        logging.error(f"Database connection error: {e}")
        return None

def execute_query(query):
    query_result = {"query": query, "result": None, "error": None}
    connection = initialize_connection()
    if connection is None:
        query_result["error"] = "Unable to establish database connection"
        return query_result
    
    try:
        cursor = connection.cursor()
        try:
            # Execute the query
            cursor.execute(query.rstrip(';'))  # Remove the semicolon if present
            logging.info(f"Executed query: {query}")

            # Fetch all rows and column names with their data types
            rows = cursor.fetchall()
            metadata = cursor.description
            columns = [(col[0], col[1]) for col in metadata]

            # Convert rows to list of dictionaries for JSON output
            result = []
            for row in rows:
                row_dict = {}
                for idx, value in enumerate(row):
                    col_name, col_type = columns[idx]
                    # Handle datatype conversions based on col_type
                    if col_type in (oracledb.DB_TYPE_TIMESTAMP, oracledb.DB_TYPE_DATE):
                        if value is not None:
                            value = value.isoformat()
                    elif col_type == oracledb.DB_TYPE_RAW:
                        if value is not None:
                            value = base64.b64encode(value).decode('utf-8')
                    row_dict[col_name] = value
                result.append(row_dict)

            # Add result to query_result
            query_result["result"] = result

        finally:
            # Close the cursor
            cursor.close()
            connection.close()

    except oracledb.DatabaseError as e:
        # Handle connection errors
        error = e.args[0]
        logging.error(f"An error occurred: {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        query_result["error"] = str(e)

    return query_result

def execute_queries_with_new_connection(queries):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Set max_workers to 10 for 10 concurrent connections
        future_to_query = {executor.submit(execute_query, query): query for query in queries}
        for future in as_completed(future_to_query):
            query = future_to_query[future]

            # Track the start time
            start_time = time.time()

            try:
                result = future.result()
                results.append(result)
                logging.info(f"Query completed: {query}")
            except Exception as exc:
                logging.error(f"Query {query} generated an exception: {exc}")
                results.append({"query": query, "result": None, "error": str(exc)})

            # Track the end time
            end_time = time.time()

            # Calculate the elapsed time
            elapsed_time = end_time - start_time
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)

            # Print the elapsed time for the query
            print(f"Time taken for query: {query} - {int(hours)} hours {int(minutes)} minutes {seconds:.2f} seconds")

    return results

def execute_multiple_query_sets(query_sets):
    all_results = []
    with ThreadPoolExecutor(max_workers=len(query_sets)) as executor:
        future_to_query_set = {executor.submit(execute_queries_with_new_connection, queries): queries for queries in query_sets}
        for future in as_completed(future_to_query_set):
            query_set = future_to_query_set[future]
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as exc:
                logging.error(f"Query set {query_set} generated an exception: {exc}")
                all_results.append({"query_set": query_set, "result": None, "error": str(exc)})
    return all_results

# Your queries
query_set_1 = [
    """
    select refnum, issuer, msgtype, pcode, host_name, CARDPRODUCT, ISSUER_DATA, 
           ACQUIRER_DATA, amount, mask_pan, respcode, alpharesponsecode AS Scheme_response, 
           acquirer, filler2, filler3, termid, termloc AS MERCHANT, merchant_type, 
           chip_index, acceptorname, omni_log_dt_utc, acq_currency_code, iss_currency_code, 
           TXN_END_TIME, authnum, member_id, trantime, pos_condition_code 
    from oasis77.shclog 
    where msgtype like ('%130%') 
          and respcode in ('09') 
          and cardproduct in ('BCMC')
    """
]


# List of query sets
query_sets = [query_set_1]

# Track the start time
start_time = time.time()

# Execute the queries
results = execute_multiple_query_sets(query_sets)

# Track the end time
end_time = time.time()

# Calculate the total elapsed time
total_elapsed_time = end_time - start_time
total_hours, total_rem = divmod(total_elapsed_time, 3600)
total_minutes, total_seconds = divmod(total_rem, 60)

# Create the output filename based on the script filename
script_filename = os.path.splitext(os.path.basename(__file__))[0]
output_filename = f"{script_filename}_output.json"

# Write output to a JSON file
with open(output_filename, 'w') as output_file:
    json.dump(results, output_file, cls=CustomJSONEncoder, indent=4)

# Print out the results
print(json.dumps(results, cls=CustomJSONEncoder, indent=4))

# Print out the total elapsed time
print(f"Total time taken for all queries: {int(total_hours)} hours {int(total_minutes)} minutes {total_seconds:.2f} seconds")
