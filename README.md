# Australian Climate Forecast Dashboard (Flask + SARIMAX + Folium)

A Flask web dashboard that generates on-demand SARIMAX forecasts for Australian locations and embeds a temporal Folium map.

---

## What it does
- Location dropdown search
- Weekly resampling + interpolation of climate series
- SARIMAX forecasting for MinTemp and MaxTemp
- Forecast horizon: **26 weeks**
- Validation: MAE/RMSE computed on MinTemp when there is at least **104 weeks** of history

---

## How to run
```bash
pip install -r requirements.txt
python app.py
```
Open: http://127.0.0.1:5000

Files

app.py — Flask app + SARIMAX forecasting + MAE/RMSE validation

index.html — UI (location dropdown + forecast results + embedded map)

cleaned_climate_data.csv — prepared dataset used by the app

location_coordinates.csv — latitude/longitude lookups

static/ — CSS and assets

Review request

Open an Issue titled: Review: climate-policy-forecasting-dashboard
Feedback wanted: code structure, endpoint clarity, and dashboard UX clarity.

