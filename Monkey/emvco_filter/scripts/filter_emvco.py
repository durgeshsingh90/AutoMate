# scripts/filter_emvco.py

import os
import xml.etree.ElementTree as ET

def element_to_string(element):
    content = []
    for elem in element.iter():
        if elem.text:
            content.append(elem.text.strip())
    return " ".join(content)

def evaluate_conditions(content, conditions):
    def parse_condition(condition):
        if ' AND ' in condition:
            sub_conditions = condition.split(' AND ')
            return all(parse_condition(sub) for sub in sub_conditions)
        elif ' OR ' in condition:
            sub_conditions = condition.split(' OR ')
            return any(parse_condition(sub) for sub in sub_conditions)
        elif ' NOT ' in condition:
            sub_conditions = condition.split(' NOT ')
            return not parse_condition(sub_conditions[1])
        else:
            return condition in content
    return parse_condition(conditions)

def filter_online_messages(xml_file_path, conditions):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    online_message_list = root.find('OnlineMessageList')
    if online_message_list is not None:
        for online_message in list(online_message_list.findall('OnlineMessage')):
            content = element_to_string(online_message)
            if evaluate_conditions(content, conditions):
                continue
            else:
                online_message_list.remove(online_message)

    base_name, ext = os.path.splitext(xml_file_path)
    output_file = f"{base_name}_pspfiltered{ext}"
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return output_file
