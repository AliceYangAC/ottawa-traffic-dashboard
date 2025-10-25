import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import asyncio
import websockets
import threading
import json
from datetime import datetime

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H2("Live Ottawa Traffic Dashboard"),
    dcc.Graph(id="hotspot-map"),
    dcc.Interval(id="interval", interval=3000, n_intervals=0)
])

latest_df = pd.DataFrame()
latest_df_lock = threading.Lock()

def start_websocket_listener():
    async def listen():
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            while True:
                msg = await websocket.recv()
                try:
                    payload = json.loads(msg)
                    events = payload.get("events", [])
                    if events:
                        df = pd.DataFrame(events)
                        with latest_df_lock:
                            global latest_df
                            latest_df = df
                            print(f"WebSocket received {len(latest_df)} events")
                    else:
                        print("WebSocket received empty event payload — latest_df not updated.")
                except Exception as e:
                    print(f"WebSocket message error: {e}")
    asyncio.run(listen())

threading.Thread(target=start_websocket_listener, daemon=True).start()

@app.callback(
    Output("hotspot-map", "figure"),
    Input("interval", "n_intervals")
)
def update_hotspot_map(n):
    with latest_df_lock:
        df = latest_df.copy()

    if df.empty or "Latitude" not in df.columns:
        empty_df = pd.DataFrame(columns=[
            "Latitude", "Longitude", "Location", "EventType",
            "Priority", "Status"
        ])
        return px.scatter_map(empty_df, lat="Latitude", lon="Longitude", title="Waiting for traffic data...")

    # Hotspot map
    map_fig = px.density_map(
        df,
        lat="Latitude",
        lon="Longitude",
        radius=15,
        hover_name="Location",
        hover_data=["EventType", "Priority", "Status"],
        center={"lat": 45.4215, "lon": -75.6972},
        zoom=10,
        map_style="carto-positron",
        title="Traffic Hotspots"
    )

    return map_fig

if __name__ == "__main__":
    app.run(debug=True)
