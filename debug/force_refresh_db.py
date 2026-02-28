import os
import sqlite3
from models import init_db

db_path = "plant_pot.db"

def force_refresh_db():
    if os.path.exists(db_path):
        print(f"Attempting to delete {db_path}...")
        try:
            os.remove(db_path)
            print("Successfully deleted database file.")
        except Exception as e:
            print(f"Failed to delete database file: {e}")
            print("Try stopping the FastAPI server first!")
            return False
            
    print("Re-initializing database...")
    try:
        init_db()
        print("Database initialized successfully with new schema.")
        
        # Verify the column
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(device)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        if "pending_audio_id" in columns:
            print("Verification SUCCESS: 'pending_audio_id' exists.")
            return True
        else:
            print("Verification FAILED: Column still missing.")
            return False
    except Exception as e:
        print(f"Error during initialization: {e}")
        return False

if __name__ == "__main__":
    force_refresh_db()
