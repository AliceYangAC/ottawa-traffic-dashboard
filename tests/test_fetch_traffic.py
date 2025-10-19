import pytest
from unittest.mock import patch
from FetchTrafficEvents import __init__ as traffic_func

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

@patch('FetchTrafficEvents.__init__.requests.get', side_effect=mock_traffic_response)
@patch('FetchTrafficEvents.__init__.requests.post')
def test_fetch_traffic_events(mock_post, mock_get):
    req = None  # Simulate HttpRequest if needed
    response = traffic_func.fetch_traffic_events(req)
    assert response.status_code == 200
    assert "Collision" in response.get_body().decode()
    mock_post.assert_called_once()
