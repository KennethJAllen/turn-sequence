import os
from itertools import product
from pathlib import Path
import requests
from dotenv import load_dotenv
import pandas as pd
from shapely.geometry import Point
import pygsheets
from pygsheets.exceptions import SpreadsheetNotFound, WorksheetNotFound
from pygsheets import Spreadsheet
from turn_sequence import utils
from turn_sequence.city_sampler import CityPoints
from turn_sequence.config import load_config, Config, SheetConfig, PathConfig

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

def get_gsheets(sheet_config: SheetConfig,
                   credential_path: Path,
                   email: str=None,
                   publish: bool=True,
                   reset: bool=False) -> Spreadsheet:
    """
    Creates Google Sheets spreadsheet for storing city, point, and direction data.
    inputs:
        sheets: An instance of the Sheets parameter class that contains the names of the sheet and worksheet.
        credential_path: The path to the credentials.
        email (optional): If you want to add your personal account as an editor
        publish (optional): Make the data public to anyone with the url.
        reset (optional): Male reset the spreadsheet
    """
    gc = pygsheets.authorize(service_file=credential_path)

    try:
        # Try to open an existing spreadsheet
        spreadsheet = gc.open(sheet_config.name)
        if reset:
            print("Resetting spreadsheet...")
            gc.drive.delete(spreadsheet.id)
            raise SpreadsheetNotFound
        print("Opening spreadsheet...")

    except SpreadsheetNotFound:
        # Create the spreadsheet if it does not exist
        print("Creating spreadsheet with worksheets...")
        spreadsheet = gc.create(sheet_config.name)
        _init_sheet(spreadsheet, sheet_config)

    # Optionally share the spreadsheet to access from personal email
    if email is not None:
        print(f"Sharing spreadsheet to email: {email}")
        spreadsheet.share(email, role='writer', emailMessage="Here is the Turning Sequence data spreadsheet!")
    if publish:
        # Make spreadsheet public with read only access
        spreadsheet.share('', role='reader', type='anyone')

    print(f"Spreadsheet URL: {spreadsheet.url}")

    return spreadsheet

def _init_sheet(spreadsheet: Spreadsheet, sheet_config: SheetConfig) -> None:
    """Initializes the spreadsheet with the proper worksheet names and headers."""
    # rename sheet1 & create the rest of the worksheets
    city_ws = spreadsheet.sheet1
    city_ws.title = sheet_config.city_worksheet
    point_ws = spreadsheet.add_worksheet(sheet_config.point_worksheet)
    directions_ws = spreadsheet.add_worksheet(sheet_config.directions_worksheet)

    # Add headers
    city_ws.insert_rows(row=0, number=1, values=[sheet_config.city_columns])
    point_ws.insert_rows(row=0, number=1, values=[sheet_config.point_columns])
    directions_ws.insert_rows(row=0, number=1, values=[sheet_config.directions_columns])

def add_to_gsheets(spreadsheet: Spreadsheet, sheet_config: SheetConfig, df: pd.DataFrame) -> None:
    """Add data to spreadsheet"""
    worksheet = spreadsheet.worksheet('title', sheet_config.city_worksheet)
    sheet_header = worksheet.get_row(1, include_tailing_empty=False)

    # Reorder the DataFrame columns to match the sheet header
    df = df[sheet_header]

    col_data = worksheet.get_col(1, include_tailing_empty=False)
    start_row = len(col_data) + 1

    # Set the DataFrame to the sheet starting at cell A1
    #worksheet.append_table(values, start='A1', end=None, dimension='ROWS', overwrite=False)

def main():
    """Main access point to the script."""
    # load variables from .env
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    email = os.getenv("EMAIL")
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)

    spreadsheet = get_gsheets(config.sheets, config.paths.oatuth_credentials, email=email, publish=True, reset=False)
    #add_to_gsheets(spreadsheet, config.sheets, df)

    return

    for city in config.map.cities:
        city_points = CityPoints(city, config.map.granulariy)
        points = get_valid_city_points(city_points, config.map.num_points, maps_api_key)

        all_double_turns = get_double_turns(points, maps_api_key)
        print(all_double_turns)

if __name__ == "__main__":
    main()
