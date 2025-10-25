import azure.functions as func
import logging
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from traffic_refresher.helper_functions.extract_coords_helper import extract_coords
import requests
import json

# Explicitly load the .env file from this folder
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
#print("Loaded connection string:", repr(os.getenv("STORAGE_CONNECTION_STRING")))

app = func.FunctionApp()

# Config (aligns with traffic_ingestor style)
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
TABLE_NAME = "TrafficEvents"
OUTPUT_CONTAINER = os.getenv("OUTPUT_CONTAINER", "visualizations")

@app.function_name(name="TrafficRefresher")
@app.event_grid_trigger(arg_name="event")
def traffic_refresher(event: func.EventGridEvent):
    print("Event Grid trigger received: %s", event.get_json())

    # Connect to Table Storage
    table_service = TableServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    table_client = table_service.get_table_client(TABLE_NAME)

    # Query recent entities
    entities = table_client.list_entities(results_per_page=200)
    rows = [dict(e) for e in entities]
    # safe_rows = json.dumps(rows, ensure_ascii=True)
    # print("Traffic events in Azure Tables:", safe_rows)

    if not rows:
        print("No traffic events found in Table Storage.")
        return

    df = pd.DataFrame(rows)

    # Parse GeoCoordinates array into Latitude/Longitude
    if "GeoCoordinates" not in df.columns:
        logging.warning("No GeoCoordinates field found in data.")
        return

    df[["Latitude", "Longitude"]] = df["GeoCoordinates"].apply(
        lambda g: pd.Series(extract_coords(g))
    )

    # Drop rows without valid coordinates
    df = df.dropna(subset=["Latitude", "Longitude"])

    if df.empty:
        print("No valid coordinates to plot.")
        return

    # Build hotspot map
    fig = px.density_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        radius=15,
        hover_name="Location",
        hover_data={"EventType": True, "Priority": True, "Status": True},
        center=dict(lat=45.4215, lon=-75.6972),  # Ottawa center
        zoom=10,
        mapbox_style="carto-positron",
        title="Ottawa Traffic Hotspots"
    )

    # Save to Blob Storage
    blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    blob_client = blob_service.get_blob_client(container=OUTPUT_CONTAINER, blob="traffic_hotspots.png")

    # Write image to memory and upload
    import io
    img_bytes = fig.to_image(format="png", engine="kaleido")
    # Ensure container exists
    container_client = blob_service.get_container_client(OUTPUT_CONTAINER)
    
    try:
        container_client.get_container_properties()
    except Exception:
        container_client.create_container()
    blob_client.upload_blob(img_bytes, overwrite=True)

    try:
        payload = df.to_dict(orient="records")
        print("Payload to be broadcasted:", len(payload))
        requests.post("http://localhost:8000/broadcast", json={"events": payload})
        print("Broadcasted traffic events to dashboard.")
    except Exception as e:
        logging.warning(f"Failed to broadcast: {e}")

    # print("Hotspot map written to Blob Storage.")
