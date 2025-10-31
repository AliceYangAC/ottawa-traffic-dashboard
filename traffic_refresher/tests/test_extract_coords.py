import pytest
from traffic_refresher.helper_functions.extract_coords_helper import extract_coords

# Test various input formats for extract_coords function
@pytest.mark.parametrize("input_coords, expected", [
    ([-75.69, 45.40], (45.40, -75.69)),                      # list of floats
    (("-75.69", "45.40"), (45.40, -75.69)),                  # tuple of strings
    ("[-75.69, 45.40]", (45.40, -75.69)),                    # JSON-style string
    ("(-75.69, 45.40)", (45.40, -75.69)),                    # Python-style string (fallback to ast)
    ("invalid", (None, None)),                               # malformed string
    (None, (None, None)),                                    # None input
    ([], (None, None)),                                      # empty list
    ([1], (None, None)),                                     # incomplete list
    ("[1]", (None, None)),                                   # incomplete JSON string
])
def test_extract_coords_various_inputs(input_coords, expected):
    assert extract_coords(input_coords) == expected
