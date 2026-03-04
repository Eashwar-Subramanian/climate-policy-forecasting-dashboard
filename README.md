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
