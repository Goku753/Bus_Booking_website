import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS buses")

cur.execute("""
CREATE TABLE buses (
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

print("✅ BUSES TABLE RECREATED SUCCESSFULLY")
