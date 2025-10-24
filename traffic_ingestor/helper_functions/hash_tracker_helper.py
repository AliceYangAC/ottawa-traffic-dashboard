from azure.data.tables import TableServiceClient
from traffic_ingestor.helper_functions.ensure_table_exists_helper import ensure_table_exists
import hashlib
import json

PARTITION_KEY = "TrafficHash"
ROW_KEY = "LastHash"

def get_last_hash(connection_string, table_name):
    try:
        table_service = TableServiceClient.from_connection_string(connection_string)
        table_client = table_service.get_table_client(table_name)
        entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
        return entity.get("Hash", None)
    except Exception:
        return None  # No hash stored yet

def update_hash(connection_string, table_name, new_hash):
    table_service = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service.get_table_client(table_name)
    entity = {
        "PartitionKey": PARTITION_KEY,
        "RowKey": ROW_KEY,
        "Hash": new_hash
    }
    table_client.upsert_entity(entity)

def has_new_events(events, connection_string, table_name):
    ensure_table_exists(connection_string, table_name)
    payload = json.dumps(events, sort_keys=True)
    current_hash = hashlib.sha256(payload.encode()).hexdigest()
    last_hash = get_last_hash(connection_string, table_name)

    print(f"[Hash Check] Current: {current_hash}, Last: {last_hash}")

    if not last_hash or current_hash != last_hash:
        update_hash(connection_string, table_name, current_hash)
        return True
    return False

