import pytest
from unittest.mock import MagicMock
from azure.data.tables import TableServiceClient
from traffic_ingestor.helper_functions import store_event_in_table, cleanup_inactive_events

STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
TABLE_NAME = "TrafficEvents"

def test_store_event_new(sample_event):
    mock_table_client = MagicMock()
    mock_table_client.get_entity.side_effect = Exception("Entity not found")

    mock_service = MagicMock()
    mock_service.get_table_client.return_value = mock_table_client

    TableServiceClient.from_connection_string = MagicMock(return_value=mock_service)

    store_event_in_table(sample_event, STORAGE_CONNECTION_STRING, TABLE_NAME)
    mock_table_client.create_entity.assert_called_once()

def test_store_event_duplicate(sample_event):
    mock_table_client = MagicMock()
    mock_table_client.get_entity.return_value = {"RowKey": "123-Collision"}

    mock_service = MagicMock()
    mock_service.get_table_client.return_value = mock_table_client

    TableServiceClient.from_connection_string = MagicMock(return_value=mock_service)

    store_event_in_table(sample_event, STORAGE_CONNECTION_STRING, TABLE_NAME)
    mock_table_client.create_entity.assert_not_called()

def test_cleanup_inactive_events():
    mock_table_client = MagicMock()
    mock_table_client.query_entities.return_value = [
        {"PartitionKey": "OttawaTraffic", "RowKey": "123-Collision", "Status": "ACTIVE"},
        {"PartitionKey": "OttawaTraffic", "RowKey": "456-Construction", "Status": "INACTIVE"},
        {"PartitionKey": "OttawaTraffic", "RowKey": "789-Closure", "Status": "ACTIVE"}  # not in current_events
    ]

    mock_service = MagicMock()
    mock_service.get_table_client.return_value = mock_table_client

    TableServiceClient.from_connection_string = MagicMock(return_value=mock_service)

    current_events = [
        {"id": "123", "eventType": "Collision"},
        {"id": "456", "eventType": "Construction"}  # This one is INACTIVE
        # "789-Closure" is missing and should be deleted
    ]

    cleanup_inactive_events(current_events, STORAGE_CONNECTION_STRING, TABLE_NAME)

    mock_table_client.delete_entity.assert_any_call(partition_key="OttawaTraffic", row_key="456-Construction")
    mock_table_client.delete_entity.assert_any_call(partition_key="OttawaTraffic", row_key="789-Closure")
    assert mock_table_client.delete_entity.call_count == 2