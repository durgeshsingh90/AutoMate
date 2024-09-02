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

# Output SQL statements
for statement in prod_sql_statements:
    print(statement)
