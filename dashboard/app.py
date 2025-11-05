import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import threading
import json
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timezone
from azure.data.tables import TableServiceClient
from dotenv import load_dotenv
import os
from flask import request
import dash_bootstrap_components as dbc

# BASE_DIR = os.path.dirname(__file__)
# load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

# Later store in Azure Key Vault
# TABLE_NAME = os.getenv("TABLE_NAME")
# STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")

# table_service = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)

# # Ensure the table exists before any callbacks run
# try:
#     table_service.create_table_if_not_exists(TABLE_NAME)
#     table_client = table_service.get_table_client(table_name=TABLE_NAME)
# except Exception as e:
#     print(f"Warning: could not ensure table exists: {e}")

# Load Ottawa ward boundaries once at startup
# Make sure you have the GeoJSON file in your project, e.g. data/ottawa_wards.geojson
BASE_DIR = os.path.dirname(__file__)
wards_path = os.path.join(BASE_DIR, "data", "ottawa_wards.geojson")
wards = gpd.read_file(wards_path).to_crs("EPSG:4326")
wards_geojson = wards.__geo_interface__

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("Live Ottawa Traffic Dashboard", className="text-primary"),
            html.Div(id="last-updated", className="fw-bold text-muted mt-2")
        ])
    ], className="my-4"),

    # Main row with three graphs
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Traffic Hotspots"),
                dbc.CardBody(dcc.Graph(id="hotspot-map", style={"height": "70vh"}))
            ], className="shadow-sm"),
            md=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Traffic Events by Ward"),
                dbc.CardBody(dcc.Graph(id="ward-choropleth", style={"height": "70vh"}))
            ], className="shadow-sm"),
            md=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Events by Priority"),
                dbc.CardBody(dcc.Graph(id="event-type-bar", style={"height": "70vh"}))
            ], className="shadow-sm"),
            md=4
        )
    ], className="g-4"),

    # Hidden stores for state
    dcc.Store(id="latest-data-store", storage_type="local"),
    dcc.Store(id="selected-ward", storage_type="memory"),
    dcc.Interval(id="poller", interval=1000, n_intervals=0),
    # Ward details collapse
    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader([
                html.Span("Ward Details", className="me-auto"),
                dbc.Button(
                    id="close-ward-details",
                    className="btn-close btn-close-white",
                    n_clicks=0
                )
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody(html.Div(id="ward-details"))
        ]),
        id="ward-details-collapse",   # must match callback Output
        is_open=False,
        className="my-4"
    )


], fluid=True)



# Shared state
latest_df = pd.DataFrame()
latest_df_lock = threading.Lock()
update_flag = threading.Event()

# Helper to parse GeoCoordinates string into (lat, lon)
def extract_coords(geo_str):
    try:
        coords = json.loads(geo_str)  # e.g. "[-75.93772, 45.29347]"
        if isinstance(coords, list) and len(coords) == 2:
            lon, lat = coords
            return lat, lon
    except Exception:
        pass
    return None, None

# Helper to assign events to wards
def assign_events_to_wards(df):
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df.Longitude, df.Latitude)],
        crs="EPSG:4326"
    )
    joined = gpd.sjoin(gdf, wards, how="left", predicate="within")
    return joined

# Endpoint to receive updates from the ingester function
@app.server.route("/update-dashboard", methods=["POST"])
def update_dashboard():
    global latest_df
    try:
        payload = request.get_json(silent=True) or {}
        events = payload.get("events", [])
        
        # Bail out early if no events
        if not events:
            return "No events provided, dashboard not updated", 400

        df = pd.DataFrame(events)

        if "GeoCoordinates" in df.columns:
            df[["Latitude", "Longitude"]] = df["GeoCoordinates"].apply(
                lambda g: pd.Series(extract_coords(g))
            )
            df = df.dropna(subset=["Latitude", "Longitude"])

        # Only update if df is non-empty after processing
        if not df.empty:
            with latest_df_lock:
                latest_df = df
                update_flag.set()
            return "Dashboard updated", 200
        else:
            return "No valid events after processing, dashboard not updated", 400

    except Exception as e:
        print(f"Update failed: {e}")
        return f"Error: {str(e)}", 400

# Dash callback to poll for updates
@app.callback(
    Output("latest-data-store", "data"),
    Input("poller", "n_intervals")
)
def poll_for_updates(n):
    if not update_flag.is_set():
        raise dash.exceptions.PreventUpdate
    with latest_df_lock:
        df = latest_df.copy()
        update_flag.clear()
    return df.to_dict("records")

# Store the selected ward when a choropleth region is clicked
@app.callback(
    Output("selected-ward", "data"),
    Input("ward-choropleth", "clickData"),
    prevent_initial_call=True
)
def store_selected_ward(clickData):
    if not clickData or "points" not in clickData:
        return None  # reset selection
    return clickData["points"][0]["location"]


# Populate ward details based on selected ward
@app.callback(
    Output("ward-details", "children"),
    Input("selected-ward", "data"),
    State("latest-data-store", "data")
)
def display_ward_details(ward, data):
    if not ward or not data:
        return "Click on a ward to see details."

    df = pd.DataFrame(data)
    joined = assign_events_to_wards(df)
    ward_events = joined[joined["WARD"] == ward]

    if ward_events.empty:
        return f"Ward {ward}: No events."

    # Summarize details
    total = len(ward_events)
    by_type = ward_events["EventType"].value_counts().to_dict()
    by_priority = ward_events["Priority"].value_counts().to_dict()

    return html.Div([
        html.H4(f"Ward {ward} Details"),
        html.P(f"Total events: {total}"),
        html.P(f"By type: {by_type}"),
        html.P(f"By priority: {by_priority}")
    ])

