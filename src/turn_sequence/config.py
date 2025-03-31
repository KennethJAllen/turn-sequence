"""Handles the config settings from config.yml."""

from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class PathConfig:
    oatuth_credentials: Path

@dataclass
class PlaceConfig:
    name: str
    city_worksheet: str
    point_worksheet: str
    directions_worksheet: str

@dataclass
class MapConfig:
    cities: list[str]
    granulariy: int
    num_points: int

@dataclass
class PlaceColumns:
    id: str
    name: str
    display_name: str
    lat_min: str
    lon_min: str
    lat_max: str
    lon_max: str
    polygon: str

@dataclass
class PointColumns:
    osm_id: str
    grid_lat: str
    grid_lon: str
    snapped_lat: str
    snapped_lon: str

@dataclass
class DirectionColumns:
    osm_id: str
    origin_id: str
    desination_id: str
    raw_directions: str
    lr_directions: str
    double_directions: str

@dataclass
class Config:
    path: PathConfig
    place: PlaceConfig
    map_: MapConfig
    place_columns: PlaceColumns
    point_columns: PointColumns
    direction_columns: DirectionColumns

def load_config(file_path: Path) -> Config:
    """Loads the configuration from the .yaml file."""
    with file_path.open('r') as f:
        data = yaml.safe_load(f)

    path_config = PathConfig(oatuth_credentials=Path(data['paths']['oatuth_credentials']).expanduser())
    place_config = PlaceConfig(**data['sheets'])
    map_config = MapConfig(**data['map'])
    place_columns = PlaceColumns(**data['place_columns'])
    point_columns = PointColumns(**data['point_columns'])
    direction_columns = DirectionColumns(**data['direction_columns'])

    config = Config(
        place=place_config,
        map_=map_config,
        path=path_config,
        place_columns=place_columns,
        point_columns=point_columns,
        direction_columns=direction_columns
        )
    return config

if __name__ == '__main__':
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)
    print(config)
