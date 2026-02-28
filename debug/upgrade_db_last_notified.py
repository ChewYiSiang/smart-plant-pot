import sqlite3
import os

db_path = "plant_pot.db"

if not os.path.exists(db_path):
    print(f"❌ Error: {db_path} not found.")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
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
except Exception as e:
    print(f"❌ Migration failed: {e}")
