import json
import ast

# Helper function to extract Latitude and Longitude from GeoCoordinates field
def extract_coords(coords):
    try:
        # If it's already a list/tuple
        if isinstance(coords, (list, tuple)) and len(coords) == 2:
            lon, lat = coords
            return float(lat), float(lon)

        # If it's a string like "[-75.69, 45.40]"
        if isinstance(coords, str):
            try:
                parsed = json.loads(coords)
            except Exception:
                parsed = ast.literal_eval(coords)  # fallback
            if isinstance(parsed, (list, tuple)) and len(parsed) == 2:
                lon, lat = parsed
                return float(lat), float(lon)
    except Exception as e:
        print(f"Failed to parse GeoCoordinates {coords}: {e}")

    return None, None
