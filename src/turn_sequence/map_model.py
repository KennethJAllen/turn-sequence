"""
Contains model for map data.
"""
import random
import osmnx as ox
import requests
import pandas as pd
from shapely.geometry import Point, Polygon
from turn_sequence import utils
from turn_sequence.config import ProjectConfig, PlaceColumns, PointColumns, DirectionColumns

class Place:
    """
    Data at the place level, e.g. in a city
    pulled from OpenStreetMap.
    """
    def __init__(self, name: str, place_columns: PlaceColumns):
        self.name: str = name

        gdf = ox.geocode_to_gdf(self.name)
        if gdf.empty:
            raise ValueError(f"Place data not returned for {self.name}")

        self.display_name: str = gdf.loc[0,'display_name']
        self.id: int = gdf.loc[0,'osm_id']
        self.lat_min: float = gdf.loc[0,'bbox_south']
        self.lon_min: float = gdf.loc[0,'bbox_west']
        self.lat_max: float = gdf.loc[0,'bbox_north']
        self.lon_max: float = gdf.loc[0,'bbox_east']
        self.polygon: Polygon = gdf.loc[0,'geometry']
        self.df: pd.DataFrame = self._to_df(place_columns)

    def __str__(self):
        return self.display_name

    def _to_df(self, place_columns: PlaceColumns):
        data = {
            place_columns.id: [self.id],
            place_columns.name: [self.name],
            place_columns.display_name: [self.display_name],
            place_columns.lat_min: [self.lat_min],
            place_columns.lat_max: [self.lat_max],
            place_columns.lon_min: [self.lon_min],
            place_columns.lon_max: [self.lon_max]
            }
        return pd.DataFrame(data)

class PlacePoints:
    """
    Generates points within a given Place.
    1) Paritions a place into grid points
    2) Splits bounding box into granulariy x granularity points
    3) Rejects points that are not within the place
    """
    def __init__(self, place: Place, map_granularity: int, point_columns: PointColumns, api_key: str = None):
        # Get a GeoDataFrame of the boundary polygon
        self.place: Place = place
        self.grid_points: list[Point] = self._generate_grid_points(map_granularity)
        if not self.grid_points:
            raise ValueError(f"No points found in: {self.place}")
        if api_key is not None:
            self.snapped_points: list[Point] = self._snap_grid_points_to_road(api_key)

        else:
            self.snapped_points = None
        self.df = self._to_df(point_columns)

    def _to_df(self, point_columns: PointColumns) -> pd.DataFrame:
        """Converts data to dataframe."""
        ids = tuple(range(len(self.grid_points)))
        grid_lat = [grid_point.y for grid_point in self.grid_points]
        grid_lon = [grid_point.x for grid_point in self.grid_points]
        if self.snapped_points is not None:
            snapped_lat = [snapped_point.y if snapped_point is not None else None for snapped_point in self.snapped_points]
            snapped_lon = [snapped_point.x if snapped_point is not None else None for snapped_point in self.snapped_points]
        else:
            snapped_lat = None
            snapped_lon = None
        data = {
            point_columns.id: ids,
            point_columns.place_id: self.place.id,
            point_columns.grid_lat: grid_lat,
            point_columns.grid_lon: grid_lon,
            point_columns.snapped_lat: snapped_lat,
            point_columns.snapped_lon: snapped_lon
        }
        return pd.DataFrame(data)

    def _generate_grid_points(self, num: int) -> list[Point]:
        """
        Partitions the place into grid points, evenly spaced along lat and lon.
        Iterates over points in bounding box.
        If they are not in the polygon bounding the Place, they are tossed.
        Returns a list of points spaced dx, dy apart inside the polygon.
        """
        print("Partioning place into evenly spaced points...")
        minx, miny, maxx, maxy = self.place.polygon.bounds
        dx = (maxx - minx)/num
        dy = (maxy - miny)/num
        points = []
        
        # Move through the bounding box in increments of dx, dy
        x = minx
        while x <= maxx:
            y = miny
            while y <= maxy:
                candidate = Point(x, y)
                if self.place.polygon.contains(candidate):
                    points.append(candidate)
                y += dy
            x += dx

        return points

    def _snap_grid_points_to_road(self, api_key: str) -> list[Point]:
        """
        Snaps all points to the road.
        Ensures each point is drivable, e.g., not in the water.
        """
        snapped_points = []
        for point in self.grid_points:
            snapped_point = self._snap_to_road(point, api_key)
            snapped_points.append(snapped_point)
        # If we have iterated through all points and have not found num_points valid points...
        if not snapped_points:
            raise ValueError(f"Could not find any valid points for {self.place}")

        return snapped_points

    def _snap_to_road(self, point: Point, api_key) -> Point:
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
        return Point(snapped_lon, snapped_lat)

