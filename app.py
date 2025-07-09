import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for Matplotlib

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pandas.tseries.offsets import DateOffset
import statsmodels.api as sm
import matplotlib.pyplot as plt
from folium import Map
from folium.plugins import TimestampedGeoJson

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('weatherAUS.csv')

# Function to process data for SARIMA forecast
def process_data(location):
    df_ts = df[df['Location'] == location].copy()
    df_ts['Date'] = pd.to_datetime(df_ts['Date'])
    df_ts.set_index('Date', inplace=True)
    df_ts = df_ts[['MinTemp', 'MaxTemp', 'Rainfall']]
    df_ts = df_ts.resample('W').mean()
    df_ts.interpolate(method='linear', inplace=True)
    return df_ts

precomputed_forecasts = {}

def sarima_forecast(location):
    if location in precomputed_forecasts:
        return precomputed_forecasts[location]
    
    location_data = process_data(location)
    mintemp_model = sm.tsa.statespace.SARIMAX(location_data['MinTemp'], order=(1, 0, 1), seasonal_order=(1, 1, 0, 52))
    maxtemp_model = sm.tsa.statespace.SARIMAX(location_data['MaxTemp'], order=(1, 0, 1), seasonal_order=(1, 1, 1, 52))
    rainfall_model = sm.tsa.statespace.SARIMAX(location_data['Rainfall'], order=(0, 0, 0), seasonal_order=(1, 1, 1, 52))
    mintemp_fit = mintemp_model.fit(disp=False)
    maxtemp_fit = maxtemp_model.fit(disp=False)
    rainfall_fit = rainfall_model.fit(disp=False)

    future_dates = [location_data.index[-1] + DateOffset(weeks=x) for x in range(1, 27)]
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'MinTemp_Forecast': mintemp_fit.forecast(steps=26),
        'MaxTemp_Forecast': maxtemp_fit.forecast(steps=26),
        'Rainfall_Forecast': rainfall_fit.forecast(steps=26)
    })

    precomputed_forecasts[location] = forecast_df
    return forecast_df






def validate_sarima(location_data):
    train_data = location_data[:-52]  # Last year for testing
    test_data = location_data[-52:]   # 52 weeks
    mintemp_model = sm.tsa.statespace.SARIMAX(train_data['MinTemp'], order=(1, 0, 1), seasonal_order=(1, 0, 0, 52))
    mintemp_fit = mintemp_model.fit(disp=False)
    forecast = mintemp_fit.forecast(steps=52)
    mae = mean_absolute_error(test_data['MinTemp'], forecast)
    return mae

# Update suggest_policies to use validation
def suggest_policies(location, forecast_data, historical_data=None):
    policies = []
    #if historical_data is not None:
     #   mae = validate_sarima(historical_data)
      #  policies.append(f"Model Validation: SARIMA MAE = {mae:.2f}°C for {location}.")
       # if mae > 2.0:
        #    policies.append(f"Note: MAE > 2.0°C suggests potential model refinement.")
    if forecast_data['MaxTemp_Forecast'].mean() > 30:
        policies.append(f"Recommend energy conservation in {location} due to avg max temp of {forecast_data['MaxTemp_Forecast'].mean():.2f}°C.")
    if forecast_data['Rainfall_Forecast'].sum() < 500:
        policies.append(f"Suggest water conservation in {location} due to total rainfall of {forecast_data['Rainfall_Forecast'].sum():.2f}mm.")
    return policies


@app.route('/temporal_map')
def temporal_map():
    m = Map(location=[-36.1, 141.0], zoom_start=4)  # Albury approx
    location = 'Albury'  # Default for now
    if location in precomputed_forecasts:
        forecast_df = precomputed_forecasts[location]
        data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [141.0, -36.1]},
                'properties': {
                    'time': forecast_df['Date'].iloc[0].strftime('%Y-%m-%dT00:00:00Z'),
                    'popup': f'{location} Forecast: Max Temp {forecast_df["MaxTemp_Forecast"].iloc[0]:.2f}°C'
                }
            }]
        }
        TimestampedGeoJson(data, period='P1D', add_last_point=True).add_to(m)
    return m._repr_html_()


@app.route('/sarima_forecast', methods=['GET'])
def get_sarima_forecast():
    location = request.args.get('location')

    if location not in df['Location'].unique():
        return jsonify({'error': 'Location not found'}), 404

    forecast_df = sarima_forecast(location)
    graph_path = f'static/forecast_{location}.png'  # Placeholder, update if plotting is re-added

    # Calculate average forecasted values
    avg_min_temp = round(forecast_df['MinTemp_Forecast'].mean(), 2)
    avg_max_temp = round(forecast_df['MaxTemp_Forecast'].mean(), 2)
    total_rainfall = round(forecast_df['Rainfall_Forecast'].sum(), 2)

    location_data = process_data(location)  # For historical data
    policies = suggest_policies(location, forecast_df, location_data)

    # Prepare forecast details
    forecast_details = []
    for i in range(len(forecast_df)):
        forecast_details.append({
            'Date': forecast_df['Date'].iloc[i].strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'MinTemp': round(forecast_df['MinTemp_Forecast'].iloc[i], 2),
            'MaxTemp': round(forecast_df['MaxTemp_Forecast'].iloc[i], 2),
            'Rainfall': round(forecast_df['Rainfall_Forecast'].iloc[i], 2)
        })

    # Return JSON data including forecast and graph path
    return jsonify({
        'avg_min_temp': avg_min_temp,
        'avg_max_temp': avg_max_temp,
        'total_rainfall': total_rainfall,
        'policies': policies,
        'forecast': forecast_details,
        'graph': graph_path  # Send the path to the generated graph
    })


# Home route
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)