from sqlmodel import Session, select
from models import SensorReading, get_engine
import json

engine = get_engine()
with Session(engine) as session:
    readings = session.exec(select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(10)).all()
    data = [{"id": r.id, "device_id": r.device_id, "moisture": r.moisture, "event": r.event, "timestamp": r.timestamp.isoformat()} for r in readings]
    with open("readings_log.json", "w") as f:
        json.dump(data, f)
    print(f"Logged {len(readings)} readings.")
