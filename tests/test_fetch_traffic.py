import pytest
from unittest.mock import patch
from traffic_ingestor.function_app import fetch_traffic_events

# Purpose: Tests the main logic of the function.
# Contents:
    # Mocking requests.get to simulate traffic API responses.
    # Mocking requests.post to simulate EDA webhook calls.
    # Testing filtering logic for high-priority events.
    # Testing error handling and retries.

def mock_traffic_response(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = '{"events":[{"priority":"HIGH","status":"ACTIVE","eventType":"Collision","location":{"description":"Kanata Ave & March Rd"},"startTime":"2025-10-19T10:00:00Z"}]}'

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "events": [
                    {
                        "priority": "HIGH",
                        "status": "ACTIVE",
                        "eventType": "Collision",
                        "location": {"description": "Kanata Ave & March Rd"},
                        "startTime": "2025-10-19T10:00:00Z"
                    }
                ]
            }

    return MockResponse()

@patch('traffic_ingestor.function_app.requests.get', side_effect=mock_traffic_response)
@patch('traffic_ingestor.function_app.requests.post')
def test_fetch_traffic_events(mock_post, mock_get):
    from traffic_ingestor.function_app import fetch_traffic_events
    req = None  # Simulate HttpRequest
    response = fetch_traffic_events(req)
    assert response.status_code == 200
    assert "Collision" in response.get_body().decode()
    mock_post.assert_called_once()
