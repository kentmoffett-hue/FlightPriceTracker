import sqlite3
from datetime import date
from fast_flights import FlightQuery, create_query, get_flights

DESTINATIONS = {
    "Porto": "OPO",
    "Edinburgh": "EDI",
    "Toulouse/Pyrenees": "TLS",
    "Biarritz": "BIQ"
}

ORIGIN = "YYZ"
TRAVEL_DATE = "2027-06-01"

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
            print(f"Fetching {name}...")
            q = create_query(
                flights=[FlightQuery(date=TRAVEL_DATE, from_airport=ORIGIN, to_airport=code)],
                seat="economy",
                trip="round-trip"
            )
            # Mode='headless' ensures no display is expected; timeout prevents hanging
            result = get_flights(q, mode="headless") 
            
            if result and hasattr(result, 'flights') and len(result.flights) > 0:
                cheapest_price = result.flights[0].price
                clean_price = int(str(cheapest_price).replace('$', '').replace(',', '').strip())
                
                cursor.execute(
                    "INSERT INTO flight_prices (record_date, destination, price_cad) VALUES (?, ?, ?)",
                    (today, name, clean_price)
                )
                print(f"[{today}] SUCCESS {name}: ${clean_price} CAD")
            else:
                print(f"[{today}] No flights found for {name}")

        except Exception as e:
            print(f"[{today}] ERROR fetching {name}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    log_daily_prices()
