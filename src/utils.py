"""Utility functions"""
from shapely.geometry import Point

def format_route_body(origin: Point, destination: Point) -> dict:
    """
    Formats post request body for Google Routes API.
    Point.x is lattitude, Point.y is longitude.
    """
    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin.x,
                    "longitude": origin.y
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination.x,
                    "longitude": destination.y
                }
            }
        },
        "travelMode": "DRIVE"
    }
    return body

def check_for_errors(maps_data: dict) -> None:
    """Raises RuntimeError if Google API returned 'error_message'."""
    if 'error_message' in maps_data:
        raise RuntimeError(f"Google API Error: {maps_data['error_message']}")

def get_maneuvers_from_routes(routes: dict) -> list[str]:
    """
    Given the route response from Google Routes API,
    process response into list of maneuvers.
    """
    if not routes:
        return []
    steps = routes["routes"][0]['legs'][0]['steps']
    maneuvers = [step['navigationInstruction']['maneuver'] for step in steps if step]
    return maneuvers

def get_turns_from_maneuvers(maneuvers: list[str]) -> list[str]:
    """
    Given a list of maneuvers,
    Returns sequence of "L" or "R" corresponding to left or right turns.
    """
    turns = []
    for m in maneuvers:
        if "LEFT" in m:
            turns.append("L")
        elif "RIGHT" in m:
            turns.append("R")
    return turns

def get_double_turns(turns: list[str]) -> list[str]:
    """
    Given a list of turns in the form "L" or "R", return a list of sequential turns.
    Possibilities are:
        - LL for left then left
        - LR for left then right
        - RL for right then left
        - RR for right then right
    """
    double_turns = []
    for index, turn in enumerate(turns[:-1]):
        t_next = turns[index+1]
        double_turns.append(turn + t_next)
    return double_turns

def alternating_metric(double_turns: list[str]) -> float:
    """Returns fraction of turns that alternate either LEFT -> RIGHT or RIGHT -> LEFT."""
    num_alternating_turns = 0
    for double_turn in double_turns:
        if double_turn not in ["LL", "RR", "LR", "RL"]:
            raise ValueError(f"All double turns must be one of 'LL', 'RR', 'LR', or 'RL'. Instead got: {double_turn}")
        if double_turn == "RL" or double_turn == "RL":
            num_alternating_turns += 1
    return num_alternating_turns / len(double_turns)
