# Example: Ensure your database query pulls all unique destinations
import json
import sqlite3

conn = sqlite3.connect("flight_tracker.db")
cursor = conn.cursor()

# Query all records
cursor.execute(
    "SELECT city, airport_name, code, price, date_searched FROM flight_data"
)
rows = cursor.fetchall()

# Export clean JSON structure for index.html
data = [
    {
        "city": row[0],
        "airport": row[1],
        "code": row[2],
        "price": row[3],
        "date": row[4],
    }
    for row in rows
]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

conn.close()
