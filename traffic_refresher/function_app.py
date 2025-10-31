import azure.functions as func
import logging
import pandas as pd
from traffic_refresher.helper_functions.extract_coords_helper import extract_coords
import requests

app = func.FunctionApp()

# Azure Function to process traffic events via Event Grid trigger and broadcast to Websocket dashboard
@app.function_name(name="TrafficRefresher")
@app.event_grid_trigger(arg_name="event")
def traffic_refresher(event: func.EventGridEvent):
    print("Event Grid trigger received.")
    raw = event.get_json()

    if not isinstance(raw, dict):
        logging.warning("Malformed Event Grid payload.")
        return

    rows = raw.get("events", [])

    df = pd.DataFrame(rows)

    # Parse GeoCoordinates array into Latitude/Longitude
    if "GeoCoordinates" not in df.columns:
        print("No GeoCoordinates field found in data.")
        return

    df[["Latitude", "Longitude"]] = df["GeoCoordinates"].apply(
        lambda g: pd.Series(extract_coords(g))
    )

    # Drop rows without valid coordinates
    df = df.dropna(subset=["Latitude", "Longitude"])

    # Broadcast to Websocket
    try:
        payload = df.to_dict(orient="records")
        requests.post("http://localhost:8000/broadcast", json={"events": payload})
        print("Broadcasted traffic events to dashboard.")
    except Exception as e:
        print("Failed to broadcast: {e}")

