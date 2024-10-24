<<<<<<< HEAD
import logging
from bs4 import BeautifulSoup
=======
>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from bs4 import BeautifulSoup
import re
import xml.dom.minidom
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurable lists and mappings
tool_comment_level_de = [
    "MTI", "DE.003.SE", "DE.004", "DE.007", "DE.012", "DE.022.SE", "DE.024", "DE.026", "DE.035", "DE.049",
    "DE.055.TAG.9F02", "DE.055.TAG.82", "DE.055.TAG.9F36", "DE.055.TAG.84", "DE.055.TAG.9F1E", "DE.055.TAG.9F09",
    "DE.055.TAG.9F1A", "DE.055.TAG.9A", "DE.055.TAG.9C", "DE.055.TAG.5F2A", "DE.055.TAG.9F37", "DE.092"
]
search_symbol_de = ["DE.002", "DE.003", "DE.011", "DE.037", "DE.041", "DE.042"]
skip_de = ["BM1", "BM2", "Byte"]

# Mapping DE to search symbol names
search_symbol_name_mapping = {
    "DE.002": "PAN",
    "DE.003": "PROCESSINGCODE",
    "DE.011": "STAN",
    "DE.022": "POINTSERVICEENTRYMODE",
    "DE.037": "RRN",
    "DE.041": "TERMINALID",
    "DE.042": "MERCHANTID"
}

def replace_quot_entities(text):
    if text:
        return text.replace('&quot;', '"')
    return text

def format_binary(binary_str):
    """Format the binary string, separating characters by spaces."""
    cleaned_binary = binary_str.replace(' ', '').replace('-', '')
    logging.debug(f"Formatted binary string: {cleaned_binary}")
    return ' '.join(cleaned_binary[i:i+2] for i in range(0, len(cleaned_binary), 2))

<<<<<<< HEAD
def create_field_element(field_data, cleaned_binary, cleaned_viewable):
    """Helper function to create and populate Field XML element."""
    logging.info(f"Creating XML field element for field: {field_data['field_id']}")
    field_elt = ET.Element('Field', ID=field_data['field_id'])
    ET.SubElement(field_elt, 'FriendlyName').text = field_data['friendly_name']
=======
def add_tool_comment_level(field_id, field_elt):
    """Add ToolCommentLevel based on the specified rules."""
    for de in tool_comment_level_de:
        if de.endswith('.SE') and de in field_id:
            ET.SubElement(field_elt, 'ToolCommentLevel').text = 'INFO'
            break
        elif not de.endswith('.SE') and de in field_id:
            ET.SubElement(field_elt, 'ToolCommentLevel').text = 'INFO'
            break
        elif de in field_id and '.SE.' not in field_id and '.TAG.' not in field_id:
            ET.SubElement(field_elt, 'ToolCommentLevel').text = 'INFO'
            break

def add_field_to_list(parent, field_data, is_subfield=False):
    """Add a field to the parent element."""
    field_id = field_data['field_id']
    if any(de in field_id for de in skip_de) or any(field_id.startswith(de) for de in skip_de):
        return None, None

    field_elt = ET.Element('Field', ID=field_id)
    ET.SubElement(field_elt, 'FriendlyName').text = field_data['friendly_name']

    if not is_subfield or ("DE.003.SE" in search_symbol_de and "NET." + field_data['mti_value'] + ".DE.003" in field_id):
        for search_de in search_symbol_de:
            if search_de in field_id and (".SE." not in field_id or search_de == "DE.003.SE"):
                search_symbol_name = search_symbol_name_mapping.get(search_de.split(".SE")[0], None)
                if search_symbol_name:
                    ET.SubElement(field_elt, 'SearchSymbol', Name=search_symbol_name, Value=field_data['viewable'])
                    break

    if field_id == "NET.1100.DE.055":
        cleaned_binary = format_binary(field_data['binary'])
        cleaned_viewable = field_data['viewable'].replace(' ', '').replace('-', '')
    elif field_id.startswith("NET.") and ".DE.055" in field_id:
        cleaned_binary = format_binary(field_data['binary'])
        cleaned_viewable = format_viewable_field(field_data['viewable'], field_data['field_id'].split('.')[-1], 2)
    else:
        cleaned_binary = field_data['binary']
        cleaned_viewable = field_data['viewable']

