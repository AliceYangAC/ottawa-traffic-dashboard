import pytest
from unittest.mock import patch, MagicMock
from traffic_ingester.helper_functions.store_event_in_table_helper import store_event_in_table

def test_store_event_skips_if_entity_exists():
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

    with patch("traffic_ingester.helper_functions.store_event_in_table_helper.TableServiceClient") as mock_tsc:
        mock_table_client = MagicMock()
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # Simulate that entity already exists
        mock_table_client.get_entity.return_value = transformed_event

        # Act
        store_event_in_table(transformed_event, "fake-conn-string", "TrafficEvents")

        # Assert: get_entity was called with correct keys
        mock_table_client.get_entity.assert_called_once_with(
            partition_key="OttawaTraffic",
            row_key="123"
        )

        # Assert: upsert_entity was NOT called
        mock_table_client.upsert_entity.assert_not_called()
