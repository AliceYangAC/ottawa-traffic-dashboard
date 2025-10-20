import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_traffic_response():
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = '{"events":[{"id":"123","priority":"HIGH","status":"ACTIVE","eventType":"Collision","message":"Kanata Ave &amp; March Rd","schedule":[{"startDateTime":"2025-10-19T10:00:00Z","endDateTime":"2025-10-19T12:00:00Z"}]},{"id":"456","priority":"LOW","status":"INACTIVE","eventType":"Construction","message":"Eagleson Rd","schedule":[{"startDateTime":"2025-10-20T08:00:00Z","endDateTime":"2025-10-20T18:00:00Z"}]}]}'

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "events": [
                    {
                        "id": "123",
                        "priority": "HIGH",
                        "status": "ACTIVE",
                        "eventType": "Collision",
                        "message": "Kanata Ave &amp; March Rd",
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

# Fixture for store_event_in_table
@pytest.fixture
def mock_store_table_service_client():
    with patch("traffic_ingestor.helper_functions.store_event_in_table.TableServiceClient") as mock_service:
        mock_table_client = MagicMock()
        mock_service.from_connection_string.return_value.get_table_client.return_value = mock_table_client
        yield mock_table_client

# Fixture for cleanup_inactive_events
@pytest.fixture
def mock_cleanup_table_service_client():
    with patch("traffic_ingestor.helper_functions.cleanup_inactive_events.TableServiceClient") as mock_service:
        mock_table_client = MagicMock()
        mock_service.from_connection_string.return_value.get_table_client.return_value = mock_table_client
        yield mock_table_client

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