import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS buses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_name TEXT,
    from_city TEXT,
    to_city TEXT,
    time TEXT,
    seats INTEGER
)
""")

conn.commit()
conn.close()

print("✅ buses table created successfully")
