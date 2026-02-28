import sqlite3
import time

db_path = "plant_pot.db"

def test_lock():
    print(f"Testing lock on {db_path}...")
    try:
        conn = sqlite3.connect(db_path, timeout=1)
        cursor = conn.cursor()
        print("Connected. Attempting to write...")
        cursor.execute("CREATE TABLE IF NOT EXISTS lock_test (id INTEGER PRIMARY KEY)")
        conn.commit()
        print("Write successful!")
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Lock detected: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_lock()
