# Turn Sequence

## Summary

Analyze the frequency of taking alternating direction turns while driving vs. taking consecutive same-direction turns. Uses Google Geocode API and Routes API.

## Which Lane to Turn In?

If there are multiple lanes to take a turn, while lane should you choose?

The hypothesis is choosing the right-most lane when taking a left turn, or the left-most lane when taking a right turn is optimal on average. This is because when traveling, each turn is an overcorrection towards your destination. For a simple model, if we are traveling on a grid, then any optimal path will alternate between left and right turns. In practice, we still make multiple of the same direction turns in a row. But how often? This project aims to answer that question.

### Approach

To answer this question, paths are sampled between pairs of points in a city, count the number of left and right turns, and calculate the ratio of the number of left-then-right and right-then-left turns to the total number of turn pairs.

### How do you sample paths from a city?

- Use `osmnx` to generate a geometric polygon from the city
- Partition latitude and longitude into evenly spaced grid points equal to `map.granulariy` in `project_config.yaml`.
- Check if each grid point is in the city polygon. Toss it if it is not.
- Snap each grid point to the road with the Google Roads API.
    - If a point does not have a road nearby it is tossed. This is useful for city polygons like Boston's which have a large portion in the ocean.
- Loop over each pair of snapped points. If they are different, calculate the route betweenn them with the Google Routes API.
    - The number of calls to Google Routes is $O(\text{granularity}^4)$. Therefore the granularity should be chosen small, e.g. less than 10.
- Process the ouptut directions into a sequence of left and right turns.

## Analysis

### Results

Directions were calculated between every two pairs of distinct snapped points. For all directions, the alternating turn fraction was calculated:

$$
\frac{\text{num(LR)} + \text{num(RL)}}{\text{num(LL)} + \text{num(LR)} + \text{num(RL)} + \text{num(RR)}}.
$$

Where $LR$ is a left-the-right turn, $RL$ is a right-then-left turn, $LL$ is a left-then-left turn, and $RR$ is a right-then-right turn. The alternating turn fraction is averaged over all paths. For each city, the results are in the following table:

| Place                           | Average Alternating Turn Percentage | Number of Paths | Alternating Turn Percentage Standard Deviation |
|---------------------------------|-------------------------------------|-----------------|------------------------------------------------|
| New York City, New York, USA    | 54.4%                               | 1980            | 18.0                                           |
| Boston, Massachusetts, USA      | 54.9%                               | 870             | 19.3                                           |
| Philadelphia, Pennsylvania, USA | 53.9%                               | 2858            | 19.2                                           |
| San Francisco, California, USA  | 65.6%                               | 30              | 22.5                                           |
| Los Angeles, California, USA    | 53.3%                               | 1803            | 19.3                                           |
| Chicago, Illinois, USA          | 54.3%                               | 2069            | 18.3                                           |
| Miami, Florida, USA             | 54.6%                               | 1630            | 25.5                                           |
| London, UK                      | 43.3%                               | 4692            | 16.8                                           |
| Paris, France                   | 52.9%                               | 5683            | 20.5                                           |
| Amsterdam, Netherlands          | 50.6%                               | 2749            | 18.6                                           |
| Berlin, Germany                 | 60.7%                               | 2970            | 16.8                                           |
| Rome, Italy                     | 46.0%                               | 1260            | 17.8                                           |
| Rio de Janeiro, Brazil          | 54.6%                               | 1332            | 14.4                                           |
| Mumbai, India                   | 56.5%                               | 2969            | 15.4                                           |
| Singapore                       | 51.0%                               | 156             | 15.3                                           |
| Total                           | 52.6%                               | 33981           | 19.1                                           |

Note that a percentage above 50% means you are more likely tu alternate turning directions compared to taking consecutive same-direction turns.

### Visualization

To ensure we only calculate routes between points on roads, and not bodies of water for example, each grid point is snapped to the road using the Google Roads API. Points that are snapped to a road are shown as green. Points that were not able to snap to a road are in red. More plots are availible in the `plots/` directory.

![Boston MA](plots/boston_massachusetts_usa.png)

### Results

#### Total

