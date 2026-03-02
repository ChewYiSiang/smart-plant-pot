import sqlite3
import os

db_path = 'plant_pot.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, is_simulator FROM device;")
        rows = cursor.fetchall()
        print("Devices found:")
        for row in rows:
            print(f"ID: {row[0]}, is_sim: {row[1]}")
    except Exception as e:
        print(f"Error querying devices: {e}")
    
    try:
        cursor.execute("SELECT id, device_id, moisture, event FROM sensorreading ORDER BY timestamp DESC LIMIT 10;")
        rows = cursor.fetchall()
        print("\nLatest readings:")
        for row in rows:
            print(f"ID: {row[0]}, Device: {row[1]}, Moisture: {row[2]}, Event: {row[3]}")
    except Exception as e:
        print(f"Error querying readings: {e}")
    conn.close()
