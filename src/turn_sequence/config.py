"""Handles the parameters and models from config files."""
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class PathConfig:
    oatuth_credentials: Path

@dataclass
class SheetNamesConfig:
    name: str
    place_worksheet: str
    point_worksheet: str
    directions_worksheet: str

@dataclass
class MapConfig:
    places: list[str]
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

    def __iter__(self):
        yield from (
            self.id,
            self.name,
            self.display_name,
            self.lat_min,
            self.lat_max,
            self.lon_min,
            self.lon_max,
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
    place_id: str
    raw_directions: str
    lr_directions: str
    direction_pairs: str

    def __iter__(self):
        yield from (
            self.id,
            self.origin_id,
            self.destination_id,
            self.place_id,
            self.raw_directions,
            self.lr_directions,
            self.direction_pairs
        )

@dataclass
class ProjectConfig:
    path: PathConfig
    sheet: SheetNamesConfig
    map_: MapConfig
    place_columns: PlaceColumns
    point_columns: PointColumns
    direction_columns: DirectionColumns

@dataclass
class GoogleIds:
    """Contains the gid for each worksheet for a specific Google sheet."""
    places: int
    points: int
    directions: int

    def __iter__(self):
        yield from (
            self.places,
            self.points,
            self.directions
        )

@dataclass
class GoogleSheetConfig:
    """Contains the sheet id and gids for a speecific Google sheet."""
    id: str
    gid: GoogleIds

def load_project_config(file_path: Path) -> ProjectConfig:
    """Loads the project configuration from the .yaml file."""
    with file_path.open('r') as f:
        data = yaml.safe_load(f)

    path_config = PathConfig(oatuth_credentials=Path(data['paths']['oatuth_credentials']).expanduser())
    sheet_config = SheetNamesConfig(**data['sheet'])
    map_config = MapConfig(**data['map'])
    place_columns = PlaceColumns(**data['place_columns'])
    point_columns = PointColumns(**data['point_columns'])
    direction_columns = DirectionColumns(**data['direction_columns'])

    config = ProjectConfig(
        sheet=sheet_config,
        map_=map_config,
        path=path_config,
        place_columns=place_columns,
        point_columns=point_columns,
        direction_columns=direction_columns
        )
    return config

def load_sheet_config(file_path: Path) -> GoogleSheetConfig:
    """Loads the Google sheets configuration .yaml file"""
    with file_path.open('r') as f:
        data = yaml.safe_load(f)
    gid = GoogleIds(**data['gid'])
    config = GoogleSheetConfig(id=data['id'], gid=gid)
    return config

def main():
    config_dir = Path.cwd() / "config"
    project_config_path = config_dir / "project_config.yaml"
    project_config = load_project_config(project_config_path)
    print(project_config)

    sheet_config_path = config_dir / "sheet_config.yaml"
    sheet_config = load_sheet_config(sheet_config_path)
    print(sheet_config)

if __name__ == '__main__':
    main()
