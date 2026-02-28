from models import get_engine
from sqlalchemy import inspect

engine = get_engine()
inspector = inspect(engine)

for table_name in inspector.get_table_names():
    print(f"\nTable: {table_name}")
    for column in inspector.get_columns(table_name):
        print(f"  Column: {column['name']} ({column['type']})")
