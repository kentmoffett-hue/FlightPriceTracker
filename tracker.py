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
# 2. VERIFY API KEY & SET SEARCH DATES
# ---------------------------------------------------------
api_key = os.getenv("SERPAPI_KEY")
today_str = date.today().isoformat()

if not api_key:
    print("❌ ERROR: SERPAPI_KEY environment variable is missing or empty!")
else:
    # Print masked key to verify it is being loaded into GitHub Actions
    print(f"🔑 SERPAPI_KEY loaded successfully (Starts with: {api_key[:4]}...)")

# Representative 1-week summer window (July 10 - July 17, 2027)
OUTBOUND_DATE = "2027-07-10"
RETURN_DATE = "2027-07-17"

if os.path.exists("airports.json"):
    with open("airports.json", "r", encoding="utf-8") as f:
        airports = json.load(f)
else:
    print("❌ WARNING: airports.json not found!")
    airports = []

for item in airports:
    base_city = item.get("city")
    code = item.get("code")
    airport_name = item.get("airport_name", code)

    display_label = (
        f"{base_city} ({code})" if base_city == "Paris" else base_city
    )

    if not api_key:
        break

    try:
        params = {
            "engine": "google_flights",
            "departure_id": "YYZ",
            "arrival_id": code,
            "outbound_date": OUTBOUND_DATE,
            "return_date": RETURN_DATE,
            "currency": "CAD",
            "hl": "en",
            "api_key": api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        # Catch SerpApi authentication or API errors directly
        if "error" in results:
            print(f"❌ SerpApi Error for {display_label}: {results['error']}")
            continue

        # Extract prices from returned flight categories
        flight_groups = results.get("best_flights", []) + results.get(
            "other_flights", []
        )
        found_prices = [
            flight["price"] for flight in flight_groups if "price" in flight
        ]

        # Fallback to price insights if flight array lacks price key
        if (
            not found_prices
            and "price_insights" in results
            and "lowest_price" in results["price_insights"]
        ):
            found_prices.append(results["price_insights"]["lowest_price"])

        if found_prices:
            lowest_price = min(found_prices)
            cursor.execute(
                """
                INSERT INTO flight_data (city, airport_name, code, price, date_searched)
                VALUES (?, ?, ?, ?, ?)
            """,
                (display_label, airport_name, code, lowest_price, today_str),
            )
            print(f"✅ Saved: {display_label} - ${lowest_price} CAD")
        else:
            print(f"⚠️ No price found in search results for {display_label}")

    except Exception as e:
        print(f"❌ Exception during execution for {display_label}: {e}")

conn.commit()

# ---------------------------------------------------------
# 3. EXPORT DATABASE TO data.json
# ---------------------------------------------------------
cursor.execute("SELECT city, price, date_searched FROM flight_data")
rows = cursor.fetchall()

json_data = [
    {"city": row[0], "price": row[1], "date": row[2]} for row in rows
]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2)

print(f"📊 Exported {len(json_data)} total records to data.json")
conn.close()
