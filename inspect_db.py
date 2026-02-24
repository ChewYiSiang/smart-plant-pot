import sqlite3
import os

db_path = "plant_pot.db"

def inspect():
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(f"Tables: {tables}")
    
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for {table_name}:")
        info = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        for col in info:
            print(f"  {col}")
            
    conn.close()

if __name__ == "__main__":
    inspect()
