from django.http import JsonResponse
import re
import logging
import json
import os

# Configure logger for detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load field definitions from the JSON file
def load_field_definitions():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'field_definitions.json')) as f:
            field_definitions = json.load(f)
            logger.debug("Field definitions loaded successfully.")
            return field_definitions.get("fields", {})
    except Exception as e:
        logger.error(f"Failed to load field definitions: {e}")
        return {}

# Load field definitions
FIELD_DEFINITIONS = load_field_definitions()

def parse_logs(request):
    if request.method == 'POST':
        try:
            # Read the JSON data directly from the request body
            data = json.loads(request.body)
            log_data = data.get('log_data', '')

            # Debug: Log the raw input data
            logger.debug(f"Received log data: {log_data}")

            # Always parse the log data
            parsed_output = parse_iso8583(log_data)

            # Debug: Log the parsed output after initial parsing
            logger.debug(f"Initial parsed output: {parsed_output}")

            # Return the parsed output
            return JsonResponse({'status': 'success', 'result': parsed_output})

        except json.JSONDecodeError as e:
            # Handle JSON decoding error
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})

    # If not a POST request, return an error
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def parse_iso8583(log_data):
    message = {}
    de007_parts = []  # Array to store parts of DE007
    bm43_parts = []  # Array to store parts of BM 43
    de055_parts = []  # Array to collect multiple lines of DE 55
    mti = ""  # Initialize MTI as an empty string

    lines = log_data.split("\n")

    # Debug: Log the number of lines processed and their content
    logger.debug(f"Number of lines received for parsing: {len(lines)}")
    for line in lines:
        logger.debug(f"Line content: '{line}'")

        # Search for MTI anywhere in the input
        if not mti:  # Only search for MTI if it hasn't been found yet
            mti_match = re.match(r"msgno\[\s*0\]<(.+)>", line.strip())
            if mti_match:
                mti = str(mti_match.group(1))
                logger.debug(f"MTI extracted: {mti}")
                continue  # Continue to the next line after extracting MTI

    # Extract Data Elements
    for line in lines:
        line = line.strip()  # Remove any extra whitespace
        if not line:
            logger.debug("Skipping empty line")
            continue  # Skip empty lines

        if "in[  126 ]" in line or "DE0129" in line:
            logger.debug(f"Skipping line with {line.strip()}")
            continue

        match = re.match(r"in\[\s*(\d+):?\s*\]<(.+)>", line)
        if match:
            field_number = match.group(1).zfill(3)
            value = match.group(2)
            logger.debug(f"Field {field_number} detected with value: {value}")

            # Retrieve field definition
            field_def = FIELD_DEFINITIONS.get(field_number)
            if field_def:
                field_length = field_def.get('length')
                
                # Adjust the length if needed
                if field_length:
                    if field_number == '003':
                        value = value.ljust(field_length, '0')
                    elif field_number == '004':
                        value = value.zfill(field_length)
                    logger.debug(f"Adjusted {field_number} value to match length: {value}")

            # Special handling for BM 60, 61, and 62
            if field_number in ['060', '061', '062']:
                value = parse_bm6x(value)
                logger.debug(f"Parsed BM {field_number}: {value}")

            # Handling for DE 55 across multiple lines
            if field_number == '055':
                de055_parts.append(value)  # Collect all parts of DE 55
                logger.debug(f"Accumulating DE 55 parts: {de055_parts}")
                continue  # Skip adding to message directly for now

            # Handling for DE007
            if field_number == '007':
                de007_parts.append(value)
                logger.debug(f"Accumulating DE 007 parts: {de007_parts}")
                continue

            # Handling for BM 43
            if field_number == '043':
                bm43_parts.append(value.strip())
                logger.debug(f"Accumulating BM 43 parts: {bm43_parts}")
                continue

            message[f"DE{field_number}"] = value

    # Combine and pad DE007
    if de007_parts:
        combined_de007 = ''.join(de007_parts)
        message["DE007"] = combined_de007.zfill(10)
        logger.debug(f"Combined DE 007: {message['DE007']}")

    # Combine parts of BM 43
    if bm43_parts:
        message["DE043"] = ' '.join(bm43_parts).strip()
        logger.debug(f"Combined BM 43: {message['DE043']}")

    # Combine parts of DE 55 and parse as TLV
    if de055_parts:
        combined_de055 = ''.join(de055_parts)  # Merge all parts into a single string
        logger.debug(f"Combined DE 55: {combined_de055}")
        parsed_de055 = parse_emv_field_55(combined_de055)  # Parse combined DE 55 value
        message["DE055"] = parsed_de055
        logger.debug(f"Parsed DE 055: {message['DE055']}")

    # Sort message by keys in ascending order
    sorted_message = dict(sorted(message.items()))

    # Place MTI at the top of the sorted message
    if mti:
        sorted_message = {"MTI": mti, **sorted_message}

    # Debug: Log the final sorted message
    logger.debug(f"Final sorted message: {sorted_message}")

    return sorted_message

def parse_emv_field_55(emv_data):
    parsed_tlvs = {}
    index = 0

    logger.debug(f"Parsing DE 55 data: {emv_data}")

    while index < len(emv_data):
        # Read Tag (1 or 2 bytes)
        tag = emv_data[index:index + 2]
        index += 2

        # Check if the tag is a two-byte tag (if first byte has the form '1F')
        if (int(tag, 16) & 0x1F) == 0x1F:  # Extended tag condition
            tag += emv_data[index:index + 2]
            index += 2

        # Read Length (1 byte or multiple bytes)
        length = int(emv_data[index:index + 2], 16)
        index += 2

        # Check for extended lengths (length > 127 indicates more bytes for length)
        if length > 127:
            length_of_length = length - 128  # Number of bytes that represent the actual length
            length = int(emv_data[index:index + length_of_length * 2], 16)
            index += length_of_length * 2

        # Read Value based on the length
        value = emv_data[index:index + length * 2]
        index += length * 2

        # Store the parsed TLV
        parsed_tlvs[tag] = value
        logger.debug(f"Parsed TLV {tag}: {value}")

    return parsed_tlvs

def parse_bm6x(value):
    subfields = []
    values = []
    i = 0

    while i < len(value):
        subfield_length = int(value[i:i + 3])
        subfield = value[i + 3:i + 5]
        subfields.append(subfield)
        values.append(value[i + 5:i + 5 + subfield_length - 2])
        i += 5 + subfield_length - 2

    parsed_fields = {subfield: values[idx] for idx, subfield in enumerate(subfields)}
    logger.debug(f"BM6x parsed fields: {parsed_fields}")
    return parsed_fields
