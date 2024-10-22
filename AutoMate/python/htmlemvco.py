from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET
import xml.dom.minidom
from bs4 import BeautifulSoup
import re

# Configurable lists and mappings
tool_comment_level_de = ["MTI", "DE.003.SE", "DE.004", "DE.007", "DE.012", "DE.022.SE", "DE.024", "DE.026", "DE.035", "DE.049", "DE.055.TAG.9F02", "DE.055.TAG.82", "DE.055.TAG.9F36", "DE.055.TAG.84", "DE.055.TAG.9F1E", "DE.055.TAG.9F09", "DE.055.TAG.9F1A", "DE.055.TAG.9A", "DE.055.TAG.9C", "DE.055.TAG.5F2A", "DE.055.TAG.9F37", "DE.092"]
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

def format_binary(binary_str):
    """Format the binary string, separating characters by spaces."""
    cleaned_binary = binary_str.replace(' ', '').replace('-', '')
    return ' '.join(cleaned_binary[i:i+2] for i in range(0, len(cleaned_binary), 2))

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

    if field_id.startswith("NET.") and ".DE.055" in field_id:
        # Specifically handle DE.055 fields
        cleaned_binary = format_binary(field_data['binary'])
        cleaned_viewable = field_data['viewable'].replace(' ', '').replace('-', '')
    else:
        cleaned_binary = field_data['binary']
        cleaned_viewable = field_data['viewable']

    ET.SubElement(field_elt, 'FieldType').text = field_data['type']
    ET.SubElement(field_elt, 'FieldBinary').text = cleaned_binary
    ET.SubElement(field_elt, 'FieldViewable').text = cleaned_viewable
    ET.SubElement(field_elt, 'ToolComment').text = field_data['comment']

    if any(de in field_id for de in tool_comment_level_de) or ('.SE.' in field_id and 'DE.003.SE' in field_id):
        ET.SubElement(field_elt, 'ToolCommentLevel').text = 'INFO'

    field_list_elt = ET.SubElement(field_elt, 'FieldList')
    parent.append(field_elt)
    return field_elt, field_list_elt

def handle_de55_field(root, mti_value, rows, index):
    """Handle DE055 field and its subfields (EMV tags)."""
    first_row = rows[index]
    tds = first_row.find_all('td')

    friendly_name = tds[1].get_text(strip=True)
    field_type = tds[2].get_text(strip=True)
    field_binary = tds[4].get_text(strip=True)
    field_viewable = format_viewable_field(tds[6].get_text(strip=True))  # Consolidate viewable field
    tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

    # Create the root element for DE055
    root_de55 = SubElement(root, "Field", {"ID": f"NET.{mti_value}.DE.055"})
    create_element(root_de55, "FriendlyName", friendly_name)
    create_element(root_de55, "FieldType", field_type)
    create_element(root_de55, "FieldBinary", field_binary)
    create_element(root_de55, "FieldViewable", field_viewable)
    create_element(root_de55, "ToolComment", tool_comment)

    # Create a FieldList element
    field_list_de55 = SubElement(root_de55, "FieldList")

    # Parse the remaining rows and create subfields
    for row in rows[index + 1:]:
        tds = row.find_all('td')
        cell1_text = tds[0].text.strip()

        if "EMVTAG" not in cell1_text:
            break

        tag = cell1_text.split('-')[-1]
        field = SubElement(field_list_de55, "Field", {"ID": f"NET.{mti_value}.DE.055.TAG." + tag})
        create_element(field, "FriendlyName", tds[1].text.strip())
        create_element(field, "FieldType", tds[2].text.strip())

        emv_data = SubElement(field, "EMVData", {
            "Tag": tag,
            "Name": tds[1].text.strip(),
            "Format": "TLV"
        })

        binary_field = format_binary_field(tds[4].text.strip())
        viewable_field = format_viewable_field(tds[6].text.strip(), tag_length=len(tag))

        create_element(field, "FieldBinary", binary_field)
        create_element(field, "FieldViewable", viewable_field)

        if len(tds) > 7:
            create_element(field, "ToolComment", tds[7].text.strip())
        else:
            create_element(field, "ToolComment", "Default")
        create_element(field, "ToolCommentLevel", "INFO")
        create_element(field, "FieldList")

    return index + 1  # Return the new index to continue parsing


def create_element(parent, tag, text=None):
    element = SubElement(parent, tag)
    if text:
        element.text = text
    return element

def format_binary_field(binary_string):
    # Remove special characters
    cleaned_binary = re.sub(r'[^a-zA-Z0-9]', '', binary_string)
    # Split into groups of 2 characters
    parts = [cleaned_binary[i:i+2] for i in range(0, len(cleaned_binary), 2)]
    return ' '.join(parts)

def format_viewable_field(viewable_string, tag_length=4):
    # Remove special characters and convert to a single continuous string
    cleaned_viewable = re.sub(r'[^a-zA-Z0-9]', '', viewable_string)
    return cleaned_viewable

def convert_html_to_xml_with_field_list(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    rows = soup.find_all('tr')
    root = ET.Element('FieldList')
    mti_value = None
    parent_fields = {}

    index = 0
    while index < len(rows):
        row = rows[index]
        tds = row.find_all('td')
        if not tds:
            continue

        field_id = tds[0].get_text().replace("&nbsp;", "").strip()

        if field_id == "":
            index += 1
            continue

        if 'MTI' in field_id:
            friendly_name = tds[1].get_text(strip=True)
            field_type = tds[2].get_text(strip=True)
            field_binary = tds[4].get_text(strip=True)
            field_viewable = tds[6].get_text()
            tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

            mti_value = field_viewable.strip()

            field_data = {
                'field_id': "MTI",
                'friendly_name': friendly_name,
                'type': field_type,
                'binary': field_binary,
                'viewable': field_viewable,
                'comment': tool_comment,
                'mti_value': mti_value
            }

            add_field_to_list(root, field_data)
            index += 1
            continue

        if any(field_id.startswith(de) for de in skip_de):
            index += 1
            continue

        if field_id == "DE055":
            index = handle_de55_field(root, mti_value, rows, index)
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
                parent_field_elt, parent_field_list_elt = add_field_to_list(root, field_data, is_subfield=True)
                parent_fields[parent_field_id] = parent_field_list_elt
        else:
            field_elt, field_list_elt = add_field_to_list(root, field_data)
            if field_elt is not None and field_list_elt is not None:
                parent_fields[field_data_id] = field_list_elt

        index += 1

    xml_str = ET.tostring(root, encoding='utf-8')
    dom = xml.dom.minidom.parseString(xml_str)
    no_decl_xml_str_pretty = dom.toprettyxml(indent="  ").split('\n', 1)[1]
    return no_decl_xml_str_pretty

# Reading and converting the HTML input
with open('input.html', 'r') as file:
    html_table = file.read()

xml_output = convert_html_to_xml_with_field_list(html_table)

# Writing the output to the XML file
with open('output.xml', 'w', encoding='utf-8') as file:
    file.write('<?xml version="1.0" encoding="utf-8"?>\n')
    file.write(xml_output)

print("XML output has been saved to 'output.xml'")
