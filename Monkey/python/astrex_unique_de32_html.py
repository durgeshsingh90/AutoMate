from bs4 import BeautifulSoup
from collections import Counter

# Path to your HTML file
html_file_path = r"C:\Users\f94gdos\Desktop\New folder (4)\ID-7117-Visa_BASE_I_(Standard)_Message_viewer_.html"

chunk_size = 1024 * 1024  # 1 MB
values = []
de032_values = []

with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as file:
    chunk = file.read(chunk_size)
    while chunk:
        # Parse the HTML content of the chunk using BeautifulSoup
        soup = BeautifulSoup(chunk, 'html.parser')

        # Extract the text content of all cells with the class "cell7"
        cells = soup.find_all('td', class_='cell7')

        # Extract and clean the values from these cells
        values.extend([cell.get_text(strip=True) for cell in cells])

        # Extract DE032 values only
        for row in soup.find_all('tr'):
            cell1 = row.find('td', class_='cell1norm')
            if cell1 and 'DE032' in cell1.get_text(strip=True):
                cell7 = row.find('td', class_='cell7')
                if cell7:
                    de032_values.append(cell7.get_text(strip=True))

        chunk = file.read(chunk_size)

# Get the count of unique values using Counter
value_counts = Counter(values)
unique_values_count = len(value_counts)
print("Count of unique values in DE032 cells:", unique_values_count)

# Print each unique value and its count
print("Unique values and their counts:")
for value, count in value_counts.items():
    print(f"{value}: {count} times")

# Get the count of DE032 unique values
de032_value_counts = Counter(de032_values)

print("Count of unique DE032 values:", len(de032_value_counts))
print("Unique DE032 values and their counts:")
for value, count in de032_value_counts.items():
    print(f"{value}: {count} times")
