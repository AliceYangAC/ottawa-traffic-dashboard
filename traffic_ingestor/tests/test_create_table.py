# traffic_ingestor/tests/test_ensure_table_exists.py
import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions.create_table import ensure_table_exists

def test_ensure_table_exists_calls_create_table():
    with patch("traffic_ingestor.helper_functions.create_table.TableServiceClient") as mock_tsc:
        # Arrange: mock service and its method
        mock_service = MagicMock()
        mock_tsc.from_connection_string.return_value = mock_service

        # Act
        ensure_table_exists("fake-conn-string", "TrafficEvents")

        # Assert: create_table_if_not_exists was called
        mock_service.create_table_if_not_exists.assert_called_once_with("TrafficEvents")
