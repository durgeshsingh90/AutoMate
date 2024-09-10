import subprocess
import threading
import string
import re
import json

# Define the SQL*Plus commands and queries
uat_command = "sqlplus oasis77/ist0py@istu2_equ"
prod_command = "sqlplus oasis77/ist0py@istu2_equ"
query = "SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 4;"
distinct_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"

def run_sqlplus_command(command, query, output_file, server_name):
    """Run SQL*Plus command and capture the output."""
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate(input=query.encode())
    if process.returncode != 0:
        raise Exception(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")

    # Process and save the output
    output_lines = [line for line in stdout.decode().splitlines() if line.strip()]
    with open(output_file, "w") as file:
        file.write("\n".join(output_lines) + "\n")

def clean_file(file_path):
    """Clean the output file by removing unnecessary lines."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find indexes for relevant content
    start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
    end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

    # Clean lines between indexes
    cleaned_lines = [
        ''.join(char for char in line if char in string.printable).strip()
        for line in lines[start_index:end_index]
        if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'DESCRIPTION'
    ]

    with open(file_path, 'w') as file:
        file.write("\n".join(cleaned_lines) + "\n")

def clean_distinct_file(file_path):
    """Clean the distinct output file and return as a list."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find indexes for relevant content
    start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
    end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

    # Clean lines between indexes
    cleaned_lines = [
        ''.join(char for char in line if char in string.printable).strip()
        for line in lines[start_index:end_index]
        if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'DESCRIPTION'
    ]

    return cleaned_lines

def process_user_input():
    """Process multiline user input to generate cleaned bin ranges."""
    print("Enter the list of bin ranges (press Enter twice to finish):")
    user_input = iter(input, "")
    bin_list = [item.strip() for line in user_input for item in line.split(',') if item.strip()]
    bin_list = remove_duplicates_and_subsets(bin_list)
    bin_range, _ = combine_consecutives(bin_list)
    return bin_range

def remove_duplicates_and_subsets(bin_list):
    """Remove duplicate and subset bins."""
    bin_set = set(bin_list)
    sorted_bins = sorted(bin_set, key=lambda x: (len(x), x))
    return [bin for bin in sorted_bins if not any(bin.startswith(existing_bin) for existing_bin in sorted_bins if existing_bin != bin)]

def combine_consecutives(bins):
    """Combine consecutive bins into ranges."""
    bins = sorted(bins, key=lambda x: int(x.split('-')[0]))
    combined, i = [], 0

    while i < len(bins):
        start_bin = end_bin = bins[i]
        while i + 1 < len(bins) and int(bins[i + 1].split('-')[0]) == int(bins[i].split('-')[0]) + 1:
            end_bin = bins[i + 1]
            i += 1
        combined.append(f"{start_bin}-{end_bin}" if start_bin != end_bin else start_bin)
        i += 1

    return combined, i

def combine_json_data(file_path):
    """Read file and combine all JSON data into a single line."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    combined_data, current_json, in_json = [], [], False
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
    """Remove control characters from a string."""
    return re.sub(r'[\x00-\x1F\x7F]', '', s)

def remove_null_values(d):
    """Recursively remove null values from a dictionary or list."""
    if isinstance(d, dict):
        return {k: remove_null_values(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        return [remove_null_values(item) for item in d if item is not None]
    else:
        return d

def clean_json_data(json_list):
    """Clean JSON data by removing control characters and null values."""
    cleaned_data = []
    for json_str in json_list:
        json_str = remove_control_characters(json_str)
        try:
            json_obj = json.loads(json_str)
            cleaned_json_obj = remove_null_values(json_obj)
            cleaned_json_obj = apply_length_checks(cleaned_json_obj)
            cleaned_data.append(json.dumps(cleaned_json_obj))
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {json_str}")
    return cleaned_data

def apply_length_checks(json_obj):
    """Apply length checks to JSON fields based on configuration."""
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
                json_obj[key] = str(value).ljust(config["length"])[:config["length"]]
            elif config["type"] == "NUMBER" and config["length"] is not None:
                json_obj[key] = str(value).zfill(config["length"])[:config["length"]]
    return json_obj

def json_to_sql_insert(json_obj, table_name):
    """Convert a JSON object to an SQL INSERT statement for a specified table."""
    keys = list(json_obj.keys())
    values = [
        f"TO_DATE('{value.strip()}', 'DD/MM/YYYY')" if key == "FILE_DATE" and value else 
        str(value) if key == "O_LEVEL" else 
        f"'{value}'" if isinstance(value, str) else str(value) 
        for key, value in json_obj.items()
    ]
    return f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({', '.join(values)});"

def convert_to_sql_insert_statements(cleaned_json_list, table_name):
    """Convert a list of cleaned JSON objects to SQL INSERT statements."""
    return [json_to_sql_insert(json.loads(json_str), table_name) for json_str in cleaned_json_list]

def save_sql_statements_to_file(statements, file_path):
    """Save SQL statements to a file."""
    with open(file_path, 'w') as file:
        file.write("\n".join(statements) + "\n")

def calculate_bins_with_neighbors(processed_bins):
    """Calculate the start and end bins along with their neighbors."""
    result = []
    for bin_range in processed_bins:
        bin_range = bin_range.strip()
        if '-' in bin_range:
            start_bin, end_bin = bin_range.split('-')
            start_bin, end_bin = start_bin.strip().ljust(15, '0'), end_bin.strip().ljust(15, '9')
            neighbor_minus_1, neighbor_plus_1 = str(int(start_bin.strip()) - 1).ljust(15, '9'), str(int(end_bin.strip()) + 1).ljust(15, '0')
        else:
            start_bin = end_bin = bin_range.strip().ljust(15, '0')
            neighbor_minus_1, neighbor_plus_1 = str(int(bin_range.strip()) - 1).ljust(15, '9'), str(int(bin_range.strip()) + 1).ljust(15, '0')

        result.append((start_bin, end_bin, neighbor_minus_1, neighbor_plus_1))
    return result

# Create and start threads for UAT and production connections
threads = [
    threading.Thread(target=run_sqlplus_command, args=(uat_command, query, "uat_output.json", "UAT")),
    threading.Thread(target=run_sqlplus_command, args=(prod_command, query, "prod_output.json", "Prod")),
    threading.Thread(target=run_sqlplus_command, args=(uat_command, distinct_query, "uat_distinct_output.txt", "UAT")),
    threading.Thread(target=run_sqlplus_command, args=(prod_command, distinct_query, "prod_distinct_output.txt", "Prod"))
]
for thread in threads: thread.start()
for thread in threads: thread.join()

# Clean output files
clean_file('uat_output.json')
clean_file('prod_output.json')
uat_distinct_list = clean_distinct_file('uat_distinct_output.txt')
prod_distinct_list = clean_distinct_file('prod_distinct_output.txt')

# Combine, clean JSON data, and convert to SQL statements
uat_json_cleaned = clean_json_data(combine_json_data('uat_output.json'))
prod_json_cleaned = clean_json_data(combine_json_data('prod_output.json'))
table_name = "OASIS77.SHCEXTBINDB"
uat_sql_statements = convert_to_sql_insert_statements(uat_json_cleaned, table_name)
prod_sql_statements = convert_to_sql_insert_statements(prod_json_cleaned, table_name)

# Save SQL statements to files
save_sql_statements_to_file(uat_sql_statements, 'uat_sql_statements.sql')
save_sql_statements_to_file(prod_sql_statements, 'prod_sql_statements.sql')

# Process user input and calculate bins
processed_bins = process_user_input()
start_end = calculate_bins_with_neighbors(processed_bins)


########################Action#################
print ('prod_sql_statements')
print (prod_sql_statements)

print ('uat_sql_statements')
print (uat_sql_statements)

print ('start_end')
print (start_end)

print ('prod_distinct_list')
print (prod_distinct_list)


# prod_sql_statements
# ["INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('2221xxxxxxxxxxx', '222776zzzzzzzzz', x, 'A', 'Europay                                           ', '5xx', '*', 'Europay             ', 'EUFILE    ', '1.1x ', TO_DATE('1zxx-x1-x1Txx:xx:xx', 'DD/MM/YYYY'));", "INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222777xxxxxxxxx', '222777zzzzzzzzz', x, 'A', 'RUSSIAN-                                          ', '5xx', '*', 'RUSSIAN-
#  ', 'EUFILE    ', '1.1x ', TO_DATE('1zxx-x1-x1Txx:xx:xx', 'DD/MM/YYYY'));", "INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222778xxxxxxxxx', '222z68zzzzzzzzz', x, 'A', 'Europay                                           ', '5xx', '*', 'Europay             ', 'EUFILE    ', '1.1x ', TO_DATE('1zxx-x1-x1Txx:xx:xx', 'DD/MM/YYYY'));", "INSERT INTO OASIS77.SHCEXTBINDB (LOWBIN, HIGHBIN, O_LEVEL, STATUS, DESCRIPTION, DESTINATION, ENTITY_ID, CARDPRODUCT, FILE_NAME, FILE_VERSION, FILE_DATE) VALUES ('222z6zxxxxxxxxx', '222z6zzzzzzzzzz', x, 'A', 'RUSSIANE                                          ', '5xx', '*', 'RUSSIANE            ', 'EUFILE    ', '1.1x ', TO_DATE('1zxx-x1-x1TxxJSON_DATA:xx:xx', 'DD/MM/YYYY'));"]
# start_end
# [('321xxxxxxxxxxxx', '321xxxxxxxxxxxx', '32xzzzzzzzzzzzz', '322xxxxxxxxxxxx'), ('22457xxxxxxxxxx', '22461zzzzzzzzzz', '22456zzzzzzzzzz', '22462xxxxxxxxxx'), ('225xxxxxxxxxxxx', '226xxzzzzzzzzzz', '224zzzzzzzzzzzz', '226x1xxxxxxxxxx'), ('223232xxxxxxxxx', '223232xxxxxxxxx', '223231zzzzzzzzz', '223233xxxxxxxxx'), ('43z432xxxxxxxxx', '43z432xxxxxxxxx', '43z431zzzzzzzzz', '43z433xxxxxxxxx')]
# prod_distinct_list
# ['AMEX', 'BCMC', 'CUP', 'Diners', 'Discover', 'EasyCash', 'Europay', 'JCB', 'Maestro', 'RUSSIAN-', 'RUSSIANE', 'RUSSIANV', 'SYRIAMC', 'SYRIAV', 'VAML', 'VISA', 'VISASMS', 'VPAY']
