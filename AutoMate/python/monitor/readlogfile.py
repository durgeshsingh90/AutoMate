import os
import time
import threading

def tail_f(file_path):
    with open(file_path, 'r') as file:
        file.seek(0, 2)  # Move the cursor to the end of the file
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)  # Sleep briefly and continue
                continue
            print(f"[{file_path}] {line}", end='')  # Print the new line with file path indication

def monitor_log_files(base_directory):
    threads = []
    # Traverse through all directories and files
    for root, _, files in os.walk(base_directory):
        for filename in files:
            if filename.endswith('.debug'):  # Customize this to match your log file types
                file_path = os.path.join(root, filename)
                print(f"Monitoring log file: {file_path}")  # Print the log file being monitored
                # Create a new thread to monitor this file
                thread = threading.Thread(target=tail_f, args=(file_path,))
                thread.daemon = True  # Allow thread to exit when the main program exits
                threads.append(thread)
                thread.start()

    # Keep the main program running to monitor log files
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    base_directory = "logs"  # Replace with your base directory path
    monitor_log_files(base_directory)
