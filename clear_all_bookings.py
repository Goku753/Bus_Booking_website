import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Delete all records from bookings table
cur.execute("DELETE FROM bookings")

conn.commit()
conn.close()

print("✅ All bookings have been cleared.")
