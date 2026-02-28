import sqlite3
import os
import sys

db_path = "plant_pot.db"

def migrate():
    print("STARTING MIGRATION SCRIPT")
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        
        # 1. Migrate 'sensorreading' table
        print("Checking sensorreading table...")
        cursor.execute("PRAGMA table_info(sensorreading)")
        sensor_columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {sensor_columns}")
        
        for col in ["temperature", "moisture", "light"]:
            if col not in sensor_columns:
                print(f"Adding '{col}' column...")
                cursor.execute(f"ALTER TABLE sensorreading ADD COLUMN {col} REAL DEFAULT 0.0")
                conn.commit()
                print(f"  Successfully added '{col}'.")
            
        conn.close()
        print("MIGRATION COMPLETED SUCCESSFULLY")
    except Exception as e:
        print(f"MIGRATION FAILED: {e}")
    finally:
        print("ENDING MIGRATION SCRIPT")

if __name__ == "__main__":
    migrate()
