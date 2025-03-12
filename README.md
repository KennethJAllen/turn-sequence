# driving-turn-sequence-analysis
When there are multiple lanes to take a turn, while lane should you choose?

Uses Google Geocode API and Routes API to analyze the frequency of left-right and right-left turns vs. left-left and right-right turns.

## Installation

- Ensure that the UV package manager is installed.
- Set up environment: `uv sync`

## Create Database
To recreate the database:
1) Request a Maps Platform API Key
2) Create a `.env` file with `GOOGLE_MAPS_API_KEY=YOUR_ACTUAL_KEY`