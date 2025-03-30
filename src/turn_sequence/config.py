"""Handles the config settings from config.yml."""

from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class PathConfig:
    oatuth_credentials: Path

@dataclass
class SheetConfig:
    name: str
    city_worksheet: str
    point_worksheet: str
    directions_worksheet: str
    city_columns: list[str]
    point_columns: list[str]
    directions_columns: list[str]

@dataclass
class MapConfig:
    cities: list[str]
    granulariy: int
    num_points: int

@dataclass
class Config:
    paths: PathConfig
    sheets: SheetConfig
    map: MapConfig

def load_config(file_path: Path) -> Config:
    """Loads the configuration from the .yaml file."""
    with file_path.open('r') as f:
        data = yaml.safe_load(f)

    paths = PathConfig(oatuth_credentials=Path(data['paths']['oatuth_credentials']).expanduser())
    sheets = SheetConfig(**data['sheets'])
    map_config = MapConfig(**data['map'])

    return Config(sheets=sheets, map=map_config, paths=paths)

if __name__ == '__main__':
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)
    print(config)
