from sqlmodel import Session, select
from models import Device, get_engine
import json

engine = get_engine()
with Session(engine) as session:
    devices = session.exec(select(Device)).all()
    data = [{"id": d.id, "name": d.name, "is_simulator": d.is_simulator} for d in devices]
    with open("devices_log.json", "w") as f:
        json.dump(data, f)
