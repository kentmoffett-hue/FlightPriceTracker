import json
import os
import sqlite3
from datetime import date
from serpapi import GoogleSearch

# ---------------------------------------------------------
# 1. DEALS DATABASE SETUP
# ---------------------------------------------------------
conn = sqlite3.connect("deals_tracker.db")
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS deal_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        airport_name TEXT,
        code TEXT,
        price REAL,
        outbound_date TEXT,
        return_date TEXT,
        date_searched TEXT
    )
"""
)
conn.commit()

# ---------------------------------------------------------
# 2. FETCH FLEXIBLE DEALS FOR JULY 2027
# ---------------------------------------------------------
api_key = os.getenv("SERPAPI_KEY")
today_str = date.today().isoformat()

if not api_key:
    print("❌ ERROR: SERPAPI_KEY environment variable is missing!")
    exit()

if os.path.exists("airports.json"):
    with open("airports.json", "r", encoding="utf-8") as f:
        airports_list = json.load(f)
    target_airports = {
        item["code"]: {
            "city": item.get("city"),
            "airport_name": item.get("airport_name", item["code"]),
            "display_label": (
                f"{item.get('city')} ({item['code']})"
                if item.get("city") == "Paris"
                else item.get("city")
            ),
        }
        for item in airports_list
    }
else:
    print("❌ WARNING: airports.json not found!")
    target_airports = {}

try:
    params = {
        "engine": "google_flights_deals",
        "departure_id": "YYZ",
        "outbound_date": "2027-07-01,2027-07-31",  # Flexible July window
        "travel_duration": 1,  # 1-week trip duration
        "currency": "CAD",
        "hl": "en",
        "api_key": api_key,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        print(f"❌ SerpApi Deals Error: {results['error']}")
    else:
        deals = results.get("deals", [])
        print(
            f"🔍 Flexible deals search returned {len(deals)} global options."
        )

        best_deals_found = {}

        for deal in deals:
            dest_code = deal.get("arrival_airport_code") or deal.get(
                "destination_id"
            )
            price = deal.get("price")

            if dest_code in target_airports and price is not None:
                if (
                    dest_code not in best_deals_found
                    or price < best_deals_found[dest_code]["price"]
                ):
                    best_deals_found[dest_code] = {
                        "price": price,
                        "outbound_date": deal.get(
                            "outbound_date", "Flexible"
                        ),
                        "return_date": deal.get("return_date", "Flexible"),
                    }

        for code, data in best_deals_found.items():
            info = target_airports[code]
            cursor.execute(
                """
                INSERT INTO deal_data (city, airport_name, code, price, outbound_date, return_date, date_searched)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    info["display_label"],
                    info["airport_name"],
                    code,
                    data["price"],
                    data["outbound_date"],
                    data["return_date"],
                    today_str,
                ),
            )
            print(
                f"✅ Saved Deal: {info['display_label']} - ${data['price']} CAD ({data['outbound_date']} to {data['return_date']})"
            )

except Exception as e:
    print(f"❌ Exception during deals fetch: {e}")

conn.commit()

# ---------------------------------------------------------
# 3. EXPORT TO deals_data.json
# ---------------------------------------------------------
cursor.execute(
    "SELECT city, price, outbound_date, return_date, date_searched FROM deal_data"
)
rows = cursor.fetchall()

json_data = [
    {
        "city": row[0],
        "price": row[1],
        "outbound": row[2],
        "return": row[3],
        "date": row[4],
    }
    for row in rows
]

with open("deals_data.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2)

print(f"📊 Exported {len(json_data)} flexible deals to deals_data.json")
conn.close()
