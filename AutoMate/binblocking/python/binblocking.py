import subprocess
import threading
import string
import re
import json

# Define the SQL*Plus commands and queries
uat_command = "sqlplus oasis77/ist0py@istu2_equ"
prod_command = "sqlplus oasis77/ist0py@istu2_equ"
query = "SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 4;"
distint_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"

# Function to run the SQL*Plus command and capture the output
def run_sqlplus_command(command, query, output_file, server_name):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate(input=query.encode())
    if process.returncode != 0:
        raise Exception(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")

    # Process the output to store it in a list
    output_lines = stdout.decode().splitlines()
    data_list = [line for line in output_lines if line.strip()]

    # Save the output to a file
    with open(output_file, "w") as file:
        for line in data_list:
            file.write(line + "\n")

# Function to clean the distinct file and return its content as a list
def clean_distinct_file(file_path):
    """
    Cleans the file by removing:
    - All lines from the start until the first occurrence of 'SQL>'.
    - All lines from the bottom until the last occurrence of 'SQL>'.
    - Any line containing 'rows selected'.
    - Any line containing only dashes or the word 'DESCRIPTION'.
    Returns:
    - A list of cleaned lines.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find the first occurrence of 'SQL>' and keep all lines after it
    start_index = 0
    for i, line in enumerate(lines):
        if 'SQL>' in line:
            start_index = i + 1
            break

    # Reverse search for the last occurrence of 'SQL>' and keep all lines before it
    end_index = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if 'SQL>' in lines[i]:
            end_index = i
            break

    # Extract the relevant content between the first and last occurrence of 'SQL>'
    cleaned_lines = lines[start_index:end_index]

    # Remove lines with 'rows selected', lines with only dashes, and 'DESCRIPTION'
    cleaned_lines = [
        ''.join(char for char in line if char in string.printable).strip()
        for line in cleaned_lines
        if 'rows selected' not in line.lower() and
        not line.strip().startswith('-') and
        line.strip() != 'DESCRIPTION'
    ]

    # Return the cleaned lines as a list
    return cleaned_lines

# Create threads for UAT and production connections
uat_thread = threading.Thread(target=run_sqlplus_command, args=(uat_command, query, "uat_output.json", "UAT"))
prod_thread = threading.Thread(target=run_sqlplus_command, args=(prod_command, query, "prod_output.json", "Prod"))

# Also create threads for running the distinct query
uat_distinct_thread = threading.Thread(target=run_sqlplus_command, args=(uat_command, distint_query, "uat_distinct_output.txt", "UAT"))
prod_distinct_thread = threading.Thread(target=run_sqlplus_command, args=(prod_command, distint_query, "prod_distinct_output.txt", "Prod"))

# Start the UAT and production threads
uat_thread.start()
prod_thread.start()
uat_distinct_thread.start()
prod_distinct_thread.start()

# Wait for all threads to complete
uat_thread.join()
prod_thread.join()
uat_distinct_thread.join()
prod_distinct_thread.join()

# Clean the distinct output files and store them as lists
uat_distinct_list = clean_distinct_file('uat_distinct_output.txt')
prod_distinct_list = clean_distinct_file('prod_distinct_output.txt')

# Print or use the cleaned lists as needed
print("UAT Distinct List:")
print(uat_distinct_list)

print("\nProduction Distinct List:")
print(prod_distinct_list)


########################################## Process json data#####################
import re
import json

def combine_json_data(file_path):
    """Reads a file and combines all JSON data within {} into a single line."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    combined_data = []
    current_json = []
    in_json = False

    for line in lines:
        if '{' in line:
            in_json = True
            current_json.append(line.strip())
        elif '}' in line and in_json:
            in_json = False
            current_json.append(line.strip())
            combined_data.append(''.join(current_json))
            current_json = []
        elif in_json:
            current_json.append(line.strip())

    return combined_data

def remove_control_characters(s):
    # Remove control characters using regex
    return re.sub(r'[\x00-\x1F\x7F]', '', s)

def remove_null_values(d):
    # Recursively remove null values from the dictionary or list
    if isinstance(d, dict):
        return {k: remove_null_values(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        return [remove_null_values(item) for item in d if item is not None]
    else:
        return d

def clean_json_data(json_list):
    cleaned_data = []
    for json_str in json_list:
        # Remove control characters
        json_str = remove_control_characters(json_str)

        # Parse JSON string to dictionary
        try:
            json_obj = json.loads(json_str)

            # Remove null values
            cleaned_json_obj = remove_null_values(json_obj)

            # Apply length checks
            cleaned_json_obj = apply_length_checks(cleaned_json_obj)

            # Convert back to JSON string
            cleaned_json_str = json.dumps(cleaned_json_obj)
            cleaned_data.append(cleaned_json_str)
        except json.JSONDecodeError:
            # Handle any JSON decoding errors if they occur
            print(f"Error decoding JSON: {json_str}")
    return cleaned_data

def apply_length_checks(json_obj):
    length_config = {
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

    for key, value in json_obj.items():
        if key in length_config:
            config = length_config[key]
            if config["type"] == "CHAR" and config["length"] is not None:
                # Ensure CHAR type fields are padded with spaces or truncated
                json_obj[key] = str(value).ljust(config["length"])[:config["length"]]
            elif config["type"] == "NUMBER" and config["length"] is not None:
                # Ensure NUMBER type fields are padded with zeros or truncated
                json_obj[key] = str(value).zfill(config["length"])[:config["length"]]
            # For DATE type or other fields, no changes needed
    return json_obj

def json_to_sql_insert(json_obj, table_name):
    """Converts a JSON object to an SQL INSERT statement for a specified table."""
    keys = []
    values = []

    for key, value in json_obj.items():
        keys.append(key)
        if key == "FILE_DATE" and value:
            # Convert FILE_DATE to SQL TO_DATE format
            formatted_date = f"TO_DATE('{value.strip()}', 'DD/MM/YYYY')"
            values.append(formatted_date)
        elif key == "O_LEVEL":
            # Ensure O_LEVEL is treated as a numeric value without quotes
            values.append(str(value))
        else:
            # Format other values
            if isinstance(value, str):
                values.append(f"'{value}'")
            else:
                values.append(str(value))

    keys_str = ', '.join(keys)
    values_str = ', '.join(values)
    sql_statement = f"INSERT INTO {table_name} ({keys_str}) VALUES ({values_str});"
    return sql_statement

def convert_to_sql_insert_statements(cleaned_json_list, table_name):
    """Converts a list of cleaned JSON objects to a list of SQL INSERT statements."""
    sql_statements = []
    for json_str in cleaned_json_list:
        json_obj = json.loads(json_str)
        sql_statement = json_to_sql_insert(json_obj, table_name)
        sql_statements.append(sql_statement)
    return sql_statements

# Combine the JSON data from both files
uat_json = combine_json_data('uat_output.json')
prod_json = combine_json_data('prod_output.json')

# Clean both uat_json and prod_json lists
uat_json_cleaned = clean_json_data(uat_json)
prod_json_cleaned = clean_json_data(prod_json)

# Set the table name
table_name = "OASIS77.SHCEXTBINDB"

# Convert cleaned JSON data to SQL INSERT statements
uat_sql_statements = convert_to_sql_insert_statements(uat_json_cleaned, table_name)
prod_sql_statements = convert_to_sql_insert_statements(prod_json_cleaned, table_name)

def save_sql_statements_to_file(statements, file_path):
    # Save SQL statements to a file
    with open(file_path, 'w') as file:
        for statement in statements:
            file.write(statement + '\n')

# Save SQL statements to files
save_sql_statements_to_file(uat_sql_statements, 'uat_sql_statements.sql')
save_sql_statements_to_file(prod_sql_statements, 'prod_sql_statements.sql')

# print ('SQL Insert Statement')
# Output SQL statements
# for statement in prod_sql_statements:
#     print(statement)

def remove_duplicates_and_subsets(bin_list):
    """
    Remove duplicate and subset bins from the list.
    """
    # Convert list to a set to remove duplicates
    bin_set = set(bin_list)

    # Sort bins first by length and then lexicographically
    sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
    final_bins = []

    # Remove bins that are subsets of any other bin
    for bin in sorted_bins:
        if not any(bin.startswith(existing_bin) for existing_bin in final_bins):
            final_bins.append(bin)

    return final_bins

def combine_consecutives(bins):
    """
    Combine consecutive bin ranges into single ranges.
    """
    combined = []
    consecutive_count = 0
    i = 0

    # Ensure bins are sorted numerically
    bins = sorted(bins, key=lambda x: int(x.split('-')[0]))

    while i < len(bins):
        current_bin = bins[i]
        start_bin = current_bin
        end_bin = current_bin

        # Check for consecutive bins directly within this loop
        while i + 1 < len(bins):
            next_bin = bins[i + 1]
            try:
                # Check if the next bin is consecutive
                if len(current_bin) == len(next_bin) and int(next_bin.split('-')[0]) == int(current_bin.split('-')[0]) + 1:
                    end_bin = next_bin
                    current_bin = next_bin
                    i += 1
                    consecutive_count += 1
                else:
                    break
            except ValueError:
                # If there's an error in checking consecutive bins, break the loop
                break

        # Append combined bin range or single bin
        combined.append(f"{start_bin}-{end_bin}" if start_bin != end_bin else start_bin)
        i += 1

    return combined, consecutive_count

def calculate_bins_with_neighbors(processed_bins):
    """
    Calculate the start and end bins for each processed bin range along with neighboring bins.
    """
    result = []

    for bin_range in processed_bins:
        bin_range = bin_range.strip()  # Clean up any extra spaces

        # Check if the bin_range is a range
        if '-' in bin_range:
            start_bin, end_bin = bin_range.split('-')
            start_bin = start_bin.strip().ljust(15, '0')  # Pad the start_bin with '0' to make it 15 characters
            end_bin = end_bin.strip().ljust(15, '9')    # Pad the end_bin with '9' to make it 15 characters

            # Calculate neighbors for the start and end bins
            start_bin_int = int(start_bin.strip())
            end_bin_int = int(end_bin.strip())
            neighbor_minus_1 = str(start_bin_int - 1).ljust(15, '9')  # Decrement start_bin and pad with '9'
            neighbor_plus_1 = str(end_bin_int + 1).ljust(15, '0')   # Increment end_bin and pad with '0'
        else:
            start_bin = end_bin = bin_range.strip()
            start_bin = start_bin.ljust(15, '0')  # Pad the bin with '0' to make it 15 characters
            end_bin = end_bin.ljust(15, '9')     # Pad the bin with '9' to make it 15 characters

            # Calculate neighbors for a single bin
            bin_int = int(bin_range.strip())
            neighbor_minus_1 = str(bin_int - 1).ljust(15, '9')  # Decrement bin and pad with '9'
            neighbor_plus_1 = str(bin_int + 1).ljust(15, '0')   # Increment bin and pad with '0'

        result.append((start_bin, end_bin, neighbor_minus_1, neighbor_plus_1))

    return result



def process_user_input():
    """
    Process multiline user input to generate cleaned bin ranges.
    Returns:
        list: A list of processed bin ranges.
    """
    print("Enter the list of bin ranges (press Enter twice to finish):")

    # Take multiline input
    user_input = []
    while True:
        line = input()
        if line == "":  # End input on empty line
            break
        user_input.append(line.strip())

    # Flatten the list into a single list of bin ranges
    bin_list = []
    for line in user_input:
        bin_list.extend(line.split(','))

    # Remove extra spaces
    bin_list = [item.strip() for item in bin_list if item.strip()]

    # Remove duplicates and subsets
    bin_list = remove_duplicates_and_subsets(bin_list)

    # Combine consecutive ranges
    bin_range, _ = combine_consecutives(bin_list)

    # Return the cleaned-up bin ranges
    return bin_range

# Run the script and process the results
if __name__ == "__main__":
    processed_bins = process_user_input()
    # print("Processed Bin Ranges:")
    # print(processed_bins)

    # Calculate the start and end bins
    start_end = calculate_bins_with_neighbors(processed_bins)
    # print("Calculated Bins (Start and End):")
    # print(start_end)

###################################Start checking bin range in sql insert statement############
# print ('uat_sql_statements')
# print (uat_sql_statements[1])

# print ('prod_sql_statements')
# print (prod_sql_statements)

# print ('processed_bins')
# print (processed_bins)

# print ('start_end')
# print (start_end)
# ############################last step 
print ('prod_sql_statements')
print (prod_sql_statements)

print ('start_end')
print (start_end)

# prod_sql_statements
# ["INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222100000000000', '222776999999999', 0, 'A', 'Europay                                           ', '500', '*', 'Europay             ', 'EUFILE    ', '1.10 ', TO_DATE('1900-01-01T00:00:00', 'DD/MM/YYYY'));", "INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222777000000000', '222777999999999', 0, 'A', 'RUSSIAN-                                          ', '500', '*', 'RUSSIAN-            ', 'EUFILE    ', '1.10 ', TO_DATE('1900-01-01T00:00:00', 'DD/MM/YYYY'));", "INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222778000000000', '222968999999999', 0, 'A', 'Europay                                           ', '500', '*', 'Europay             ', 'EUFILE    ', '1.10 ', TO_DATE('1900-01-01T00:00:00', 'DD/MM/YYYY'));", "INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222969000000000', '222969999999999', 0, 'A', 'RUSSIANE                                          ', '500', '*', 'RUSSIANE            ', 'EUFILE    ', '1.10 ', TO_DATE('1900-01-01T00:00:00', 'DD/MM/YYYY'));"]
# start_end
# [('321000000000000', '321999999999999', '320999999999999', '322000000000000'), ('224570000000000', '224619999999999', '224569999999999', '224620000000000'), ('225000000000000', '226009999999999', '224999999999999', '226010000000000'), ('223232000000000', '223232999999999', '223231999999999', '223233000000000'), ('439432000000000', '439432999999999', '439431999999999', '439433000000000')]
