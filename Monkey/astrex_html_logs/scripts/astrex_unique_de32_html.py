from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime
import uuid
import multiprocessing

def process_file_chunk(html_chunk):
    soup = BeautifulSoup(html_chunk, 'lxml')
    de032_values = []
    de007_dates = []

    for row in soup.find_all('tr'):
        cell1 = row.find('td', class_='cell1norm')
        if cell1:
            cell1_text = cell1.get_text(strip=True)
            # Check for DE032 values
            if 'DE032' in cell1_text:
                cell7 = row.find('td', class_='cell7')
                if cell7:
                    de032_values.append(cell7.get_text(strip=True))
            # Extract DE007 date-time
            if 'DE007' in cell1_text:
                cell8 = row.find('td', class_='cell8norm')
                if cell8:
                    date_str = cell8.get_text(strip=True)
                    if "Date and time of [" in date_str:
                        date_str = date_str.split("[")[-1].strip("]")
                        try:
                            de007_dates.append(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
                        except ValueError as e:
                            print(f"Error parsing date: {e}")

    return de032_values, de007_dates

def extract_de032_counts_from_html(html_file_path):
    """
    Extract and count unique DE032 values from a given HTML file.

    Args:
        html_file_path (str): Path to the HTML file.

    Returns:
        dict: A dictionary containing DE032 values as keys and their counts.
        int: The number of unique DE032 values found.
        str: The first DE007 date and time extracted from the table.
        str: The last DE007 date and time extracted from the table.
        str: The generated session key.
    """
    def chunks(file, size=1024*1024*5): # 5MB chunks
        while True:
            chunk = file.read(size)
            if not chunk:
                break
            yield chunk

    try:
        de032_counter = Counter()
        de007_dates = []

        with open(html_file_path, 'rb') as file:
            # Using a ProcessPoolExecutor to parallelize the processing of file chunks
            with multiprocessing.Pool() as pool:
                results = pool.map(process_file_chunk, chunks(file))
                for de032_values, dates in results:
                    de032_counter.update(de032_values)
                    de007_dates.extend(dates)

        if de007_dates:
            start_time = min(de007_dates).strftime("%Y-%m-%d %H:%M:%S")
            end_time = max(de007_dates).strftime("%Y-%m-%d %H:%M:%S")
        else:
            start_time = ""
            end_time = ""

        # Generate session key
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_key = f"session_{timestamp}_{uuid.uuid4().hex[:6]}"

        return de032_counter, len(de032_counter), start_time, end_time, session_key

    except Exception as e:
        print(f"Error while processing HTML: {e}")
        return {}, 0, "", "", ""

# Example usage:
# result = extract_de032_counts_from_html("path_to_your_html_file.html")
# print(result)
