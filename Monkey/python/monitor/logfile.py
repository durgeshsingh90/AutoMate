import paramiko
import time
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import threading
import signal
import sys

# List of servers and their log files
servers = [
    {
        'hostname': 'a5cvap1003.1dc.com',
        'port': 22,
        'username': 'z94gdos',
        'private_key_path': r'C:\Users\f94gdos\.ssh\id_rsa',
        'log_files': [
            '/app/dev77/site/log/debug/visadump.debug',
            '/app/dev77/site/log/debug/mcnormaldump.debug',
            '/app/dev77/site/log/debug/iso8583dump.debug',
            '/app/dev77/site/log/debug/dinersdump.debug',
            '/app/dev77/site/log/debug/shcdump.debug',
        ]
    },
    {
        'hostname': 'a5cvap1004.1dc.com',
        'port': 22,
        'username': 'z94gdos',
        'private_key_path': r'C:\Users\f94gdos\.ssh\id_rsa',
        'log_files': [
            '/app/test77/site/log/debug/visadump.debug',
            '/app/test77/site/log/debug/mcnormaldump.debug',
            '/app/test77/site/log/debug/iso8583dump.debug',
            '/app/test77/site/log/debug/dinersdump.debug',
            '/app/test77/site/log/debug/shcdump.debug',
        ]
    }
]


local_base_path = 'logs'  # Base folder to store logs
duration_minutes = 10  # Set the duration to 10 minutes
max_lines = 1000  # Set the max number of lines to keep in the log file
buffer_size = 50  # Number of lines to buffer before writing to file
summary_interval = 10  # Interval in seconds to update the summary

if not os.path.exists(local_base_path):
    os.makedirs(local_base_path)

# Create a stop event
stop_event = threading.Event()

def create_directory(hostname):
    folder_path = os.path.join(local_base_path, hostname)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_log_to_file(local_file_path, buffer):
    with open(local_file_path, 'a') as f:
        f.writelines(buffer)

def read_log_from_server(server, log_file):
    hostname = server['hostname']
    port = server['port']
    username = server['username']
    private_key_path = server['private_key_path']

    # Load private key
    try:
        private_key = paramiko.RSAKey(filename=private_key_path)
    except Exception as e:
        print(f"Error loading private key for {hostname}: {e}")
        stop_event.set()
        return

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the server using the private key
        ssh.connect(hostname, port, username, pkey=private_key)
    except Exception as e:
        print(f"Error connecting to {hostname}: {e}")
        stop_event.set()
        return

    try:
        # Open SFTP session
        sftp = ssh.open_sftp()

        local_folder = create_directory(hostname)
        log_file_name = os.path.basename(log_file)
        local_file_path = os.path.join(local_folder, log_file_name)

        # Open the remote log file and start at the end for tailing
        with sftp.open(log_file, 'r') as remote_file:
            # Move the file pointer to the end of the file
            remote_file.seek(0, 2)

            # Use deque to maintain a fixed number of lines
            lines = deque(maxlen=max_lines)
            buffer = []
            line_count = 0
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            last_summary_time = datetime.now()

            while datetime.now() < end_time and not stop_event.is_set():
                try:
                    line = remote_file.readline()
                    if line:
                        lines.append(line)
                        buffer.append(line)
                        line_count += 1
                        # Write buffer to file periodically
                        if len(buffer) >= buffer_size:
                            save_log_to_file(local_file_path, buffer)
                            buffer.clear()

                    # Print summary at regular intervals
                    if (datetime.now() - last_summary_time).seconds >= summary_interval:
                        print_summary(hostname, log_file_name, line_count)
                        last_summary_time = datetime.now()

                    # Sleep briefly to avoid busy-waiting (adjust interval as necessary)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error reading log file {log_file} on {hostname}: {e}")
                    stop_event.set()
                    break

            if buffer:
                save_log_to_file(local_file_path, buffer)

            if stop_event.is_set():
                print(f"Stopped reading {log_file} on {hostname} due to stop event!")
    except Exception as e:
        print(f"Error processing {log_file} on {hostname}: {e}")
        stop_event.set()
    finally:
        # Close the SFTP session and SSH connection
        try:
            if 'sftp' in locals():
                sftp.close()
            ssh.close()
        except Exception as e:
            print(f"Error closing connection to {hostname}: {e}")

def print_summary(hostname, log_file_name, line_count):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Host: {hostname}, Log File: {log_file_name}, Total Lines Read: {line_count}")

# Signal handler for stopping threads
def signal_handler(sig, frame):
    print('Stopping all connections...')
    stop_event.set()
    # Allow some time for threads to terminate gracefully
    time.sleep(2)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Create a ThreadPoolExecutor to read logs in parallel
with ThreadPoolExecutor() as executor:
    futures = []
    for server in servers:
        for log_file in server['log_files']:
            futures.append(executor.submit(read_log_from_server, server, log_file))

    # Wait for all futures to complete
    for future in futures:
        future.result()