The total average percentage of alternating turns is 52.6% which exceeds 50%, suggesting a slight tilt toward alternating turns rather than consecutive same‐direction turns.

#### Variation By City

In all places except London, UK and Rome, Italy, the number of alternatting turns is higher than the number of consecutive same-direction turns. Some notable cities are

- San Francisco (65.6%) has the highest percentage but also the smallest number of paths (30), so that high figure may be less reliable.

- London (43.3%) is notably below 50% with a large sample size (4692).

- Berlin (60.7%) is substantially above 50% with a large sample size (2,970).

These differences could stem from factors such as the city layout (e.g. one-way roads) or the sampling method.

#### Large Standard Deviation

The standard deviation for each location is large, ranging from about 15 to 20 percent, meaning there is large variability in turning patterns between routes.

#### Conclusion

The proportion of alternating turns is slightly, but consistently, above 50%, with variability between cities. Meaning when taking a left turn, your next turn is most likely a right, and after taking a right turn, the next turn is most likely a left.

It would be nice to gather more data, but the cost of Google Routes API calls is prohibitive, as it cost $264 of $300 of free Google Cloud credits to generate this data.

## Data

Data is pulled from Google Roads and Routes APIs, processed, and stored in Google Sheets.

Route data that I have processed and stored can be viewed on [Google Sheets](https://docs.google.com/spreadsheets/d/1-AbBNuG1uom7djGymecf2jKBZFztmmOv9t5yPM3L354/edit?gid=1705379481#gid=1705379481).

### Why Google Sheets?

While a SQL database would be more natural, Google Sheets has the convenient option of easily publically sharing the data as read only. 

## Using The Package

### Setup

- Ensure that the UV package manager is installed.
- Set up environment: `uv sync`
- Build project `uv build`
- To 

### Analysis

The analysis can be re-created with the `analysis.py` script in the `turn_sequence` directory. An API key is not required to run it as the data is [Google Sheets](https://docs.google.com/spreadsheets/d/1-AbBNuG1uom7djGymecf2jKBZFztmmOv9t5yPM3L354/edit?gid=1705379481#gid=1705379481) is publically read-only.

### Re-create Google Sheets Database

To recreate the database, you need a [Google Cloud](https://console.cloud.google.com/) API key with access to the Google Sheets API, Google Drive API, Roads API, and Routes API.

After setting up, the Google Sheet can be re-created using the `data_pipeline.py` script.

#### API Key
1) Request a Maps Platform API Key.
2) Create a `.env` file in the root directory with `GOOGLE_MAPS_API_KEY=YOUR_ACTUAL_KEY`.
    - Optionally, if you would like to add write privileges to your email account for the Google Sheets database, add `EMAIL=YOUR_ACTUAL_EMAIL`.

#### OAuth Credentials
OAuth credentials are required to write to Google Sheets.
3) Create a service account and generate a JSON key file.
4) Download the JSON file with your OAuth credentials, and save to `~/.credentials/sheets_oauth.json`, or specified the path in `project_config.yaml`.

### Parameters

#### project_config.yaml
- `map.places`: A list of locations to sample points from. Geocoded with the `osmnx` package.
- `map.granularity`: The grid size granularity. Warning, this parameter should be kept small (12 or less) to avoid excessive calls to Google Routes.
- `place_columns`: The column names in the [Places Google Worksheet](https://docs.google.com/spreadsheets/d/1-AbBNuG1uom7djGymecf2jKBZFztmmOv9t5yPM3L354/edit?gid=1705379481#gid=1705379481) and dataframe.
- `point_columns`: The column names in the [Point Google Worksheet](https://docs.google.com/spreadsheets/d/1-AbBNuG1uom7djGymecf2jKBZFztmmOv9t5yPM3L354/edit?gid=1650120780#gid=1650120780) and dataframe.
- `direction_columns`: The column names in the [Directions Google Worksheet](https://docs.google.com/spreadsheets/d/1-AbBNuG1uom7djGymecf2jKBZFztmmOv9t5yPM3L354/edit?gid=1040326083#gid=1040326083) and dataframe.

#### sheet_config.yaml
Contains the Google Sheet id, and Google worksheet gids, needed for reading data from the read-only worksheet without an API key.
