import sqlite3
from datetime import date
from fast_flights import FlightQuery, create_query, get_flights

# Define your target routes from Toronto (YYZ)
DESTINATIONS = {
    "Porto": "OPO",
    "Edinburgh": "EDI",
    "Toulouse/Pyrenees": "TLS",
    "Biarritz": "BIQ"
}

ORIGIN = "YYZ"
TRAVEL_DATE = "2027-06-01" # Target departure window

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
    conn = sqlite3.connect('flight_tracker.db')
    cursor = conn.cursor()
    today = date.today().isoformat()

    for name, code in DESTINATIONS.items():
        try:
            # Query the Google Flights engine via fast_flights
            q = create_query(
                flights=[FlightQuery(date=TRAVEL_DATE, from_airport=ORIGIN, to_airport=code)],
                seat="economy",
                trip="round-trip"
            )
            result = get_flights(q)
            cheapest_price = result.flights[0].price # Extracts top result fare

            cursor.execute(
                "INSERT INTO flight_prices (record_date, destination, price_cad) VALUES (?, ?, ?)",
                (today, name, int(cheapest_price))
            )
            print(f"[{today}] {name}: ${cheapest_price} CAD")
        except Exception as e:
            print(f"Failed to fetch {name}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    log_daily_prices()