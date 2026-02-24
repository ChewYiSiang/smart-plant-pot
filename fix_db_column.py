import sqlite3
import os
import time

db_path = "plant_pot.db"

def run_migration():
    if not os.path.exists(db_path):
        print(f"❌ Error: {db_path} not found in {os.getcwd()}")
        return

    print(f"🧐 Checking database: {db_path}...")
    
    for attempt in range(5):
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute("PRAGMA table_info(device)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "last_notified_reading_id" not in columns:
                print("🛠️ Adding last_notified_reading_id column to device table...")
                cursor.execute("ALTER TABLE device ADD COLUMN last_notified_reading_id INTEGER")
                conn.commit()
                print("✅ Column added successfully.")
            else:
                print("✅ Column already exists.")
                
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print(f"⚠️ Database is locked (Attempt {attempt+1}/5). Waiting 2s...")
                time.sleep(2)
            else:
                print(f"❌ Operational Error: {e}")
                return
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return

if __name__ == "__main__":
    run_migration()
