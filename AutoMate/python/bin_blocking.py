prod_insert_statements = [
    "INSERT INTO PROD_SHCEXTBINDB (LOWBIN, HIGHBIN, DESCRIPTION, BIN_LENGTH, CARDPRODUCT, COUNTRY_CODE, DESTINATION, ENTITY_ID, FILE_DATE, FILE_NAME, FILE_VERSION, NETWORK_CONFIG, NETWORK_DATA, LEVEL, STATUS) VALUES (221000000000000, 221672999999999, 'Europay', None, 'Europay', None, '500', None, '2003-06-25', 'EUFILE', '1.10', None, None, 0, 'A');",
    "INSERT INTO PROD_SHCEXTBINDB (LOWBIN, HIGHBIN, DESCRIPTION, BIN_LENGTH, CARDPRODUCT, COUNTRY_CODE, DESTINATION, ENTITY_ID, FILE_DATE, FILE_NAME, FILE_VERSION, NETWORK_CONFIG, NETWORK_DATA, LEVEL, STATUS) VALUES (221673000000000, 221673999999999, 'Russian', None, 'Russian', None, '500', None, '2024-08-28', 'EUFILE', '1.10', None, None, 0, 'B');"
]
processed_bins = 221673

def binblocking(processed_bins, production_data):
    # Step 1: Print processed_bins and production_data
    print(f"Processed Bins: {processed_bins}")
    print(f"Production Data: {production_data}")
    
    # Store production_data in a variable
    original_production_data = production_data
    
    # Create a copy of the production data
    production_data_copy = production_data[:]

    # Print the original and the copy to verify
    print(f"Original Production Data: {original_production_data}")
    print(f"Copied Production Data: {production_data_copy}")

    # Dummy value for sorted_production_rows_copy
    sorted_production_rows_copy = ["Dummy Value"]

    return sorted_production_rows_copy

# Call the function
binblocking(processed_bins, '\n'.join(prod_insert_statements))
