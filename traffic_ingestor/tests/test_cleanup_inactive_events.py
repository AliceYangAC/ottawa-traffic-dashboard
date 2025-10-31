import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions.cleanup_inactive_events_helper import cleanup_inactive_events

# Test to ensure that inactive events are marked correctly
def test_cleanup_inactive_events_marks_entities_inactive():
    # --- Incoming transformed entities ---
    current_entities = [
        {"RowKey": "123-Collision", "Status": "ACTIVE"},
        {"RowKey": "456-Construction", "Status": "INACTIVE"},
    ]
    current_keys = {"123-Collision", "456-Construction"}

    # --- Stored entities in Table Storage ---
    stored_entities = [
        {"PartitionKey": "OttawaTraffic", "RowKey": "123-Collision", "Status": "ACTIVE"},       # should be kept
        {"PartitionKey": "OttawaTraffic", "RowKey": "789-Roadwork", "Status": "ACTIVE"},        # should be marked INACTIVE
        {"PartitionKey": "OttawaTraffic", "RowKey": "456-Construction", "Status": "INACTIVE"},  # already inactive, no update
    ]

    with patch("traffic_ingestor.helper_functions.cleanup_inactive_events_helper.TableServiceClient") as mock_tsc:
        # Mock table client and its query/update methods
        mock_table_client = MagicMock()
        mock_table_client.query_entities.return_value = stored_entities
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # Act
        cleanup_inactive_events(current_entities, "fake-conn-string", "TrafficEvents")

        # Assert: update_entity should be called only for 789-Roadwork
        assert mock_table_client.update_entity.call_count == 1

        # Extract updated entity
        updated_entity = mock_table_client.update_entity.call_args[0][0]
        assert updated_entity["RowKey"] == "789-Roadwork"
        assert updated_entity["Status"] == "INACTIVE"
        assert "LastSeen" in updated_entity
