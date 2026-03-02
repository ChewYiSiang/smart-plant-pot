from datetime import datetime
import sqlite3
import os

print(f"Current System Time (Local): {datetime.now()}")
print(f"Current System Time (UTC): {datetime.utcnow()}")

db_path = 'plant_pot.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM sensorreading ORDER BY timestamp DESC LIMIT 5;")
    rows = cursor.fetchall()
    print("\nLatest reading timestamps in DB:")
    for row in rows:
        print(f"ID: {row[0]}, Timestamp: {row[1]}")
    conn.close()
else:
    print("DB not found.")
