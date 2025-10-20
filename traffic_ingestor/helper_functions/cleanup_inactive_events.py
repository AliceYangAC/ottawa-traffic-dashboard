from azure.data.tables import TableServiceClient

# Helper function to delete inactive events every time the function is triggered
# in real time
def cleanup_inactive_events(STORAGE_CONNECTION_STRING, TABLE_NAME):
    try:
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)

        entities = table_client.query_entities("PartitionKey eq 'OttawaTraffic'")
        
        all_keys = {entity["RowKey"] for entity in entities}
        print("Checking if all the entries here are active:", all_keys)
        for entity in entities:
            status = entity.get("Status", "")
            if status != "ACTIVE":
                print(f"Deleting inactive event: {entity['RowKey']}")
                table_client.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
    except Exception as e:
        print(f"Failed to clean up inactive events: {str(e)}")