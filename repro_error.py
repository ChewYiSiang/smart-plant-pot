from sqlmodel import Session, select
from models import get_engine, SensorReading
from datetime import datetime, timedelta

def reproduce():
    engine = get_engine()
    with Session(engine) as session:
        ten_mins_ago = datetime.utcnow() - timedelta(minutes=10)
        statement = select(SensorReading).where(
            SensorReading.device_id == "s3_devkitc_plant_pot",
            SensorReading.timestamp >= ten_mins_ago
        ).order_by(SensorReading.timestamp.desc()).limit(1)
        
        recent_reading = session.exec(statement).first()
        print(f"Type of recent_reading: {type(recent_reading)}")
        if recent_reading:
            print(f"Content: {recent_reading}")
            try:
                print(f"Temperature: {recent_reading.temperature}")
            except Exception as e:
                print(f"Error accessing temperature: {e}")
        else:
            print("No recent reading found.")

if __name__ == "__main__":
    reproduce()
