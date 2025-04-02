import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import shutil
import os
from datetime import datetime

# Define paths
html_file_path = r"C:\Users\f94gdos\Desktop\emv\ID-7121-Visa_BASE_I_(Standard)_Message_viewer__part0.html"
template_path = r"C:\Durgesh\Office\Automation\Monkey\Monkey\python\astrex_html_logfilter\emvco_template.xml"

# Prepare the output path
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
base_name = os.path.basename(html_file_path).replace('.html', '')
output_file_path = os.path.join(os.path.dirname(html_file_path), f"{base_name}_emvco_{current_time}.xml")

# Create a copy of the template
shutil.copy(template_path, output_file_path)

# Parse the copied XML file
tree = ET.parse(output_file_path)
root = tree.getroot()

# Find the OnlineMessageList element
online_message_list = root.find(".//OnlineMessageList")

# Read the HTML file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Extract table data
tables = soup.find_all('table')

# Process each table
for table in tables:
    rows = table.find_all('tr')
    for i, row in enumerate(rows):
        cells = row.find_all('td')
        if len(cells) > 0:
            online_message = ET.SubElement(online_message_list, "OnlineMessage")
            cell_text = ' | '.join(cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells)
            online_message.text = cell_text
        else:
            # Use the <th> if there are no <td> tags
            headers = row.find_all('th')
            if headers:
                online_message = ET.SubElement(online_message_list, "OnlineMessage")
                header_text = ' | '.join(header.get_text(strip=True).replace('\xa0', ' ') for header in headers)
                online_message.text = header_text

# Save the modified XML to the output file
tree.write(output_file_path, encoding="utf-8", xml_declaration=True)

print(f"XML log has been updated and saved to {output_file_path}")
