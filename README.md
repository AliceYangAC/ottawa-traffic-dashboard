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
  - Unit tests with mocks for ingestion and refresher logic  
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

STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
TRAFFIC_URL=https://traffic.ottawa.ca/map/service/events?accept-language=en
FUNCTION_URL=https://your-function-url/api/FetchTrafficEvents
```

```ini
# traffic_refresher

# Azurite connection string for testing
STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
# API url for Ottawa's traffic event stream
TRAFFIC_URL=https://traffic.ottawa.ca/map/service/events?accept-language=en
OUTPUT_CONTAINER="visualizations"


```

---

## Running Locally

### 1. Start Azurite in VS Code
- Install the **Azurite** extension in VS Code.  
- Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`), then run:  
  - **Azurite: Start Table Service**  
  - **Azurite: Start Blob Service**  
  - **Azurite: Start Queue Service**  

### 2. Ensure `PYTHONPATH` and `AzureWebJobsStorage` is set
To make imports consistent between pytest and `func start`, set `PYTHONPATH` to the repo root (`../`) for each function app. You can do this with:
UseDevelopmentStorage=true
```bash
cd traffic_ingestor
func settings add PYTHONPATH 
../
func settings add AzureWebJobsStorage
UseDevelopmentStorage=true

cd ../traffic_refresher
func settings add PYTHONPATH 
../
func settings add AzureWebJobsStorage
UseDevelopmentStorage=true
```

This adds the setting into each app’s `local.settings.json`.

### 3. Run the Functions
- Start the **ingestor** (default port 7071):
  ```bash
  cd traffic_ingestor
  func start
  ```
- Start the **refresher** on a different port (e.g. 7072):
  ```bash
  cd traffic_refresher
  func start -p 7072
  ```

⚠️ Reminder: You must run the refresher on a different port than the ingestor, otherwise the second host will fail to bind.

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

### 2. Automatic refresher trigger
When the refresher is triggered by the simulated Event Grid event, it will:
- Read the newly populated events from the `TrafficEvents` table.  
- Parse and validate coordinates.  
- Generate a density map of active traffic events.  
- Write the visualization (`traffic_hotspots.png`) into the `visualizations` container in Azurite Blob Storage.

---

### 3. Download the visualization
To pull the generated PNG down into your project root, run the provided helper script:

```bash
python traffic_refresher/scripts/check_visualizations.py
```

This script connects to Azurite, downloads `traffic_hotspots.png`, and saves it locally so you can open and inspect the visualization.

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

## CI/CD with GitHub Actions

- All tests run automatically on push and pull requests to `main`.  
- Workflow includes linting & unit tests against Azurite.  

---

## Future Plans

- Scheduled ingestion with Azure Logic Apps  
- Visualization dashboards in Grafana or Power BI  
- Integration tests for E2E testing  
- Support for additional data sources (e.g., weather, transit)  
- Optional integration with Nokia EDA for event-driven automation  

---

## License

MIT License
