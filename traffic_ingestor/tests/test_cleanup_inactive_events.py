# traffic_ingestor/tests/test_cleanup_inactive_events.py
import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions import cleanup_inactive_events

def test_cleanup_inactive_events_deletes_outdated_entities():
    # Mock incoming events from API
    incoming_events = [
        {"id": "123", "eventType": "Collision", "status": "ACTIVE"},
        {"id": "456", "eventType": "Construction", "status": "INACTIVE"},
    ]
    expected_keys = {"123-Collision", "456-Construction"}

    # Mock stored entities in Table Storage
    stored_entities = [
        {"PartitionKey": "OttawaTraffic", "RowKey": "123-Collision", "Status": "ACTIVE"},       # should be kept
        {"PartitionKey": "OttawaTraffic", "RowKey": "789-Roadwork", "Status": "INACTIVE"},      # should be deleted
        {"PartitionKey": "OttawaTraffic", "RowKey": "456-Construction", "Status": "INACTIVE"},  # should be deleted
    ]

    with patch("traffic_ingestor.helper_functions.cleanup_inactive_events.TableServiceClient") as mock_tsc:
        # Mock table client and its query/delete methods
        mock_table_client = MagicMock()
        mock_table_client.query_entities.return_value = stored_entities
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # Act
        cleanup_inactive_events(incoming_events, "fake-conn-string", "TrafficEvents")

        # Assert: delete_entity should be called for 2 outdated/inactive entities
        assert mock_table_client.delete_entity.call_count == 2

        # Extract actual calls
        deleted_keys = {
            call.kwargs["row_key"]
            for call in mock_table_client.delete_entity.call_args_list
        }

        assert deleted_keys == {"789-Roadwork", "456-Construction"}
