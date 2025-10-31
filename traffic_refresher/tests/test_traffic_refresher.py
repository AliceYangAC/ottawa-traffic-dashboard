import pytest
from unittest.mock import patch, MagicMock
from traffic_refresher.function_app import traffic_refresher
from azure.functions import EventGridEvent

# Test the successful traffic_refresher flow for processing events and broadcasting only those with valid coordinates
def test_traffic_refresher_broadcasts_valid_events():
    # --- Fake event with GeoCoordinates ---
    fake_event_data = {
        "events": [
            {
                "RowKey": "123-Collision",
                "GeoCoordinates": "[-75.69, 45.40]",
                "Location": "Accident on Highway 417",
                "EventType": "Collision",
                "Priority": "High",
                "Status": "ACTIVE"
            },
            {
                "RowKey": "456-Construction",
                "GeoCoordinates": "invalid-coords",
                "Location": "Roadwork on Bank St",
                "EventType": "Construction",
                "Priority": "Medium",
                "Status": "INACTIVE"
            }
        ]
    }

    dummy_event = EventGridEvent(
        id="test-id",
        data=fake_event_data,
        topic="/subscriptions/fake-sub/resourceGroups/fake-rg/providers/Microsoft.EventGrid/topics/fake-topic",
        subject="traffic/ingestion",
        event_type="Traffic.Ingested",
        event_time="2025-10-21T14:00:00Z",
        data_version="1.0"
    )

    with patch("traffic_refresher.function_app.extract_coords") as mock_extract, \
         patch("traffic_refresher.function_app.requests.post") as mock_post:

        # Mock coordinate extraction
        mock_extract.side_effect = lambda g: (45.40, -75.69) if g == "[-75.69, 45.40]" else (None, None)

        # Mock broadcast response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        traffic_refresher(dummy_event)

        # Assert: extract_coords called for each event
        assert mock_extract.call_count == 2

        # Assert: requests.post called once with filtered payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:8000/broadcast"
        assert "events" in kwargs["json"]
        assert len(kwargs["json"]["events"]) == 1  # Only one valid coordinate
        assert kwargs["json"]["events"][0]["RowKey"] == "123-Collision"
