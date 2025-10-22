from azure.data.tables import TableServiceClient

# Helper function to delete inactive events every time the function is triggered
# in real time

def cleanup_inactive_events(events, STORAGE_CONNECTION_STRING, TABLE_NAME):
    try:
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)

        # Build set of current RowKeys from API response
        current_keys = set()
        for event in events:
            event_id = event.get("id", "Unknown")
            event_type = event.get("eventType", "Unknown")
            row_key = f"{event_id}-{event_type}"
            current_keys.add(row_key)

        # Query all entities in storage
        entities = table_client.query_entities("PartitionKey eq 'OttawaTraffic'")
        for entity in entities:
            row_key = entity["RowKey"]
            status = entity.get("Status", "")
            if status != "ACTIVE" or row_key not in current_keys:
                print(f"Deleting outdated or inactive event: {row_key}")
                table_client.delete_entity(partition_key=entity["PartitionKey"], row_key=row_key)
    except Exception as e:
        print(f"Failed to clean up inactive or outdated events: {str(e)}")