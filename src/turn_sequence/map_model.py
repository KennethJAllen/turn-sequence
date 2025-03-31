"""
Contains CityPoints method which generates polygon
and evenly partitioned grid points for a city
"""
from itertools import product
import osmnx as ox
import requests
import pandas as pd
from shapely.geometry import Point, Polygon
from turn_sequence import utils
from turn_sequence.config import Config, PlaceColumns, PointColumns, DirectionColumns

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
        self.osm_id: int = gdf.loc[0,'osm_id']
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
            place_columns.id: [self.osm_id],
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
    1) Paritions a city into grid points
    2) Splits bounding box into granulariy x granularity points
    3) Rejects points that are not within the city
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
        grid_lat = [grid_point.y for grid_point in self.grid_points]
        grid_lon = [grid_point.x for grid_point in self.grid_points]
        if self.snapped_points is not None:
            snapped_lat = [snapped_point.y if snapped_point is not None else None for snapped_point in self.snapped_points]
            snapped_lon = [snapped_point.x if snapped_point is not None else None for snapped_point in self.snapped_points]
        else:
            snapped_lat = None
            snapped_lon = None
        data = {
            point_columns.place_id: self.place.osm_id,
            point_columns.grid_lat: grid_lat,
            point_columns.grid_lon: grid_lon,
            point_columns.snapped_lat: snapped_lat,
            point_columns.snapped_lon: snapped_lon
        }
        return pd.DataFrame(data)

    def _generate_grid_points(self, num: int) -> list[Point]:
        """
        Partitions the city into grid points, evenly spaced along lat and lon.
        Iterates over points in bounding box.
        If they are not in the polygon bounding the Place, they are tossed.
        Returns a list of points spaced dx, dy apart inside the polygon.
        """
        print("Partioning city into evenly spaced points...")
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
        Returns at most num_points from city points
        Ensures each point is drivable withing the city
        e.g., not in the water.
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
    """Handles directions between place points."""
    def __init__(self, place_points: PlacePoints, direction_columns: DirectionColumns, api_key: str):
        pass

    def get_route_data(self, origin: Point, destination: Point, api_key: str):
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

    def get_double_turns(self, points: list[Point], api_key) -> float:
        """
        Parameters:
            - A list of points to calculate pairwise turns
            - Google Cloud API key
        Returns
            - Percentage of turns that alternate between left, right or right, left
            for choices of two points as origin and destination.
        """
        
        print("Calculating turn sequences...")
        all_double_turns = []
        for origin, destination in product(points, points):
            if origin == destination:
                continue
            route_data = self.get_route_data(origin, destination, api_key)
            maneuvers = utils.get_maneuvers_from_routes(route_data)
            turns = utils.get_turns_from_maneuvers(maneuvers)
            double_turns = utils.get_double_turns(turns)
            all_double_turns += double_turns

        return all_double_turns


class MapModel:
    """Contains all place, point, and direction data."""
    def __init__(self, name: str, config: Config, api_key: str=None):
        self.place = Place(name, config.place_columns)
        self.points = PlacePoints(self.place,
                                  config.map_.granulariy,
                                  config.point_columns,
                                  api_key=api_key)
        if api_key is not None:
            raise NotImplementedError()
        else:
            self.directions = None

def main():
    from pathlib import Path
    import os
    from dotenv import load_dotenv
    from turn_sequence.config import load_config
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)
    #name = "Philadelphia, Pennsylvania, USA"
    name = "Boston, Massachusetts, USA"

    model = MapModel(name, config, api_key=api_key)
    print(model.place.df)
    print(model.points.df)

if __name__ == "__main__":
    main()
