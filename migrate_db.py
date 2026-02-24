import sqlite3
import os

db_path = "plant_pot.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. No migration needed (it will be created fresh).")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Migrate 'device' table
        cursor.execute("PRAGMA table_info(device)")
        device_columns = [row[1] for row in cursor.fetchall()]
        
        if "pending_audio_id" not in device_columns:
            print("Adding 'pending_audio_id' column to 'device' table...")
            cursor.execute("ALTER TABLE device ADD COLUMN pending_audio_id INTEGER")
            conn.commit()
            print("  Successfully added 'pending_audio_id' to 'device'.")

        if "is_simulator" not in device_columns:
            print("Adding 'is_simulator' column to 'device' table...")
            cursor.execute("ALTER TABLE device ADD COLUMN is_simulator BOOLEAN DEFAULT 0")
            conn.commit()
            print("  Successfully added 'is_simulator' to 'device'.")
        
        # 2. Migrate 'sensorreading' table
        cursor.execute("PRAGMA table_info(sensorreading)")
        sensor_columns = [row[1] for row in cursor.fetchall()]
        
        missing_sensors = []
        if "temperature" not in sensor_columns: missing_sensors.append("temperature")
        if "moisture" not in sensor_columns: missing_sensors.append("moisture")
        if "light" not in sensor_columns: missing_sensors.append("light")
        
        for col in missing_sensors:
            print(f"Adding '{col}' column to 'sensorreading' table...")
            cursor.execute(f"ALTER TABLE sensorreading ADD COLUMN {col} REAL DEFAULT 0.0")
            conn.commit()
            print(f"  Successfully added '{col}' to 'sensorreading'.")
            
        if not missing_sensors and "pending_audio_id" in device_columns:
            print("No missing columns detected in 'device' or 'sensorreading' tables.")
            
        conn.close()
        print("Migration check complete.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
