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
            try:
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

if __name__ == '__main__':
    main()
