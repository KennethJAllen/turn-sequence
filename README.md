# Turn Sequence

## Summary

Uses Google Geocode API and Routes API to analyze the frequency of left-right and right-left turns vs. left-left and right-right turns.

# Hypothesis

While driving, if there are multiple lanes to take a turn, while lane should you choose?

The hypothesis is choosing the right-most lane when taking a left turn, or the left-most lane when taking a right turn is most otimal.

This is because when traveling, each turn is an overcorrection towards your destination.

For a simple model, if we are traveling on a grid, then any optimal path will alternate between left and right turns.

In practice, we still make multiple of the same direction turns in a row. But how often? This project aims to answer that question.

## Installation

- Ensure that the UV package manager is installed.
- Set up environment: `uv sync`
- Build project `uv build`

## Data

Data is pulled from Google Roads and Routes APIs, processed, and stored in Google Sheets.

[Route data that I have processed and stored can be viewed as read-only here.](https://docs.google.com/spreadsheets/d/1-AbBNuG1uom7djGymecf2jKBZFztmmOv9t5yPM3L354/edit?gid=1756577916#gid=1756577916).

### Why Google Sheets?

While a SQL database would be more natural, Google Sheets has the convenient option of easily publically sharing the data as read only. 

## Re-create Google Sheets Database

### API Key
To recreate the database, you need a [Google Cloud](https://console.cloud.google.com/) API key with access to the Google Sheets API, Google Drive API, Roads API, and Routes API.
1) Request a Maps Platform API Key.
2) Create a `.env` file in the root directory with `GOOGLE_MAPS_API_KEY=YOUR_ACTUAL_KEY`.
    - Optionally, if you would like to add write privileges to your email account for the Google Sheets database, add `EMAIL=YOUR_ACTUAL_EMAIL`.

### OAuth Credentials
OAuth credentials are required to write to Google Sheets.
3) Create a service account and generate a JSON key file.
4) Download the JSON file with your OAuth credentials, and save to `~/.credentials/sheets_oauth.json`, or specified the path in `project_config.yaml`.