>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da
    ET.SubElement(field_elt, 'FieldType').text = field_data['type']
    ET.SubElement(field_elt, 'FieldBinary').text = cleaned_binary
    ET.SubElement(field_elt, 'FieldViewable').text = cleaned_viewable

<<<<<<< HEAD
    if any(de in field_data['field_id'] for de in tool_comment_level_de):
        ET.SubElement(field_elt, 'ToolCommentLevel').text = 'INFO'
        logging.debug(f"Added ToolCommentLevel INFO for field: {field_data['field_id']}")

    return field_elt

def handle_search_symbol(field_id, field_data, field_elt):
    """Helper function to handle search symbol mapping and append to XML."""
    for search_de in search_symbol_de:
        if search_de in field_id and (".SE." not in field_id or search_de == "DE.003.SE"):
            search_symbol_name = search_symbol_name_mapping.get(search_de.split(".SE")[0], None)
            if search_symbol_name:
                ET.SubElement(field_elt, 'SearchSymbol', Name=search_symbol_name, Value=field_data['viewable'])
                logging.info(f"Added SearchSymbol for field: {field_id}, Name: {search_symbol_name}, Value: {field_data['viewable']}")
                break

def add_field_to_list(parent, field_data, is_subfield=False):
    """Add a field to the parent element."""
    field_id = field_data['field_id']
    if any(de in field_id for de in skip_de):
        logging.warning(f"Skipping field: {field_id} due to skip list match")
        return None, None

    cleaned_binary = format_binary(field_data['binary']) if 'DE.055' in field_id else field_data['binary']
    cleaned_viewable = field_data['viewable'].replace(' ', '').replace('-', '') if 'DE.055' in field_id else field_data['viewable']

    field_elt = create_field_element(field_data, cleaned_binary, cleaned_viewable)

    # Handle search symbol if needed
    if not is_subfield:
        handle_search_symbol(field_id, field_data, field_elt)
=======
    tool_comment_elt = ET.SubElement(field_elt, 'ToolComment')
    tool_comment_elt.text = replace_quot_entities(field_data['comment'])

    add_tool_comment_level(field_id, field_elt)
>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da

    field_list_elt = ET.SubElement(field_elt, 'FieldList')
    parent.append(field_elt)
    return field_elt, field_list_elt

<<<<<<< HEAD
def extract_field_data(tds, field_id, mti_value):
    """Extracts field data from the table row (tds) and returns a dictionary."""
    try:
        friendly_name = tds[1].get_text(strip=True)
        field_type = tds[2].get_text(strip=True)
        field_binary = tds[4].get_text(strip=True)
        field_viewable = tds[6].get_text()
        tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"
        logging.debug(f"Extracted field data for {field_id}: FriendlyName={friendly_name}, FieldType={field_type}")
    except IndexError as e:
        logging.error(f"Error extracting data from row: {e}")
        return None

    return {
        'field_id': field_id,
        'friendly_name': friendly_name,
        'type': field_type,
        'binary': field_binary,
        'viewable': field_viewable,
        'comment': tool_comment,
        'mti_value': mti_value
    }

def convert_html_to_xml_with_field_list(html_table):
    logging.info("Starting HTML to XML conversion")
    soup = BeautifulSoup(html_table, 'html.parser')
    rows = soup.find_all('tr')
    root = ET.Element('FieldList')
    parent_fields = {}
    de55_field_list = None
    mti_value = None
=======
def format_raw_data(raw_data_str):
    """Format the raw data string into space-separated hexadecimal bytes."""
    cleaned_raw_data = re.sub(r'[^a-fA-F0-9]', '', raw_data_str)
    return ' '.join(cleaned_raw_data[i:i+2] for i in range(0, len(cleaned_raw_data), 2))
>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da

