import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

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

def execute_query(connection, query, connection_lock):
    query_result = {}
    try:
        with connection_lock:
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
                query_result[query] = result

            finally:
                # Close the cursor
                cursor.close()

    except oracledb.DatabaseError as e:
        # Handle connection errors
        error = e.args[0]
        logging.error(f"An error occurred: {error.code}: {error.message}")

        if error.isrecoverable:
            logging.error("The error is recoverable. You might want to retry the connection.")
        else:
            logging.error("The error is not recoverable. Check your configuration and network.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return query_result

def execute_queries_with_connection(queries):
    connection = initialize_connection()
    if connection:
        connection_lock = Lock()
        results = []
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            future_to_query = {executor.submit(execute_query, connection, query, connection_lock): query for query in queries}
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result()
                    results.append(result)
                    logging.info(f"Query completed: {query}")
                except Exception as exc:
                    logging.error(f"Query {query} generated an exception: {exc}")
        # Close the connection
        connection.close()
        logging.info("Database connection closed")
        return results

# Main logic
if __name__ == "__main__":
    # Define sets of SQL queries
    queries_set_1 = [
        "select * from oasis77.shclog where refnum in ('434013101234') order by omni_log_dt_utc desc",
        # "select * from oasis77.shclog where refnum in ('433913103057') order by omni_log_dt_utc desc",
        # Add more queries here as needed for set 1
    ]

    # queries_set_2 = [
    #     # Add queries for the second set here
    #     "select * from oasis77.shclog where refnum in ('433913103059') order by omni_log_dt_utc desc",
    #     "select * from oasis77.shclog where refnum in ('433913103060') order by omni_log_dt_utc desc"
    # ]
    
    # queries_set_3 = [
    #     # Add queries for the third set here
    #     "select * from oasis77.shclog where refnum in ('433913103061') order by omni_log_dt_utc desc",
    #     "select * from oasis77.shclog where refnum in ('433913103062') order by omni_log_dt_utc desc"
    # ]

    # Execute each set of queries with their own connection and collect the results
    all_results = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [
            executor.submit(execute_queries_with_connection, queries_set_1),
            # executor.submit(execute_queries_with_connection, queries_set_2),
            # executor.submit(execute_queries_with_connection, queries_set_3)
        ]
        for future in as_completed(futures):
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as exc:
                logging.error(f"Query set generated an exception: {exc}")

    # Print all collected results
    json_result = json.dumps(all_results, indent=2, cls=CustomJSONEncoder)
    print (json_result)
    logging.info(f"All query results: {json_result}")
