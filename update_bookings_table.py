import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

try:
    cur.execute("""
    ALTER TABLE bookings
    ADD COLUMN user_id INTEGER
    """)
    print("✅ user_id column added")
except Exception as e:
    print("⚠️", e)

conn.commit()
conn.close()