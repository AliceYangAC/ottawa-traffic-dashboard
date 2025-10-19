import azure.functions as func
import logging
import requests
import time
import os
from azure.data.tables import TableServiceClient
from jsonschema import validate, ValidationError
from dotenv import load_dotenv

load_dotenv()

app = func.FunctionApp()

# Configuration; later store in key vault or environment variables
# Store EDA_WEBHOOK_URL in Azure Key Vault to avoid hardcoding secrets.
EDA_WEBHOOK_URL = os.getenv("EDA_WEBHOOK_URL")
TRAFFIC_URL = os.getenv("TRAFFIC_URL")
STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

TABLE_NAME = "TrafficEvents"

EDA_PAYLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "eventType": {"type": "string"},
        "location": {"type": "string"},
        "timestamp": {"type": "string"},
        "priority": {"type": "string"},
        "status": {"type": "string"}
    },
    "required": ["eventType", "location", "timestamp", "priority", "status"]
}

# Retry configuration
MAX_RETRIES = 3
BACKOFF_SECONDS = 5

KANATA_KEYWORDS = [
    "Kanata", "March Road", "Terry Fox Drive", "Eagleson Road",
    "Carling Avenue", "Legget Drive", "Solandt Road", "Campeau Drive",
    "Innovation Drive", "Klondike Road", "Huntmar Drive"
]

# Helper function to see if the traffic event if near a Kanata street
def is_kanata_event(event):
    location = event.get("location", {})
    description = location.get("description", "").lower()
    return any(keyword.lower() in description for keyword in KANATA_KEYWORDS)

# Helper function to store new events in Azure Table Storage, delete them if no longer active,
# and avoid duplicating existing events
def store_event_in_table(event):
    try:
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)

        location = event.get("location", {})
        description = location.get("description", "Unknown location")
        event_type = event.get("eventType", "Unknown event")
        timestamp = event.get("startTime", "")
        priority = event.get("priority", "")
        status = event.get("status", "")

        row_key = f"{event_type}-{timestamp.replace(':', '').replace('-', '').replace('T', '')}"

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
            "Timestamp": timestamp,
            "Priority": priority,
            "Status": status
        }

        table_client.create_entity(entity)
        print(f"Stored new event in Table Storage: {row_key}")
    except Exception as e:
        print(f"Failed to store event in Table Storage: {str(e)}")

# Helper function to delete inactive events every time the function is triggered
# in real time
def cleanup_inactive_events(current_event_keys):
    try:
        table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name=TABLE_NAME)

        entities = table_client.query_entities("PartitionKey eq 'OttawaTraffic'")
        for entity in entities:
            if entity["RowKey"] not in current_event_keys:
                print(f"Deleting inactive event: {entity['RowKey']}")
                table_client.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
    except Exception as e:
        print(f"Failed to clean up inactive events: {str(e)}")

@app.function_name(name="FetchTrafficEvents")
@app.route(route="FetchTrafficEvents", auth_level=func.AuthLevel.ANONYMOUS)
def fetch_traffic_events(req: func.HttpRequest) -> func.HttpResponse:
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            print(f"Attempt {attempt + 1} to fetch traffic events")
            response = requests.get(TRAFFIC_URL, timeout=10)
            response.raise_for_status()

            # Log raw response for debugging
            print(f"Raw response (truncated): {response.text[:500]}")

            # Try to parse and log keys
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"Top-level keys in response: {list(data.keys())}")
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    print(f"Keys in first list item: {list(data[0].keys())}")
                else:
                    print("Response is not a dict or list of dicts.")
            except Exception as e:
                print(f"Failed to parse JSON or extract keys: {str(e)}")

            # Parse JSON safely
            data = response.json()

            # If the API returns a dict with 'events' key, extract it
            if isinstance(data, dict) and "events" in data:
                events = data["events"]
            elif isinstance(data, list):
                events = data
            else:
                print("Unexpected data format from traffic API")
                return func.HttpResponse("Unexpected data format", status_code=500)

            high_priority = [
                e for e in events
                if isinstance(e, dict) and
                e.get("priority") == "HIGH" and
                e.get("status") == "ACTIVE" 
                # and is_kanata_event(e)
            ]

            # Store the current events to later ensure no duplication in Azure Table
            current_event_keys = set()

            for event in high_priority:
                description = event.get("message", "Unknown location")
                event_type = event.get("eventType", "Unknown event")

                print(f"Triggering EDA for {event_type} at {description}".encode('ascii', 'replace').decode())
                payload = {
                    "eventType": event_type,
                    "location": description,
                    "timestamp": event.get("startTime", ""),
                    "priority": event.get("priority", ""),
                    "status": event.get("status", "")
                }
                
                # Generate RowKey
                start_time = event.get("startTime", "unknown")
                row_key = f"{event.get('eventType', 'UnknownEvent')}-{start_time.replace(':', '').replace('-', '').replace('T', '')}"
                current_event_keys.add(row_key)
                
                try:
                    validate(instance=payload, schema=EDA_PAYLOAD_SCHEMA)
                    eda_response = requests.post(EDA_WEBHOOK_URL, json=payload, timeout=10)
                    eda_response.raise_for_status()
                    print(f"EDA triggered successfully for {event_type} at {description}: {eda_response.status_code}")
                    store_event_in_table(event)
                except ValidationError as ve:
                    print(f"Payload validation failed: {ve.message}".encode('ascii', 'replace').decode())
                except requests.exceptions.RequestException as e:
                    print(f"Failed to trigger EDA for {event_type} at {description}: {str(e)}".encode('ascii', 'replace').decode())

            cleanup_inactive_events(current_event_keys)
            return func.HttpResponse(str(high_priority), status_code=200)

        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {type(e).__name__} - {str(e)}")
            attempt += 1
            time.sleep(BACKOFF_SECONDS * attempt)

    print("All retries failed. Could not fetch traffic events.")
    return func.HttpResponse("Failed to fetch traffic events after retries", status_code=500)
