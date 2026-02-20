import sqlite3
import os

db_path = "plant_pot.db"

if not os.path.exists(db_path):
    print(f"Database {db_path} not found. No migration needed (it will be created fresh).")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column exists
        cursor.execute("PRAGMA table_info(device)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "pending_audio_id" not in columns:
            print("Adding 'pending_audio_id' column to 'device' table...")
            cursor.execute("ALTER TABLE device ADD COLUMN pending_audio_id INTEGER")
            conn.commit()
            print("Migration successful.")
        else:
            print("'pending_audio_id' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")
