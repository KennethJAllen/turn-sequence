"""Utility functions"""
import pandas as pd
from shapely.geometry import Point
from pygsheets import Worksheet

def format_route_body(origin: Point, destination: Point) -> dict:
    """
    Formats post request body for Google Routes API.
    Point.x is lattitude, Point.y is longitude.
    """
    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin.y,
                    "longitude": origin.x
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination.y,
                    "longitude": destination.x
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

def get_column_index_from_name(worksheet: Worksheet, column_name: str) -> int:
    """
    Retrieve the column index for a given header in a pygsheets worksheet.

    Args:
        worksheet: The pygsheets worksheet object.
        column_name: The header string to find.

    Returns:
        An integer representing the 1-indexed column position of the header,
        or None if the header is not found.
    """
    header = worksheet.get_row(1, include_tailing_empty=False)
    try:
        # Convert to 1-indexed
        column_index = header.index(column_name) + 1
        return column_index
    except ValueError:
        return None

def get_max_value_from_worksheet_column(worksheet: Worksheet, column_name: str) -> float:
    """
    Gets the maximum value from a worksheet corresponding to a given column name.
    If there are no numeric values in the column, return 0.
    """
    col_index = get_column_index_from_name(worksheet, column_name)
    col_values = worksheet.get_col(col_index, include_tailing_empty=False)
    numeric_values = []
    for value in col_values[1:]:
        try:
            numeric_values.append(float(value))
        except (ValueError, TypeError):
            continue
    if not numeric_values:
        return 0
    return max(numeric_values)

def get_gsheet_df(sheet_id: str, gid: int) -> pd.DataFrame:
    """
    Reads worksheet correspongin to gid
    from google sheets and returns it as a dataframe.
    """
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&id={sheet_id}&gid={gid}'
    df = pd.read_csv(url)
    return df
