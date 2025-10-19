import pytest
from jsonschema import validate, ValidationError
from FetchTrafficEvents.helpers import EDA_PAYLOAD_SCHEMA


# Purpose: Tests the payload validation logic using jsonschema.
# Contents:
    # Valid payload test
    # Missing field test
    # Incorrect data type test

def test_valid_payload():
    payload = {
        "eventType": "Collision",
        "location": "Kanata Ave & March Rd",
        "timestamp": "2025-10-19T10:00:00Z",
        "priority": "HIGH",
        "status": "ACTIVE"
    }
    validate(instance=payload, schema=EDA_PAYLOAD_SCHEMA)

def test_missing_field():
    payload = {
        "eventType": "Collision",
        "location": "Kanata Ave & March Rd",
        "timestamp": "2025-10-19T10:00:00Z",
        "priority": "HIGH"
    }
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=EDA_PAYLOAD_SCHEMA)