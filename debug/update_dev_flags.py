from sqlmodel import Session, select
from models import Device, get_engine

def update_device_flags():
    engine = get_engine()
    with Session(engine) as session:
        # Update Simulator
        sim = session.get(Device, "pot_simulator_001")
        if sim:
            print("Flagging 'pot_simulator_001' as simulator.")
            sim.is_simulator = True
            session.add(sim)
        
        # Update Real Pot
        hw = session.get(Device, "s3_devkitc_plant_pot")
        if hw:
            print("Flagging 's3_devkitc_plant_pot' as hardware.")
            hw.is_simulator = False
            session.add(hw)
            
        # Optional: Auto-detect others
        statement = select(Device)
        devices = session.exec(statement).all()
        for dev in devices:
            if dev.id not in ["pot_simulator_001", "s3_devkitc_plant_pot"]:
                if "sim" in dev.id.lower():
                    print(f"Auto-flagging '{dev.id}' as simulator.")
                    dev.is_simulator = True
                    session.add(dev)
                else:
                    print(f"Auto-flagging '{dev.id}' as hardware.")
                    dev.is_simulator = False
                    session.add(dev)
                    
        session.commit()
        print("Done.")

if __name__ == "__main__":
    update_device_flags()
