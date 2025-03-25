# AutoMate/emvco_filter/scripts/formatxml.py

import xml.etree.ElementTree as ET

def format_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    def indent(elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for e in elem:
                indent(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
        return elem

    indent(root)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)
