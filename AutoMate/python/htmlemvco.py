from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import xml.dom.minidom

# Configurable lists for tool comment level, search symbols, and DEs to skip
tool_comment_level_de = ["MTI", "DE.003.SE", "DE.004", "DE.007", "DE.012", "DE.022.SE", "DE.024", "DE.026", "DE.035", "DE.049", "DE.055.TAG.9F02", "DE.055.TAG.82", "DE.055.TAG.9F36", "DE.055.TAG.84", "DE.055.TAG.9F1E", "DE.055.TAG.9F09", "DE.055.TAG.9F1A", "DE.055.TAG.9A", "DE.055.TAG.9C", "DE.055.TAG.5F2A", "DE.055.TAG.9F37", "DE.092"]
search_symbol_de = ["DE.002", "DE.003", "DE.011", "DE.037", "DE.041", "DE.042"]
skip_de = ["BM1", "BM2", "Byte"]

# Mapping of DEs to specific search symbol names
search_symbol_name_mapping = {
    "DE.002": "PAN",
    "DE.003": "PROCESSINGCODE",
    "DE.011": "STAN",
    "DE.022": "POINTSERVICEENTRYMODE",
    "DE.037": "RRN",
    "DE.041": "TERMINALID",
    "DE.042": "MERCHANTID"
}

def format_binary(binary_str):
    """
    Formats the binary string to ensure groups of two characters are separated by spaces.
    """
    cleaned_binary = binary_str.replace(' ', '').replace('-', '')
    return ' '.join(cleaned_binary[i:i+2] for i in range(0, len(cleaned_binary), 2))

def add_field_to_list(field_list, field_data, is_subfield=False):
    field_id = field_data['field_id']

    # Skip fields in the skip_de list or fields starting with entries in skip_de
    if any(de in field_id for de in skip_de) or any(field_id.startswith(de) for de in skip_de):
        return None

    field = ET.Element('Field', ID=field_id)
    ET.SubElement(field, 'FriendlyName').text = field_data['friendly_name']

    if not is_subfield:
        for search_de in search_symbol_de:
            if search_de in field_id:
                search_symbol_name = search_symbol_name_mapping.get(search_de, None)
                if search_symbol_name:
                    ET.SubElement(field, 'SearchSymbol', Name=search_symbol_name, Value=field_data['viewable'])
                    break

    ET.SubElement(field, 'FieldType').text = field_data['type']

    # Handle DE.055.TAG properly
    if "DE.055.TAG." in field_id:
        tag_value = field_id.split(".TAG.")[1]
        ET.SubElement(field, 'EMVData', Tag=tag_value, Name=field_data['friendly_name'], Format='TLV')

        cleaned_binary = format_binary(field_data['binary'])
        cleaned_viewable = cleaned_binary[9:].replace(" ", "")  # Remove the tag and length from the viewable part
    else:
        cleaned_binary = format_binary(field_data['binary'])
        cleaned_viewable = field_data['viewable'].replace(' ', '').replace('-', '')

    ET.SubElement(field, 'FieldBinary').text = cleaned_binary
    ET.SubElement(field, 'FieldViewable').text = cleaned_viewable

    # Use the value from cell8norm for ToolComment
    ET.SubElement(field, 'ToolComment').text = field_data['comment']

    # Only add ToolCommentLevel if field_id is in tool_comment_level_de
    if any(de in field_id for de in tool_comment_level_de):
        ET.SubElement(field, 'ToolCommentLevel').text = 'INFO'

    ET.SubElement(field, 'FieldList')
    field_list.append(field)
    return field


def convert_html_to_xml_with_field_list(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    rows = soup.find_all('tr')
    root = ET.Element('FieldList')
    mti_value = None
    current_parent_field = None
    primary_field_mapping = {}
    de_055_field = None

    for row in rows:
        tds = row.find_all('td')
        if not tds:
            continue

        field_id = tds[0].get_text(strip=True).replace("&nbsp;", "").replace(" ", "")

        # Skip fields if they meet skip_de conditions
        if any(field_id.startswith(de) for de in skip_de):
            continue

        friendly_name = tds[1].get_text(strip=True)
        field_type = tds[2].get_text(strip=True)
        field_binary = tds[4].get_text(strip=True)
        field_viewable = tds[6].get_text(strip=True)
        tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

        if field_id == "MTI":
            mti_value = field_viewable

        # Handling primary fields and subfields
        if 'S' in field_id and field_id.startswith('DE'):
            parent_field_id = field_id.split('S')[0]
            subfield_number = field_id.split('S')[-1]; subfield_number_padded = subfield_number.zfill(3)
            field_data_id = f"NET.{mti_value}.DE.{parent_field_id[2:]}.SE.{subfield_number_padded}"
            is_subfield = True
        elif field_id.startswith('DE'):
            field_data_id = f"NET.{mti_value}.DE.{field_id[2:]}"
            is_subfield = False
        elif field_id.startswith('EMVTAG'):
            tag_value = field_id.split('-')[-1]
            field_data_id = f"NET.{mti_value}.DE.055.TAG.{tag_value}"
            is_subfield = False
        else:
            field_data_id = field_id
            is_subfield = False

        field_data = {
            'field_id': field_data_id,
            'friendly_name': friendly_name,
            'type': field_type,
            'binary': field_binary,
            'viewable': field_viewable,
            'comment': tool_comment,
            'mti_value': mti_value
        }

        # For DE.055 field
        if field_id == "DE055" or field_id == "DE.055":
            de_055_field = add_field_to_list(root, field_data)
            continue

        # For DE.055.TAG fields nested under DE.055
        if de_055_field and "DE.055.TAG." in field_id:
            de_055_list = de_055_field.find("FieldList")
            add_field_to_list(de_055_list, field_data)
            continue

        if is_subfield:
            if parent_field_id not in primary_field_mapping:
                primary_field_mapping[parent_field_id] = current_parent_field
            primary_field = primary_field_mapping[parent_field_id]
            if primary_field is not None:
                parent_field_list = primary_field.find('FieldList')
                add_field_to_list(parent_field_list, field_data, is_subfield=True)
        else:
            current_parent_field = add_field_to_list(root, field_data)
            if 'DE.003' in field_data_id:
                primary_field_mapping[field_id] = current_parent_field

    xml_str = ET.tostring(root, encoding='utf-8')
    dom = xml.dom.minidom.parseString(xml_str)
    no_decl_xml_str_pretty = dom.toprettyxml(indent="  ").split('\n', 1)[1]  # Removes the dom's xml declaration
    return no_decl_xml_str_pretty


with open('input.html', 'r') as file:
    html_table = file.read()

xml_output = convert_html_to_xml_with_field_list(html_table)

# Save the output to a file
with open('output.xml', 'w', encoding='utf-8') as file:
    file.write('<?xml version="1.0" encoding="utf-8"?>\n')
    file.write(xml_output)

print("XML output has been saved to 'output.xml'")
