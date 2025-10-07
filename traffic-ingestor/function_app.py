import azure.functions as func
import logging
import requests
import time

app = func.FunctionApp()

TRAFFIC_URL = "https://traffic.ottawa.ca/map/service/events?accept-language=en"

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
                # Simulate Nokia EDA trigger here

            return func.HttpResponse(str(high_priority), status_code=200)

        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {type(e).__name__} - {str(e)}")
            attempt += 1
            time.sleep(BACKOFF_SECONDS * attempt)

    logging.error("All retries failed. Could not fetch traffic events.")
    return func.HttpResponse("Failed to fetch traffic events after retries", status_code=500)
