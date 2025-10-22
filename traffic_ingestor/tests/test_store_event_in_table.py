# traffic_ingestor/tests/test_store_event_in_table.py
import pytest
from unittest.mock import patch, MagicMock
from traffic_ingestor.helper_functions import store_event_in_table

def test_store_event_inserts_new_entity():
    # --- Fake event ---
    event = {
        "id": "123",
        "eventType": "Collision",
        "schedule": [{"startDateTime": "2025-10-21T10:00:00Z", "endDateTime": "2025-10-21T12:00:00Z"}],
        "message": "Kanata Ave & March Rd",
        "priority": "HIGH",
        "status": "ACTIVE",
        "geodata": {"coordinates": "[-75.69, 45.40]"}
    }

    with patch("traffic_ingestor.helper_functions.store_event_in_table.ensure_table_exists") as mock_ensure, \
         patch("traffic_ingestor.helper_functions.store_event_in_table.TableServiceClient") as mock_tsc:

        # Mock table client 
        mock_table_client = MagicMock()
        mock_table_client.get_entity.side_effect = Exception("Not found")  # simulate missing entity
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        # Act
        store_event_in_table(event, "fake-conn-string", "TrafficEvents")

        # Assert: ensure_table_exists was called
        mock_ensure.assert_called_once_with("fake-conn-string", "TrafficEvents")

        # Assert: get_entity was called to check for duplicates
        mock_table_client.get_entity.assert_called_once_with(partition_key="OttawaTraffic", row_key="123-Collision")

        # Assert: create_entity was called to insert the new event
        mock_table_client.create_entity.assert_called_once()
        inserted_entity = mock_table_client.create_entity.call_args[0][0]
        assert inserted_entity["RowKey"] == "123-Collision"
        assert inserted_entity["Location"] == "Kanata Ave & March Rd"
