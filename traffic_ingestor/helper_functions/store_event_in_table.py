from azure.data.tables import TableServiceClient
# Helper function to store new events in Azure Table Storage, delete them if no longer active,
# and avoid duplicating existing events
def store_event_in_table(event, STORAGE_CONNECTION_STRING, TABLE_NAME):
    try:
        # print("Checking to see if I need to or can store this event in the function:", event)
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)

        event_id = event.get("id", "Unknown ID")
        event_type = event.get("eventType", "Unknown event")
        row_key = f"{event_id}-{event_type}"

        # Handle both structures
        if "schedule" in event and isinstance(event["schedule"], list):
            start_time = event["schedule"][0].get("startDateTime", "")
            end_time = event["schedule"][0].get("endDateTime", "")
            location = event.get("message", "Unknown location")
        else:
            start_time = event.get("created", "")
            end_time = event.get("updated", "")
            location = event.get("headline", event.get("message", "Unknown location"))

        priority = event.get("priority", "")
        status = event.get("status", "")
        geodata = event.get("geodata", {}).get("coordinates", "")

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
            "Location": location,
            "StartTime": start_time,
            "EndTime": end_time,
            "Priority": priority,
            "Status": status,
            "GeoCoordinates": geodata
        }

        print(f"Attempting to insert the event: {entity}")
        table_client.create_entity(entity)
        print(f"Stored new event in Table Storage: {row_key}")
    except Exception as e:
        print(f"Failed to store event in Table Storage: {str(e)}")

