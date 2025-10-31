import pytest
from unittest.mock import patch, MagicMock
import os
from dotenv import load_dotenv
from traffic_ingestor.function_app import fetch_traffic_events
import azure.functions as func

# Get the absolute path to the .env file
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)

# Test the successful ingestion flow of fetch_traffic_events
def test_fetch_traffic_events_successful_ingestion_flow():
    # --- Raw API response ---
    raw_events = [
        {
            "id": "123",
            "eventType": "Collision",
            "headline": "Accident on Main St",
            "schedule": [{"startDateTime": "2025-10-21T10:00:00Z", "endDateTime": "2025-10-21T12:00:00Z"}],
            "priority": "HIGH",
            "status": "ACTIVE",
            "geodata": {"coordinates": "[-75.69, 45.40]"}
        },
        {
            "id": "456",
            "eventType": "Construction",
            "headline": "Roadwork on Bank St",
            "schedule": [],
            "priority": "MEDIUM",
            "status": "INACTIVE",
            "geodata": {"coordinates": "[-75.70, 45.41]"}
        }
    ]

    transformed_events = [
        {
            "PartitionKey": "OttawaTraffic",
            "RowKey": "123",
            "EventType": "Collision",
            "Location": "Accident on Main St",
            "StartTime": "2025-10-21T10:00:00Z",
            "EndTime": "2025-10-21T12:00:00Z",
            "Priority": "HIGH",
            "Status": "ACTIVE",
            "GeoCoordinates": "[-75.69, 45.40]"
        },
        {
            "PartitionKey": "OttawaTraffic",
            "RowKey": "456",
            "EventType": "Construction",
            "Location": "Roadwork on Bank St",
            "StartTime": None,
            "EndTime": None,
            "Priority": "MEDIUM",
            "Status": "INACTIVE",
            "GeoCoordinates": "[-75.70, 45.41]"
        }
    ]

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = str(raw_events)
    fake_response.json.return_value = {"events": raw_events}

    with patch("traffic_ingestor.function_app.requests.get", return_value=fake_response) as mock_get, \
         patch("traffic_ingestor.function_app.sanitize_event", side_effect=lambda e: e) as mock_sanitize, \
         patch("traffic_ingestor.function_app.transform_events", return_value=transformed_events) as mock_transform, \
         patch("traffic_ingestor.function_app.has_new_events", return_value=True) as mock_has_new, \
         patch("traffic_ingestor.function_app.store_event_in_table") as mock_store, \
         patch("traffic_ingestor.function_app.cleanup_inactive_events") as mock_cleanup, \
         patch("traffic_ingestor.function_app.publish_events") as mock_publish:

        dummy_req = MagicMock(spec=func.HttpRequest)

        # Act
        response = fetch_traffic_events(dummy_req)

        # Assert: traffic API was called
        mock_get.assert_called_once()

        # Assert: hash check was performed
        mock_has_new.assert_called_once_with(raw_events, os.getenv("STORAGE_CONNECTION_STRING"), "TrafficMetadata")

        # Assert: sanitize and transform were called
        assert mock_sanitize.call_count == len(raw_events)
        mock_transform.assert_called_once()

        # Assert: only ACTIVE event was stored
        mock_store.assert_called_once_with(transformed_events[0], os.getenv("STORAGE_CONNECTION_STRING"), "TrafficEvents")

        # Assert: cleanup and publish were called
        mock_cleanup.assert_called_once_with(transformed_events, os.getenv("STORAGE_CONNECTION_STRING"), "TrafficEvents")
        mock_publish.assert_called_once_with(transformed_events)

        # Assert: HTTP response is 200 and contains transformed events
        assert response.status_code == 200
        assert "123" in response.get_body().decode()
