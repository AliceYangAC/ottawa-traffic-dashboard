import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions.publish_event_helper import publish_events

def test_publish_events_posts_correct_payload():
    # --- Mock events list ---
    mock_events = [
        {
            "id": "123",
            "eventType": "Collision",
            "Location": "Kanata Ave & March Rd",
            "Status": "ACTIVE"
        }
    ]

    # --- Mock response ---
    mock_response = MagicMock()
    mock_response.status_code = 202

    with patch("traffic_ingestor.helper_functions.publish_event_helper.requests.post", return_value=mock_response) as mock_post:
        # Act
        publish_events(mock_events)

        # Assert: requests.post was called once
        mock_post.assert_called_once()

        # Extract call arguments
        called_url = mock_post.call_args[0][0]
        called_kwargs = mock_post.call_args[1]

        # Verify URL
        assert called_url.startswith("http://localhost:7072/runtime/webhooks/eventgrid")

        # Verify headers
        headers = called_kwargs["headers"]
        assert headers["aeg-event-type"] == "Notification"
        assert headers["Content-Type"] == "application/json"

        # Verify payload structure
        payload = called_kwargs["json"]
        assert isinstance(payload, list)
        assert payload[0]["eventType"] == "Traffic.Ingested"
        assert "eventTime" in payload[0]
        assert "data" in payload[0]
        assert "events" in payload[0]["data"]
        assert payload[0]["data"]["events"] == mock_events
