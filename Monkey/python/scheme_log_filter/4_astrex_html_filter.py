import os
import multiprocessing
import time
import queue
import json
import logging
from lxml import etree

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processing.log"),
        logging.StreamHandler()
    ]
)

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

def sanitize_filename(filename):
    return filename.replace("'", "").replace(' ', '_').replace(",", "")

def extract_style(html):
    parser = etree.HTMLParser()
    tree = etree.HTML(html, parser)
    styles = tree.xpath('//style')
    if styles:
        return etree.tostring(styles[0], pretty_print=True, encoding='unicode')
    return ""

def extract_matching_tables(html, conditions_list):
    parser = etree.HTMLParser()
    tree = etree.HTML(html, parser)
    
    tables = tree.xpath('//table')
    matching_tables = []

    for table in tables:
        rows = table.xpath('.//tr')
        for row in rows:
            cells = row.xpath('.//td')
            if len(cells) > 6:
                value = cells[6].text.strip()
                if match_conditions(value, conditions_list):
                    matching_tables.append(etree.tostring(table, pretty_print=True, encoding='unicode'))
                    break

    output_html = ""
    for table in matching_tables:
        output_html += table
    return output_html

def process_file(file_path, conditions_list, output_filepath):
    logging.info(f"Processing file: {file_path} with conditions: {conditions_list}")
    with open(file_path, 'r', encoding='utf-8') as file:
        input_html = file.read()
    
    output_html = extract_matching_tables(input_html, conditions_list)
    
    if not output_html.strip():
        logging.info(f"No tables matched the given conditions in file: {file_path}")
        return False

    with open(output_filepath, 'a', encoding='utf-8') as file:
        file.write(output_html)
    
    logging.info(f"Filtered HTML appended to {output_filepath}")
    return True

def worker(task_queue, output_filepath, match_queue):
    match_found = False
    while True:
        try:
            file_path, conditions_list = task_queue.get_nowait()
            if process_file(file_path, conditions_list, output_filepath):
                match_found = True
        except queue.Empty:
            break
    match_queue.put(match_found)

def process_files_condition_by_condition(json_path, conditions_lists, num_processes=10):
    start_time = time.time()

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    style_html = ""
    file_paths_dict = {}
    for condition in conditions_lists:
        file_paths_dict[frozenset(condition)] = []

    part0_file_path = None
    
    for file in data["files"]:
        file_name = file["file_name"]
        de032_value_counts = file["de032_value_counts"]
        if part0_file_path is None and "part0" in file_name:
            part0_file_path = file_name

        for condition in conditions_lists:
            condition_str = frozenset(condition)
            if any(c in de032_value_counts for c in condition):
                file_paths_dict[condition_str].append(file_name)
    
    if part0_file_path:
        with open(part0_file_path, 'r', encoding='utf-8') as file:
            style_html = extract_style(file.read())

    output_dir = os.path.dirname(json_path)

    for conditions_list in conditions_lists:
        logging.info(f"Processing with conditions: {conditions_list}")

        conditions_str = "_".join(sanitize_filename(condition) for condition in conditions_list)
        base_name = os.path.basename(part0_file_path).split('__part')[0] if part0_file_path else "output"
        output_filename = f"{base_name}_filtered_{conditions_str}.html"

        # Use the directory of the JSON file for output
        output_filepath = os.path.join(output_dir, output_filename)
        
        # Ensure we write the style at the beginning
        with open(output_filepath, 'w', encoding='utf-8') as file:
            # file.write("<html><head>")
            file.write(style_html)
            # file.write("</head><body>")
        
        task_queue = multiprocessing.Queue()
        match_queue = multiprocessing.Queue()

        for file_path in file_paths_dict[frozenset(conditions_list)]:
            task_queue.put((file_path, conditions_list))

        processes = []
        for _ in range(num_processes):
            p = multiprocessing.Process(target=worker, args=(task_queue, output_filepath, match_queue))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
        
        match_found = any(match_queue.get() for _ in processes)

        if not match_found:
            if os.path.exists(output_filepath):
                os.remove(output_filepath)
                logging.info(f"Deleted {output_filepath} as no tables matched the conditions")
            continue

        # with open(output_filepath, 'a', encoding='utf-8') as file:
            # file.write("</body></html>")

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    logging.info(f"Processing completed in {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")

if __name__ == '__main__':
    # Path to the JSON file
    json_path = r"C:\Users\f94gdos\Desktop\2025-03-31\unique_bm32.json"

    # Define your search conditions as a list of lists
    conditions_lists = [
        ["004642"],  # Condition 1
        ["014206"]   # Condition 2
        # Add more conditions as needed
    ]

    # Process the files condition by condition in parallel
    process_files_condition_by_condition(json_path, conditions_lists)

