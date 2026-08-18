import json
import os
import sqlite3
from datetime import date
from serpapi import GoogleSearch

# ---------------------------------------------------------
# 1. DATABASE SETUP
# ---------------------------------------------------------
conn = sqlite3.connect("flight_tracker.db")
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS flight_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        airport_name TEXT,
        code TEXT,
        price REAL,
        date_searched TEXT
    )
"""
)
conn.commit()

# ---------------------------------------------------------
# 2. LOAD AIRPORTS & SCRAPE FLIGHT PRICES
# ---------------------------------------------------------
api_key = os.getenv("SERPAPI_KEY")
today_str = date.today().isoformat()

# Load target destinations from airports.json
if os.path.exists("airports.json"):
    with open("airports.json", "r", encoding="utf-8") as f:
        airports = json.load(f)
else:
    print("Warning: airports.json not found! Skipping API fetch.")
    airports = []

for item in airports:
    city = item.get("city")
    code = item.get("code")
    airport_name = item.get("airport_name", code)

    if not api_key:
        print("SERPAPI_KEY environment variable not set. Skipping API calls.")
        break

    try:
        # Search Toronto (YYZ) to Target Airport
        params = {
            "engine": "google_flights",
            "departure_id": "YYZ",
            "arrival_id": code,
            "outbound_date": "2026-10-15",  # Adjust sample flight date as needed
            "currency": "CAD",
            "hl": "en",
            "api_key": api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        # Extract lowest price from best_flights or other_flights
        flights = results.get("best_flights", []) + results.get(
            "other_flights", []
        )

        if flights and "price" in flights[0]:
            lowest_price = flights[0]["price"]

            # Insert into database
            cursor.execute(
                """
                INSERT INTO flight_data (city, airport_name, code, price, date_searched)
                VALUES (?, ?, ?, ?, ?)
            """,
                (city, airport_name, code, lowest_price, today_str),
            )
            print(f"Saved: {city} ({code}) - ${lowest_price} CAD")
        else:
            print(f"No price found for {city} ({code})")

    except Exception as e:
        print(f"Error fetching data for {city} ({code}): {e}")

conn.commit()

# ---------------------------------------------------------
# 3. EXPORT DATABASE TO data.json FOR INDEX.HTML
# ---------------------------------------------------------
cursor.execute("SELECT city, price, date_searched FROM flight_data")
rows = cursor.fetchall()

# Format as a list of dicts for Chart.js
json_data = [
    {"city": row[0], "price": row[1], "date": row[2]} for row in rows
]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2)

print(f"Exported {len(json_data)} total records to data.json")

conn.close()
