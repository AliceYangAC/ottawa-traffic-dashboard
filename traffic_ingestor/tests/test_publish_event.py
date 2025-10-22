# traffic_ingestor/tests/test_publish_event.py
import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions.publish_event import publish_event

def test_publish_event_posts_to_refresher():
    # Arrange: mock response object
    mock_response = MagicMock()
    mock_response.status_code = 202

    with patch("traffic_ingestor.helper_functions.publish_event.requests.post", return_value=mock_response) as mock_post:
        # Act
        publish_event()

        # Assert: requests.post was called once
        assert mock_post.call_count == 1

        # Extract call arguments
        called_url = mock_post.call_args[0][0]
        called_kwargs = mock_post.call_args[1]

        # Verify URL
        assert "http://127.0.0.1:7072/runtime/webhooks/EventGrid" in called_url

        # Verify headers
        headers = called_kwargs["headers"]
        assert headers["aeg-event-type"] == "Notification"
        assert headers["Content-Type"] == "application/json"

        # Verify payload
        payload = called_kwargs["json"]
        assert isinstance(payload, list)
        assert payload[0]["eventType"] == "Traffic.Ingested"
        assert payload[0]["data"]["message"] == "New traffic events ingested"
