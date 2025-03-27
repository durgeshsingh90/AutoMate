import os
import re
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger()

# Function to extract date and timestamp from a line
def extract_timestamp(line):
    timestamp_patterns = [
        r'\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}',  # Pattern with milliseconds
        r'\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}'           # Pattern without milliseconds
    ]
    
    for pattern in timestamp_patterns:
        match = re.match(pattern, line)
        if match:
            return match.group(0)
    return None

# Sorting logs based on timestamp
def sort_logs(logs):
    def parse_timestamp(timestamp):
        try:
            # Try parsing with milliseconds first
            return datetime.strptime(timestamp, '%y.%m.%d %H:%M:%S.%f')
        except ValueError:
            # If parsing with milliseconds fails, try without milliseconds
            return datetime.strptime(timestamp, '%y.%m.%d %H:%M:%S')
        except ValueError as e:
            logger.error(f"Error parsing timestamp {timestamp}: {e}")
            raise

    try:
        logs.sort(key=lambda x: parse_timestamp(x[0]))
    except ValueError:
        logger.critical("Critical error encountered while parsing timestamps. Terminating script.")
        exit(1)

    return logs

# Reading and combining logs from multiple files
def process_log_files(log_files):
    logs = []
    for file_path in log_files:
        try:
            logger.info(f"Processing file: {file_path}")
            with open(file_path, 'r') as f:
                current_timestamp = None
                for line in f:
                    timestamp = extract_timestamp(line)
                    if timestamp:
                        current_timestamp = timestamp
                        logs.append((current_timestamp, line.strip(), file_path, True))
                        logger.debug(f"File: {os.path.basename(file_path)} - Timestamp found: {current_timestamp}")
                    else:
                        if current_timestamp:
                            logs.append((current_timestamp, line.strip(), file_path, False))
                            logger.debug(f"File: {os.path.basename(file_path)} - Appending line to previous timestamp: {current_timestamp}")
            logger.info(f"Finished processing file: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    return logs

# Writing combined and sorted logs to an output file
def write_combined_logs(logs, output_file):
    try:
        with open(output_file, 'w') as f:
            for _, log, file_path, has_timestamp in logs:
                if has_timestamp:
                    f.write(f'{os.path.basename(file_path)} {log}\n')
                else:
                    f.write(f'{log}\n')
        logger.info(f"Combined log file created at {output_file}")
    except Exception as e:
        logger.error(f"Error writing to output file {output_file}: {e}")

# Function to find message ID for the given search pattern
def find_message_id(combined_log_file, search_pattern):
    try:
        with open(combined_log_file, 'r') as f:
            lines = f.readlines()

        message_id = None
        for i, line in enumerate(lines):
            if 'INBOUND MESSAGE ID' in line:
                message_id_match = re.search(r'INBOUND MESSAGE ID\[(.*?)\]', line)
                if message_id_match:
                    message_id = message_id_match.group(1)
                    # Check if the subsequent lines contain the search pattern
                    for j in range(i + 1, min(i + 11, len(lines))):
                        if search_pattern in lines[j]:
                            return message_id

        logger.error(f"Message ID not found preceding the search pattern '{search_pattern}'.")
        return None

    except Exception as e:
        logger.error(f"Error finding message ID in combined log: {e}")
        return None

# Function to search for the message ID and extract relevant lines
def search_and_extract(combined_log_file, message_id):
    try:
        with open(combined_log_file, 'r') as f:
            lines = f.readlines()

        first_message_id_idx = None
        last_message_id_idx = None
        for i, line in enumerate(lines):
            if message_id in line:
                if first_message_id_idx is None:
                    first_message_id_idx = i
                last_message_id_idx = i

        if first_message_id_idx is None or last_message_id_idx is None:
            logger.error(f"Message ID '{message_id}' not found in the combined log.")
            return None

        # Extract the lines between the first and last occurrence of the message ID
        extracted_lines = lines[first_message_id_idx:last_message_id_idx + 1]
        return extracted_lines

    except Exception as e:
        logger.error(f"Error searching and extracting log: {e}")
        return None

# Main function to read all .debug files and combine them
def main():
    folder_path = input("Enter the folder path: ")
    log_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.debug')]
    
    # Filter out empty files
    log_files = [file for file in log_files if os.path.getsize(file) > 0]
    
    if not log_files:
        logger.info("No .debug files found or all files are empty.")
        return

    logger.info(f"Found {len(log_files)} log files to process.")

    combined_logs = process_log_files(log_files)

    if not combined_logs:
        logger.info("No logs were processed. Please check the log files for valid content.")
        return

    logger.info(f"Total logs processed: {len(combined_logs)}")

    sorted_logs = sort_logs(combined_logs)
    output_file = os.path.join(folder_path, 'combined.log')
    write_combined_logs(sorted_logs, output_file)

    # Search for the message ID based on user input
    user_input = input("Enter the string to search for: ")
    search_pattern = f"in[ 37: ]<{user_input}>"

    message_id = None
    
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()

        message_id = None
        for i, line in enumerate(lines):
            if 'INBOUND MESSAGE ID' in line:
                message_id_match = re.search(r'INBOUND MESSAGE ID\[(.*?)\]', line)
                if message_id_match:
                    message_id = message_id_match.group(1)
                    # Check if the subsequent lines contain the search pattern
                    for j in range(i + 1, min(i + 21, len(lines))):  # Increasing range for more context
                        if search_pattern in lines[j]:
                            break
                    else:
                        message_id = None  # reset if match not found
            if message_id:
                break

        if message_id:
            # Function call to extract relevant lines from log
            extracted_lines = search_and_extract(output_file, message_id)
            if extracted_lines:
                # Save extracted lines to a new file
                extracted_file = os.path.join(folder_path, 'extracted.log')
                with open(extracted_file, 'w') as f:
                    f.writelines(extracted_lines)
                logger.info(f"Extracted log file created at {extracted_file}")
        else:
            logger.error(f"Message ID not found preceding the search pattern '{search_pattern}'.")

    except Exception as e:
        logger.error(f"Error processing log: {e}")

if __name__ == '__main__':
    main()
