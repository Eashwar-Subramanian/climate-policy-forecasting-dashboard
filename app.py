# app.py
import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from pandas.tseries.offsets import DateOffset
from sklearn.metrics import mean_absolute_error
from folium import Map
from folium.plugins import TimestampedGeoJson
import warnings
warnings.filterwarnings('ignore', category=UserWarning)  # Suppress non-invertible warnings temporarily

app = Flask(__name__)

# Load and prepare dataset
df = pd.read_csv("cleaned_climate_data.csv")
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Location'])  # Ensure no null Locations
df = df.sort_values(['Location', 'Date'])

# Precomputed forecasts dictionary
precomputed_forecasts = {}

def process_data(location):
    loc_data = df[df['Location'] == location].copy()
    if loc_data.empty:
        return pd.DataFrame()  # Return empty if no data
    loc_data.set_index('Date', inplace=True)
    loc_data = loc_data[['MinTemp', 'MaxTemp', 'Rainfall']].resample('W').mean().interpolate(method='linear')
    return loc_data

def sarima_forecast(location):
    if location in precomputed_forecasts:
        return precomputed_forecasts[location]
    
    ts_data = process_data(location)
    if ts_data.empty or len(ts_data) < 52:  # Need at least 1 year of data
        return pd.DataFrame(columns=['Date', 'MinTemp_Forecast', 'MaxTemp_Forecast', 'Rainfall_Forecast'])
    
    # Adjusted SARIMA orders to address convergence issues
    mintemp_model = sm.tsa.statespace.SARIMAX(ts_data['MinTemp'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 52))
    maxtemp_model = sm.tsa.statespace.SARIMAX(ts_data['MaxTemp'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 52))
    rainfall_model = sm.tsa.statespace.SARIMAX(ts_data['Rainfall'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 52))
    
    try:
        mintemp_fit = mintemp_model.fit(maxiter=1000, disp=False)  # Increase iterations for convergence
        maxtemp_fit = maxtemp_model.fit(maxiter=1000, disp=False)
        rainfall_fit = rainfall_model.fit(maxiter=1000, disp=False)
    except Exception as e:
        print(f"Convergence failed for {location}: {e}")
        return pd.DataFrame(columns=['Date', 'MinTemp_Forecast', 'MaxTemp_Forecast', 'Rainfall_Forecast'])

    future_dates = [ts_data.index[-1] + DateOffset(weeks=i) for i in range(1, 27)]
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'MinTemp_Forecast': mintemp_fit.forecast(26),
        'MaxTemp_Forecast': maxtemp_fit.forecast(26),
        'Rainfall_Forecast': rainfall_fit.forecast(26)
    })
    precomputed_forecasts[location] = forecast_df
    return forecast_df



from sklearn.metrics import mean_absolute_error, mean_squared_error

def validate_model(ts_data):
    if len(ts_data) < 104:  # 2 years
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
        policies.append(f"Optional: Heatwave action plans for {location} (avg max {forecast_df['MaxTemp_Forecast'].mean():.2f}°C, MAE {mae}°C).")
    if forecast_df['Rainfall_Forecast'].sum() < 100 and mae is not None and mae < 2.5:
        policies.append(f"Optional: Water conservation for {location} (total rainfall {forecast_df['Rainfall_Forecast'].sum():.2f}mm, MAE {mae}°C).")
    return policies

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/sarima_forecast')
def get_forecast():
    location = request.args.get("location", "Albury").title()  # Default to Albury, capitalize for consistency
    if location not in df['Location'].str.title().unique():
        return jsonify({"error": f"Location '{location}' not found. Try Albury, Melbourne, etc."})
    
    ts_data = process_data(location)
    if ts_data.empty:
        return jsonify({"error": f"No data available for {location}."})
    
    forecast_df = sarima_forecast(location)
    policies = suggest_policies(location, forecast_df, ts_data)

    # Plot forecast
    plt.figure(figsize=(10, 5))
    plt.plot(ts_data.index, ts_data['MaxTemp'], label='Historical Max Temp', color='blue')
    plt.plot(forecast_df['Date'], forecast_df['MaxTemp_Forecast'], label='Forecast Max Temp', color='orange')
    plt.title(f"{location} - 26 Week Max Temp Forecast")
    plt.xlabel("Date")
    plt.ylabel("Temperature (°C)")
    plt.legend()
    plot_path = f"static/{location}_forecast.png"
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    
    forecast_summary = [{
        "Date": row['Date'].strftime('%d %b %Y'),
        "MinTemp": round(row['MinTemp_Forecast'], 2),
        "MaxTemp": round(row['MaxTemp_Forecast'], 2),
        "Rainfall": round(row['Rainfall_Forecast'], 2)
    } for _, row in forecast_df.iterrows()]

    return jsonify({
        "location": location,
        "avg_min_temp": round(forecast_df['MinTemp_Forecast'].mean(), 2),
        "avg_max_temp": round(forecast_df['MaxTemp_Forecast'].mean(), 2),
        "total_rainfall": round(forecast_df['Rainfall_Forecast'].sum(), 2),
        "policies": policies,
        "forecast": forecast_summary,
        "graph": plot_path
    })

@app.route('/temporal_map')
def temporal_map():
    location = request.args.get("location", "Albury").title()
    if location not in df['Location'].str.title().unique():
        return "Location not found. Defaulting to Albury."
    forecast_df = precomputed_forecasts.get(location, sarima_forecast(location))
    
    # Get approximate coordinates (simplified, replace with actual geo data if available)
    loc_coords = {'Melbourne': [-37.8136, 144.9631], 'Albury': [-36.1, 141.0]}.get(location, [-25.0, 133.0])
    m = Map(location=loc_coords, zoom_start=7, control_scale=True)

    geo_data = {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [loc_coords[1], loc_coords[0]]},
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