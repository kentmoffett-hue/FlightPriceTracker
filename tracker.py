import os
import sqlite3
from datetime import date
from serpapi import GoogleSearch

DESTINATIONS = {
    "Porto": "OPO",
    "Edinburgh": "EDI",
    "Toulouse/Pyrenees": "TLS",
    "Biarritz": "BIQ"
}

ORIGIN = "YYZ"
TRAVEL_DATE = "2027-06-01"
RETURN_DATE = "2027-06-12"

def init_db():
    conn = sqlite3.connect('flight_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date DATE,
            destination TEXT,
            price_cad INT
        )
    ''')
    conn.commit()
    conn.close()

def log_daily_prices():
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("ERROR: SERPAPI_KEY environment variable not found.")
        return

    conn = sqlite3.connect('flight_tracker.db')
    cursor = conn.cursor()
    today = date.today().isoformat()

    for name, code in DESTINATIONS.items():
        try:
            print(f"Fetching {name} via SerpAPI...")
            params = {
                "engine": "google_flights",
                "departure_id": ORIGIN,
                "arrival_id": code,
                "outbound_date": TRAVEL_DATE,
                "return_date": RETURN_DATE,
                "currency": "CAD",
                "hl": "en",
                "api_key": api_key
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Extract lowest price from best_flights or other_flights
            flights = results.get("best_flights", []) or results.get("other_flights", [])
            
            if flights and "price" in flights[0]:
                clean_price = flights[0]["price"]
                cursor.execute(
                    "INSERT INTO flight_prices (record_date, destination, price_cad) VALUES (?, ?, ?)",
                    (today, name, clean_price)
                )
                print(f"[{today}] SUCCESS {name}: ${clean_price} CAD")
            else:
                print(f"[{today}] No price returned for {name}")

        except Exception as e:
            print(f"[{today}] ERROR fetching {name}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    log_daily_prices()
