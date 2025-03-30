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
    def __init__(self, city: str, map_granularity: int):
        # Get a GeoDataFrame of the boundary polygon
        gdf = ox.geocode_to_gdf(city)
        if not gdf:
            raise ValueError("Didn't get a city")
        self._name: str = gdf.display_name
        self.osm_id = gdf['osm_id'][0]
        self.bbox_west = gdf.bbox_west
        self.bbox_south = gdf.bbox_south
        self.bbox_east = gdf.bbox_east
        self.bbox_north = gdf.bbox_north
        self._polygon: Polygon = gdf['geometry'][0]
        self._grid_points: list[Point] = self._grid_sample_polygon(map_granularity)

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

    def _grid_sample_polygon(self, num: int) -> list[Point]:
        """
        Partitions the city into evenly spaces
        Returns a list of points spaced dx, dy apart inside the polygon.
        """
        print("Partioning city into evenly spaced points...")
        minx, miny, maxx, maxy = self._polygon.bounds
        dx = (maxx - minx)/num
        dy = (maxy - miny)/num
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
