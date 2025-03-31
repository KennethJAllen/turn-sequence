"""Turn sequence analysis module."""
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from turn_sequence.map_model import MapModel
from turn_sequence.config import PointColumns

def alternating_metric(double_turns: list[str]) -> float:
    """Returns fraction of turns that alternate either LEFT -> RIGHT or RIGHT -> LEFT."""
    num_alternating_turns = 0
    for double_turn in double_turns:
        if double_turn not in ["LL", "RR", "LR", "RL"]:
            raise ValueError(f"All double turns must be one of 'LL', 'RR', 'LR', or 'RL'. Instead got: {double_turn}")
        if double_turn == "RL" or double_turn == "RL":
            num_alternating_turns += 1
    return num_alternating_turns / len(double_turns)

def plot_place_points(model: MapModel, point_columns: PointColumns, plot_path: Path) -> None:
    """Plots points on map."""
    fig = plt.figure(figsize=(8, 6))
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

def main():
    # TODO: move this to tests
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

    plot_dir = Path.cwd() / "plots"
    plot_dir.mkdir(exist_ok=True)
    filename = name.lower().replace(', ', '_') + '.png'
    plot_path = plot_dir / filename

    plot_place_points(model, config.point_columns, plot_path)

if __name__ == "__main__":
    main()
