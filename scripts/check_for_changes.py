import os
import requests
from azure.data.tables import TableServiceClient

# Load environment variables
TRAFFIC_URL = os.getenv("TRAFFIC_URL")
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
TABLE_NAME = os.getenv("TABLE_NAME", "TrafficEvents")
FUNCTION_URL = os.getenv("FUNCTION_URL")

def fetch_traffic_data():
    try:
        response = requests.get(TRAFFIC_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "events" in data:
            return data["events"]
        elif isinstance(data, list):
            return data
        else:
            print("Unexpected data format from traffic API")
            return []
    except Exception as e:
        print(f"Error fetching traffic data: {e}")
        return []

def load_existing_events():
    try:
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)
        entities = table_client.query_entities("PartitionKey eq 'OttawaTraffic'")
        return {entity["RowKey"]: entity for entity in entities}
    except Exception as e:
        print(f"Error loading existing events: {e}")
        return {}

def detect_changes(new_events, existing_events):
    changes = []
    for event in new_events:
        event_id = event.get("id", "Unknown")
        event_type = event.get("eventType", "Unknown")
        row_key = f"{event_id}-{event_type}"
        priority = event.get("priority", "")
        status = event.get("status", "")

        existing = existing_events.get(row_key)
        if not existing or existing.get("Priority") != priority or existing.get("Status") != status:
            changes.append(row_key)
    return changes

def trigger_function(changed_keys):
    if not FUNCTION_URL:
        print("FUNCTION_URL not set. Skipping function trigger.")
        return
    try:
        payload = {"changed_keys": changed_keys}
        response = requests.post(FUNCTION_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Function triggered successfully. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error triggering Azure Function: {e}")

if __name__ == "__main__":
    new_events = fetch_traffic_data()
    existing_events = load_existing_events()
    changed_keys = detect_changes(new_events, existing_events)

    if changed_keys:
        print(f"Detected {len(changed_keys)} new or changed events:")
        for key in changed_keys:
            print(f" - {key}")
        trigger_function(changed_keys)
    else:
        print("No new or changed events detected.")