class Directions:
    """
    Handles directions between place points.
    If choose_n_random is provided, chooses n random points to compute pairwise directions
    instead of computing pairwise directions for all snapped points.
    Otherwise, computes all pairwise directions for all snapped points.

    WARNING: if there are n snapped points in points,
    makes O(n^2) API calls to find all pairwise directions.
    """
    def __init__(self, points: PlacePoints,
                 direction_columns: DirectionColumns,
                 api_key: str,
                 choose_random: int = None):
        self.points = points
        snapped_points = [snapped_point for snapped_point in self.points.snapped_points if snapped_point is not None]
        if choose_random is not None:
            random.shuffle(snapped_points)
            points = snapped_points[:choose_random]
        else:
            points = snapped_points
        self.df = self._to_df(points, direction_columns, api_key)

    def _get_route_data(self, origin: Point, destination: Point, api_key: str):
        """
        Given an origin and desitination as Point objects,
        return the route data from Google Routes API.
        """
        if origin == destination:
            raise ValueError("Origin and destination must be different.")

        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
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

    def _to_df(self, points: list[Point], direction_columns: DirectionColumns, api_key: str) -> pd.DataFrame:
        """
        Finds and processes pairwise directions for all pairwise points in points.
        Uses Google Routes API to find directions.
        returns data formatted as dataframe.
        WARNING: if there are n points in points, this functions makes O(n^2) API calls to find all pairwise directions.
        """
        origin_id_col = []
        destination_id_col = []
        raw_directions_col = []
        lr_directions_col = []
        double_directions_col = []

        for origin_id, origin in enumerate(points):
            for destination_id, destination in enumerate(points):
                if origin == destination:
                    continue
                route_data = self._get_route_data(origin, destination, api_key)
                if not route_data:
                    continue
                raw_directions = utils.get_maneuvers_from_routes(route_data)
                lr_directions = utils.get_turns_from_maneuvers(raw_directions)
                double_directions = utils.get_double_turns(lr_directions)

                origin_id_col.append(origin_id)
                destination_id_col.append(destination_id)
                raw_directions_col.append(raw_directions)
                lr_directions_col.append(lr_directions)
                double_directions_col.append(double_directions)

        ids = tuple(range(len(raw_directions_col)))
        data = {
            direction_columns.id: ids,
            direction_columns.origin_id: origin_id_col,
            direction_columns.destination_id: destination_id_col,
            direction_columns.place_id: self.points.place.id,
            direction_columns.raw_directions: raw_directions_col,
            direction_columns.lr_directions: lr_directions_col,
            direction_columns.double_directions: double_directions_col
        }
        return pd.DataFrame(data)

class MapModel:
    """Contains all place, point, and direction data."""
    def __init__(self, name: str, config: ProjectConfig, api_key: str=None):
        self.place = Place(name, config.place_columns)
        self.points = PlacePoints(self.place,
                                  config.map_.granulariy,
                                  config.point_columns,
                                  api_key=api_key)
        if api_key is not None:
            self.directions = Directions(self.points, config.direction_columns, api_key=api_key)
        else:
            self.directions = None

def main():
    from pathlib import Path
    import os
    from dotenv import load_dotenv
    from turn_sequence.config import load_project_config
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    config_path = Path.cwd() / "config" / "project_config.yaml"
    config = load_project_config(config_path)
    name = "Philadelphia, Pennsylvania, USA"
    #name = "Boston, Massachusetts, USA"

    model = MapModel(name, config, api_key=api_key)
    print(model.place.df)
    print(model.points.df)
    print(model.directions.df)

if __name__ == "__main__":
    main()
