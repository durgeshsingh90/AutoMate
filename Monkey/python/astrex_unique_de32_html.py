from bs4 import BeautifulSoup
from collections import Counter

# Path to your HTML file
# html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7106-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer_.html"
# html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer_.html"

# html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7106-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer__filtered_20250327_202140.html"
html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer__filtered_20250327_202308.html"
# Read the HTML file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Extract the text content of all cells with the class "cell7"
cells = soup.find_all('td', class_='cell7')

# Extract and clean the values from these cells
values = [cell.get_text(strip=True) for cell in cells]

# Get the count of unique values using Counter
value_counts = Counter(values)

# Print the count of unique values
unique_values_count = len(value_counts)
# print("Count of unique values in DE032 cells:", unique_values_count)

# Print each unique value and its count
# print("Unique values and their counts:")
# for value, count in value_counts.items():
#     print(f"{value}: {count} times")

# Additional: If you want to extract unique DE032 values only
de032_values = []
for row in soup.find_all('tr'):
    cell1 = row.find('td', class_='cell1norm')
    if cell1 and 'DE032' in cell1.get_text(strip=True):
        cell7 = row.find('td', class_='cell7')
        if cell7:
            de032_values.append(cell7.get_text(strip=True))

de032_value_counts = Counter(de032_values)

print("Count of unique DE032 values:", len(de032_value_counts))
print("Unique DE032 values and their counts:")
for value, count in de032_value_counts.items():
    print(f"{value}: {count} times")
