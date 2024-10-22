import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def process_online_messages(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Iterating through all OnlineMessage elements
    for online_message in root.findall(".//OnlineMessage"):
        # Find the Field with ID "NET.1100.DE.007" in the current OnlineMessage
        field_element = online_message.find(".//Field[@ID='NET.1100.DE.007']")
        
        if field_element is not None:
            # Extract the date from the ToolComment tag
            tool_comment = field_element.find("ToolComment").text
            date_str = tool_comment.split('[')[-1].rstrip(']')
            try:
                # Convert the date string to a datetime object
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                
                # Subtract one hour from the date
                new_date_obj = date_obj - timedelta(hours=1)
                
                # Convert the datetime back to string
                new_date_str = new_date_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                
                # Update the Date-Time in MessageInfo of the current OnlineMessage
                date_time_element = online_message.find(".//MessageInfo/Date-Time")
                if date_time_element is not None:
                    date_time_element.text = new_date_str
            except ValueError as e:
                print(f"Date format error: {e}, in comment: {tool_comment}")

    # Write the modified tree back to a file (or you can overwrite the original file)
    tree.write('modified_' + xml_file, encoding='utf-8', xml_declaration=True)

# Example use
# Assumes 'big_file.xml' is the filename of your large XML file.
process_online_messages('output.xml')
