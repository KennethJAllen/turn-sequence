import os
from pathlib import Path
import pandas as pd
import pygsheets
from pygsheets.exceptions import SpreadsheetNotFound
from pygsheets import Spreadsheet, Worksheet
from turn_sequence.map_model import MapModel
from turn_sequence.config import load_project_config, ProjectConfig

def get_gsheet(config: ProjectConfig,
               email: str=None,
               publish: bool=True,
               reset: bool=False) -> Spreadsheet:
    """
    Creates Google Sheets spreadsheet for storing place, point, and direction data.
    inputs:
        config: Contains the names of the sheet and worksheet.
        email (optional): If you want to add your personal account as an editor
        publish (optional): Make the data public to anyone with the url.
        reset (optional): Male reset the spreadsheet
    """
    gc = pygsheets.authorize(service_file=config.path.oatuth_credentials)

    try:
        # Try to open an existing spreadsheet
        spreadsheet = gc.open(config.sheet.name)
        if reset:
            print("Resetting spreadsheet worksheets...")
            # Iterate over a copy of the worksheet list to delete them safely.
            for ws in spreadsheet.worksheets():
                spreadsheet.del_worksheet(ws)
            # Google Sheets requires at least one worksheet in the spreadsheet so clear the last one
            remaining_ws = spreadsheet.worksheets()[0]
            remaining_ws.clear()
            _init_sheet(spreadsheet, config)
        else:
            print("Opening spreadsheet...")

    except SpreadsheetNotFound:
        # Create the spreadsheet if it does not exist
        print("Creating spreadsheet with worksheets...")
        spreadsheet = gc.create(config.sheet.name)
        _init_sheet(spreadsheet, config)

    # Optionally share the spreadsheet to access from personal email
    if email is not None:
        print(f"Sharing spreadsheet to email: {email}")
        spreadsheet.share(email, role='writer', emailMessage="Here is the Turning Sequence data spreadsheet!")
    if publish:
        # Make spreadsheet public with read only access
        spreadsheet.share('', role='reader', type='anyone')

    print(f"Spreadsheet URL: {spreadsheet.url}")

    return spreadsheet

def _init_sheet(spreadsheet: Spreadsheet, config: ProjectConfig) -> None:
    """Initializes the spreadsheet with the proper worksheet names and headers."""
    if spreadsheet.worksheets():
        # Case when the spreradsheet is created form scratch
        place_ws = spreadsheet.worksheets()[0]
        place_ws.title = config.sheet.place_worksheet
    else:
        # Case when the spreadsheet is reset
        place_ws = spreadsheet.add_worksheet(config.sheet.place_worksheet)
    point_ws = spreadsheet.add_worksheet(config.sheet.point_worksheet)
    directions_ws = spreadsheet.add_worksheet(config.sheet.directions_worksheet)

    # Add headers
    place_ws.insert_rows(row=0, number=1, values=[list(config.place_columns)])
    point_ws.insert_rows(row=0, number=1, values=[list(config.point_columns)])
    directions_ws.insert_rows(row=0, number=1, values=[list(config.direction_columns)])

def add_map_model_to_gsheet(map_model: MapModel, spreadsheet: Spreadsheet, project_config: ProjectConfig) -> None:
    """
    Push all data from the Place, PlacePoints, and Directions dataframes
    from MapModel to Google Sheets.

    - Checks if a row with the same unique place id already exists. If it does, do not push that dataframe.
    """
    # First, add place to sheet
    place_worksheet = spreadsheet.worksheet('title', project_config.sheet.place_worksheet)
    place_id = map_model.place.id

    existing_place_ids = place_worksheet.get_col(1, include_tailing_empty=False)[1:]
    if place_id in existing_place_ids:
        print(f"Place {map_model.place.display_name} with id {place_id} already exists. Skipping insertion into place worksheet.")
    else:
        add_df_to_worksheet(map_model.place.df, place_worksheet)

    # Next, add points to sheet
    point_worksheet = spreadsheet.worksheet('title', project_config.sheet.point_worksheet)
    add_df_to_worksheet(map_model.points.df, point_worksheet)

    # Finally add directions to sheet
    directions_sheet = spreadsheet.worksheet('title', project_config.sheet.directions_worksheet)
    add_df_to_worksheet(map_model.directions.df, directions_sheet)

def add_df_to_worksheet(df: pd.DataFrame, worksheet: Worksheet) -> None:
    """
    Push dataframe to worksheet.
    Ensures there are enough rows in the spreadsheet, and appends the row if needed.
    """
    header = worksheet.get_row(1, include_tailing_empty=False)

    # Reorder the DataFrame columns to match the sheet header
    df = df[header]

    col_data = worksheet.get_col(1, include_tailing_empty=False)
    start_row = len(col_data) + 1

    # Add rows if needed to ensure the target row exists
    if start_row > worksheet.rows:
        worksheet.add_rows(start_row - worksheet.rows)

    worksheet.set_dataframe(df, (start_row, 1), copy_head=False)

def main():
    """Main access point to the script."""
    # load variables from .env
    from dotenv import load_dotenv
    load_dotenv()
    email = os.getenv("EMAIL")
    config_path = Path.cwd() / "config" / "project_config.yaml"
    config = load_project_config(config_path)

    spreadsheet = get_gsheet(config, email=email, publish=True, reset=False)

    name = "Philadelphia, Pennsylvania, USA"
    #name = "Boston, Massachusetts, USA"
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    model = MapModel(name, config, api_key=api_key)

    add_map_model_to_gsheet(model, spreadsheet, config)

if __name__ == "__main__":
    main()
