import os
from datetime import datetime
from bs4 import BeautifulSoup

def condition_to_expression(conditions_list):
    conditions_str = " ".join(conditions_list)
    conditions_str = conditions_str.replace("'", "")
    conditions_str = conditions_str.replace('AND', 'and')
    conditions_str = conditions_str.replace('OR', 'or')
    conditions_str = conditions_str.replace('NOT', 'not')
    return conditions_str

def match_conditions(value, conditions_list):
    expr = condition_to_expression(conditions_list)
    expr = expr.replace("and", " and ").replace("or", " or ").replace("not", " not ")
    variables = set(expr.split())

    for var in variables:
        if var not in {"and", "or", "not"}:
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

    output_html = "".join(str(style) for style in styles)
    output_html += "".join(matching_tables)
    return output_html

def filter_html_by_conditions(html_file_path, conditions_list):
    """
    Filters HTML tables based on conditions and writes to a new file.

    Args:
        html_file_path (str): Path to the input HTML file.
        conditions_list (list): List of conditions as strings.

    Returns:
        str: Output file path if matches found, otherwise None.
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            input_html = file.read()

        output_html = extract_matching_tables(input_html, conditions_list)

        if not output_html.strip():
            print("No tables matched the given conditions.")
            return None

        sanitized_conditions = "_".join(conditions_list).replace(" ", "_").replace("/", "_")
        base, ext = os.path.splitext(html_file_path)
        output_filepath = f"{base}_filtered_{sanitized_conditions}{ext}"


        with open(output_filepath, 'w', encoding='utf-8') as file:
            file.write(output_html)

        print(f"Filtered HTML saved as {output_filepath}")
        return output_filepath

    except Exception as e:
        print(f"Error processing HTML file: {e}")
        return None
