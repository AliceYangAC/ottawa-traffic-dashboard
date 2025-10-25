import pytest
from traffic_ingestor.helper_functions.transform_events_helper import transform_events  # adjust import path if needed

def test_transform_events_creates_expected_entity():
    # --- Input: raw event from API ---
    raw_event = {
        "id": "123",
        "eventType": "Collision",
        "headline": "Kanata Ave & March Rd",
        "schedule": [{"startDateTime": "2025-10-21T10:00:00Z", "endDateTime": "2025-10-21T12:00:00Z"}],
        "priority": "HIGH",
        "status": "ACTIVE",
        "geodata": {"coordinates": "[-75.69, 45.40]"}
    }

    # --- Act ---
    entities = transform_events([raw_event])

    # --- Assert ---
    assert len(entities) == 1
    entity = entities[0]

    # Field-level assertions
    assert entity["PartitionKey"] == "OttawaTraffic"
    assert entity["RowKey"] == "123"
    assert entity["EventType"] == "Collision"
    assert entity["Location"] == "Kanata Ave & March Rd"
    assert entity["StartTime"] == "2025-10-21T10:00:00Z"
    assert entity["EndTime"] == "2025-10-21T12:00:00Z"
    assert entity["Priority"] == "HIGH"
    assert entity["Status"] == "ACTIVE"
    assert entity["GeoCoordinates"] == "[-75.69, 45.40]"
