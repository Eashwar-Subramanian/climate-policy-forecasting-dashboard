🌍 Climate Analysis Dashboard

Overview

The Climate Analysis Dashboard is a comprehensive web-based application designed to assist governments and environmental stakeholders in analyzing historical climate patterns, forecasting future climate trends, and generating actionable policy recommendations. Using SARIMA (Seasonal AutoRegressive Integrated Moving Average) models, the dashboard forecasts key variables like temperature and rainfall and links those insights to real-world policy suggestions.

🔑 Key Features
📈 Climate Forecasting with SARIMA
Predicts minimum/maximum temperature and rainfall for selected locations using historical climate data.

🌐 Interactive Interface
Search by location and view forecasts through intuitive charts.

📊 Model Evaluation Metrics
Evaluated using MAE, RMSE, and MAPE to ensure the reliability of predictions.

🧪 Technologies Used
Technology	Purpose
Python	Core backend logic
Flask	Web framework to serve the dashboard
Pandas & NumPy	Data preprocessing and manipulation
Statsmodels	SARIMA model implementation
Matplotlib	Visualization of forecast data
Folium	Interactive map integration
HTML/CSS/JS & Bootstrap	Frontend structure and responsiveness

🚀 Installation & Setup
Prerequisites
Python 3.x

Pip (Python package manager)

Install Dependencies
pip install -r requirements.txt

💻 Usage
Search Climate Data
Enter a location (e.g., "Sydney", "Melbourne") in the search bar to retrieve historical weather data.

View Forecasts
Forecasts for temperature and rainfall are displayed in graphical form using SARIMA.

📈 Model Evaluation Metrics
Metric	Description
MAE	Measures average magnitude of prediction errors
RMSE	Penalizes larger errors more than MAE

These metrics validate the model’s accuracy and support confidence in the generated policy suggestions.

⚙️ How It Works
Data Preprocessing
Historical climate data is cleaned, resampled (weekly), and interpolated to fill gaps.

SARIMA Forecasting
Time-series models predict future trends based on historical seasonal patterns.

🤝 Contributing
Pull requests are welcome! If you have suggestions or want to fix a bug, feel free to:

Open an issue

Fork the repo and submit a PR

🙏 Acknowledgments
SARIMA model powered by Statsmodels

Climate datasets sourced from public repositories (e.g., BOM, NOAA)

