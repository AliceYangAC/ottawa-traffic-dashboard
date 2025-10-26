# Ottawa Traffic Ingestion & Visualization

This project is an **Azure Functions–based system** for ingesting and visualizing real-time traffic events in Ottawa. It fetches, filters, and stores high-priority traffic events in **Azure Table Storage**, which triggers a simulated **Event Grid** to generate **map-based visualizations** of active events using **Plotly** and **Azure Blob Storage**.  

> Note: This project is no longer integrated with Nokia EDA, but future integration may be considered.

---

## Project Structure

```
.
└── ottawa-traffic-dashboard/
    ├── dashboard/                      # Dash app for visualizing live traffic data
    │   └── app.py                      # Main entry point for the dashboard UI
    ├── traffic_ingestor/    
    │   ├── tests/                      # Tests for ingestion logic and Azure Function
    │   ├── helper_functions/          # Helpers for fetching, transforming, storing, and publishing traffic events
    │   └── function_app.py            # Azure Function that ingests traffic data from the API
    ├── traffic_refresher/    
    │   ├── tests/                      # Tests for refresher logic and Azure Function
    │   ├── helper_functions/          # Helpers for coordinate parsing and broadcast preparation
    │   └── function_app.py            # Azure Function that broadcasts traffic updates to the dashboard
    ├── websocket/   
    │   └── server.py                   # WebSocket server that streams traffic events to connected clients
    ├── pytest.ini                      # Configuration for running tests with pytest
    └── run.sh                          # Startup script for launching the full system locally

```

---

## Features

- **Traffic ingestion**  
  - Fetches live traffic data from Ottawa’s public API  
  - Sanitizes and transforms events into a consistent schema  
  - Stores active events in Azure Table Storage (`TrafficEvents`)  
  - Publishes updates to Event Grid and cleans up inactive events  

- **Traffic refresher**  
  - Listens for new ingested events via Event Grid  
  - Parses and validates geocoordinates for mapping  
  - Broadcasts events to the dashboard through WebSocket  
  - Keeps the dashboard updated with the latest traffic conditions  

- **Dashboard**  
  - Dash app that visualizes traffic hotspots on an interactive map  
  - Displays event details such as type, priority, and status  
  - Updates automatically as new events are broadcasted  

- **WebSocket server**  
  - Streams traffic events in real time to connected dashboard clients  
  - Ensures low-latency updates without page refreshes  

- **Local development**  
  - Uses **Azurite** for local Table and Blob Storage emulation  
  - Runs Functions locally with **Azure Functions Core Tools** (`func start`)  
  - `run.sh` script to orchestrate services for local testing  

- **Testing**  
  - Unit & integration tests for ingestion and refresher pipelines  
  - Mocks for API calls, storage, and Event Grid publishing  
  - CI/CD integration with GitHub Actions for automated validation  

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
pip install -r requirements.txt
```

3. **Configure environment variables**

Each function app (`traffic_ingestor` and `traffic_refresher`) should have its own `.env` file with storage connection strings and API URLs. 
```ini
# traffic_ingestor

# Azurite connection string for testing
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
TRAFFIC_URL=https://traffic.ottawa.ca/map/service/events?accept-language=en
```

```ini
# traffic_refresher

# Azurite connection string for testing
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
# API url for Ottawa's traffic event stream
OUTPUT_CONTAINER="visualizations"
```

1. Install Azurite CLI:
``` bash
npm install -g azurite
```

---

## Running Locally

### 1. Ensure `PYTHONPATH` is set:
To make imports consistent between pytest and `func start`, set `PYTHONPATH` to the repo root (`../`) for each function app. You can do this with:
```bash
cd traffic_ingestor
func settings add PYTHONPATH 
../

cd ../traffic_refresher
func settings add PYTHONPATH 
../
```

This adds the setting into each app’s `local.settings.json`.

### 2. Run the Functions from root:

```bash
chmod +x run.sh
./run.sh
```
---

## Testing the Functions

### 1. Fetch live traffic data (Ingestor)
Trigger the ingestion function to fetch and store traffic events:

```bash
curl http://localhost:7071/api/FetchTrafficEvents
```

This will populate the `TrafficEvents` table in Azurite.  
At the same time, the ingestion function also **simulates an Event Grid event**, which automatically triggers the **Traffic Refresher** function to broadcast new events to the Dash dashboard through Websocket communication. The stored data will be used for aggregate historical data models later.

---

### 2. Visit the Dash app to view the hotspots generated from the traffic.

```bash
http://localhost:8050/
```

---

### **Testing and CI/CD**

- **Unit Tests with Mocks**  
  Each helper function in both the ingestion and refresher pipelines is covered by isolated unit tests using `pytest` and `unittest.mock`. These tests:
  - Mock Azure SDK clients (`TableServiceClient`, `BlobServiceClient`, `EventGridPublisherClient`) to avoid real cloud calls.
  - Validate logic for event storage, cleanup, publishing, and coordinate parsing.
  - Ensure robustness against malformed inputs and edge cases.

- **Integration Tests for Function Apps**  
  The main Azure Functions (`fetch_traffic_events` and `traffic_refresher`) are tested with mocked dependencies to verify orchestration logic. These tests:
  - Simulate traffic API responses and Event Grid triggers.
  - Confirm correct invocation of helper functions.
  - Validate side effects like blob uploads and HTTP responses.

- **CI/CD with GitHub Actions**  
  GitHub Actions automates testing and deployment:
  - On every push or pull request to `main`, workflows run all unit and integration tests.
  - Deployments are gated by test success using `needs: test` in the workflow YAML.
  - Branch protection rules ensure that code cannot be merged unless all tests pass.

---

## Future Plans

- Implement Redis for caching instead of thread-locking between Dash and Websocket.
- Add additional data diagrams using both real time events via Websocket and historical data in Azurite Table Storage.
- Set up Grafana dashboard to show telemetry stats of performance.

---
