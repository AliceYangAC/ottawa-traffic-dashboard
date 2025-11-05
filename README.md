# Ottawa Traffic Ingestion & Visualization

This project is an **Azure Functions–based system** for ingesting and visualizing real-time traffic events in Ottawa. It fetches, sanitizes, and transforms traffic events from the City of Ottawa’s public API, stores them in **Azure Table Storage** for historical analysis (future plans), and broadcasts current updates directly to a **Dash dashboard** for visualization.  

---

## Project Structure

```
.
└── ottawa-traffic-dashboard/
    ├── dashboard/                      # Dash app for visualizing live traffic data
    │   └── app.py                      # Main entry point for the dashboard UI
    ├── traffic_ingester/    
    │   ├── tests/                      # Tests for ingestion logic and Azure Function
    │   ├── helper_functions/           # Helpers for fetching, transforming, storing, and publishing traffic events
    │   └── function_app.py             # Azure Function that ingests traffic data from the API and broadcasts to dashboard
    ├── pytest.ini                      # Configuration for running tests with pytest
    └── run.sh                          # Startup script for launching the system locally
```

---

## Features

- **Traffic ingestion**  
  - Fetches live traffic data from Ottawa’s public API  
  - Sanitizes and transforms events into a consistent schema  
  - Stores active events in Azure Table Storage (`TrafficEvents`)  
  - Cleans up inactive events  
  - Broadcasts new events directly to the dashboard  

- **Dashboard**  
  - Built with Dash and Plotly for interactive visualization  
  - Displays three main panels:
    - **Traffic Hotspots Map**: density map of active traffic events across Ottawa  
    - **Traffic Events by Ward**: choropleth map showing counts of events per ward, clickable to reveal ward-level details  
    - **Events by Priority**: bar chart summarizing events by priority level  
  - Collapsible details card that shows event summaries for a selected ward (total events, breakdown by type and priority)  
  - Updates automatically as new events are ingested and broadcast  

- **Local development**  
  - Uses **Azurite** for local Table Storage emulation  
  - Runs Functions locally with **Azure Functions Core Tools** (`func start`)  
  - `run.sh` script orchestrates services for local testing  

- **Testing**  
  - Unit and integration tests for ingestion and dashboard update logic  
  - Mocks for API calls and storage operations  
  - CI/CD integration with GitHub Actions for automated validation  

---

## System Architecture

```
        City of Ottawa Traffic API
                    │
                    ▼
        ┌─────────────────────────┐
        │  traffic_ingester (AF)  │
        │  - Fetch & sanitize     │
        │  - Transform schema     │
        │  - Store ACTIVE events  │
        │  - Cleanup inactive     │
        │  - Broadcast updates    │
        └─────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
 Azure Table Storage       Dash Dashboard (Plotly)
   (TrafficEvents)         - Hotspot density map
                           - Ward choropleth map
                           - Events by priority bar chart
                           - Collapsible ward details card
```

---

## Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/AliceYangAC/EDAzure-ottawa-traffic.git
cd EDAzure-ottawa-traffic
```

2. **Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies for both services
pip install -r dashboard/requirements.txt
pip install -r traffic_ingester/requirements.txt

```

3. **Configure environment variables**

Create a `.env` file in `traffic_ingester` and in `dashboard` with the following configs:

```ini
# traffic_ingester

STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
TRAFFIC_URL=https://traffic.ottawa.ca/map/service/events?accept-language=en
TABLE_NAME=TrafficEvents
```

```ini
# dashboard

STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
TABLE_NAME=TrafficEvents
```

4. **Install Azurite CLI**

```bash
npm install -g azurite
```

---

## Demo

1. **Run shell command from root**
  
```bash
./run.sh
```

This will start Azurite, start the scheduled ingestion Azure Function, and start the dashboard to receive the real time data.

2. **Open the dashboard**

Visit:

```bash
http://localhost:8050/
```

You will see:
- A density map of traffic hotspots  
- A ward-level choropleth with clickable drill-downs  
- A bar chart of events by priority  
- A collapsible card with details for the selected ward  

---

## Testing and CI/CD

- **Unit Tests with Mocks**  
  - Cover helper functions for event sanitization, transformation, storage, and cleanup  
  - Mock Azure SDK clients to avoid real cloud calls in dev/test

- **Integration Tests**  
  - Verify orchestration logic of the ingestion function with mocked dependencies  
  - Simulate traffic API responses and confirm correct broadcast to the dashboard  

- **CI/CD with GitHub Actions**  
  - Runs all tests on each push, pull, and merge request  
  - Blocks deployment unless tests pass  

---

## Future Plans

- Add caching for improved performance  
- Extend dashboard with historical trend visualizations  
- Integrate telemetry and monitoring with Grafana  
