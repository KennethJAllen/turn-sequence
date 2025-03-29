# driving-turn-sequence-analysis
When there are multiple lanes to take a turn, while lane should you choose?

Uses Google Geocode API and Routes API to analyze the frequency of left-right and right-left turns vs. left-left and right-right turns.

## Installation

- Ensure that the UV package manager is installed.
- Set up environment: `uv sync`
- Build project `uv build`

## Re-create Google Sheets Database

### API Key
To recreate the database, you need a [Google Cloud](https://console.cloud.google.com/) API key with access to the Google Sheets API, Roads API, and Routes API.
1) Request a Maps Platform API Key
2) Create a `.env` file in the root directory with `GOOGLE_MAPS_API_KEY=YOUR_ACTUAL_KEY`

### OAuth Credentials
OAuth credentials are required to write to Google Sheets.
3) Create Oath credentials in the Google Cloud Console.
4) Download the JSON file with your OAuth credentials, and save to `~/.credentials/sheets_oauth.json`
