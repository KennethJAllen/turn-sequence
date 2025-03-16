import os
import random
import requests
from pprint import pprint
from dotenv import load_dotenv
from src import utils

def check_for_errors(maps_data: dict) -> None:
    """Raises RuntimeError if API returned 'error_message'."""
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

def compute_routes(points, api_key):
    """
    Calls the Google Routes API to retrieve route information
    between origins.
    Returns response data.
    """
    routes_url = 'https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix'
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition"
    }

    # Construct the POST body for the Routes API
    waypoint_dicts = utils.points_to_waypoints(points)
    body = {
        "origins": waypoint_dicts,
        "destinations": waypoint_dicts,
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_UNAWARE"
    }
    pprint(body)

    # Make the POST request
    response = requests.post(routes_url, headers=headers, json=body, timeout=15)
    response.raise_for_status()
    route_data = response.json()
    check_for_errors(route_data)
    return route_data


def process_directions(routes: dict) -> list[int]:
    """
    Processes google maps route. Returns sequence of 1s and 0s from instructions,
    1 if there was a right turn, 0 if there was a left turn, skips otherwise.
    """
    if not routes:
        return []
    route = routes["routes"][0]['legs'][0]['steps']
    maneuvers = [instruction['navigationInstruction']['maneuver'] for instruction in route if instruction]
    turns = []
    for m in maneuvers:
        if "LEFT" in m:
            turns.append(0)
        elif "RIGHT" in m:
            turns.append(1)
    return turns


def random_point_in_bounds(south, west, north, east):
    """
    Returns a random lat/lng coordinate within the bounding box.
    """
    # TODO: Ensure sufficiently far away
    lat = random.uniform(south, north)
    lng = random.uniform(west, east)
    return lat, lng

def alternating_metric(turns: list[int]) -> float:
    """Returns fraction of turns that alternate either LEFT -> RIGHT or RIGHT -> LEFT."""
    if not turns or len(turns) == 1:
        return
    num_alternating = 0
    for index, turn in enumerate(turns[:-1]):
        if turn != turns[index+1]:
            # If the turns are the different, increment
            num_alternating += 1
    return num_alternating/(len(turns) - 1)

def get_points(num_points: int, bounds):
    """Returns num_points random points within bounds"""
    points = []
    for _ in range(num_points):
        point = random_point_in_bounds(*bounds)
        points.append(point)
    return points

def main():
    """Main access point to the script."""
    # loads variables from .env
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # TODO: Add city/state
    city_name = "new york city"
    # TODO: Only compute if not in db config
    # TODO: reject point if not valid
    
    city_bounds = geocode_city(city_name, maps_api_key)
    num_points = 2
    points = get_points(num_points, city_bounds)

    route_data = compute_routes(points, maps_api_key)
    turns = process_directions(route_data)
    frac_alternating = alternating_metric(turns)

    num_valid_routes = 0
    total_frac_alternating = 0
    if frac_alternating:
        num_valid_routes += 1
        total_frac_alternating += frac_alternating

    average_frac_alternating = total_frac_alternating/num_valid_routes
    print(f"Average fraction of alternating instructions: {average_frac_alternating} for {city_name}")

    # TODO: Store data in sqlite with sqlalchemy


if __name__ == "__main__":
    main()
