import subprocess

def connect_to_oracle_sqlplus(query):
    """
    Connect to an Oracle database using SQL*Plus and execute a query.

    Args:
        query (str): The SQL query to execute, which can be multiline.

    Returns:
        str: The output of the SQL*Plus command.
    """
    # Connection details
    conn_str = "oasis77/ist0py@istu2_equ"

    # Command to execute using SQL*Plus
    sqlplus_command = f"sqlplus -S {conn_str}"

    try:
        # Run the command using subprocess
        result = subprocess.run(sqlplus_command, input=query, text=True, capture_output=True, shell=True)
        # Return the output
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return str(e)

# Example usage with a multiline query
query = """
SELECT * 
FROM your_table
WHERE column1 = 'value1'
AND column2 = 'value2';
"""  # Replace with your actual SQL query

output = connect_to_oracle_sqlplus(query)
print(output)
