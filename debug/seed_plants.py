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
            biological_info="Ocimum basilicum is a culinary herb that loves warmth and water.",
            care_tips="Requires 6-8 hours of sun. Soil should be consistently moist but not soggy. Ideal temp: 21-30C.",
            lore="I'm the king of herbs! Without enough water, I'll droop faster than a tragic hero."
        )
        cactus = PlantKnowledge(
            species="Cactus",
            biological_info="Cacti are desert dwellers that store water in their stems.",
            care_tips="Needs bright direct light. Only water when soil is bone dry. Ideal temp: 18-35C.",
            lore="I'm tough and prickly. If you overwater me, I'll literally rot. Give me sun or give me nothing."
        )
        lavender = PlantKnowledge(
            species="Lavender",
            biological_info="Lavandula is known for its fragrance and love of Mediterranean sun.",
            care_tips="Needs full sun and very well-drained, slightly alkaline soil. Drought tolerant. Ideal temp: 15-27C.",
            lore="I'm the essence of calm. Don't let my feet get wet, or I'll lose my cool."
        )
        aloe = PlantKnowledge(
            species="Aloe Vera",
            biological_info="Aloe vera is a succulent species with medicinal gel in its leaves.",
            care_tips="Prefers bright, indirect light. Water deeply but infrequently. Ideal temp: 13-27C.",
            lore="I'm your personal first-aid kit. I'm patient, but don't leave me in the dark."
        )
        spider = PlantKnowledge(
            species="Spider Plant",
            biological_info="Chlorophytum comosum is a resilient, air-purifying indoor plant.",
            care_tips="Thrives in indirect light. Keep soil slightly moist. Ideal temp: 15-24C.",
            lore="I'm an easy-going roommate. I'll clean your air while you ignore my children (the spiderettes)."
        )
        lily = PlantKnowledge(
            species="Peace Lily",
            biological_info="Spathiphyllum is an elegant plant that signals thirst by drooping.",
            care_tips="Prefers low to medium indirect light. Loves humidity. Ideal temp: 18-27C.",
            lore="I'm a bit of a drama queen. If I don't get a drink, I'll faint for the world to see."
        )
        
        session.add_all([basil, cactus, lavender, aloe, spider, lily])
        session.commit()
        print("Seeded rich botanical lore for all species.")

if __name__ == "__main__":
    seed_plants()
