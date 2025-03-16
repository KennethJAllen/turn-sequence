import os
from pprint import pprint
import requests
from dotenv import load_dotenv
from shapely.geometry import Point
from src import utils
from src.city_sampler import CityPoints

def check_for_errors(maps_data: dict) -> None:
    """Raises RuntimeError if Google API returned 'error_message'."""
    if 'error_message' in maps_data:
        raise RuntimeError(f"Google API Error: {maps_data['error_message']}")

def compute_routes(points: list[Point], api_key):
    """
    Calls the Google Routes API to retrieve route information between origins.
    Returns response data.
    """
    routes_url = 'https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix'
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition"
    }

    # Construct the POST body for the Routes API
    waypoint_dicts = utils.format_point_for_waypoints(points)
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

def alternating_metric(turns: list[int]) -> float:
    """Returns fraction of turns that alternate either LEFT -> RIGHT or RIGHT -> LEFT."""
    if not turns or len(turns) == 1:
        raise ValueError(f"Not enough turns provided: {turns}")
    num_alternating = 0
    for index, turn in enumerate(turns[:-1]):
        if turn != turns[index+1]:
            # If the turns are the different, increment
            num_alternating += 1
    return num_alternating/(len(turns) - 1)

def get_valid_points(city_points: CityPoints, num_points: int, api_key: str) -> list[Point]:
    """
    Returns at most num_points from city points
    Ensures each point is drivable withing the city
    e.g., not in the water.
    """
    valid_points = []
    num_valid_points = 0
    for point in city_points.get_shuffled_grid_points():
        snapped_point = snap_to_road(point, api_key)
        if snapped_point is None:
            continue
        valid_points.append(snapped_point)
        num_valid_points += 1
        if len(valid_points) == num_points:
            return valid_points
    # If we have iterated through all points and have not found num_points valid points...
    if not valid_points:
        raise ValueError(f"Could not find any valid points for {city_points}")

    print((f"Could not find {num_points} points in {city_points}.\n"
           f"Found {len(valid_points)} valid points out of {len(city_points)}"))
    return valid_points

def snap_to_road(point: Point, api_key) -> Point:
    """
    Returns a (lat, lng) snapped to the nearest road, or None if no road is found.
    """
    lat = point.x
    lon = point.y
    base_url = "https://roads.googleapis.com/v1/snapToRoads"
    params = {
        "path": f"{lat},{lon}",
        "interpolate": "false",
        "key": api_key
    }
    response = requests.get(base_url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    check_for_errors(data)

    # 'snappedPoints' will be empty if there's no road within ~50m
    snapped_points = data.get("snappedPoints", [])
    if not snapped_points:
        return None  # Means no road found near your point

    # The first snapped point is the nearest road location
    snapped_location = snapped_points[0]["location"]
    snapped_lat = snapped_location["latitude"]
    snapped_lon = snapped_location["longitude"]
    return Point(snapped_lat, snapped_lon)

def main():
    """Main access point to the script."""
    # loads variables from .env
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    city_name = "Philadelphia, Pennsylvania, USA"
    granulariy = 10
    # TODO: Only compute if not in db config
    city_points = CityPoints(city_name, granulariy)
    
    num_points = 2
    points = get_valid_points(city_points, num_points, maps_api_key)

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
