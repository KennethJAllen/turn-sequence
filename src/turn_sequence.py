import os
import random
import requests
from dotenv import load_dotenv

def check_for_errors(maps_data: dict) -> None:
    """Raises """
    if 'error_message' in maps_data:
        raise RuntimeError(f"API Error: {maps_data['error_message']}")

def geocode_city(city_name, maps_api_key) -> tuple[float, float, float, float]:
    """
    Returns bounding box (south, west, north, east) of the city
    using the Google Geocoding API.
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": city_name,
        "key": maps_api_key
    }
    response = requests.get(base_url, params=params, timeout=15)
    response.raise_for_status()
    maps_data = response.json()
    check_for_errors(maps_data)

    # Approximate bounding box from geometry's viewport
    viewport = maps_data["results"][0]["geometry"]["viewport"]
    south = viewport["southwest"]["lat"]
    west = viewport["southwest"]["lng"]
    north = viewport["northeast"]["lat"]
    east = viewport["northeast"]["lng"]

    return south, west, north, east

def compute_routes(start, end, api_key):
    """
    Calls the Google Routes API to retrieve route information
    between start and end points. Returns a list of maneuvers
    (e.g., 'TURN_LEFT', 'TURN_RIGHT').
    """
    routes_url = f"https://routes.googleapis.com/directions/v2:computeRoutes"
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"
    }

    # Construct the POST body for the Routes API
    # This is a minimal example for 'DRIVE' mode. You can add more fields as needed.
    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": start[0],
                    "longitude": start[1]
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": end[0],
                    "longitude": end[1]
                }
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE"
    }

    # Make the POST request
    response = requests.post(routes_url, headers=headers, json=body, timeout=15)
    response.raise_for_status()
    data = response.json()
    check_for_errors(data)
    return data


def process_directions(routes: dict) -> list[str]:
    """Processes google maps """
    route = routes["routes"][0]

    distance_meters = route["distanceMeters"]          # e.g. 51734
    duration_seconds = int(route["duration"][:-1])     # "2847s" -> 2847 (seconds)
    encoded_polyline = route["polyline"]["encodedPolyline"]
    turns = [] # PLACEHOLDER
    return turns


def random_point_in_bounds(south, west, north, east):
    """
    Returns a random lat/lng coordinate within the bounding box.
    """
    # TODO: Ensure sufficiently far away
    lat = random.uniform(south, north)
    lng = random.uniform(west, east)
    return lat, lng

def main():
    # loads variables from .env
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # TODO: Add city/state
    city_name = "boston"
    # TODO: Only compute if not in config
    city_bounds = geocode_city(city_name, maps_api_key)
    start = random_point_in_bounds(*city_bounds)
    end = random_point_in_bounds(*city_bounds)
    routes = compute_routes(start, end, maps_api_key)
    turns = process_directions(routes)
    pass
    # TODO: Store data in sqlite with sqlalchemy


if __name__ == "__main__":
    main()
