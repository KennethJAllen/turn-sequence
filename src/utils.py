"""Utility functions"""
from shapely.geometry import Point

def format_point_for_waypoints(points: list[Point]) -> list[dict]:
    """
    Turns list of points (lat, lon) into list of waypoints
    formatted for input into the Routes Google API
    """
    waypoint_dicts = []
    for point in points:
        waypoint_dict = {
            "waypoint": {
                "location": {
                    "latLng": {
                        "latitude": point.x,
                        "longitude": point.y
                        }}}}
        waypoint_dicts.append(waypoint_dict)
    return waypoint_dicts
