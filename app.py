import folium
import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from pandas.tseries.offsets import DateOffset
from sklearn.metrics import mean_absolute_error, mean_squared_error
from folium import Map
from folium.plugins import TimestampedGeoJson
import warnings
import os
warnings.filterwarnings('ignore', category=UserWarning)

app = Flask(__name__)

# Load and prepare dataset
df = pd.read_csv("cleaned_climate_data.csv")
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Location'])
df = df.sort_values(['Location', 'Date'])

location_coords_df = pd.read_csv("location_coordinates.csv")
location_coords_df['Location'] = location_coords_df['Location'].str.title()
location_coords_dict = location_coords_df.set_index("Location")[["Latitude", "Longitude"]].T.to_dict()

df['Location'] = df['Location'].str.replace(r'\s+', ' ', regex=True).str.title()
location_coords_df['Location'] = location_coords_df['Location'].str.replace(r'\s+', ' ', regex=True).str.title()

# Precomputed forecasts dictionary (now on-demand)
precomputed_forecasts = {}

def process_data(location):
    loc_data = df[df['Location'] == location].copy()
    if loc_data.empty:
        return pd.DataFrame()
    loc_data.set_index('Date', inplace=True)
    loc_data = loc_data[['MinTemp', 'MaxTemp']].resample('W').mean().interpolate(method='linear')
    return loc_data

def sarima_forecast(location):
    if location in precomputed_forecasts:
        return precomputed_forecasts[location]

    ts_data = process_data(location)
    if ts_data.empty or len(ts_data) < 52:
        return pd.DataFrame(columns=['Date', 'MinTemp_Forecast', 'MaxTemp_Forecast'])

    mintemp_model = sm.tsa.statespace.SARIMAX(ts_data['MinTemp'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 52))
    maxtemp_model = sm.tsa.statespace.SARIMAX(ts_data['MaxTemp'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 52))
    try:
        mintemp_fit = mintemp_model.fit(maxiter=1000, disp=False)
        maxtemp_fit = maxtemp_model.fit(maxiter=1000, disp=False)
        future_dates = [ts_data.index[-1] + DateOffset(weeks=i) for i in range(1, 27)]
        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'MinTemp_Forecast': mintemp_fit.forecast(26),
            'MaxTemp_Forecast': maxtemp_fit.forecast(26)
        })
        precomputed_forecasts[location] = forecast_df
        # Generate and save plot
        if not os.path.exists('static'):
            os.makedirs('static')
        plt.figure(figsize=(10, 5))
        plt.plot(ts_data.index, ts_data['MaxTemp'], label='Historical Max Temp', color='blue')
        plt.plot(forecast_df['Date'], forecast_df['MaxTemp_Forecast'], label='Forecast Max Temp', color='orange')
        plt.title(f"{location} - 26 Week Max Temp Forecast")
        plt.xlabel("Date")
        plt.ylabel("Temperature (°C)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'static/{location}_forecast.png')
        plt.close()
    except Exception as e:
        print(f"Forecast failed for {location}: {e}")
        return pd.DataFrame(columns=['Date', 'MinTemp_Forecast', 'MaxTemp_Forecast'])
    return forecast_df

def validate_model(ts_data):
    if len(ts_data) < 104:
        return None, None
    train = ts_data[:-52]
    test = ts_data[-52:]
    model = sm.tsa.statespace.SARIMAX(train['MinTemp'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 52))
    try:
        fit = model.fit(maxiter=1000, disp=False)
        forecast = fit.forecast(52)
        mae = mean_absolute_error(test['MinTemp'], forecast)
        rmse = mean_squared_error(test['MinTemp'], forecast, squared=False)
        return round(mae, 2), round(rmse, 2)
    except Exception:
        return None, None

def suggest_policies(location, forecast_df, hist_data):
    policies = []
    mae, rmse = validate_model(hist_data)
    if mae is not None:
        policies.append(f"Validation: MAE = {mae}°C, RMSE = {rmse}°C")
    if forecast_df['MaxTemp_Forecast'].mean() > 35 and mae is not None and mae < 2.5:
        policies.append(f"Optional: Heatwave action plans for {location} (avg max {forecast_df['MaxTemp_Forecast'].mean():.2f}°C, MAE {mae}°C)")
    return policies

@app.route('/')
def home():
    locations = sorted(df['Location'].unique().tolist())
    return render_template("index.html", locations=locations)

@app.route('/sarima_forecast')
def get_forecast():
    location = request.args.get("location", "Albury").title()
    if location not in df['Location'].str.title().unique():
        return jsonify({"error": f"Location '{location}' not found. Try {', '.join(df['Location'].unique()[:5])}..."})
    ts_data = process_data(location)
    if ts_data.empty:
        return jsonify({"error": f"No data available for {location}."})
    forecast_df = sarima_forecast(location)
    if forecast_df.empty:
        return jsonify({"error": f"Forecast generation failed for {location}."})
    policies = suggest_policies(location, forecast_df, ts_data)
    return jsonify({
        "location": location,
        "avg_min_temp": round(forecast_df['MinTemp_Forecast'].mean(), 2),
        "avg_max_temp": round(forecast_df['MaxTemp_Forecast'].mean(), 2),
        "policies": policies,
        "graph": f"static/{location}_forecast.png"
    })

@app.route('/temporal_map')
def temporal_map():
    location = request.args.get("location", "Albury").title()
    if location not in df['Location'].str.title().unique():
        return "Location not found. Defaulting to Albury."
    forecast_df = sarima_forecast(location)  # Generate on-demand
    loc_coords = location_coords_dict.get(location, {'Latitude': -25.0, 'Longitude': 133.0})
    lat_lon = [loc_coords['Latitude'], loc_coords['Longitude']]
    m = Map(location=lat_lon, zoom_start=7, control_scale=True)
    if forecast_df.empty:
        folium.Marker(lat_lon, popup=f"No forecast data for {location}").add_to(m)
    else:
        geo_data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [loc_coords['Longitude'], loc_coords['Latitude']]},
                'properties': {
                    'time': row['Date'].strftime('%Y-%m-%dT00:00:00Z'),
                    'popup': f"{location} - Max Temp: {row['MaxTemp_Forecast']:.2f}°C"
                }
            } for _, row in forecast_df.iterrows()]
        }
        TimestampedGeoJson(geo_data, period='P1W', auto_play=False, loop=False).add_to(m)
    return m._repr_html_()

@app.route('/powerbi')
def powerbi_info():
    return render_template('powerbi.html')

if __name__ == "__main__":
    app.run(debug=True)