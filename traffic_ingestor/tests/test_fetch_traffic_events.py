import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.function_app import fetch_traffic_events
import azure.functions as func
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="traffic_ingestor/.env")

def test_fetch_traffic_events_successful_flow_with_new_data():
    # --- Fake traffic API response ---
    fake_events = [
        {"id": "123", "eventType": "Collision", "message": "Accident on Main St", "status": "ACTIVE"},
        {"id": "456", "eventType": "Construction", "message": "Roadwork on Bank St", "status": "INACTIVE"}
    ]
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = str(fake_events)
    fake_response.json.return_value = {"events": fake_events}

    with patch("traffic_ingestor.function_app.requests.get", return_value=fake_response) as mock_get, \
         patch("traffic_ingestor.function_app.store_event_in_table") as mock_store, \
         patch("traffic_ingestor.function_app.cleanup_inactive_events") as mock_cleanup, \
         patch("traffic_ingestor.function_app.publish_event") as mock_publish, \
         patch("traffic_ingestor.function_app.has_new_events", return_value=True) as mock_has_new:

        # --- Simulate Timer trigger ---
        dummy_timer = MagicMock(spec=func.TimerRequest)

        # Act
        fetch_traffic_events(dummy_timer)

        # Assert: traffic API was called
        mock_get.assert_called_once()

        # Assert: hash check was performed
        mock_has_new.assert_called_once_with(fake_events, os.getenv("STORAGE_CONNECTION_STRING"), "TrafficMetadata")

        # Assert: ACTIVE event was stored
        mock_store.assert_called_once_with(fake_events[0], os.getenv("STORAGE_CONNECTION_STRING"), "TrafficEvents")

        # Assert: cleanup and publish were called
        mock_cleanup.assert_called_once_with(fake_events, os.getenv("STORAGE_CONNECTION_STRING"), "TrafficEvents")
        mock_publish.assert_called_once()


def test_fetch_traffic_events_skips_publish_if_no_new_data():
    fake_events = [
        {"id": "123", "eventType": "Collision", "message": "Accident on Main St", "status": "ACTIVE"},
        {"id": "456", "eventType": "Construction", "message": "Roadwork on Bank St", "status": "INACTIVE"}
    ]
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = str(fake_events)
    fake_response.json.return_value = {"events": fake_events}

    with patch("traffic_ingestor.function_app.TRAFFIC_URL", "http://mock.api"), \
         patch("traffic_ingestor.function_app.requests.get", return_value=fake_response), \
         patch("traffic_ingestor.function_app.has_new_events", return_value=False) as mock_has_new, \
         patch("traffic_ingestor.function_app.publish_event") as mock_publish:

        dummy_timer = MagicMock(spec=func.TimerRequest)
        fetch_traffic_events(dummy_timer)

        mock_has_new.assert_called_once_with(fake_events, os.getenv("STORAGE_CONNECTION_STRING"), "TrafficMetadata")
        mock_publish.assert_not_called()
