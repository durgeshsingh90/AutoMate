import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('your_database_name.db')

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# SQL command to create the PROD_SHCEXTBINDB table
prod_table = """
CREATE TABLE PROD_SHCEXTBINDB (
    BIN_LENGTH INTEGER,
    CARDPRODUCT TEXT,
    COUNTRY_CODE TEXT,
    DESCRIPTION TEXT,
    DESTINATION TEXT,
    ENTITITY_ID INTEGER,
    FILE_DATE DATE,
    FILE_NAME TEXT,
    FILE_VERSION TEXT,
    HIGHBIN INTEGER,
    LOWBIN INTEGER,
    NETWORK_CONFIG TEXT,
    NETWORK_DATA TEXT,
    LEVEL INTEGER,
    STATUS TEXT
);
"""

# Execute the command
cursor.execute(prod_table)

# SQL command to create the UAT_SHCEXTBINDB table
uat_table = """
CREATE TABLE UAT_SHCEXTBINDB (
    BIN_LENGTH INTEGER,
    CARDPRODUCT TEXT,
    COUNTRY_CODE TEXT,
    DESCRIPTION TEXT,
    DESTINATION TEXT,
    ENTITITY_ID INTEGER,
    FILE_DATE DATE,
    FILE_NAME TEXT,
    FILE_VERSION TEXT,
    HIGHBIN INTEGER,
    LOWBIN INTEGER,
    NETWORK_CONFIG TEXT,
    NETWORK_DATA TEXT,
    LEVEL INTEGER,
    STATUS TEXT
);
"""

# Execute the command
cursor.execute(uat_table)

# Commit the changes
conn.commit()

# Close the connection
conn.close()
