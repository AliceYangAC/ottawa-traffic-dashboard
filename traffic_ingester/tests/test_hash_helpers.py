# traffic_ingester/tests/test_hash_helpers.py
import pytest
import json
import hashlib
from unittest.mock import patch, MagicMock
from traffic_ingester.helper_functions.hash_tracker_helper import (
    get_last_hash,
    update_hash,
    has_new_events
)

PARTITION_KEY = "TrafficHash"
ROW_KEY = "LastHash"
TABLE_NAME = "TrafficMetadata"
CONNECTION_STRING = "UseevelopmentStorage=true"

# Test get_last_hash returns the correct hash value
def test_get_last_hash_returns_value():
    mock_entity = {"Hash": "abc123"}
    mock_table_client = MagicMock()
    mock_table_client.get_entity.return_value = mock_entity

    with patch("traffic_ingester.helper_functions.hash_tracker_helper.TableServiceClient") as mock_tsc:
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client
        result = get_last_hash(CONNECTION_STRING, TABLE_NAME)
        assert result == "abc123"
        mock_table_client.get_entity.assert_called_once_with(partition_key=PARTITION_KEY, row_key=ROW_KEY)

# Test get_last_hash handles exceptions and returns None
def test_get_last_hash_returns_none_on_exception():
    mock_table_client = MagicMock()
    mock_table_client.get_entity.side_effect = Exception("Entity not found")

    with patch("traffic_ingester.helper_functions.hash_tracker_helper.TableServiceClient") as mock_tsc:
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client
        result = get_last_hash(CONNECTION_STRING, TABLE_NAME)
        assert result is None

# Test update_hash calls upsert_entity with correct parameters
def test_update_hash_calls_upsert_entity():
    with patch("traffic_ingester.helper_functions.hash_tracker_helper.TableServiceClient") as mock_tsc:
        mock_table_client = MagicMock()
        mock_tsc.from_connection_string.return_value.get_table_client.return_value = mock_table_client

        update_hash(CONNECTION_STRING, TABLE_NAME, "newhash123")

        mock_table_client.upsert_entity.assert_called_once_with({
            "PartitionKey": PARTITION_KEY,
            "RowKey": ROW_KEY,
            "Hash": "newhash123"
        })

# Test has_new_events detects change and updates hash
def test_has_new_events_detects_change_and_updates_hash():
    events = [{"id": "1", "status": "ACTIVE"}]
    current_hash = "newhash123"
    old_hash = "oldhash456"

    with patch("traffic_ingester.helper_functions.hash_tracker_helper.ensure_table_exists"), \
         patch("traffic_ingester.helper_functions.hash_tracker_helper.get_last_hash", return_value=old_hash), \
         patch("traffic_ingester.helper_functions.hash_tracker_helper.update_hash") as mock_update:

        result = has_new_events(events, CONNECTION_STRING, TABLE_NAME)
        assert result is True
        mock_update.assert_called_once()

def test_has_new_events_detects_no_change():
    events = [{"id": "1", "status": "ACTIVE"}]
    payload = json.dumps(events, sort_keys=True)
    same_hash = hashlib.sha256(payload.encode()).hexdigest()

    with patch("traffic_ingester.helper_functions.hash_tracker_helper.ensure_table_exists"), \
         patch("traffic_ingester.helper_functions.hash_tracker_helper.get_last_hash", return_value=same_hash), \
         patch("traffic_ingester.helper_functions.hash_tracker_helper.update_hash") as mock_update:

        result = has_new_events(events, CONNECTION_STRING, TABLE_NAME)
        assert result is False
        mock_update.assert_not_called()
