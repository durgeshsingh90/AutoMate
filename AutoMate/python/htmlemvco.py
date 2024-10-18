from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import xml.dom.minidom
def add_field_to_list(field_list, field_data, is_subfield=False, subfield_num=None):
    if is_subfield:
        mti_value = field_data['mti_value']
        field_id = f"NET.{mti_value}.DE.003.SE.{subfield_num:03d}"
    else:
        field_id = field_data['field_id']
    field = ET.Element('Field', ID=field_id)
    ET.SubElement(field, 'FriendlyName').text = field_data['friendly_name']
    if "NET" in field_id and ("DE.002" in field_id or ("DE.003" in field_id and not is_subfield)):
        search_symbol_name = "PAN" if "DE.002" in field_id else "PROCESSINGCODE"
        ET.SubElement(field, 'SearchSymbol', Name=search_symbol_name, Value=field_data['viewable'])
    ET.SubElement(field, 'FieldType').text = field_data['type']
    ET.SubElement(field, 'FieldBinary').text = field_data['binary']
    ET.SubElement(field, 'FieldViewable').text = field_data['viewable']
    ET.SubElement(field, 'ToolComment').text = field_data['comment']
    if field_id == "MTI" or (is_subfield and "DE.003" in field_id):
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
    subfield_counter = 1
    for row in rows:
        tds = row.find_all('td')
        if not tds:
            continue
        field_id = tds[0].get_text(strip=True).replace(" ", "")
        friendly_name = tds[1].get_text(strip=True)
        field_type = tds[2].get_text(strip=True)
        field_binary = tds[4].get_text(strip=True)
        field_viewable = tds[6].get_text(strip=True)
        tool_comment = tds[7].get_text(strip=True) if tds[7].get_text(strip=True) else "Default"
        if field_id == "MTI":
            mti_value = field_viewable
        if field_id.startswith('DE'):
            field_id = f"NET.{mti_value}.{field_id.replace('DE', 'DE.')}"
        else:
            field_id = field_id
        field_data = {
            'field_id': field_id,
            'friendly_name': friendly_name,
            'type': field_type,
            'binary': field_binary,
            'viewable': field_viewable,
            'comment': tool_comment,
            'mti_value': mti_value
        }      
        if "DE.003S" in field_id:
            if current_parent_field is not None:
                parent_field_list = current_parent_field.find('FieldList')
                add_field_to_list(parent_field_list, field_data, is_subfield=True, subfield_num=subfield_counter)
                subfield_counter += 1
        else:
            current_parent_field = add_field_to_list(root, field_data)
            subfield_counter = 1
    xml_str = ET.tostring(root, encoding='unicode')
    xml_str_pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")
    return xml_str_pretty
with open('input.html', 'r') as file:
    html_table = file.read()
xml_output = convert_html_to_xml_with_field_list(html_table)
print(xml_output)
