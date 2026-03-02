from sqlmodel import Session, select
from models import Device, get_engine

engine = get_engine()
with Session(engine) as session:
    devices = session.exec(select(Device)).all()
    print("Devices in the DB:")
    for device in devices:
        print(f"ID: {device.id}, Name: {device.name}, is_simulator: {device.is_simulator}")
