from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceNotFoundError

def store_event_in_table(event, connection_string, table_name):
    table_service = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service.get_table_client(table_name)

    partition_key = event["PartitionKey"]
    row_key = event["RowKey"]

    try:
        # Check if entity already exists
        existing = table_client.get_entity(partition_key=partition_key, row_key=row_key)
        print(f"Event {row_key} already exists in Table Storage: {existing} Skipping insert.")
    except ResourceNotFoundError:
        # Entity does not exist — safe to insert
        try:
            table_client.upsert_entity(event)
            print(f"Stored event {row_key} in Table Storage.")
        except Exception as e:
            print(f"Failed to store entity {row_key}: {e}")
