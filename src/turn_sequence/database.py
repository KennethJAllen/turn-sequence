import os
from itertools import product
import requests
from dotenv import load_dotenv
from shapely.geometry import Point
import pygsheets
from turn_sequence import utils
from turn_sequence.city_sampler import CityPoints

def get_route_data(origin: Point, destination: Point, api_key: str):
    """
    Given an origin and desitination as Point objects,
    return the route data from Google Routes API.
    Point.x is lattitude, Point.y is longitude.
    """
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    if origin == destination:
        raise ValueError("Origin and destination must be different.")
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "routes.legs.steps.navigationInstruction.maneuver"
        )
    }

    body = utils.format_route_body(origin, destination)

    response = requests.post(url, headers=headers, json=body, timeout=15)
    response.raise_for_status()
    route_data = response.json()
    utils.check_for_errors(route_data)
    return route_data


def get_valid_city_points(city_points: CityPoints, num_points: int, api_key: str) -> list[Point]:
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
    lon = point.x
    lat = point.y
    base_url = "https://roads.googleapis.com/v1/snapToRoads"
    params = {
        "path": f"{lat},{lon}",
        "interpolate": "false",
        "key": api_key
    }
    response = requests.get(base_url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    utils.check_for_errors(data)

    # 'snappedPoints' will be empty if there's no road within ~50m
    snapped_points = data.get("snappedPoints", [])
    if not snapped_points:
        return None  # Means no road found near your point

    # The first snapped point is the nearest road location
    snapped_location = snapped_points[0]["location"]
    snapped_lat = snapped_location["latitude"]
    snapped_lon = snapped_location["longitude"]
    return Point(snapped_lat, snapped_lon)

def get_double_turns(points: list[Point], api_key) -> float:
    """
    Parameters:
        - A city name in the form 'City, State, Country'
        - Number of points to sample from the city
        - Granularity of partitioning the city into points
        - A Google API key with access to the Routes and Roads APIs
    Returns
        - Percentage of turns that alternate between left, right or right, left
        for choices of two points as origin and destination.
    """
    
    print("Calculating turn sequences...")
    all_double_turns = []
    for origin, destination in product(points, points):
        if origin == destination:
            continue
        route_data = get_route_data(origin, destination, api_key)
        maneuvers = utils.get_maneuvers_from_routes(route_data)
        turns = utils.get_turns_from_maneuvers(maneuvers)
        double_turns = utils.get_double_turns(turns)
        all_double_turns += double_turns

    return all_double_turns

def main():
    """Main access point to the script."""
    # load variables from .env
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    city_name = "Philadelphia, Pennsylvania, USA"
    map_granulariy = 10
    num_points = 3

    city_points = CityPoints(city_name, map_granulariy)
    points = get_valid_city_points(city_points, num_points, maps_api_key)

    all_double_turns = get_double_turns(points, maps_api_key)

    # from turn_sequence import analysis
    # alternating_turn_frequency = analysis.alternating_metric(all_double_turns)
    # print(f"Fraction of alternating turns: {alternating_turn_frequency} for {city_name}")

if __name__ == "__main__":
    main()
