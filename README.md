# Australian Climate Forecast Dashboard (Flask + SARIMAX + Folium)

Flask web dashboard that generates on-demand weekly SARIMAX forecasts for Australian locations and renders a temporal Folium map for the selected location.

## What’s in this repo
- `app.py` — Flask app, weekly resampling, SARIMAX forecasting, and MAE/RMSE validation
- `index.html` — UI page (must be placed under `templates/` for Flask)
- `cleaned_climate_data.csv` — prepared dataset used by the app
- `location_coordinates.csv` — latitude/longitude lookup per location
- `locations.py` — helper script (geocoding list of locations)
- `static/css/styles.css` — styling
- `static/images/image.png` — image asset

## What the app does (based on the code)
- Location selection (from the dataset’s available locations)
- Weekly resampling + interpolation of climate series
- SARIMAX forecasting for:
  - `MinTemp` (forecast horizon: 26 weeks)
  - `MaxTemp` (forecast horizon: 26 weeks)
- Validation (only when history is sufficient):
  - MAE/RMSE computed on MinTemp when there are at least 104 weekly observations
- Outputs:
  - Forecast plot saved to `static/<Location>_forecast.png`
  - JSON response including avg forecast values and validation metrics (when available)
  - Temporal Folium map endpoint for the chosen location

## Run locally
### 1) Install dependencies
Run:
- `pip install flask pandas numpy statsmodels scikit-learn matplotlib folium geopy`

### 2) Fix the Flask template location (required)
Flask expects templates under `templates/`.

Mac/Linux:
- `mkdir -p templates`
- `mv index.html templates/index.html`

Windows PowerShell:
- `New-Item -ItemType Directory -Force templates`
- `Move-Item index.html templates/index.html`

### 3) Start the app
- `python app.py`

Then open:
- `http://127.0.0.1:5000/`

## Main endpoints (useful for reviewers)
- `/` — main UI
- `/forecast` — returns forecast stats + image path for a location
- `/temporal_map` — renders a timestamped Folium map for the selected location

## Feedback I want
Open a GitHub Issue titled: **Review: climate-policy-forecasting-dashboard** and tell me:
1) If the run steps are clear and reproducible on first try  
2) Whether the endpoints and response fields are well named  
3) What you would change to make the UX feel “dashboard-ready”
