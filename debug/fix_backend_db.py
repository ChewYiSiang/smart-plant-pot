import sqlite3
import os

db_path = "plant_pot.db"

def fix():
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. It will be created fresh by the server.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(device)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "pending_audio_id" not in columns:
            print("Attempting to add 'pending_audio_id' column...")
            cursor.execute("ALTER TABLE device ADD COLUMN pending_audio_id INTEGER")
            conn.commit()
            print("Successfully added column.")
        else:
            print("Column 'pending_audio_id' already exists.")
            
        conn.close()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("ERROR: Database is locked! You MUST stop your FastAPI server before running this script.")
        else:
            print(f"SQL Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    fix()
