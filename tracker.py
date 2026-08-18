import json
import sqlite3
from pathlib import Path

# Path to your existing json config
config_path = Path(__file__).parent / "airports.json"

with open(config_path, "r", encoding="utf-8") as f:
    airports = json.load(f)

for target in airports:
    code = target["code"]
    city = target["city"]
    airport_name = target["airport_name"]
    
    print(f"Fetching SerpAPI results for: {city} ({airport_name} - {code})...")
    
    # Pass 'code' into your existing SerpAPI search function:
    # flight_data = fetch_serpapi_flights(arrival_code=code)
    # save_to_db(flight_data, city=city, airport_name=airport_name)
