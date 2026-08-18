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
# 2. FLEXIBLE 1-WEEK (7-DAY) SUMMER 2027 WINDOWS
# ---------------------------------------------------------
api_key = os.getenv("SERPAPI_KEY")
today_str = date.today().isoformat()

# Sample 7-day trip windows across July & August 2027
sample_windows = [
    {"outbound": "2027-07-03", "return": "2027-07-10"},
    {"outbound": "2027-07-17", "return": "2027-07-24"},
    {"outbound": "2027-08-07", "return": "2027-08-14"},
]

if os.path.exists("airports.json"):
    with open("airports.json", "r", encoding="utf-8") as f:
        airports = json.load(f)
else:
    print("Warning: airports.json not found!")
    airports = []

for item in airports:
    base_city = item.get("city")
    code = item.get("code")
    airport_name = item.get("airport_name", code)

    display_label = (
        f"{base_city} ({code})" if base_city == "Paris" else base_city
    )

    if not api_key:
        print("SERPAPI_KEY environment variable not set. Skipping API calls.")
        break

    lowest_found_price = None

    # Test each 1-week window to find the lowest price for this city
    for window in sample_windows:
        try:
            params = {
                "engine": "google_flights",
                "departure_id": "YYZ",
                "arrival_id": code,
                "outbound_date": window["outbound"],
                "return_date": window["return"],
                "type": "2",  # Round-Trip
                "currency": "CAD",
                "hl": "en",
                "api_key": api_key,
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            flights = results.get("best_flights", []) + results.get(
                "other_flights", []
            )

            if flights and "price" in flights[0]:
                price = flights[0]["price"]
                if lowest_found_price is None or price < lowest_found_price:
                    lowest_found_price = price

        except Exception as e:
            print(
                f"Error checking window {window['outbound']} for {display_label}: {e}"
            )

    # Save the lowest 1-week price found to the database
    if lowest_found_price is not None:
        cursor.execute(
            """
            INSERT INTO flight_data (city, airport_name, code, price, date_searched)
            VALUES (?, ?, ?, ?, ?)
        """,
            (display_label, airport_name, code, lowest_found_price, today_str),
        )
        print(
            f"Saved Best 1-Week Fare: {display_label} - ${lowest_found_price} CAD"
        )
    else:
        print(f"No summer prices found yet for {display_label}")

conn.commit()

# ---------------------------------------------------------
# 3. EXPORT DATABASE TO data.json FOR INDEX.HTML
# ---------------------------------------------------------
cursor.execute("SELECT city, price, date_searched FROM flight_data")
rows = cursor.fetchall()

json_data = [
    {"city": row[0], "price": row[1], "date": row[2]} for row in rows
]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2)

print(f"Exported {len(json_data)} total records to data.json")
conn.close()
