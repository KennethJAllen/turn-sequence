"""Handles the config settings from config.yml."""

from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class Paths:
    oatuth_credentials: Path

@dataclass
class MapConfig:
    cities: list[str]
    granulariy: int
    num_points: int

@dataclass
class Config:
    paths: Paths
    map: MapConfig

def load_config(file_path: Path) -> Config:
    """Loads the configuration from the .yaml file."""
    with file_path.open('r') as f:
        data = yaml.safe_load(f)

    paths = Paths(oatuth_credentials=Path(data['paths']['oatuth_credentials']).expanduser())
    map_config = MapConfig(**data['map'])

    return Config(paths=paths, map=map_config)

if __name__ == '__main__':
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)
    print(config)
