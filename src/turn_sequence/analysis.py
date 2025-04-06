"""Turn sequence analysis module."""
from pathlib import Path
import ast
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from turn_sequence.map_model import MapModel
from turn_sequence import utils
from turn_sequence.config import ProjectConfig, PointColumns, GoogleSheetConfig

def get_all_dfs_from_gsheets(sheet_config: GoogleSheetConfig) -> tuple[pd.DataFrame]:
    """Gets the places, points, and directions dataframes from Google Sheets."""
    places_df = utils.get_gsheet_df(sheet_config.id, sheet_config.gid.places)
    points_df = utils.get_gsheet_df(sheet_config.id, sheet_config.gid.points)
    directions_df = utils.get_gsheet_df(sheet_config.id, sheet_config.gid.directions)
    return places_df, points_df, directions_df

def alternating_turn_metric(double_turns: list[str]) -> float:
    """Returns fraction of turns that alternate either LEFT -> RIGHT or RIGHT -> LEFT."""
    num_alternating_turns = 0
    for double_turn in double_turns:
        if double_turn not in ["LL", "RR", "LR", "RL"]:
            raise ValueError(f"All double turns must be one of 'LL', 'RR', 'LR', or 'RL'. Instead got: {double_turn}")
        if double_turn == "RL" or double_turn == "LR":
            num_alternating_turns += 1
    return num_alternating_turns / len(double_turns)

def place_alternating_turn_metric(name: str, places_df: pd.DataFrame, directions_df: pd.DataFrame, config: ProjectConfig) -> float:
    """Returns fraction of turns that alternate either LEFT -> RIGHT or RIGHT -> LEFT for a given city."""
    place_mask = places_df[config.place_columns.name] == name
    place_id = places_df.loc[place_mask, config.place_columns.id].item()
    directions_mask = directions_df[config.direction_columns.place_id] == place_id
    double_turns_raw = directions_df.loc[directions_mask, config.direction_columns.direction_pairs]
    # convert from string to list
    double_turns_sequence = double_turns_raw.apply(ast.literal_eval)
    alternating_turns_sequence = []
    for double_turns in double_turns_sequence:
        if not double_turns:
            continue
        fraction_alternating_turns = alternating_turn_metric(double_turns)
        alternating_turns_sequence.append(fraction_alternating_turns)
    return sum(alternating_turns_sequence) / len(alternating_turns_sequence)

def plot_place_points_from_model(model: MapModel, point_columns: PointColumns, plot_path: Path) -> None:
    """Plots points on map."""
    plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # lat/lon map bounds
    bounds = [
        model.place.lon_min,
        model.place.lon_max,
        model.place.lat_min,
        model.place.lat_max
        ]
    ax.set_extent(bounds, crs=ccrs.PlateCarree())

    # plot the grid points
    ax.plot(model.points.df[point_columns.grid_lon], model.points.df[point_columns.grid_lat], 'r+', transform=ccrs.PlateCarree())

    # plot the snapped points
    ax.plot(model.points.df[point_columns.snapped_lon], model.points.df[point_columns.snapped_lat], 'go', transform=ccrs.PlateCarree())

    # plot the place polygon
    ax.add_geometries([model.place.polygon], crs=ccrs.PlateCarree(),
                  edgecolor='blue', facecolor='none', linewidth=2)

    plt.savefig(plot_path)
    plt.close()

def plot_place_points_from_df(name: str, points_df: pd.DataFrame, point_columns: PointColumns, plot_path: Path) -> None:
    """Plots points on map."""
    gdf = ox.geocode_to_gdf(name)

    plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # lat/lon map bounds
    lon_min = gdf.loc[0,'bbox_west']
    lon_max = gdf.loc[0,'bbox_east']
    lat_min = gdf.loc[0,'bbox_south']
    lat_max = gdf.loc[0,'bbox_north']
    
    bounds = [lon_min, lon_max, lat_min, lat_max]
    ax.set_extent(bounds, crs=ccrs.PlateCarree())

    # plot the grid points
    ax.plot(points_df[point_columns.grid_lon], points_df[point_columns.grid_lat], 'r+',
            label='Grid Points', transform=ccrs.PlateCarree())

    # plot the snapped points
    ax.plot(points_df[point_columns.snapped_lon], points_df[point_columns.snapped_lat], 'go',
            label='Snapped to Road Points', transform=ccrs.PlateCarree())

    # plot the place polygon
    polygon = gdf.loc[0,'geometry']
    ax.add_geometries([polygon], crs=ccrs.PlateCarree(), edgecolor='blue', facecolor='none', linewidth=2)

    plt.title(name)
    plt.legend()
    plt.savefig(plot_path, bbox_inches='tight', pad_inches=0.2)
    plt.close()

def main():
    from turn_sequence.config import load_project_config, load_sheet_config

    project_config_path = Path.cwd() / "config" / "project_config.yaml"
    project_config = load_project_config(project_config_path)
    sheet_config_path = Path.cwd() / "config" / "sheet_config.yaml"
    sheet_config = load_sheet_config(sheet_config_path)
    places_df, points_df, directions_df = get_all_dfs_from_gsheets(sheet_config)

    plot_dir = Path.cwd() / "plots"
    plot_dir.mkdir(exist_ok=True)

    for name in project_config.map_.places:
        plotname = name.lower().replace(', ', '_') + '.png'
        plot_path = plot_dir / plotname
        plot_place_points_from_df(name, points_df, project_config.point_columns, plot_path)
        fraction_alternating_turns = place_alternating_turn_metric(name, places_df, directions_df, project_config)
        print(f"{name} : {fraction_alternating_turns}")

if __name__ == "__main__":
    main()
