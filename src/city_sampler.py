"""
Contains CityPoints method which generates polygon
and evenly partitioned grid points for a city
"""
import random
import osmnx as ox
from shapely.geometry import Point, Polygon

class CityPoints:
    """
    Generates random points within a given city.
    1) Gets polygon and bounding box of city
    2) Splits bounding box into granulariy x granularity points
    3) Rejects points that are not within the city
    """
    def __init__(self, city_name: str, granularity: int):
        self._name: str = city_name
        self._polygon: Polygon = self._get_city_polygon()
        self._grid_points: list[Point] = self._grid_sample_polygon(granularity, granularity)

    def __str__(self):
        return self._name

    def __len__(self):
        return len(self._grid_points)

    def get_shuffled_grid_points(self) -> list[Point]:
        """
        Returns shuffled evenly spaces grid points for the city.
        The number of points is at most granulaity x granularity
        """
        if not self._grid_points:
            raise ValueError(f"No points found in city: {self._name}")
        random.shuffle(self._grid_points)
        return self._grid_points

    def _get_city_polygon(self) -> Polygon:
        """Generates the latlon coordinates that define a polygon for a given city."""
        # Get a GeoDataFrame of the boundary polygon
        print(f"Getting city polygon for: {self._name}")
        gdf = ox.geocode_to_gdf(self._name)
        city_polygon = gdf.iloc[0].geometry

        return city_polygon

    def _grid_sample_polygon(self, num_x: int, num_y: int) -> list[Point]:
        """
        Partitions the city into evenly spaces
        Returns a list of points spaced dx, dy apart inside the polygon.
        """
        print("Partioning city into evenly spaced points...")
        minx, miny, maxx, maxy = self._polygon.bounds
        dx = (maxx - minx)/num_x
        dy = (maxy - miny)/num_y
        points = []
        
        # Move through the bounding box in increments of dx, dy
        x = minx
        while x <= maxx:
            y = miny
            while y <= maxy:
                candidate = Point(x, y)
                if self._polygon.contains(candidate):
                    points.append(candidate)
                y += dy
            x += dx

        return points

def test():
    city_name = "Philadelphia, Pennsylvania, USA"
    granularity = 10
    city_points = CityPoints(city_name, granularity)
    print(city_points.get_shuffled_grid_points())
    print(city_points.get_shuffled_grid_points())

if __name__ == "__main__":
    test()