# Dash callback to toggle the collapse for ward details
@app.callback(
    Output("ward-details-collapse", "is_open"),
    Input("selected-ward", "data"),
    Input("close-ward-details", "n_clicks"),
    State("ward-details-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_collapse(ward, close_clicks, is_open):
    trigger = dash.ctx.triggered_id  # Dash 2.9+ clean API

    if trigger == "selected-ward" and ward:
        return True
    elif trigger == "close-ward-details":
        return False
    return is_open


# Dash callback to update the hotspot density map
@app.callback(
    Output("hotspot-map", "figure"),
    Input("latest-data-store", "data"),
    Input("selected-ward", "data"),   # ward number or None
    State("hotspot-map", "relayoutData")
)
def update_hotspot_map(data, ward_click, relayout_data):
    df = pd.DataFrame(data)
    if df.empty:
        return px.density_map(
            pd.DataFrame(columns=["Latitude", "Longitude"]),
            lat="Latitude", lon="Longitude", z=None,
            radius=15,
            center={"lat": 45.4215, "lon": -75.6972},
            zoom=10,
            map_style="carto-positron",
            title="Waiting for traffic data..."
        )

    # Always enrich with ward info
    df = assign_events_to_wards(df)

    # If a ward was clicked, filter
    if ward_click:
        df = df[df["WARD"] == ward_click]

    if df.empty:
        return px.density_map(
            pd.DataFrame(columns=["Latitude", "Longitude"]),
            lat="Latitude", lon="Longitude", z=None,
            radius=15,
            center={"lat": 45.4215, "lon": -75.6972},
            zoom=10,
            map_style="carto-positron",
            title="No events for selected ward"
        )

    fig = px.density_map(
        df,
        lat="Latitude",
        lon="Longitude",
        z=None,
        radius=15,
        hover_name="Location",
        hover_data=["EventType", "Priority", "Status", "WARD", "NAME"],
        center={"lat": 45.4215, "lon": -75.6972},
        zoom=10,
        map_style="carto-positron",
        title="Traffic Hotspots"
    )

    # Preserve user zoom/pan if present
    if relayout_data:
        center = relayout_data.get("map.center")
        zoom = relayout_data.get("map.zoom")
        if center and zoom:
            fig.update_layout(map_center=center, map_zoom=zoom)

    return fig


# Dash callback to update the event type bar chart
@app.callback(
    Output("event-type-bar", "figure"),
    Input("latest-data-store", "data"),
    Input("selected-ward", "data"),
    State("event-type-bar", "relayoutData")
)
def update_event_type_bar(data, ward_click, relayout_data):
    df = pd.DataFrame(data)
    if df.empty:
        return px.bar(title="Waiting for traffic data...")

    if ward_click:
        joined = assign_events_to_wards(df)
        df = joined[joined["WARD"] == ward_click]

    if df.empty:
        return px.bar(title="No events for selected ward")

    counts = df["Priority"].value_counts().reset_index()
    counts.columns = ["Priority", "Count"]

    fig = px.bar(counts, x="Priority", y="Count",
                 title="Events by Priority", text="Count")
    fig.update_layout(yaxis_title="Number of Events")

    if relayout_data:
        if "xaxis.range" in relayout_data:
            fig.update_xaxes(range=relayout_data["xaxis.range"])
        if "yaxis.range" in relayout_data:
            fig.update_yaxes(range=relayout_data["yaxis.range"])
    return fig

@app.callback(
    Output("ward-choropleth", "figure"),
    Input("latest-data-store", "data"),
    State("ward-choropleth", "relayoutData")
)
def update_ward_choropleth(data, relayout_data):
    df = pd.DataFrame(data)
    if df.empty or "Latitude" not in df.columns or "Longitude" not in df.columns:
        wards_with_counts = wards.copy()
        wards_with_counts["Count"] = 0
    else:
        joined = assign_events_to_wards(df)
        counts = joined.groupby(["WARD", "NAME"]).size().reset_index(name="Count")
        wards_with_counts = wards.merge(counts, on=["WARD", "NAME"], how="left").fillna(0)

    fig = px.choropleth(
        wards_with_counts,
        geojson=wards_geojson,
        locations="WARD",
        color="Count",
        featureidkey="properties.WARD",
        projection="mercator",
        title="Traffic Events by Ward",
        hover_data={"WARD": True, "NAME": True, "NAME_FR": True, "Count": True}
    )
    fig.update_traces(marker_line_width=1.5, marker_line_color="black")
    fig.update_geos(fitbounds="locations", visible=False)
    if relayout_data and "geo.center" in relayout_data:
        fig.update_geos(
            center=relayout_data.get("geo.center"),
            projection_scale=relayout_data.get("geo.projection.scale", 1)
        )
    return fig

@app.callback(
    Output("last-updated", "children"),
    Input("latest-data-store", "data")
)
def update_timestamp(data):
    if not data:
        return "Last updated: no data yet"
    return f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


if __name__ == "__main__":
    app.run(debug=True)
