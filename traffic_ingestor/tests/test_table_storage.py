import pytest
from traffic_ingestor.helper_functions import store_event_in_table, cleanup_inactive_events

STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
TABLE_NAME = "TrafficEvents"

@pytest.mark.usefixtures("mock_store_table_service_client")
@pytest.mark.usefixtures("mock_cleanup_table_service_client")
def test_store_event_new(mock_store_table_service_client):
    mock_store_table_service_client.get_entity.side_effect = Exception("Entity not found")

    new_event = {
        "id": "999",
        "message": "New Location",
        "eventType": "TestEvent",
        "schedule": [{"startDateTime": "2025-10-20T10:00:00Z", "endDateTime": "2025-10-20T12:00:00Z"}],
        "priority": "HIGH",
        "status": "ACTIVE"
    }

    store_event_in_table(new_event, STORAGE_CONNECTION_STRING, TABLE_NAME)
    mock_store_table_service_client.create_entity.assert_called_once()

def test_store_event_duplicate(mock_store_table_service_client, sample_event):
    mock_store_table_service_client.get_entity.return_value = {"RowKey": "123-Collision"}

    store_event_in_table(sample_event, STORAGE_CONNECTION_STRING, TABLE_NAME)
    mock_store_table_service_client.create_entity.assert_not_called()

def test_cleanup_inactive_events(mock_cleanup_table_service_client):
    mock_cleanup_table_service_client.query_entities.return_value = [
        {"PartitionKey": "OttawaTraffic", "RowKey": "123-Collision", "Status": "ACTIVE"},
        {"PartitionKey": "OttawaTraffic", "RowKey": "456-Construction", "Status": "INACTIVE"}
    ]

    cleanup_inactive_events(STORAGE_CONNECTION_STRING, TABLE_NAME)

    mock_cleanup_table_service_client.delete_entity.assert_called_once_with(
        partition_key="OttawaTraffic", row_key="456-Construction"
    )