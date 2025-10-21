import pytest
import os
from dotenv import load_dotenv, find_dotenv
import sys
from unittest.mock import MagicMock, patch

# --- Ensure project root is on sys.path ---
# This prevents import collisions (e.g. between traffic_ingestor.helper_functions
# and traffic_refresher.helper_functions).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Load environment variables from nearest .env ---
load_dotenv(find_dotenv())

@pytest.fixture
def mock_traffic_response():
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = '{"events":[{"id":"123","priority":"HIGH","status":"ACTIVE","eventType":"Collision","message":"Kanata Ave & March Rd","schedule":[{"startDateTime":"2025-10-19T10:00:00Z","endDateTime":"2025-10-19T12:00:00Z"}]},{"id":"456","priority":"LOW","status":"INACTIVE","eventType":"Construction","message":"Eagleson Rd","schedule":[{"startDateTime":"2025-10-20T08:00:00Z","endDateTime":"2025-10-20T18:00:00Z"}]}]}'

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "events" : [
                    {
                        "id": "123",
                        "priority": "HIGH",
                        "status": "ACTIVE",
                        "eventType": "Collision",
                        "message": "Kanata Ave & March Rd",
                        "schedule": [
                            {
                                "startDateTime": "2025-10-19T10:00:00Z",
                                "endDateTime": "2025-10-19T12:00:00Z"
                            }
                        ]
                    },
                    {
                        "id": "456",
                        "priority": "LOW",
                        "status": "INACTIVE",
                        "eventType": "Construction",
                        "message": "Eagleson Rd",
                        "schedule": [
                            {
                                "startDateTime": "2025-10-20T08:00:00Z",
                                "endDateTime": "2025-10-20T18:00:00Z"
                            }
                        ]
                    }
                ]
            }

    return MockResponse()

@pytest.fixture
def sample_event():
    return {
        "id": "123",
        "message": "March Road & Carling Ave",
        "eventType": "Collision",
        "schedule": [{"startDateTime": "2025-10-19T12:00:00Z", "endDateTime": "2025-10-19T14:00:00Z"}],
        "priority": "HIGH",
        "status": "ACTIVE"
    }
