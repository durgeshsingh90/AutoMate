import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from bs4 import BeautifulSoup
import re
import xml.dom.minidom
from datetime import datetime

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
    return ' '.join(cleaned_binary[i:i+2] for i in range(0, len(cleaned_binary), 2))

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

    ET.SubElement(field_elt, 'FieldType').text = field_data['type']
    ET.SubElement(field_elt, 'FieldBinary').text = cleaned_binary
    ET.SubElement(field_elt, 'FieldViewable').text = cleaned_viewable

    tool_comment_elt = ET.SubElement(field_elt, 'ToolComment')
    tool_comment_elt.text = replace_quot_entities(field_data['comment'])

    add_tool_comment_level(field_id, field_elt)

    field_list_elt = ET.SubElement(field_elt, 'FieldList')
    parent.append(field_elt)
    return field_elt, field_list_elt

def format_raw_data(raw_data_str):
    """Format the raw data string into space-separated hexadecimal bytes."""
    cleaned_raw_data = re.sub(r'[^a-fA-F0-9]', '', raw_data_str)
    return ' '.join(cleaned_raw_data[i:i+2] for i in range(0, len(cleaned_raw_data), 2))

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
    if tag == "9F02":
        return cleaned_viewable.zfill(12)
    if tag:
        tag_length = len(tag) + extra_digits
        return cleaned_viewable[tag_length:]
    return cleaned_viewable

def format_viewable_field_for_de055(viewable_string):
    """Format FieldViewable for NET.1100.DE.055 specifically."""
    return re.sub(r'[^a-zA-Z0-9]', '', viewable_string)

# Add this import for parsing date strings
from dateutil import parser

def convert_html_to_xml_with_field_list(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    rows = soup.find_all('tr')
    root = ET.Element('OnlineMessage', {'Source': 'Standard', 'Destination': 'Default'})  # Initialize without Class attribute
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

            # Determine the MTI Class value based on the last two digits
            mti_class_value = "REQUEST" if mti_value[-2:] == "00" else "RESPONSE"
            root.set('Class', mti_class_value)  # Set the Class attribute once MTI is encountered

            field_data = {
                'field_id': "MTI",
                'friendly_name': friendly_name,
                'type': field_type,
                'binary': field_binary,
                'viewable': field_viewable,
                'comment': tool_comment,
                'mti_value': mti_value
            }

            if 'FieldList' in locals():
                add_field_to_list(field_list, field_data)
            else:
                field_list = ET.SubElement(root, 'FieldList')
                add_field_to_list(field_list, field_data)

            index += 1
            continue

        if any(field_id.startswith(de) for de in skip_de):
            index += 1
            continue

        if field_id == "DE055":
            index = handle_de55_field(field_list, mti_value, rows, index)
            continue

        # Detect and handle Raw data row separately
        if 'Raw data' in field_id and raw_data_index == -1:  # Only handle the first occurrence of Raw data
            raw_data_field = tds[1].get_text()
            formatted_raw_data = format_raw_data(raw_data_field)
            if root is None:
                root = ET.Element('OnlineMessage', {'Class': 'UNKNOWN', 'Source': 'Standard', 'Destination': 'Default'})
            raw_data = ET.Element('RawData')
            raw_data.text = formatted_raw_data
            root.append(raw_data)  # Insert RawData immediately after OnlineMessage element
            
            # Add MessageInfo element with the extracted DE007 date-time
            message_info = ET.Element('MessageInfo')
            date_time_element = ET.SubElement(message_info, 'Date-Time')
            date_time_element.text = de007_date_time if de007_date_time else datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            root.append(message_info)

            raw_data_index = index
            if 'FieldList' not in locals():
                field_list = ET.SubElement(root, 'FieldList')
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

        # Handle other fields and subfields
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

    xml_str = ET.tostring(root, encoding='utf-8')
    dom = xml.dom.minidom.parseString(xml_str)
    no_decl_xml_str_pretty = dom.toprettyxml(indent="  ").split('\n', 1)[1]
    return no_decl_xml_str_pretty

# Rest of the code remains unchanged

def read_file(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_name}: {str(e)}")
        return None

def write_to_file(file_name, content):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>\n')
            file.write(content)
        print(f"XML output has been saved to '{file_name}'")
    except Exception as e:
        print(f"Error writing to file {file_name}: {str(e)}")

html_table = read_file('input.html')
if html_table:
    xml_output = convert_html_to_xml_with_field_list(html_table)
    write_to_file('output.xml', xml_output)
