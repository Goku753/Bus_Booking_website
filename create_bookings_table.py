import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    bus_id INTEGER,
    seat_no INTEGER,
    from_city TEXT,
    to_city TEXT,
    travel_date TEXT
)
""")

conn.commit()
conn.close()

print("Database Updated")