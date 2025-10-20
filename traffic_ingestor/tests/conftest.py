import pytest
from unittest.mock import MagicMock, patch

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
