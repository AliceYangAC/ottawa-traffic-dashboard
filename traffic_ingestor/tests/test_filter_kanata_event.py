# tests/test_filter_kanata_event.py

from traffic_ingestor.helper_functions import is_kanata_event
import sys
print(sys.path)

# Purpose: Make sure that the data flow is filtered to roads near Kanata Tech Hub

def test_event_in_kanata():
    event = {
        "location": {
            "description": "Collision at March Road and Carling Avenue"
        }
    }
    assert is_kanata_event(event) is True

def test_event_not_in_kanata():
    event = {
        "location": {
            "description": "Accident on Bank Street downtown"
        }
    }
    assert is_kanata_event(event) is False

def test_event_with_missing_location():
    event = {}
    assert is_kanata_event(event) is False

def test_event_with_empty_description():
    event = {
        "location": {
            "description": ""
        }
    }
    assert is_kanata_event(event) is False