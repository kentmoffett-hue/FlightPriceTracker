# Example: Ensure your database query pulls all unique destinations
import json
import sqlite3

# Connect to database and export data to JSON
conn = sqlite3.connect("flight_tracker.db")
cursor = conn.cursor()

# 2. Ensure table exists BEFORE querying or inserting data
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

# Query all records
cursor.execute("SELECT city, airport_name, code, price, date_searched FROM flight_data")
rows = cursor.fetchall()

# Export clean JSON structure for index.html
data = [{"city": row[0], "price": row[1], "date": row[2]} for row in rows]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

conn.close()
