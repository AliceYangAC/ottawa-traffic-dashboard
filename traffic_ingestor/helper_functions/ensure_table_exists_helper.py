from azure.data.tables import TableServiceClient

def ensure_table_exists(STORAGE_CONNECTION_STRING, TABLE_NAME):
    """
    Ensure that the given table exists in Table Storage (Azurite or Azure).
    Creates it if it does not exist.
    """
    try:
        service = TableServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        service.create_table_if_not_exists(TABLE_NAME)
        print(f"Table '{TABLE_NAME}' is ready.")
    except Exception as e:
        print(f"Failed to ensure table exists: {e}")
