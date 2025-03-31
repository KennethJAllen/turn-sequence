"""Handles the config settings from config.yml."""
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class PathConfig:
    oatuth_credentials: Path

@dataclass
class SheetsConfig:
    name: str
    city_worksheet: str
    point_worksheet: str
    directions_worksheet: str

@dataclass
class MapConfig:
    cities: list[str]
    granulariy: int

@dataclass
class PlaceColumns:
    id: str
    name: str
    display_name: str
    lat_min: str
    lat_max: str
    lon_min: str
    lon_max: str
    polygon: str

    def __iter__(self):
        yield from (
            self.id,
            self.name,
            self.display_name,
            self.lat_min,
            self.lat_max,
            self.lon_min,
            self.lon_max,
            self.polygon
        )

@dataclass
class PointColumns:
    id: str
    place_id: str
    grid_lat: str
    grid_lon: str
    snapped_lat: str
    snapped_lon: str

    def __iter__(self):
        yield from (
            self.id,
            self.place_id,
            self.grid_lat,
            self.grid_lon,
            self.snapped_lat,
            self.snapped_lon
        )

@dataclass
class DirectionColumns:
    id: str
    origin_id: str
    destination_id: str
    raw_directions: str
    lr_directions: str
    double_directions: str

    def __iter__(self):
        yield from (
            self.id,
            self.origin_id,
            self.destination_id,
            self.raw_directions,
            self.lr_directions,
            self.double_directions
        )

@dataclass
class Config:
    path: PathConfig
    sheets: SheetsConfig
    map_: MapConfig
    place_columns: PlaceColumns
    point_columns: PointColumns
    direction_columns: DirectionColumns

def load_config(file_path: Path) -> Config:
    """Loads the configuration from the .yaml file."""
    with file_path.open('r') as f:
        data = yaml.safe_load(f)

    path_config = PathConfig(oatuth_credentials=Path(data['paths']['oatuth_credentials']).expanduser())
    sheets_config = SheetsConfig(**data['sheets'])
    map_config = MapConfig(**data['map'])
    place_columns = PlaceColumns(**data['place_columns'])
    point_columns = PointColumns(**data['point_columns'])
    direction_columns = DirectionColumns(**data['direction_columns'])

    config = Config(
        sheets=sheets_config,
        map_=map_config,
        path=path_config,
        place_columns=place_columns,
        point_columns=point_columns,
        direction_columns=direction_columns
        )
    return config

def main():
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)
    print(config)

if __name__ == '__main__':
    main()
