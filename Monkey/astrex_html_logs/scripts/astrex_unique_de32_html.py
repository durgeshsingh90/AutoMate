from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime
import uuid
def extract_de032_counts_from_html(html_file_path):
    """
    Extract and count unique DE032 values from a given HTML file.

    Args:
        html_file_path (str): Path to the HTML file.

    Returns:
        dict: A dictionary containing DE032 values as keys and their counts as values.
        int: The number of unique DE032 values found.
    """
    try:
        # Read the HTML file
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract DE032 values
        de032_values = []
        for row in soup.find_all('tr'):
            cell1 = row.find('td', class_='cell1norm')
            if cell1 and 'DE032' in cell1.get_text(strip=True):
                cell7 = row.find('td', class_='cell7')
                if cell7:
                    de032_values.append(cell7.get_text(strip=True))

        # Count DE032 values
        de032_value_counts = Counter(de032_values)
        #dummy start and end time
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate session key
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_key = f"session_{timestamp}_{uuid.uuid4().hex[:6]}"
        return de032_value_counts, len(de032_value_counts), start_time, end_time, session_key


    except Exception as e:
        print(f"Error while processing HTML: {e}")
        return {}, 0