def handle_de55_field(root, mti_value, rows, index):
    """Handle DE055 field and its subfields (EMV tags)."""
    first_row = rows[index]
    tds = first_row.find_all('td')
    friendly_name = tds[1].get_text(strip=True)
    field_type = tds[2].get_text(strip=True)
    field_binary = tds[4].get_text(strip=True)
    field_viewable = tds[6].get_text(strip=True)
    tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

    root_de55 = SubElement(root, "Field", {"ID": f"NET.{mti_value}.DE.055"})
    create_element(root_de55, "FriendlyName", friendly_name)
    create_element(root_de55, "FieldType", field_type)
    create_element(root_de55, "FieldBinary", field_binary)
    create_element(root_de55, "FieldViewable", format_viewable_field_for_de055(field_viewable))
    tool_comment_de55 = ET.SubElement(root_de55, "ToolComment")
    tool_comment_de55.text = replace_quot_entities(tool_comment)
    field_list_de55 = SubElement(root_de55, "FieldList")

    final_index = index
    for row in rows[index + 1:]:
        final_index += 1
        tds = row.find_all('td')
        if not tds:
            continue
<<<<<<< HEAD

        field_id = tds[0].get_text().replace("&nbsp;", "").strip()

        if field_id == "":
            logging.debug("Empty field ID, skipping row")
            continue

        if 'MTI' in field_id:
            field_data = extract_field_data(tds, "MTI", None)
            if field_data:
                mti_value = field_data['viewable'].strip()
                field_data['mti_value'] = mti_value
                add_field_to_list(root, field_data)
            continue

        if field_id == "DE055":
            field_data = extract_field_data(tds, f"NET.{mti_value}.DE.055", mti_value)
            if field_data:
                de55_field, de55_field_list = add_field_to_list(root, field_data)
                parent_fields[field_data['field_id']] = de55_field_list
            continue

        if field_id.startswith("EMVTAG") and de55_field_list:
            tag_value = field_id.split('-')[-1]
            field_data = extract_field_data(tds, f"NET.{mti_value}.DE.055.TAG.{tag_value}", mti_value)
            if field_data:
                emv_data_elt = ET.Element('EMVData', Tag=tag_value, Name=field_data['friendly_name'], Format="TLV")
                field_elt = create_field_element(field_data, field_data['binary'], field_data['viewable'])
                field_elt.append(emv_data_elt)
                de55_field_list.append(field_elt)
            continue

        field_data = extract_field_data(tds, f"NET.{mti_value}.DE.{field_id[2:]}", mti_value)
        if field_data:
            if ".SE." in field_data['field_id']:
                parent_field_id = field_data['field_id'].rsplit(".SE.", 1)[0]
                if parent_field_id in parent_fields:
                    add_field_to_list(parent_fields[parent_field_id], field_data, is_subfield=True)
                else:
                    parent_field_elt, parent_field_list_elt = add_field_to_list(root, field_data, is_subfield=True)
                    parent_fields[parent_field_id] = parent_field_list_elt
            else:
                field_elt, field_list_elt = add_field_to_list(root, field_data)
                if field_elt is not None and field_list_elt is not None:
                    parent_fields[field_data['field_id']] = field_list_elt
=======
        cell1_text = tds[0].get_text(strip=True)
        if "EMVTAG" not in cell1_text:
            break
        tag = cell1_text.split('-')[-1]
        field_id = f"NET.{mti_value}.DE.055.TAG." + tag
        field = SubElement(field_list_de55, "Field", {"ID": field_id})
        create_element(field, "FriendlyName", tds[1].get_text(strip=True))
        create_element(field, "FieldType", tds[2].get_text(strip=True))
        emv_data = SubElement(field, "EMVData", {
            "Tag": tag,
            "Name": tds[1].get_text(strip=True),
            "Format": "TLV"
        })
        binary_field = format_binary_field(tds[4].get_text(strip=True))
        viewable_field = format_viewable_field(tds[6].get_text(strip=True), tag, 2)
        create_element(field, "FieldBinary", binary_field)
        create_element(field, "FieldViewable", viewable_field)
        if len(tds) > 7:
            tool_comment_subfield = tds[7].get_text(strip=True)
        else:
            tool_comment_subfield = "Default"
        create_element_with_text(field, "ToolComment", replace_quot_entities(tool_comment_subfield))
        add_tool_comment_level(field_id, field)
        create_element(field, "FieldList")

    return final_index

def create_element_with_text(parent, tag, text=None):
    element = SubElement(parent, tag)
    if text is not None:
        element.text = text
    return element

def create_element(parent, tag, text=None):
    element = SubElement(parent, tag)
    if text:
        element.text = text
    return element

def format_binary_field(binary_string):
    cleaned_binary = re.sub(r'[^a-zA-Z0-9]', '', binary_string)
    parts = [cleaned_binary[i:i+2] for i in range(0, len(cleaned_binary), 2)]
    return ' '.join(parts)

