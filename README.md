
# Ottawa Traffic Ingestion

This project is an Azure-based traffic ingestion system focused on real-time traffic events in Ottawa. It is designed to fetch, filter, and store high-priority traffic events using Azure Functions and Azure Table Storage to visualize and analyze patterns through Grafana dashboard in future integration

> Note: This project is no longer integrated with Nokia EDA, but future integration may be considered.

## 📁 Project Structure

```
./
├── traffic_ingestor/
│   ├── helper_functions/         # Contains logic for fetching, storing and cleaning up traffic events
│   ├── tests/                    # Pytest-based unit and integration tests
│   └── function_app.py           # Main Azure Function for traffic ingestion
├── pytest.ini                    # Pytest configuration file
└── requirements.txt              # Python dependencies
```

## 🚀 Features

- Fetches traffic data from Ottawa's public traffic API
- Filters for high-priority and active events
- Stores events in Azure Table Storage
- Cleans up inactive events
- Fully tested with Pytest and GitHub Actions CI/CD

## 🛠 Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/AliceYangAC/EDAzure-ottawa-traffic.git
cd EDAzure-ottawa-traffic
```

2. **Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the root or use Azure App Settings:

```
TRAFFIC_URL=https://traffic.ottawa.ca/map/service/events?accept-language=en
STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
```

## Running Tests

Tests are configured using `pytest.ini`. To run all tests, go to root and run:

```bash
pytest
```

## CI/CD with GitHub Actions

Tests are automatically run on every push and pull request to `main` using GitHub Actions.

## Future Plans

- Optional integration with Nokia EDA for event-driven automation
- Visualization dashboard using Grafana or Power BI
- Support for additional data sources (e.g., weather, transit)

## License

MIT License
