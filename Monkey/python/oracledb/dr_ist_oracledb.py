import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Oracle connection details
username = 'F94GDOS'
password = 'Ireland2025!'
dsn_alias = 'A4PCDO8001.ESH.PAR_IST'  # Alias defined in TNSNAMES.ORA

# Provide the path to the Oracle Instant Client libraries
oracle_client_path = r"C:\Oracle\Ora12c_64\BIN"

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
        oracledb.init_oracle_client(lib_dir=oracle_client_path)
        logging.info(f"Oracle client initialized from {oracle_client_path}")
        connection = oracledb.connect(user=username, password=password, dsn=dsn_alias)
        logging.info("Successfully connected to the database")
        return connection
    except oracledb.DatabaseError as e:
        logging.error(f"Database connection error: {e}")
        return None

def fetch_data_in_batches(cursor, batch_size=1000):
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        yield rows

def execute_query(query):
    query_result = {"query": query, "result": [], "error": None}
    connection = initialize_connection()
    if connection is None:
        query_result["error"] = "Unable to establish database connection"
        return query_result

    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query.rstrip(';'))
            logging.info(f"Executed query: {query}")

            metadata = cursor.description
            columns = [col[0] for col in metadata]

            for rows in fetch_data_in_batches(cursor):
                for row in rows:
                    row_dict = {columns[idx]: value for idx, value in enumerate(row)}
                    query_result["result"].append(row_dict)
        finally:
            cursor.close()
            connection.close()
    except oracledb.DatabaseError as e:
        error = e.args[0]
        logging.error(f"An error occurred: {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        query_result["error"] = str(e)

    return query_result

def execute_queries_with_new_connection(queries):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {executor.submit(execute_query, query): query for query in queries}
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            start_time = time.time()

            try:
                result = future.result()
                results.append(result)
                logging.info(f"Query completed: {query}")
            except Exception as exc:
                logging.error(f"Query {query} generated an exception: {exc}")
                results.append({"query": query, "result": None, "error": str(exc)})

            end_time = time.time()
            elapsed_time = end_time - start_time
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
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

# # Your queries
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
select  transaction_log_id,systems_trace_audit_number,message_type_identifier, host_start_time, host_end_time, destination_key, transaction_amount as amount ,internal_response_code_rsp as respcode, destination_response_code_rsp as alpharespcode,retrieval_reference_number as REFNUM,authorization_id_code as AUTHCODE,  acquiring_inst_id_code_in as ACQUIRER, card_acceptor_merchant_name as psp, extractValue(ADDITIONAL_FIELDS,'//response/bcmc_reject_code[1]' ) as REJECT_CODE, transaction_complete, transaction_declined, card_acceptor_id_code as TERMLOC, acceptor_key, switch_key, pan, extractValue(ADDITIONAL_FIELDS,'//response/bcmc_reject_code[1]' ) as REJECT_CODE

from novate.transaction_log

WHERE 
  MSGTYPE LIKE '%130%'
  AND CARDPRODUCT LIKE '%BCMC%'
  AND RESPCODE IN ( '09')
  AND refnum IN ('506320844443')
  AND OMNI_LOG_DT_UTC BETWEEN TO_DATE('07-Apr-2025 00:00:00', 'DD-MON-YYYY HH24:MI:SS')
                          AND TO_DATE('07-Apr-2025 23:59:59', 'DD-MON-YYYY HH24:MI:SS')

"""]
query_sets = [query_set_1]

# Track the start time
start_time = time.time()

# Execute the queries
results = execute_multiple_query_sets(query_sets)

# Track the end time
end_time = time.time()
total_elapsed_time = end_time - start_time
total_hours, total_rem = divmod(total_elapsed_time, 3600)
total_minutes, total_seconds = divmod(total_rem, 60)

# Create output filename based on the script filename
script_filename = os.path.splitext(os.path.basename(__file__))[0]
output_filename = f"{script_filename}_output.json"

# Write output to a JSON file
with open(output_filename, 'w') as output_file:
    json.dump(results, output_file, cls=CustomJSONEncoder, indent=4)

# Print out the results
print(json.dumps(results, cls=CustomJSONEncoder, indent=4))

# Print total elapsed time
print(f"Total time taken for all queries: {int(total_hours)} hours {int(total_minutes)} minutes {total_seconds:.2f} seconds")
