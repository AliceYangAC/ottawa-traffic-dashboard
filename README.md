# Ottawa Traffic Ingestion & Visualization

This project is an **Azure Functions–based system** for ingesting and visualizing real-time traffic events in Ottawa. It fetches, filters, and stores high-priority traffic events in **Azure Table Storage**, which triggers a simulated **Event Grid** to generate **map-based visualizations** of active events using **Plotly** and **Azure Blob Storage**.  

> Note: This project is no longer integrated with Nokia EDA, but future integration may be considered.

---

## Project Structure

```
./
├── traffic_ingestor/
│   ├── helper_functions/         # Logic for fetching, storing, and cleaning up traffic events
│   ├── tests/                    # Unit and integration tests for ingestion
│   └── function_app.py           # Azure Function for ingesting traffic events
│
├── traffic_refresher/
│   ├── helper_functions/         # Logic for parsing coordinates and visualization
│   ├── tests/                    # Unit and integration tests for refresher
│   └── function_app.py           # Azure Function for refreshing visualizations
│
├── tests/                        # Global test fixtures (conftest.py) for Azurite, Blob, and Table
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Python dependencies
```

---

## Features

- **Traffic ingestion**  
  - Fetches traffic data from Ottawa’s public traffic API  
  - Filters for high-priority and active events  
  - Stores events in Azure Table Storage (`TrafficEvents`)  
  - Cleans up inactive events  

- **Traffic refresher**  
  - Reads events from Table Storage  
  - Parses and validates geocoordinates  
  - Generates density maps with Plotly  
  - Saves visualizations as PNGs in Azure Blob Storage  

- **Local development**  
  - Uses **Azurite** (via VS Code extension) for Table and Blob emulation  
  - Functions run locally with **Azure Functions Core Tools** (`func start`)  

- **Testing**  
  - Unit & integration tests with mocks for ingestion and refresher logic  
  - CI/CD with GitHub Actions  

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

4. Install Azurite CLI (for automated scripts; optional otherwise):
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
Linux
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
At the same time, the ingestion function also **simulates an Event Grid event**, which automatically triggers the **Traffic Refresher** function.

---

### 2. Automatic refresher trigger (edit this for Dash later)
When the refresher is triggered by the simulated Event Grid event, it will:
- Read the newly populated events from the `TrafficEvents` table.  
- Parse and validate coordinates.  
- Generate a density map of active traffic events.  
- Write the visualization (`traffic_hotspots.png`) into the `visualizations` container in Azurite Blob Storage.

---

## Verifying Results in Azurite

- **List table entities**:
  ```bash
  az storage entity query --connection-string "UseDevelopmentStorage=true" --table-name TrafficEvents
  ```

- **List blobs**:
  ```bash
  az storage blob list --connection-string "UseDevelopmentStorage=true" --container-name visualizations --output table
  ```

- **Download the visualization**:
  ```bash
  az storage blob download --connection-string "UseDevelopmentStorage=true" --container-name visualizations --name traffic_hotspots.png --file hotspot.png
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

- Scheduled ingestion with Azure Logic Apps  
- Visualization dashboards in Grafana or Power BI  
- Integration tests for E2E testing  
- Support for additional data sources (e.g., weather, transit)  

---

## License

MIT License
