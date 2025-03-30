# call_queries.py

import json
import logging
import os
from django.conf import settings
from oracledb_queries import execute_multiple_query_sets, CustomJSONEncoder

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def get_query_sets_from_json(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get("query_sets", [])
    except FileNotFoundError:
        logging.error(f"The file {file_path} was not found.")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return []

# Example function to call oracledb_queries with multiple sets of queries and get results
def get_all_query_results(query_sets):
    try:
        results = execute_multiple_query_sets(query_sets)
        # Convert results to JSON for easy viewing
        json_result = json.dumps(results, indent=2, cls=CustomJSONEncoder)
        logging.info(f"All query results: {json_result}")
        return results
    except Exception as e:
        logging.error(f"An error occurred while executing queries: {e}")
        return None

# Main logic
if __name__ == "__main__":
    # Define the JSON file path using settings and os.path
    json_file_path = os.path.join(settings.BASE_DIR, 'media', 'global', 'dbqueries', 'queries.json')
    
    # Get the query sets from the JSON file
    query_sets = get_query_sets_from_json(json_file_path)
    
    # If query sets are successfully loaded, proceed to get and print all query results
    if query_sets:
        results = get_all_query_results(query_sets)
    
        # Print the query results
        if results:
            print(json.dumps(results, indent=2, cls=CustomJSONEncoder))
    else:
        logging.error("No query sets found in the JSON file.")
