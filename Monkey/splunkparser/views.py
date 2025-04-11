import json
import logging
import os
import re
import random
from django.http import JsonResponse
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('splunkparser')

settings_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'settings.json')
output_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'output.json')
field_definitions_path = os.path.join(settings.MEDIA_ROOT, 'global', 'omnipay_fields_definitions.json')

def editor_page(request):
    logger.info("Rendering the main editor page.")
    return render(request, 'splunkparser/index.html')

def config_editor_page(request):
    logger.info("Rendering the settings editor page.")
    return render(request, 'splunkparser/settings.html')

def get_settings(request):
    if request.method == 'GET':
        try:
            with open(settings_file_path, 'r') as f:
                data = json.load(f)
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': f'Failed to load settings.json: {str(e)}'}, status=500)
    return HttpResponseNotAllowed(['GET'])

@csrf_exempt
def save_settings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            with open(settings_file_path, 'w') as f:
                json.dump(data, f, indent=4)

            return JsonResponse({'status': 'success', 'message': 'Settings saved successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return HttpResponseBadRequest('Only POST method is allowed')

@csrf_exempt
def clear_output_file(request):
    if request.method == 'POST':
        try:
            with open(output_file_path, 'w') as f:
                f.write('{}')
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def save_output_file(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            output_data = data.get('output_data', '{}')
            with open(output_file_path, 'w') as f:
                f.write(output_data)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def parse_logs(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log_data = data.get('log_data', '')
            logger.info("Received request for log parsing.")

            parsed_output = parse_iso8583(log_data)

            return JsonResponse({'status': 'success', 'result': parsed_output})
        except Exception as e:
            logger.exception("Unexpected error during log parsing")
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def set_default_values(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        # Load output.json (parsed ISO8583 message)
        with open(output_file_path, 'r') as f:
            output_data = json.load(f)

        data_elements = output_data.get('data_elements', {})

        # Load settings.json (default config)
        with open(settings_file_path, 'r') as f:
            settings_data = json.load(f)

        # Extract DE002 value
        de002_value = data_elements.get('DE002', '')
        if not de002_value:
            return JsonResponse({'status': 'error', 'message': 'DE002 not found in output.json'})

        logger.info(f"Original DE002: {de002_value}")

        # Progressive prefix matching
        prefix_to_try = de002_value[:4]  # Start with first 4 digits
        logger.info(f"Starting prefix search with: {prefix_to_try}")

        match_found = False
        default_card = None
        scheme_name = None

        # Keep reducing prefix length until at least 1 character is left
        while len(prefix_to_try) > 0:
            logger.info(f"Trying prefix: {prefix_to_try}")

            # Find all matching cards for current prefix
            matching_cards = []
            for scheme in settings_data.get('configs', []):
                for card in scheme.get('cards', []):
                    card_de002 = card.get('DE002', '')
                    if card_de002.startswith(prefix_to_try):
                        matching_cards.append({
                            'scheme': scheme.get('scheme'),
                            'card': card
                        })

            if matching_cards:
                match_found = True
                # Pick one randomly if multiple found
                selected = random.choice(matching_cards)
                scheme_name = selected['scheme']
                default_card = selected['card']
                logger.info(f"Match found! Using scheme: {scheme_name}, card: {default_card.get('cardName')}")
                break

            # Reduce the prefix by 1 character
            prefix_to_try = prefix_to_try[:-1]

        if not match_found:
            logger.error(f"No matching card found for prefix {de002_value[:4]}")
            return JsonResponse({'status': 'error', 'message': f'No matching default card found for prefix {de002_value[:4]}'})

        # Replace masked fields
        for field in ['DE002', 'DE014', 'DE035', 'DE048']:
            current_value = data_elements.get(field, '')
            if '*' in current_value or current_value.strip('*') == '':
                logger.info(f"Replacing masked {field} with default value {default_card.get(field)}")
                data_elements[field] = default_card.get(field, '')

        # Save updated output.json
        with open(output_file_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Return success response including scheme and card name
        return JsonResponse({
            'status': 'success',
            'message': 'Default values applied',
            'result': output_data,
            'scheme': scheme_name,
            'cardName': default_card.get('cardName'),
            'prefix_used': prefix_to_try
        })

    except Exception as e:
        logger.exception("Error applying default values")
        return JsonResponse({'status': 'error', 'message': str(e)})

#=====================Do not edit below lines
# Configure logger for detailed logging
logger = logging.getLogger('splunkparser')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# Load field definitions from the JSON file
def load_field_definitions():
    try:
        with open(field_definitions_path) as f:
            field_definitions = json.load(f)
            logger.info("Field definitions loaded successfully.")
            return field_definitions.get("fields", {})
    except Exception as e:
        logger.error(f"Failed to load field definitions: {e}")
        return {}

# Load field definitions
FIELD_DEFINITIONS = load_field_definitions()

@csrf_exempt
def parse_logs(request):
    if request.method == 'POST':
        try:
            content_type = request.content_type
            if content_type == 'application/json':
                data = json.loads(request.body)
                log_data = data.get('log_data', '')
            elif content_type.startswith('multipart/form-data'):
                file = request.FILES.get('file')
                if file:
                    log_data = file.read().decode('utf-8')
                else:
                    return JsonResponse({'status': 'error', 'message': 'File not provided'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': 'Unsupported content type'}, status=415)

            logger.info("Received request for log parsing.")
            logger.debug(f"Raw log data received: {log_data}")

            parsed_output = parse_iso8583(log_data)

            logger.info("Log data parsed successfully.")
            logger.debug(f"Parsed output: {parsed_output}")

            return JsonResponse({'status': 'success', 'result': parsed_output})

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            logger.critical(f"Unexpected error during log parsing: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
def parse_iso8583(log_data):
    message = {}
    de007_parts = []
    bm43_parts = []
    de053_parts = []
    de055_parts = []
    de090_parts = []
    mti = ""

    lines = log_data.split("\n")
    logger.debug(f"Number of lines received for parsing: {len(lines)}")

    # Detect if log uses only one of "in[" or "out["
    has_in = any("in[" in line for line in lines)
    has_out = any("out[" in line for line in lines)

    if has_in and has_out:
        logger.error("❌ Mixed input: both 'in[' and 'out[' detected.")
        raise ValueError("Log input cannot contain both 'in[' and 'out[' lines. Use only one direction.")

    prefix = "in[" if has_in else "out[" if has_out else None

    if not prefix:
        logger.error("❌ No valid 'in[' or 'out[' prefix detected in input.")
        raise ValueError("Log input must contain either 'in[' or 'out[' lines.")

    escaped_prefix = prefix.replace('[', r'\[').replace(']', r'\]')  # Escape for regex

    data_elements = {}  # Dictionary to store Data Elements

    # Define which DE fields should be converted to integers
    integer_fields = ['004', '049']  # Add more fields if needed
    # Define which DE fields need to be zero-padded and their respective lengths
    pad_zero_fields = {
        '013': 4,
        '019': 3,
        '022': 3,
        '023': 3,
        '025': 2
    }

    # Define the flags for DE053
    first_bm53_skipped = False

    # Search for MTI anywhere in the input
    for line in lines:
        logger.debug(f"Processing line: '{line.strip()}'")
        if not mti:
            mti_match = re.match(r"msgno\[\s*0\]<(.+)>", line.strip())
            if mti_match:
                mti = mti_match.group(1)
                logger.info(f"MTI extracted: {mti}")
                continue

    # Extract Data Elements
    for line in lines:
        line = line.strip()
        if not line:
            logger.debug("Skipping empty line.")
            continue

        if "in[129: ]" in line or "DE0129" in line:
            logger.info(f"Skipping line with sensitive information: {line.strip()}")
            continue

        match = re.match(rf"{escaped_prefix}\s*(\d+):?\s*\]<(.+)>", line)
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
                    if value.strip() and value.strip('0'):  # Ensure non-empty and not just zeros
                        value = int(value.lstrip('0'))
                    else:
                        value = 0
                    logger.debug(f"Set field {field_number} to {value}")

            # Special handling for DE060, 061, and 062
            if field_number in ['060', '061', '062', '066']:
                value = parse_bm6x(value)
                logger.info(f"Parsed DE {field_number}: {value}")

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

            # Handling for DE090
            if field_number == '090':
                de090_parts.append(value)
                logger.debug(f"Accumulating DE 090 parts: {de090_parts}")
                continue

            # Handling for DE 43
            if field_number == '043':
                bm43_parts.append(value)  # Append value without stripping spaces
                logger.debug(f"Accumulating DE 43 parts: {bm43_parts}")
                continue

            # Handling for DE 53: Ignore the first line and combine the rest
            if field_number == '053':
                if not first_bm53_skipped:
                    first_bm53_skipped = True
                    logger.debug(f"Skipping first DE 53 part: {value}")
                else:
                    de053_parts.append(value.strip())  # You can decide whether to strip or not
                    logger.debug(f"Accumulating DE 53 parts: {de053_parts}")
                continue

            # Convert to integer if the field is in the integer_fields list, and it's not empty
            if field_number in integer_fields and field_number != '004':  # Skip DE004 here, as it's handled above
                if value.strip():  # Ensure value is not empty
                    value = int(value.lstrip('0'))
                    logger.debug(f"Converted field {field_number} to integer: {value}")

            # Pad with zeros if the field is in the pad_zero_fields list
            if field_number in pad_zero_fields:
                value = value.zfill(pad_zero_fields[field_number])
                logger.debug(f"Padded field {field_number} with zeros: {value}")

            data_elements[f"DE{field_number}"] = value

    # Combine and pad DE007
    if de007_parts:
        combined_de007 = ''.join(de007_parts)
        data_elements["DE007"] = combined_de007.zfill(10)
        logger.info(f"Combined DE007: {data_elements['DE007']}")

    # Combine and pad DE090
    if de090_parts:
        combined_de090 = ''.join(de090_parts)
        logger.debug(f"Combined DE090: {combined_de090}")
        parsed_de090 = parse_de090_fields(combined_de090)  # Call parse function for DE090
        data_elements["DE090"] = parsed_de090
        logger.info(f"Parsed DE090: {data_elements['DE090']}")

    # Combine parts of DE043 without stripping spaces
    if bm43_parts:
        data_elements["DE043"] = ''.join(bm43_parts)  # Combine without stripping spaces
        logger.info(f"Combined DE043: {data_elements['DE043']}")

    # Combine parts of DE053
    if de053_parts:
        data_elements["DE053"] = ''.join(de053_parts)  # Retain spaces if needed
        logger.info(f"Combined DE053: {data_elements['DE053']}")

    # Combine parts of DE055 and parse as TLV
    if de055_parts:
        combined_de055 = ''.join(de055_parts)
        logger.debug(f"Combined DE055: {combined_de055}")
        parsed_de055 = parse_emv_field_55(combined_de055)  # Parse the combined DE55
        # Update the DE55 data if necessary
        update_de55(parsed_de055)
        data_elements["DE055"] = parsed_de055
        logger.info(f"Parsed DE055: {data_elements['DE055']}")

    # Sort data_elements by keys in ascending order
    sorted_data_elements = dict(sorted(data_elements.items()))

    logger.info("Final data elements constructed successfully.")
    logger.debug(f"Final sorted data elements: {sorted_data_elements}")

    # Convert MTI to integer if it is numeric
    try:
        mti = int(mti)
    except ValueError:
        logger.debug(f"MTI is not numeric: {mti}")

    # Construct the final message
    if mti:
        message["mti"] = mti

    message["data_elements"] = sorted_data_elements

    logger.info("Final message constructed successfully with data elements.")
    logger.debug(f"Final message: {message}")

    return message

# Function to parse DE090 and format its components
def parse_de090_fields(value):
    fields = {
        "orig_mti": value[0:3].zfill(4),
        "orig_stan": value[3:9].zfill(6),
        "orig_xmsn_datetime": value[9:18].zfill(10),
        "orig_acq_id": value[18:29].zfill(11),
        "orig_frwd_id": value[29:40].zfill(11)
    }
    return fields

def parse_emv_field_55(emv_data):
    parsed_tlvs = {}
    index = 3  # Skip the first 3 digits which represent the total length of DE 55
    total_bm55_value_length = 0  # Variable to accumulate the total length of DE55 values

    # Tags that have their value length as exact, not doubled
    exact_length_tags = ["9F1E", "9F13"]  # Add more tags if needed
    # Tags that follow the special logic
    special_tags = ["9F1A", "5F2A", "9C"]  # Add 9C to the list
    de055_subfields = FIELD_DEFINITIONS.get("DE055", {}).get("subfields", {})
    logger.debug(f"Parsing DE 55 data with available subfields: {de055_subfields.keys()}")

    while index < len(emv_data):
        # Determine if the tag is 2 or 4 characters long
        tag = emv_data[index:index + 2]
        index += 2

        # If the first part of the tag is "9F", "5F", or "DF", the tag is 4 characters long
        if tag.startswith(("9F", "5F", "DF")):
            tag += emv_data[index:index + 2]
            index += 2

        # Log the tag extraction
        logger.debug(f"Extracted tag: {tag}")

        # Check if the tag is defined in the subfields
        if tag not in de055_subfields:
            logger.warning(f"Tag {tag} not defined in DE 55 subfields.")
            continue

        # The next two characters represent the length of the value in bytes
        length = int(emv_data[index:index + 2], 16)
        index += 2

        # Log the length
        logger.debug(f"Length of value for tag {tag}: {length}")

        # Special handling for 9F1A, 5F2A, and 9C
        if tag == "9F1A" or tag == "5F2A":
            value = emv_data[index:index + 3]  # Pick only 3 characters for these tags
            index += 3

            # Peek at the next two characters to check if it's a valid tag
            next_two_chars = emv_data[index:index + 2]
            logger.debug(f"Next two characters after {tag}: {next_two_chars}")

            # Check if the next two characters form a valid tag
            if next_two_chars in de055_subfields or next_two_chars.startswith(("9F", "5F", "DF")):
                # If valid, prefix the value with '0'
                value = '0' + value
                logger.debug(f"Prefixed {tag} value: {value}")
        
        elif tag == "9C":
            value = emv_data[index:index + 1]  # Pick only 1 character for 9C
            index += 1

            # Peek at the next two characters to check if it's a valid tag
            next_two_chars = emv_data[index:index + 2]
            logger.debug(f"Next two characters after 9C: {next_two_chars}")

            # Check if the next two characters form a valid tag
            if next_two_chars in de055_subfields or next_two_chars.startswith(("9F", "5F", "DF")):
                # If valid, prefix the value with '0'
                value = '0' + value
                logger.debug(f"Prefixed 9C value: {value}")

        elif tag in exact_length_tags:
            # For exact-length tags, pick exactly the specified number of hex characters
            value = emv_data[index:index + length]
            index += length
            logger.debug(f"Exact-length value for tag {tag}: {value}")
        else:
            # For other tags, pick twice the length (since the value is in hex)
            value = emv_data[index:index + length * 2]
            index += length * 2
            logger.debug(f"Hex-doubled value for tag {tag}: {value}")

        # Store the tag and value in the parsed TLVs dictionary
        parsed_tlvs[tag] = value

        # Accumulate the length of DE55 values
        total_bm55_value_length += len(value)

        logger.debug(f"Extracted value for tag {tag}: {value}")

    # Log the total length of DE55 values
    logger.info(f"Total length of DE55 values: {total_bm55_value_length} characters")

    logger.info("Completed parsing DE 55.")
    return parsed_tlvs

def update_de55(de55_data):
    if '9F1E' in de55_data:
        original_value = de55_data['9F1E']
        hex_value = ''.join(format(ord(c), '02x') for c in original_value)
        de55_data['9F1E'] = hex_value
        logger.info(f"Converted 9F1E value to hexadecimal: {hex_value}")
    else:
        logger.debug("Tag 9F1E not present in DE55 data.")

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
    logger.debug(f"DE6x parsed fields: {parsed_fields}")
    return parsed_fields
