from flask import Flask, request, jsonify, render_template, jsonify, send_from_directory
from pymongo import MongoClient
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import matplotlib
import os
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io, base64
from datetime import datetime

app = Flask(__name__, static_url_path='')

@app.route('/amcharts_weather_icons_1.0.0/<path:path>')
def send_weather_icons(path):
    return send_from_directory('amcharts_weather_icons_1.0.0', path)

def get_weather_icon(condition):
    """Map weather conditions to Weather Icons classes"""
    icon_map = {
        'clear': 'wi-day-sunny',
        'sunny': 'wi-day-sunny',
        'partly cloudy': 'wi-day-cloudy',
        'cloudy': 'wi-cloudy',
        'overcast': 'wi-cloudy',
        'rain': 'wi-rain',
        'light rain': 'wi-sprinkle',
        'heavy rain': 'wi-rain-mix',
        'thunderstorm': 'wi-thunderstorm',
        'snow': 'wi-snow',
        'fog': 'wi-fog',
        'mist': 'wi-fog',
        'windy': 'wi-strong-wind'
    }
    condition = condition.lower() if condition else 'clear'
    return icon_map.get(condition, 'wi-day-sunny')

# Function to get weather stations from database
def get_weather_stations():
    stations = {}
    pipeline = [
        {"$group": {
            "_id": "$station_meta.station_id",
            "name": {"$first": "$station_meta.name"},
            "position": {"$first": "$station_meta.position"}
        }}
    ]
    
    for station in collection.aggregate(pipeline):
        station_id = station['_id'].lower()
        stations[station_id] = {
            'name': station['name'],
            'position': station['position']
        }
    return stations

# MongoDB connection with proper timeout and retry settings
MONGODB_URI = os.environ.get('MONGODB_URI', 
    "mongodb+srv://ninoespe:ninoespe@cluster0.9gbawhm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Configure MongoDB client with proper settings
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=120000,  # Increase timeout to 30 seconds
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    maxPoolSize=50,
    retryWrites=True,
    retryReads=True,
    ssl=True,
    tlsAllowInvalidCertificates=True  # Only if needed for development
)

try:
    # Verify the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise

db = client["weatherDB"]
collection = db["weather_data"]

@app.route("/hourly-stats")
def hourly_stats():
    selected_station = request.args.get('station', 'mati')
    
    # Get the current datetimez
    current_time = datetime.now()
    
    # Query for the last 24 hours of data
    query = {
        "station_meta.station_id": {"$regex": f"^{selected_station}$", "$options": "i"},
        "timestamp": {
            "$gte": current_time - pd.Timedelta(hours=24),
            "$lte": current_time
        }
    }
    
    hourly_data = list(collection.find(
        query,
        {"_id": 0, "timestamp": 1, "temperature": 1, "humidity": 1, "wind_speed": 1}
    ).sort("timestamp", 1))
    
    return jsonify(hourly_data)

@app.route("/daily-stats")
def daily_stats():
    selected_station = request.args.get('station', 'mati')
    
    # Case-insensitive query
    query = {"station_meta.station_id": {"$regex": f"^{selected_station}$", "$options": "i"}}
    data = list(collection.find(
        query,
        {"_id":0, "timestamp":1, "temperature":1}
    ))
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate daily averages
    daily_avg = df.groupby(df['timestamp'].dt.date)['temperature'].mean().reset_index()
    
    # Prepare data for ARIMA forecast
    model = ARIMA(daily_avg['temperature'], order=(5,1,0))
    model_fit = model.fit()
    
    # Generate 7-day forecast
    forecast = model_fit.forecast(steps=7)
    forecast_dates = pd.date_range(start=daily_avg['timestamp'].max(), periods=8)[1:]
    
    # Prepare response with both historical and forecast data
    historical_data = [{"timestamp": d.strftime("%Y-%m-%d"), "temperature": t, "type": "historical"} 
                      for d, t in zip(daily_avg['timestamp'], daily_avg['temperature'])]
    
    forecast_data = [{"timestamp": d.strftime("%Y-%m-%d"), "temperature": t, "type": "forecast"} 
                    for d, t in zip(forecast_dates, forecast)]
    
    return jsonify(historical_data + forecast_data)

@app.route("/debug")
def debug():
    # Get all distinct station IDs
    stations = collection.distinct("station_meta.station_id")
    
    # Get a sample record for each station
    sample_data = {}
    for station in stations:
        sample = collection.find_one({"station_meta.station_id": station})
        if sample:
            sample_data[station] = {
                "name": sample.get("station_meta", {}).get("name", "Unknown"),
                "sample_timestamp": sample.get("timestamp"),
                "sample_temperature": sample.get("temperature")
            }
    
    return f"""
        <h2>Available Stations:</h2>
        <pre>{str(stations)}</pre>
        <h2>Sample Data:</h2>
        <pre>{str(sample_data)}</pre>
    """

@app.route("/")
def dashboard():
    # Get weather stations from database
    weather_stations = get_weather_stations()
    
    # Get selected station or default to first available station
    selected_station = request.args.get('station', 'mati')
    if selected_station not in weather_stations and weather_stations:
        selected_station = list(weather_stations.keys())[0]
    
    # ---- Get Data from MongoDB ----
    print(f"Querying for station: {selected_station}")
    
    # First, let's check what data exists in the collection
    all_stations = list(weather_stations.keys())
    print(f"Available stations in DB: {all_stations}")
    
    # Check total number of documents in collection
    total_docs = collection.count_documents({})
    print(f"Total documents in collection: {total_docs}")
    
    # Get a sample document to verify structure
    sample = collection.find_one({})
    print(f"Sample document structure: {sample}")
    
    # Case-insensitive query
    query = {"station_meta.station_id": {"$regex": f"^{selected_station}$", "$options": "i"}}
    print(f"Using query: {query}")
    
    data = list(collection.find(
        query,
        {"_id":0, "timestamp":1, "temperature":1}
    ))
    print(f"Found {len(data)} records for station {selected_station}")
    
    # Additional debugging
    if len(data) == 0:
        sample_doc = collection.find_one({})
        if sample_doc:
            print("Sample document from DB:", sample_doc)
    
    df = pd.DataFrame(data)

    if df.empty:
        error_msg = f'No data available for station: {selected_station}. Available stations: {all_stations}'
        return render_template('error.html', message=error_msg)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # ---- Daily Stats ----
    daily_avg = df['temperature'].resample('D').mean()

    # ---- Forecast ----
    model = ARIMA(daily_avg, order=(5,1,0))
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=7)

    # Get weather conditions and map to icon
    weather_condition = "clear"  # You should get this from your data
    weather_icon = get_weather_icon(weather_condition)

    # Get weather conditions for each time slot
    weather_conditions = {
        '6:00 AM': 'cloudy',
        '9:00 AM': 'partly cloudy',
        '12:00 PM': 'clear',
        '3:00 PM': 'clear',
        '6:00 PM': 'clear',
        '9:00 PM': 'clear'
    }
    
    # Map conditions to icons
    weather_icons = {time: get_weather_icon(condition) 
                    for time, condition in weather_conditions.items()}
    
    return render_template('dashboard.html',
                         stations=weather_stations,
                         selected_station=selected_station,
                         weather_icons=weather_icons,
                         current_weather_icon=get_weather_icon('clear'),
                         current_time=datetime.now().strftime('%B %d, %Y %H:%M'))

if __name__ == "__main__":
    # Use production server when deployed, development server locally
    if os.environ.get('RENDER'):
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    else:
        app.run(debug=True, port=8000)
