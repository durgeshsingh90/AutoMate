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
username = 'F94GDOS'
password = 'Ireland2025!'
dsn_alias = 'A5PCDO8001.EQU.IST'  # Alias defined in TNSNAMES.ORA

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
            # print(f"Time taken for query: {query} - {int(hours)} hours {int(minutes)} minutes {seconds:.2f} seconds")

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


# query_set_1 = [""" select * from oasis77.card_scheme """]
# query_set_2 = [""" select * from oasis77.institution """]
# query_set_3 = [""" select * from oasis77.acq_profile """]
# query_set_4 = [""" select * from oasis77.iss_profile """]
# query_set_5 = [""" select * from oasis77.inst_profile """]
# query_set_6 = [""" select * from oasis77.shcbin """]
# query_set_7 = [""" select * from oasis77.shckeys """]
# query_set_8 = [""" select * from oasis77.shcextbindb """]
# query_set_9 = [""" select * from oasis77.istreplaytab """]
# query_set_10 = [""" select * from oasis77.pinverparm """]
# query_set_11 = [""" select * from oasis77.inst_business_day """]
# query_set_12 = [""" select * from oasis77.omni_multiroutedb """]
# query_set_13 = [""" select * from oasis77.omni_rcc """]
# query_set_14 = [""" select * from oasis77.rc_mapping """]
# query_set_15 = [""" select * from oasis77.acq_entity """]
# query_set_16 = [""" select * from oasis77.acq_entity_address """]
# query_set_17 = [""" select * from oasis77.master_address """]
# query_set_18 = [""" select * from oasis77.alt_merchant_id """]
# query_set_19 = [""" select * from oasis77.terminal """]
# query_set_20 = [""" select * from oasis77.merchant_type """]
# query_set_21 = [""" select * from oasis77.entity_level """]
# query_set_22 = [""" select * from oasis77.pos_msg_format """]
# query_set_23 = [""" select * from oasis77.pos_msg_brand """]
# query_set_24 = [""" select * from oasis77.pos_term_type """]
# query_set_25 = [""" select * from oasis77.pos_term_keys """]
# query_set_26 = [""" select * from oasis77.pos_shc2pos_rc """]
# query_set_27 = [""" select * from oasis77.allowance """]
# query_set_28 = [""" select * from oasis77.allw_floor_lim """]
# query_set_29 = [""" select * from oasis77.allw_pos_format """]
# query_set_30 = [""" select * from oasis77.allw_mcc """]
# query_set_31 = [""" select * from oasis77.istcurpnt """]
# query_set_32 = [""" select * from oasis77.istcurr """]
# query_set_33 = [""" select * from oasis77.global_seq_ctrl """]
# query_set_34 = [""" select * from oasis77.global_value_ctrl """]
# query_set_35 = [""" select * from oasis77.shcbin_counter """]
# query_set_36 = [""" select * from oasis77.IST_SINGLETON """]
# query_set_37 = [""" select * from oasis77.PROVINCE """]
# query_set_38 = [""" select * from oasis77.LANGUAGE """]
# query_set_39 = [""" select * from oasis77.CURRENCY_CODE """]
# query_set_40 = [""" select * from oasis77.COUNTRY """]
# query_set_41 = [""" select * from oasis77.MCC """]
 
# query_sets = [
#     query_set_1,
#     query_set_2,
#     query_set_3,
#     query_set_4,
#     query_set_5,
#     query_set_6,
#     query_set_7,
#     query_set_8,
#     query_set_9,
#     query_set_10,
#     query_set_11,
#     query_set_12,
#     query_set_13,
#     query_set_14,
#     query_set_15,
#     query_set_16,
#     query_set_17,
#     query_set_18,
#     query_set_19,
#     query_set_20,
#     query_set_21,
#     query_set_22,
#     query_set_23,
#     query_set_24,
#     query_set_25,
#     query_set_26,
#     query_set_27,
#     query_set_28,
#     query_set_29,
#     query_set_30,
#     query_set_31,
#     query_set_32,
#     query_set_33,
#     query_set_34,
#     query_set_35,
#     query_set_36,
#     query_set_37,
#     query_set_38,
#     query_set_39,
#     query_set_40,
#     query_set_41
# ]


query_set_1 = [""" 
select
  acquiring_inst_id_code_in, destination_key,message_type_identifier,
substr(pan,1,6) || '****'|| substr(pan, -4) as pan, transaction_amount, retrieval_reference_number,INTERNAL_RESPONSE_CODE_RSP,destination_key,
host_start_time as DATE_TIME, card_acceptor_id_code, card_acceptor_merchant_name 
--extractValue(ADDITIONAL_FIELDS,'//response/bcmc_reject_code[1]' ) as REJECT_CODE
FROM NOVATE.TRANSACTION_LOG 
where 
host_start_time     between to_date('07-Apr-2025 00:01:00', 'dd-mon-yyyy hh24:mi:ss')               and to_date('07-APR-2025 23:59:00', 'dd-mon-yyyy hh24:mi:ss') 
--and message_type_identifier = '0230'
and RETRIEVAL_REFERENCE_NUMBER like '506320844443'
--INTERNAL_RESPONSE_CODE_RSP like '%rigi%'
--and INTERNAL_RESPONSE_CODE_RSP in ('unable-to-locate-record')
"""]
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
