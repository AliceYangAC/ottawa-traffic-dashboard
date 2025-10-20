from azure.data.tables import TableServiceClient
# Helper function to store new events in Azure Table Storage, delete them if no longer active,
# and avoid duplicating existing events
def store_event_in_table(event, STORAGE_CONNECTION_STRING, TABLE_NAME):
    try:
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)
        event_id = event.get("id", "Unknown ID")
        description = event.get("message", "Unknown location")
        event_type = event.get("eventType", "Unknown event")
        start_time = event.get("schedule", {})[0].get("startDateTime", "")
        end_time = event.get("schedule", "")[0].get("endDateTime", "")
        priority = event.get("priority", "")
        status = event.get("status", "")

        row_key = f"{event_id}-{event_type}"

        # Check if entity already exists
        try:
            existing = table_client.get_entity(partition_key="OttawaTraffic", row_key=row_key)
            print(f"Event already exists in Table Storage: {row_key}")
            return  # Skip storing duplicate
        except Exception:
            pass  # Entity does not exist, proceed to insert

        entity = {
            "PartitionKey": "OttawaTraffic",
            "RowKey": row_key,
            "EventType": event_type,
            "Location": description,
            "StartTime": start_time,
            "EndTime": end_time,
            "Priority": priority,
            "Status": status
        }
        print(f"Attempting to insert the event: {entity}")
        table_client.create_entity(entity)
        print(f"Stored new event in Table Storage: {row_key}")
    except Exception as e:
        print(f"Failed to store event in Table Storage: {str(e)}")

