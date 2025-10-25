import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions.store_event_in_table_helper import store_event_in_table

def test_store_event_upserts_transformed_entity():
    # --- Transformed event ---
    transformed_event = {
        "PartitionKey": "OttawaTraffic",
        "RowKey": "123",
        "EventType": "Collision",
        "Location": "Kanata Ave & March Rd",
        "StartTime": "2025-10-21T10:00:00Z",
        "EndTime": "2025-10-21T12:00:00Z",
        "Priority": "HIGH",
        "Status": "ACTIVE",
        "GeoCoordinates": "[-75.69, 45.40]"
    }

    with patch("traffic_ingestor.helper_functions.store_event_in_table_helper.TableServiceClient") as mock_tsc:
        # Mock table client
        mock_table_client = MagicMock()
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # Act
        store_event_in_table(transformed_event, "fake-conn-string", "TrafficEvents")

        # Assert: Table client was initialized correctly
        mock_tsc.from_connection_string.assert_called_once_with("fake-conn-string")
        mock_tsc.from_connection_string.return_value.get_table_client.assert_called_once_with("TrafficEvents")

        # Assert: upsert_entity was called with the correct event
        mock_table_client.upsert_entity.assert_called_once_with(transformed_event)
