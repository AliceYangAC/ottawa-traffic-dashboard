from azure.data.tables import TableServiceClient

def store_event_in_table(event, connection_string, table_name):
    table_service = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service.get_table_client(table_name)

    try:
        table_client.upsert_entity(event)
        print(f"Stored event {event['RowKey']} in Table Storage.")
    except Exception as e:
        print(f"Failed to store entity {event['RowKey']}: {e}")
