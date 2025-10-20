import azure.functions as func
import logging
import requests
import time
import os
from jsonschema import validate, ValidationError
from dotenv import load_dotenv
from helper_functions import cleanup_inactive_events, get_eda_access_token, store_event_in_table

load_dotenv()

app = func.FunctionApp()

# Later store in Azure Key Vault
TRAFFIC_URL = os.getenv("TRAFFIC_URL")
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
# KEYCLOAK_TOKEN_URL = os.getenv("KEYCLOAK_TOKEN_URL")
# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# USERNAME = os.getenv("USERNAME")
# PASSWORD = os.getenv("PASSWORD")

TABLE_NAME = "TrafficEvents"

# Retry configuration
MAX_RETRIES = 3
BACKOFF_SECONDS = 5

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
                print(f"Looping through high priority list to store {event_type} at {description}".encode('ascii', 'replace').decode())
                try:
                    store_event_in_table(event, STORAGE_CONNECTION_STRING, TABLE_NAME)
                except ValidationError as ve:
                    print(f"Payload validation failed: {ve.message}".encode('ascii', 'replace').decode())
                    break
                except requests.exceptions.RequestException as e:
                    print(f"Failed to store event for {event_type} at {description}: {str(e)}".encode('ascii', 'replace').decode())
                    break

            cleanup_inactive_events(STORAGE_CONNECTION_STRING, TABLE_NAME)
            return func.HttpResponse(str(high_priority), status_code=200)
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {type(e).__name__} - {str(e)}")
            attempt += 1
            time.sleep(BACKOFF_SECONDS * attempt)

    print("All retries failed. Could not fetch traffic events.")
    return func.HttpResponse("Failed to fetch traffic events after retries", status_code=500)
