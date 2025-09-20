from pymongo import MongoClient
from datetime import datetime, timedelta
import random

# --- MongoDB connection ---
client = MongoClient("mongodb+srv://ninoespe:ninoespe@cluster0.9gbawhm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client.weatherDB
col = db.weather_data

# --- Weather Stations Config ---
STATIONS = {
    'boston': {'name': 'Boston Weather Station', 'position': [7.870517, 126.376426]},
    'cateel': {'name': 'Cateel Weather Station', 'position': [ 7.763384, 126.410727]},
    'baganga': {'name': 'Baganga Weather Station', 'position': [7.580644, 126.567651]},
    'caraga': {'name': 'Caraga Weather Station', 'position': [7.328232, 126.565358]},
    'manay': {'name': 'Manay Weather Station', 'position': [7.210933, 126.539914]},
    'tarragona': {'name': 'Tarragona Weather Station', 'position': [7.0497525, 125.567651]},
    'mati': {'name': 'Mati Weather Station', 'position': [6.952166 , 126.216676]},
    'banaybanay': {'name': 'Banaybanay Weather Station', 'position': [6.9669, 126.010756]},
    'lupon': {'name': 'Lupon Weather Station', 'position': [ 6.897712, 126.145256]},
    'san_isidro': {'name': 'San Isidro Weather Station', 'position': [6.834534, 126.087172]},
    'governor_generoso': {'name': 'Governor Generoso Weather Station', 'position': [6.653526, 126.07201]}
}

# --- Clear all existing mock data ---
col.delete_many({})

# --- Generate 30 days of hourly mock data for each station ---
start_time = datetime.utcnow() - timedelta(days=30)
total_records = 0

for station_id, station_info in STATIONS.items():
    docs = []
    # Base temperature varies slightly by station
    base_temp = random.uniform(28, 30)
    
    for i in range(30*24):  # 30 days * 24 hours
        ts = start_time + timedelta(hours=i)
        hour = ts.hour
        
        # Temperature varies throughout the day
        if 6 <= hour < 12:  # Morning: rising temperature
            temp_offset = (hour - 6) * 0.5
        elif 12 <= hour < 15:  # Afternoon: peak temperature
            temp_offset = 3
        elif 15 <= hour < 18:  # Late afternoon: decreasing
            temp_offset = 2
        else:  # Night: cooler
            temp_offset = -1
        
        # Higher chance of rain in the afternoon
        rain_chance = 0.4 if 13 <= hour <= 16 else 0.2
        
        doc = {
            "timestamp": ts,
            "temperature": round(base_temp + temp_offset + random.uniform(-1, 1), 1),
            "humidity": round(75 + random.uniform(-15, 15), 1),
            "pressure": round(1010 + random.uniform(-5, 5), 1),
            "rainfall": round(random.uniform(0, 8), 2) if random.random() < rain_chance else 0.0,
            "wind_speed": round(random.uniform(0, 15), 1),
            "wind_direction": random.choice(["N","NE","E","SE","S","SW","W","NW"]),
            "station_meta": {
                "station_id": station_id,  # This matches the IDs in app.py
                "position": station_info['position'],
                "name": station_info['name']
            }
        }
        docs.append(doc)
    
    col.insert_many(docs)
    total_records += len(docs)
    print(f"✅ Inserted {len(docs)} records for {station_info['name']}")

print(f"\n🎉 Total records inserted: {total_records}")
