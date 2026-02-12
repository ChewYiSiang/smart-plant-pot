import sys
import os
from sqlmodel import Session, create_engine, select

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import PlantKnowledge, get_engine, init_db

def seed_plants():
    engine = get_engine()
    init_db()
    
    with Session(engine) as session:
        # Check if already seeded
        existing = session.exec(select(PlantKnowledge)).first()
        if existing:
            print("Database already contains plant knowledge. Skipping seed.")
            return

        basil = PlantKnowledge(
            species="Basil",
            biological_info="Ocimum basilicum is a culinary herb of the family Lamiaceae (mints).",
            care_tips="Requires at least 6 hours of sun, well-draining soil, and consistent moisture.",
            lore="Historically associated with love and prosperity in many Mediterranean cultures."
        )
        
        session.add(basil)
        session.commit()
        print("Seeded Basil information.")

if __name__ == "__main__":
    seed_plants()
