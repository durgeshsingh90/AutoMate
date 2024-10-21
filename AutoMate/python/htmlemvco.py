from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import xml.dom.minidom

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

def convert_html_to_xml_with_field_list(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    rows = soup.find_all('tr')
    root = ET.Element('FieldList')
    mti_value = None
    parent_fields = {}
    de55_field = None
    de55_field_list = None

    for row in rows:
        tds = row.find_all('td')
        if not tds:
            continue

        field_id = tds[0].get_text().replace("&nbsp;", "").strip()

        if field_id == "":
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
            continue

        if field_id == "DE055":
            friendly_name = tds[1].get_text(strip=True)
            field_type = tds[2].get_text(strip=True)
            field_binary = tds[4].get_text(strip=True)
            field_viewable = tds[6].get_text()
            tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

            field_data = {
                'field_id': f"NET.{mti_value}.DE.055",
                'friendly_name': friendly_name,
                'type': field_type,
                'binary': field_binary,
                'viewable': field_viewable,
                'comment': tool_comment,
                'mti_value': mti_value
            }

            de55_field, de55_field_list = add_field_to_list(root, field_data)
            parent_fields[field_data['field_id']] = de55_field_list
            continue

        if field_id.startswith("EMVTAG") and de55_field_list:
            tag_value = field_id.split('-')[-1]
            friendly_name = tds[1].get_text(strip=True)
            field_type = tds[2].get_text(strip=True)
            field_binary = tds[4].get_text(strip=True)
            if not field_binary:
                field_binary = tds[6].get_text(strip=True)
            field_viewable = field_binary.replace("-", "").replace(" ", "").strip()
            tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"

            field_data = {
                'field_id': f"NET.{mti_value}.DE.055.TAG.{tag_value}",
                'friendly_name': friendly_name,
                'type': field_type,
                'binary': field_binary,
                'viewable': field_viewable,
                'comment': tool_comment,
                'mti_value': mti_value
            }

            emv_data_elt = ET.Element('EMVData')
            emv_data_elt.set("Tag", tag_value)
            emv_data_elt.set("Name", friendly_name)
            emv_data_elt.set("Format", "TLV")

            field_elt = ET.Element('Field', ID=field_data['field_id'])
            ET.SubElement(field_elt, 'FriendlyName').text = friendly_name
            ET.SubElement(field_elt, 'FieldType').text = field_type
            field_elt.append(emv_data_elt)

            cleaned_binary = format_binary(field_binary)
            cleaned_viewable = field_viewable

            ET.SubElement(field_elt, 'FieldBinary').text = cleaned_binary
            ET.SubElement(field_elt, 'FieldViewable').text = cleaned_viewable
            ET.SubElement(field_elt, 'ToolComment').text = tool_comment

            if any(de in field_data['field_id'] for de in tool_comment_level_de):
                ET.SubElement(field_elt, 'ToolCommentLevel').text = 'INFO'

            de55_field_list.append(field_elt)
            continue

        if de55_field_list and (
                not field_id.startswith("EMVTAG") or
                any(keyword in field_id for keyword in ["Byte", "oooo"])
        ):
            continue

        if any(field_id.startswith(de) for de in skip_de):
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
                parent_field_elt, parent_field_list_elt = add_field_to_list(root, field_data, is_subfield=True)
                parent_fields[parent_field_id] = parent_field_list_elt
        else:
            field_elt, field_list_elt = add_field_to_list(root, field_data)
            if field_elt is not None and field_list_elt is not None:
                parent_fields[field_data_id] = field_list_elt

    xml_str = ET.tostring(root, encoding='utf-8')
    dom = xml.dom.minidom.parseString(xml_str)
    no_decl_xml_str_pretty = dom.toprettyxml(indent="  ").split('\n', 1)[1]
    return no_decl_xml_str_pretty

with open('input.html', 'r') as file:
    html_table = file.read()

xml_output = convert_html_to_xml_with_field_list(html_table)

with open('output.xml', 'w', encoding='utf-8') as file:
    file.write('<?xml version="1.0" encoding="utf-8"?>\n')
    file.write(xml_output)

print("XML output has been saved to 'output.xml'")
