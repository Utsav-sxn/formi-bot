import json
import os

# Load and process knowledge_chunks.json once, cache it for the app lifetime
def load_location_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(BASE_DIR, 'knowledge_chunks.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    locations = {}

    # Your data is an array of dicts, each containing outlet info
    # We'll convert it into a dictionary keyed by a normalized location name (e.g. 'indiranagar')

    for outlet in data:
        # Normalize the location key from outlet['outlet'] (e.g. "Indiranagar")
        loc_key = outlet.get('outlet', '').strip().lower().replace(' ', '_')

        # Extract required info safely, fallback empty strings/dicts if keys missing
        locations[loc_key] = {
            "address": outlet.get("address", ""),
            "phone_numbers": outlet.get("phone_numbers", []),
            "timings": outlet.get("timings", {}),
            "amenities": outlet.get("amenities", {}),
            "offers": outlet.get("offers", {}),
        }

    return locations


# Load once and keep global
LOCATIONS_DATA = load_location_data()
