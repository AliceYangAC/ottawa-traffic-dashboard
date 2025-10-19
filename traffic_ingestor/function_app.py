import azure.functions as func
import logging
import requests
import time
from jsonschema import validate, ValidationError

app = func.FunctionApp()

# Configuration; later store in key vault or environment variables
# Store EDA_WEBHOOK_URL in Azure Key Vault to avoid hardcoding secrets.
EDA_WEBHOOK_URL = "https://your-nokia-eda-endpoint.com/api/trigger"
TRAFFIC_URL = "https://traffic.ottawa.ca/map/service/events?accept-language=en"

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

@app.function_name(name="FetchTrafficEvents")
@app.route(route="FetchTrafficEvents", auth_level=func.AuthLevel.ANONYMOUS)
def fetch_traffic_events(req: func.HttpRequest) -> func.HttpResponse:
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logging.info(f"Attempt {attempt + 1} to fetch traffic events")
            response = requests.get(TRAFFIC_URL, timeout=10)
            response.raise_for_status()

            # Log raw response for debugging
            logging.info(f"Raw response: {response.text[:500]}")

            # Parse JSON safely
            data = response.json()

            # If the API returns a dict with 'events' key, extract it
            if isinstance(data, dict) and "events" in data:
                events = data["events"]
            elif isinstance(data, list):
                events = data
            else:
                logging.error("Unexpected data format from traffic API")
                return func.HttpResponse("Unexpected data format", status_code=500)

            high_priority = [
                e for e in events
                if isinstance(e, dict) and e.get("priority") == "HIGH" and e.get("status") == "ACTIVE"
            ]

            for event in high_priority:
                location = event.get("location", {})
                description = location.get("description", "Unknown location")
                event_type = event.get("eventType", "Unknown event")

                logging.info(f"Triggering EDA for {event_type} at {description}")
                payload = {
                    "eventType": event_type,
                    "location": description,
                    "timestamp": event.get("startTime", ""),
                    "priority": event.get("priority", ""),
                    "status": event.get("status", "")
                }

                try:
                    validate(instance=payload, schema=EDA_PAYLOAD_SCHEMA)
                    eda_response = requests.post(EDA_WEBHOOK_URL, json=payload, timeout=10)
                    eda_response.raise_for_status()
                    logging.info(f"EDA triggered successfully for {event_type} at {description}: {eda_response.status_code}")
                except ValidationError as ve:
                    logging.error(f"Payload validation failed: {ve.message}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"Failed to trigger EDA for {event_type} at {description}: {str(e)}")

            return func.HttpResponse(str(high_priority), status_code=200)

        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {type(e).__name__} - {str(e)}")
            attempt += 1
            time.sleep(BACKOFF_SECONDS * attempt)

    logging.error("All retries failed. Could not fetch traffic events.")
    return func.HttpResponse("Failed to fetch traffic events after retries", status_code=500)
