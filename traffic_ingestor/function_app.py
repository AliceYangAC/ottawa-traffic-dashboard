import azure.functions as func
import logging
import requests
import time
import os
from dotenv import load_dotenv
from traffic_ingestor.helper_functions import ensure_table_exists, transform_events, sanitize_event, cleanup_inactive_events, publish_events, store_event_in_table, has_new_events, update_hash, get_last_hash

# Explicitly load the .env file from this folder
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

app = func.FunctionApp()

# Later store in Azure Key Vault
TRAFFIC_URL = os.getenv("TRAFFIC_URL")
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
TABLE_NAME = "TrafficEvents"

ensure_table_exists(STORAGE_CONNECTION_STRING, TABLE_NAME)

# Retry configuration
MAX_RETRIES = 3
BACKOFF_SECONDS = 5

# Azure Function to fetch traffic events from Ottawa Traffic API
@app.function_name(name="FetchTrafficEvents")
# @app.schedule(schedule="*/5 * * * *", arg_name="timer", run_on_startup=True, use_monitor=False)
# def fetch_traffic_events(timer: func.TimerRequest) -> None:
@app.route(route="FetchTrafficEvents", auth_level=func.AuthLevel.ANONYMOUS)
def fetch_traffic_events(req: func.HttpRequest) -> func.HttpResponse:
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            # Ensure that traffic events was successfully fetched from the Ottawa Traffic API
            response = requests.get(TRAFFIC_URL, timeout=10)
            response.raise_for_status()

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
                return
                # return func.HttpResponse("Unexpected data format", status_code=500)

            print(f"Total events fetched: {len(events)}")
            
            # Check to see if there are new events using hashing
            if not has_new_events(events, STORAGE_CONNECTION_STRING, "TrafficMetadata"):
                #print("No new traffic events detected. Skipping Event Grid publish.")
                #return
                return func.HttpResponse("No new traffic events detected. Skipping Event Grid publish.", status_code=200)

            # New events exist; transform the events for data visualization, deactivate events not in current
            # API request, and broadcast through Websocket
            else: 
                # Ensure the data has valid characters and keys
                events = transform_events([sanitize_event(e) for e in events])
                for event in events:
                    description = event.get("Location", "Unknown location")
                    event_type = event.get("EventType", "Unknown event")
                    status = event.get("Status", "UNKNOWN")
                    
                    # If the data is ACTIVE, we want to store it
                    try:
                        if status == "ACTIVE":
                            store_event_in_table(event, STORAGE_CONNECTION_STRING, TABLE_NAME)
                        else:
                            pass
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to store event for {event_type} at {description}: {str(e)}".encode('ascii', 'replace').decode())
                        break

                cleanup_inactive_events(events, STORAGE_CONNECTION_STRING, TABLE_NAME)
                # Publish event to trigger traffic_refresher
                publish_events(events)
                print("Ingestion complete.")
                return func.HttpResponse(str(events), status_code=200)
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {type(e).__name__} - {str(e)}")
            attempt += 1
            time.sleep(BACKOFF_SECONDS * attempt)

    print("All retries failed. Could not fetch traffic events.")
    return func.HttpResponse("Failed to fetch traffic events after retries", status_code=500)
