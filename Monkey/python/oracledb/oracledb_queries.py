# oracledb_queries.py

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

def execute_query(connection, query):
    query_result = {}
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

def execute_queries_with_new_connection(queries):
    connection = initialize_connection()
    if connection:
        results = []
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            future_to_query = {executor.submit(execute_query, connection, query): query for query in queries}
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
    return []

def execute_multiple_query_sets(query_sets):
    with ThreadPoolExecutor(max_workers=len(query_sets)) as executor:
        future_to_query_set = {executor.submit(execute_queries_with_new_connection, queries): queries for queries in query_sets}
        all_results = []
        for future in as_completed(future_to_query_set):
            query_set = future_to_query_set[future]
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as exc:
                logging.error(f"Query set {query_set} generated an exception: {exc}")
    return all_results
