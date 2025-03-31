import os
from pathlib import Path
import pandas as pd
import pygsheets
from pygsheets.exceptions import SpreadsheetNotFound, WorksheetNotFound
from pygsheets import Spreadsheet
from turn_sequence.config import load_config, PlaceConfig

def get_gsheets(sheet_config: PlaceConfig,
                   credential_path: Path,
                   email: str=None,
                   publish: bool=True,
                   reset: bool=False) -> Spreadsheet:
    """
    Creates Google Sheets spreadsheet for storing city, point, and direction data.
    inputs:
        sheets: An instance of the Sheets parameter class that contains the names of the sheet and worksheet.
        credential_path: The path to the credentials.
        email (optional): If you want to add your personal account as an editor
        publish (optional): Make the data public to anyone with the url.
        reset (optional): Male reset the spreadsheet
    """
    gc = pygsheets.authorize(service_file=credential_path)

    try:
        # Try to open an existing spreadsheet
        spreadsheet = gc.open(sheet_config.name)
        if reset:
            print("Resetting spreadsheet...")
            gc.drive.delete(spreadsheet.id)
            raise SpreadsheetNotFound
        print("Opening spreadsheet...")

    except SpreadsheetNotFound:
        # Create the spreadsheet if it does not exist
        print("Creating spreadsheet with worksheets...")
        spreadsheet = gc.create(sheet_config.name)
        _init_sheet(spreadsheet, sheet_config)

    # Optionally share the spreadsheet to access from personal email
    if email is not None:
        print(f"Sharing spreadsheet to email: {email}")
        spreadsheet.share(email, role='writer', emailMessage="Here is the Turning Sequence data spreadsheet!")
    if publish:
        # Make spreadsheet public with read only access
        spreadsheet.share('', role='reader', type='anyone')

    print(f"Spreadsheet URL: {spreadsheet.url}")

    return spreadsheet

def _init_sheet(spreadsheet: Spreadsheet, sheet_config: PlaceConfig) -> None:
    """Initializes the spreadsheet with the proper worksheet names and headers."""
    # rename sheet1 & create the rest of the worksheets
    city_ws = spreadsheet.sheet1
    city_ws.title = sheet_config.city_worksheet
    point_ws = spreadsheet.add_worksheet(sheet_config.point_worksheet)
    directions_ws = spreadsheet.add_worksheet(sheet_config.directions_worksheet)

    # Add headers
    city_ws.insert_rows(row=0, number=1, values=[sheet_config.city_columns])
    point_ws.insert_rows(row=0, number=1, values=[sheet_config.point_columns])
    directions_ws.insert_rows(row=0, number=1, values=[sheet_config.directions_columns])

def add_to_gsheets(spreadsheet: Spreadsheet, sheet_config: PlaceConfig, df: pd.DataFrame) -> None:
    """Add data to spreadsheet"""
    worksheet = spreadsheet.worksheet('title', sheet_config.city_worksheet)
    sheet_header = worksheet.get_row(1, include_tailing_empty=False)

    # Reorder the DataFrame columns to match the sheet header
    df = df[sheet_header]

    col_data = worksheet.get_col(1, include_tailing_empty=False)
    start_row = len(col_data) + 1

    # Set the DataFrame to the sheet starting at cell A1
    #worksheet.append_table(values, start='A1', end=None, dimension='ROWS', overwrite=False)

def main():
    """Main access point to the script."""
    #TODO: move to tests
    # load variables from .env
    from dotenv import load_dotenv
    load_dotenv()
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    email = os.getenv("EMAIL")
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)

    #spreadsheet = get_gsheets(config.sheets, config.paths.oatuth_credentials, email=email, publish=True, reset=False)

if __name__ == "__main__":
    main()
