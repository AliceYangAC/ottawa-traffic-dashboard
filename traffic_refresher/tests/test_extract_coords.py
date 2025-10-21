# traffic_refresher/tests/test_extract_coords.py
import pytest
from traffic_refresher.helper_functions.extract_coords import extract_coords

@pytest.mark.parametrize(
    "input_val, expected",
    [
        # Already a list
        ([-75.69, 45.40], (45.40, -75.69)),
        # Already a tuple
        ((-75.70, 45.41), (45.41, -75.70)),
        # JSON string
        ("[-75.71, 45.42]", (45.42, -75.71)),
        # Python literal string
        ("(-75.72, 45.43)", (45.43, -75.72)),
        # Bad string
        ("not a coord", (None, None)),
        # Wrong length
        ([1.0], (None, None)),
        # Completely invalid type
        (12345, (None, None)),
    ]
)
def test_extract_coords_various_inputs(input_val, expected):
    assert extract_coords(input_val) == expected
