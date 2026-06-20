import sqlite3

conn = sqlite3.connect("database.db")

conn.execute('''
CREATE TABLE IF NOT EXISTS buses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_name TEXT,
    from_city TEXT,
    to_city TEXT,
    time TEXT,
    seats INTEGER,
    stops TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    bus_id INTEGER,
    seat_no INTEGER,
    from_city TEXT,
    to_city TEXT,
    travel_date TEXT
)
''')

conn.commit()
conn.close()
print("✅ Database created and ready.")
