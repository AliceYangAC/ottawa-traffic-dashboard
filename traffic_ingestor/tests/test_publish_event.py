# traffic_ingestor/tests/test_function_app_publish.py
from unittest.mock import patch, MagicMock
import traffic_ingestor.function_app as function_app

# Patch publish_event as imported in function_app
@patch("traffic_ingestor.function_app.publish_event")
def test_publish_event(mock_publish):
    # Arrange: make publish_event a no-op
    mock_publish.return_value = None

    # Act: call the function under test
    response = function_app.fetch_traffic_events(None)

    # Assert: publish_event was called once
    mock_publish.assert_called_once()
    # And the function returned an HTTP response
    assert response.status_code == 200
