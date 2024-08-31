from django.http import JsonResponse
import re
import logging
import json
import os

# Configure logger for detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define a console handler for outputting log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Define a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)

# Load field definitions from the JSON file
def load_field_definitions():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'omnipay_fields_definitions.json')) as f:
            field_definitions = json.load(f)
            logger.info("Field definitions loaded successfully.")
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

            logger.info("Received request for log parsing.")
            logger.debug(f"Raw log data received: {log_data}")

            # Always parse the log data
            parsed_output = parse_iso8583(log_data)

            logger.info("Log data parsed successfully.")
            logger.debug(f"Parsed output: {parsed_output}")

            # Return the parsed output
            return JsonResponse({'status': 'success', 'result': parsed_output})

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            logger.critical(f"Unexpected error during log parsing: {e}")
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'})

    logger.warning(f"Invalid request method: {request.method}")
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def parse_iso8583(log_data):
    message = {}
    de007_parts = []
    bm43_parts = []
    de055_parts = []
    mti = ""

    lines = log_data.split("\n")
    logger.debug(f"Number of lines received for parsing: {len(lines)}")

    # Search for MTI anywhere in the input
    for line in lines:
        logger.debug(f"Processing line: '{line.strip()}'")
        if not mti:
            mti_match = re.match(r"msgno\[\s*0\]<(.+)>", line.strip())
            if mti_match:
                mti = str(mti_match.group(1))
                logger.info(f"MTI extracted: {mti}")
                continue

    # Extract Data Elements
    for line in lines:
        line = line.strip()
        if not line:
            logger.debug("Skipping empty line.")
            continue

        if "in[  126 ]" in line or "DE0129" in line:
            logger.info(f"Skipping line with sensitive information: {line.strip()}")
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
                if field_number == '003':
                    value = value.ljust(field_length, '0')
                    logger.debug(f"Adjusted field {field_number} to match length: {value}")
                elif field_number == '004':
                    value = value.zfill(field_length)
                    logger.debug(f"Adjusted field {field_number} to match length: {value}")

            # Special handling for BM 60, 61, and 62
            if field_number in ['060', '061', '062']:
                value = parse_bm6x(value)
                logger.info(f"Parsed BM {field_number}: {value}")

            # Handling for DE 55 across multiple lines
            if field_number == '055':
                de055_parts.append(value)
                logger.debug(f"Accumulating DE 55 parts: {de055_parts}")
                continue

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

            message[f"BM{field_number}"] = value

    # Combine and pad DE007
    if de007_parts:
        combined_de007 = ''.join(de007_parts)
        message["BM007"] = combined_de007.zfill(10)
        logger.info(f"Combined BM 007: {message['BM007']}")

    # Combine parts of BM 43
    if bm43_parts:
        message["BM043"] = ' '.join(bm43_parts).strip()
        logger.info(f"Combined BM 43: {message['BM043']}")

    # Combine parts of DE 55 and parse as TLV
    if de055_parts:
        combined_de055 = ''.join(de055_parts)
        logger.debug(f"Combined DE 55: {combined_de055}")
        parsed_de055 = parse_emv_field_55(combined_de055)
        message["BM055"] = parsed_de055
        logger.info(f"Parsed BM 055: {message['BM055']}")

    # Sort message by keys in ascending order
    sorted_message = dict(sorted(message.items()))

    # Place MTI at the top of the sorted message
    if mti:
        sorted_message = {"MTI": mti, **sorted_message}

    logger.info("Final message constructed successfully.")
    logger.debug(f"Final sorted message: {sorted_message}")

    return sorted_message

def parse_emv_field_55(emv_data):
    parsed_tlvs = {}
    index = 0

    de055_subfields = FIELD_DEFINITIONS.get("DE055", {}).get("subfields", {})
    logger.debug(f"Parsing DE 55 data with available subfields: {de055_subfields.keys()}")

    while index < len(emv_data):
        tag = emv_data[index:index + 2]
        index += 2

        if (int(tag, 16) & 0x1F) == 0x1F:
            tag += emv_data[index:index + 2]
            index += 2

        if tag not in de055_subfields:
            logger.warning(f"Tag {tag} not defined in DE 55 subfields.")
            continue

        length = int(emv_data[index:index + 2], 16)
        index += 2

        if length > 127:
            length_of_length = length - 128
            length = int(emv_data[index:index + length_of_length * 2], 16)
            index += length_of_length * 2

        max_length = de055_subfields[tag]["max_length"]
        if length > max_length:
            logger.warning(f"Truncating length for tag {tag} from {length} to {max_length}.")
            length = max_length

        value = emv_data[index:index + length * 2]
        index += length * 2

        parsed_tlvs[tag] = value
        logger.debug(f"Parsed TLV {tag}: {value}")

    logger.info("Completed parsing DE 55.")
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
