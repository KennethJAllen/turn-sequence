import os
from pathlib import Path
import pandas as pd
import pygsheets
from pygsheets.exceptions import SpreadsheetNotFound
from pygsheets import Spreadsheet
from turn_sequence.map_model import MapModel
from turn_sequence.config import load_project_config, SheetNamesConfig, ProjectConfig

def get_gsheets(config: ProjectConfig,
                email: str=None,
                publish: bool=True,
                reset: bool=False) -> Spreadsheet:
    """
    Creates Google Sheets spreadsheet for storing place, point, and direction data.
    inputs:
        sheets: An instance of the Sheets parameter class that contains the names of the sheet and worksheet.
        credential_path: The path to the credentials.
        email (optional): If you want to add your personal account as an editor
        publish (optional): Make the data public to anyone with the url.
        reset (optional): Male reset the spreadsheet
    """
    gc = pygsheets.authorize(service_file=config.path.oatuth_credentials)

    try:
        # Try to open an existing spreadsheet
        spreadsheet = gc.open(config.sheets.name)
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
        spreadsheet = gc.create(config.sheets.name)
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
        place_ws.title = config.sheets.place_worksheet
    else:
        # Case when the spreadsheet is reset
        place_ws = spreadsheet.add_worksheet(config.sheets.place_worksheet)
    point_ws = spreadsheet.add_worksheet(config.sheets.point_worksheet)
    directions_ws = spreadsheet.add_worksheet(config.sheets.directions_worksheet)

    # Add headers
    place_ws.insert_rows(row=0, number=1, values=[list(config.place_columns)])
    point_ws.insert_rows(row=0, number=1, values=[list(config.point_columns)])
    directions_ws.insert_rows(row=0, number=1, values=[list(config.direction_columns)])

def get_gsheets_df(sheet_id: str, gid: int) -> pd.DataFrame:
    """
    Reads worksheet correspongin to gid
    from google sheets and returns it as a dataframe.
    """
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&id={sheet_id}&gid={gid}'
    df = pd.read_csv(url)
    return df

def add_to_gsheets(map_model: MapModel, spreadsheet: Spreadsheet, sheet_names: SheetNamesConfig) -> None:
    """Data in map model to Google Sheets."""
    worksheet = spreadsheet.worksheet('title', sheet_names.place_worksheet)
    sheet_header = worksheet.get_row(1, include_tailing_empty=False)

    # Reorder the DataFrame columns to match the sheet header
    #df = df[sheet_header]

    col_data = worksheet.get_col(1, include_tailing_empty=False)
    start_row = len(col_data) + 1

    raise NotImplementedError()
    # TODO: Finish this
    # Set the DataFrame to the sheet starting at cell A1
    #worksheet.append_table(values, start='A1', end=None, dimension='ROWS', overwrite=False)

def main():
    """Main access point to the script."""
    # load variables from .env
    from dotenv import load_dotenv
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    email = os.getenv("EMAIL")
    config_path = Path.cwd() / "config" / "project_config.yaml"
    config = load_project_config(config_path)

    spreadsheet = get_gsheets(config, email=email, publish=True, reset=True)

if __name__ == "__main__":
    main()
