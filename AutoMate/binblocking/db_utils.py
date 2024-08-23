import subprocess

def run_sqlplus_query(username, password, connection_string, query):
    try:
        # Construct the sqlplus command
        command = f'sqlplus -S {username}/{password}@{connection_string}'
        
        # Add the query to the command
        full_command = f'echo "{query}" | {command}'
        
        # Run the command and capture the output
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"Error executing query: {stderr.decode('utf-8')}")

        # Return the output
        return stdout.decode('utf-8')

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
