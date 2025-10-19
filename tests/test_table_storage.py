import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.function_app import store_event_in_table, cleanup_inactive_events

# Purpose: Make sure that the data flow can be validated in Azure Tables correctly
# Contents:
    # Storing a new event.
    # Avoiding duplicate storage.
    # Cleaning up inactive events.

# Sample event
sample_event = {
    "eventType": "Collision",
    "location": {"description": "March Road & Carling Ave"},
    "startTime": "2025-10-19T12:00:00Z",
    "priority": "HIGH",
    "status": "ACTIVE"
}

def generate_row_key(event):
    return f"{event['eventType']}-{event['startTime'].replace(':', '').replace('-', '').replace('T', '')}"

@patch("traffic_ingestor.function_app.TableServiceClient")
def test_store_event_new(mock_table_service_client):
    mock_table_client = MagicMock()
    mock_table_service_client.from_connection_string.return_value.get_table_client.return_value = mock_table_client

    # Simulate get_entity raising an exception (entity not found)
    mock_table_client.get_entity.side_effect = Exception("Entity not found")

    store_event_in_table(sample_event)

    # Should call create_entity once
    assert mock_table_client.create_entity.call_count == 1

@patch("traffic_ingestor.function_app.TableServiceClient")
def test_store_event_duplicate(mock_table_service_client):
    mock_table_client = MagicMock()
    mock_table_service_client.from_connection_string.return_value.get_table_client.return_value = mock_table_client

    # Simulate get_entity returning an existing entity
    mock_table_client.get_entity.return_value = {"RowKey": generate_row_key(sample_event)}

    store_event_in_table(sample_event)

    # Should NOT call create_entity
    mock_table_client.create_entity.assert_not_called()

@patch("traffic_ingestor.function_app.TableServiceClient")
def test_cleanup_inactive_events(mock_table_service_client):
    mock_table_client = MagicMock()
    mock_table_service_client.from_connection_string.return_value.get_table_client.return_value = mock_table_client

    # Simulate existing entities in storage
    mock_table_client.query_entities.return_value = [
        {"PartitionKey": "OttawaTraffic", "RowKey": "Collision-20251019120000"},
        {"PartitionKey": "OttawaTraffic", "RowKey": "Construction-20251019130000"}
    ]

    # Only one event is currently active
    current_event_keys = {"Collision-20251019120000"}

    cleanup_inactive_events(current_event_keys)

    # Should delete the inactive event
    mock_table_client.delete_entity.assert_called_once_with(
        partition_key="OttawaTraffic", row_key="Construction-20251019130000"
    )