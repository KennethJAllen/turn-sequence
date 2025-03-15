"""Utility functions"""

def points_to_waypoints(points: list[tuple[float, float]]) -> list[dict]:
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
                        "latitude": point[0],
                        "longitude": point[1]
                        }}}}
        waypoint_dicts.append(waypoint_dict)
    return waypoint_dicts
