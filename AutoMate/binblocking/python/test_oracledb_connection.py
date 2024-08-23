import oracledb

# Replace these values with your actual database connection details
username = 'oasis77'
password = 'ist0py'
dsn = 'istu2_equ'  # This is your TNS name

try:
    connection = oracledb.connect(
        user=username,
        password=password,
        dsn=dsn
    )
    print("Connection successful!")

    # Create a cursor
    cursor = connection.cursor()

    # Run a test query
    test_query = "SELECT * FROM your_table_name WHERE ROWNUM <= 10"
    cursor.execute(test_query)

    # Fetch and print the results
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except oracledb.DatabaseError as e:
    error, = e.args
    print(f"Database connection error: {error.message}")
