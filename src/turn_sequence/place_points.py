"""
Contains CityPoints method which generates polygon
and evenly partitioned grid points for a city
"""
from dataclasses import dataclass, field
import osmnx as ox
import requests
from shapely.geometry import Point, Polygon
from turn_sequence import utils

@dataclass
class Place:
    """
    Data at the place level, e.g. in a city
    pulled from OpenStreetMap.
    """
    name: str
    display_name: str = field(init=False)
    osm_id: int = field(init=False)
    bbox_west: float = field(init=False)
    bbox_south: float = field(init=False)
    bbox_east: float = field(init=False)
    bbox_north: float = field(init=False)
    polygon: Polygon = field(init=False)

    def __str__(self):
        return self.display_name

    def __post_init__(self):
        gdf = ox.geocode_to_gdf(self.name)
        if gdf.empty:
            raise ValueError(f"Place data not returned for {self.name}")
        self.display_name = gdf.loc[0,'display_name']
        self.osm_id = gdf.loc[0,'osm_id']
        self.bbox_west = gdf.loc[0,'bbox_west']
        self.bbox_south = gdf.loc[0,'bbox_south']
        self.bbox_east = gdf.loc[0,'bbox_east']
        self.bbox_north = gdf.loc[0,'bbox_north']
        self.polygon = gdf.loc[0,'geometry']

class PlacePoints:
    """
    Generates points within a given Place.
    1) Paritions a city into grid points
    2) Splits bounding box into granulariy x granularity points
    3) Rejects points that are not within the city
    """
    def __init__(self, place: Place, map_granularity: int, api_key: str = None):
        # Get a GeoDataFrame of the boundary polygon
        self.place: Place = place
        self.grid_points: list[Point] = self._generate_grid_points(map_granularity)
        if not self.grid_points:
            raise ValueError(f"No points found in: {self.place}")
        if api_key is not None:
            self.snapped_points: list[Point] = self._snap_grid_points_to_road(api_key)
        else:
            self.snapped_points = None

    def __len__(self):
        return len(self.grid_points)

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
            if snapped_point is None:
                continue
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
        return Point(snapped_lat, snapped_lon)

def main():
    place_name = "Philadelphia, Pennsylvania, USA"
    granularity = 4
    place = Place(place_name)
    place_points = PlacePoints(place, granularity)
    print(place_points.grid_points)
    print(place_points.snapped_points)

if __name__ == "__main__":
    main()