def format_viewable_field(viewable_string, tag=None, extra_digits=0):
    cleaned_viewable = re.sub(r'[^a-zA-Z0-9]', '', viewable_string)
    # if tag == "9F02":
    #     return cleaned_viewable.zfill(12)
    if tag:
        tag_length = len(tag) + extra_digits
        return cleaned_viewable[tag_length:]
    return cleaned_viewable

def format_viewable_field_for_de055(viewable_string):
    """Format FieldViewable for NET.1100.DE.055 specifically."""
    return re.sub(r'[^a-zA-Z0-9]', '', viewable_string)

# Add this import for parsing date strings
from dateutil import parser

import xml.etree.ElementTree as ET
import xml.dom.minidom
from datetime import datetime
from bs4 import BeautifulSoup
import re
from xml.etree.ElementTree import SubElement

import xml.etree.ElementTree as ET
import xml.dom.minidom
from bs4 import BeautifulSoup
import re
from datetime import datetime


# Extend skip_de to include specific patterns
skip_de.extend(["DE039MTI"])

def convert_html_to_xml_with_field_list(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    tables = soup.find_all('table')
    
    print(f"Found {len(tables)} tables")  # Debug: Check number of tables found

    root = ET.Element('OnlineMessageList')
    
    for tbl_index, table in enumerate(tables):
        print(f"Processing table {tbl_index + 1}")  # Debug: Processing table
        rows = table.find_all('tr')
        message_root = ET.Element('OnlineMessage', {'Source': 'Standard', 'Destination': 'Default'})  # Initialize without Class attribute
        mti_value = None
        parent_fields = {}

        index = 0
        raw_data_index = -1
        de007_date_time = ""  # Initialize a variable to hold the DE007 date-time

        while index < len(rows):
            row = rows[index]
            tds = row.find_all('td')
            if not tds:
                index += 1
                continue

            field_id = tds[0].get_text().replace("&nbsp;", "").strip()

            # Ignore special DE039MTIxxxx pattern
            if any(field_id.startswith(de) for de in skip_de) or "DE039MTI" in field_id:
                index += 1
                continue

            if field_id == "":
                index += 1
                continue

            if 'MTI' in field_id:
                friendly_name = tds[1].get_text(strip=True)
                field_type = tds[2].get_text(strip=True)
                field_binary = tds[4].get_text(strip=True)
                field_viewable = tds[6].get_text().strip()
                tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

                mti_value = field_viewable
                
                print(f"Found MTI: {mti_value}")  # Debug: Found MTI

                # Determine the MTI Class value based on the last two digits
                mti_class_value = "REQUEST" if mti_value[-2:] == "00" else "RESPONSE"
                message_root.set('Class', mti_class_value)  # Set the Class attribute once MTI is encountered

                field_data = {
                    'field_id': "MTI",
                    'friendly_name': friendly_name,
                    'type': field_type,
                    'binary': field_binary,
                    'viewable': field_viewable,
                    'comment': tool_comment,
                    'mti_value': mti_value
                }

                field_list = ET.SubElement(message_root, 'FieldList')
                add_field_to_list(field_list, field_data)

                index += 1
                continue

            if field_id == "DE055":
                index = handle_de55_field(field_list, mti_value, rows, index)
                continue

            # Detect and handle Raw data row separately
            if 'Raw data' in field_id and raw_data_index == -1:  # Only handle the first occurrence of Raw data
                raw_data_field = tds[1].get_text()
                formatted_raw_data = format_raw_data(raw_data_field)
                raw_data = ET.Element('RawData')
                raw_data.text = formatted_raw_data
                message_root.append(raw_data)  # Insert RawData immediately after OnlineMessage element
                
                # Add MessageInfo element with the extracted DE007 date-time
                message_info = ET.Element('MessageInfo')
                date_time_element = ET.SubElement(message_info, 'Date-Time')
                date_time_element.text = de007_date_time if de007_date_time else datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                message_root.append(message_info)

                raw_data_index = index
                index += 1
                continue

            # Handle DE007 separately to extract the date-time value
            if field_id == "DE007":
                field_viewable = tds[6].get_text(strip=True)
                if len(field_viewable) == 10:
                    # Format the DE007 value into the correct ISO 8601 format with milliseconds and 'Z' timezone
                    de007_date_time = f"20{field_viewable[:2]}-{field_viewable[2:4]}-{field_viewable[4:6]}T{field_viewable[6:8]}:{field_viewable[8:10]}:00.000Z"
                
                # Continue normal process for DE007 conversion
                friendly_name = tds[1].get_text(strip=True)
                field_type = tds[2].get_text(strip=True)
                field_binary = tds[4].get_text(strip=True)
                tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

                field_data_id = f"NET.{mti_value}.DE.{field_id[2:]}"

                field_data = {
                    'field_id': field_data_id,
                    'friendly_name': friendly_name,
                    'type': field_type,
                    'binary': field_binary,
                    'viewable': field_viewable,
                    'comment': tool_comment,
                    'mti_value': mti_value
                }

                if field_data_id not in parent_fields:
                    field_elt, field_list_elt = add_field_to_list(field_list, field_data)
                    if field_elt is not None and field_list_elt is not None:
                        parent_fields[field_data_id] = field_list_elt

                index += 1
                continue

            friendly_name = tds[1].get_text(strip=True)
            field_type = tds[2].get_text(strip=True)
            field_binary = tds[4].get_text(strip=True)
            field_viewable = tds[6].get_text()
            tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

            if 'S' in field_id and field_id.startswith('DE'):
                parent_field_id = field_id.split('S')[0]
                subfield_number = field_id.split('S')[-1]
                subfield_number_padded = subfield_number.zfill(3)
                field_data_id = f"NET.{mti_value}.DE.{parent_field_id[2:]}.SE.{subfield_number_padded}"
            elif field_id.startswith('DE'):
                field_data_id = f"NET.{mti_value}.DE.{field_id[2:]}"
            elif field_id.startswith('EMVTAG'):
                tag_value = field_id.split('-')[-1]
                field_data_id = f"NET.{mti_value}.DE.055.TAG.{tag_value}"
            else:
                field_data_id = field_id

            field_data = {
                'field_id': field_data_id,
                'friendly_name': friendly_name,
                'type': field_type,
                'binary': field_binary,
                'viewable': field_viewable,
                'comment': tool_comment,
                'mti_value': mti_value
            }

            if ".SE." in field_data_id:
                parent_field_id = field_data_id.rsplit(".SE.", 1)[0]
                if parent_field_id in parent_fields:
                    add_field_to_list(parent_fields[parent_field_id], field_data, is_subfield=True)
                else:
                    parent_field_elt, parent_field_list_elt = add_field_to_list(field_list, field_data, is_subfield=True)
                    parent_fields[parent_field_id] = parent_field_list_elt
            else:
                if field_data_id not in parent_fields:
                    field_elt, field_list_elt = add_field_to_list(field_list, field_data)
                    if field_elt is not None and field_list_elt is not None:
                        parent_fields[field_data_id] = field_list_elt

            index += 1

        root.append(message_root)
>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da

    xml_str = ET.tostring(root, encoding='utf-8')
    dom = xml.dom.minidom.parseString(xml_str)
    no_decl_xml_str_pretty = dom.toprettyxml(indent="  ").split('\n', 1)[1]
    logging.info("Finished HTML to XML conversion")
    return no_decl_xml_str_pretty

<<<<<<< HEAD
with open('input.html', 'r') as file:
    logging.info("Reading HTML file")
    html_table = file.read()
=======
>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da

def read_file(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_name}: {str(e)}")
        return None

<<<<<<< HEAD
with open('output.xml', 'w', encoding='utf-8') as file:
    logging.info("Saving XML output to 'output.xml'")
    file.write('<?xml version="1.0" encoding="utf-8"?>\n')
    file.write(xml_output)

logging.info("XML output has been saved to 'output.xml'")
=======
def write_to_file(file_name, content):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>\n')
            file.write(content)
        print(f"XML output has been saved to '{file_name}'")
    except Exception as e:
        print(f"Error writing to file {file_name}: {str(e)}")

html_table = read_file('matching_blocks.html')
if html_table:
    xml_output = convert_html_to_xml_with_field_list(html_table)
    write_to_file('output.xml', xml_output)
>>>>>>> 6d97673ce14ce1e830bb10fc6e51287d8d5f23da
