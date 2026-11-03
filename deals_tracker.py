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

# Drop and recreate table to cleanly handle the new country column
cursor.execute("DROP TABLE IF EXISTS deal_data")
cursor.execute(
    """
    CREATE TABLE deal_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        country TEXT,
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
# 2. FETCH GLOBAL FLEXIBLE DEALS FOR JULY 2027
# ---------------------------------------------------------
api_key = os.getenv("SERPAPI_KEY")
today_str = date.today().isoformat()

if not api_key:
    print("❌ ERROR: SERPAPI_KEY environment variable is missing!")
    exit()

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
        print(f"🔍 Global deals search returned {len(deals)} options.")

        best_deals_found = {}

        for deal in deals:
            dest_code = deal.get("arrival_airport_code") or deal.get(
                "destination_id"
            )
            raw_name = (
                deal.get("name")
                or deal.get("arrival_airport_name")
                or deal.get("destination_name")
                or deal.get("snippet")
            )
            price = deal.get("price")
            country = deal.get("country") or deal.get("destination_country")

            # Parse city and country if raw name contains a comma (e.g., "Muscat, Oman")
            city_name = raw_name
            if not country and raw_name and "," in raw_name:
                parts = [p.strip() for p in raw_name.split(",")]
                if len(parts) >= 2:
                    city_name = parts[0]
                    country = parts[-1]

            if dest_code and price is not None:
                if not city_name or city_name == dest_code:
                    city_name = dest_code
                if not country:
                    country = ""

                # Keep the cheapest price found for each unique destination
                if (
                    dest_code not in best_deals_found
                    or price < best_deals_found[dest_code]["price"]
                ):
                    best_deals_found[dest_code] = {
                        "city": city_name,
                        "country": country,
                        "code": dest_code,
                        "price": price,
                        "outbound_date": deal.get(
                            "outbound_date", "Flexible"
                        ),
                        "return_date": deal.get("return_date", "Flexible"),
                    }

        for code, data in best_deals_found.items():
            cursor.execute(
                """
                INSERT INTO deal_data (city, country, code, price, outbound_date, return_date, date_searched)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["city"],
                    data["country"],
                    code,
                    data["price"],
                    data["outbound_date"],
                    data["return_date"],
                    today_str,
                ),
            )
            print(
                f"✅ Saved Global Deal: {data['city']}, {data['country']} ({code}) - ${data['price']} CAD"
            )

except Exception as e:
    print(f"❌ Exception during deals fetch: {e}")

conn.commit()

# ---------------------------------------------------------
# 3. EXPORT TO deals_data.json
# ---------------------------------------------------------
cursor.execute(
    "SELECT city, country, code, price, outbound_date, return_date, date_searched FROM deal_data"
)
rows = cursor.fetchall()

json_data = [
    {
        "city": row[0],
        "country": row[1],
        "code": row[2],
        "price": row[3],
        "outbound": row[4],
        "return": row[5],
        "date": row[6],
    }
    for row in rows
]

with open("deals_data.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2)

print(f"📊 Exported {len(json_data)} global deals to deals_data.json")
conn.close()
