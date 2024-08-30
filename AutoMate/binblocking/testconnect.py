def connect_to_oracle_sqlplus(connection):
  """
  Generate SQL INSERT statements for the data retrieved from the Oracle database using SQL*Plus.
  """
  logger.info(f"Generating SQL insert statements for environment: {connection.environment}")
  try:
      # Construct the SQL*Plus connection string
      conn_str = f"{connection.username}/{connection.password}@{connection.DatabaseTNS}"

      # Construct the query to fetch data
      # query = f"SELECT * FROM {connection.table_name} ORDER BY LOWBIN;"
      query = f"SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 2;" 
      # Command to execute using SQL*Plus
      sqlplus_command = f"sqlplus -S {conn_str}"

      # Run the SQL query using subprocess
      result = subprocess.run(sqlplus_command, input=query, text=True, capture_output=True, shell=True)

      # Check for errors in SQL*Plus execution
      if result.returncode != 0:
          logger.error(f"SQL*Plus error for {connection.environment}: {result.stderr}")
          return []

      # Parse the output from SQL*Plus
      output = result.stdout.strip().splitlines()

prod_insert_statements = connect_to_oracle_sqlplus(prod)