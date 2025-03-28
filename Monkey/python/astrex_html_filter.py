import os
from datetime import datetime
from bs4 import BeautifulSoup

def condition_to_expression(conditions_list):
    # Convert the conditions list into a Python expression string
    conditions_str = " ".join(conditions_list)
    conditions_str = conditions_str.replace("'", "")
    conditions_str = conditions_str.replace('AND', 'and')
    conditions_str = conditions_str.replace('OR', 'or')
    conditions_str = conditions_str.replace('NOT', 'not')
    return conditions_str

def match_conditions(value, conditions_list):
    # Dynamically generate the boolean expression to check all conditions
    expr = condition_to_expression(conditions_list)
    expr = expr.replace("and", " and ").replace("or", " or ").replace("not", " not ")
    variables = set(expr.split())
    
    for var in variables:
        if var not in {"and", "or", "not"}:
            # Replace variable names with True/False based on presence in the value
            expr = expr.replace(var, str(var in value))

    return eval(expr)

def extract_matching_tables(html, conditions_list):
    soup = BeautifulSoup(html, 'lxml')
    styles = soup.find_all('style')
    tables = soup.find_all('table')

    matching_tables = []

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 6:
                value = cells[6].text.strip()
                if match_conditions(value, conditions_list):
                    matching_tables.append(str(table))
                    break

    # Combine styles and matching tables
    output_html = ""
    for style in styles:
        output_html += str(style)
    for table in matching_tables:
        output_html += table
    return output_html

# Define the path to your input HTML file
# html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7106-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer_.html"
html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer_.html"

# Read your input HTML file
with open(html_file_path, 'r', encoding='utf-8') as file:
    input_html = file.read()

# Define your search conditions as a list
conditions_list = ["'00000367631'"]

# Extract matching tables
output_html = extract_matching_tables(input_html, conditions_list)

# If no tables match, inform the user and do not create an empty file
if not output_html.strip():
    print("No tables matched the given conditions.")
else:
    # Generate the output filename with suffix and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(html_file_path)
    output_filepath = f"{base}_filtered_{timestamp}{ext}"

    # Write the output to a new HTML file
    with open(output_filepath, 'w', encoding='utf-8') as file:
        file.write(output_html)

    print(f"Filtered HTML saved as {output_filepath}")
