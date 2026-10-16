from app.db.database import engine, Base, SessionLocal
from app.models.db_models import PlantationProfile, CostScenario, FarmDiaryEntry


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed default plantation profile if none exists
    db = SessionLocal()
    try:
        if db.query(PlantationProfile).count() == 0:
            default_plantation = PlantationProfile(
                name="Thirthahalli Arecanut Estate",
                owner_name="Manasa Hegde",
                village="Thirthahalli, Shivamogga",
                latitude=13.6934,
                longitude=75.2427,
                total_acres=2.5,
                bearing_trees=1430,
                crop_type="arecanut",
                last_sprayed_date="2026-06-08",
                spray_rounds_done=1
            )
            db.add(default_plantation)
            db.commit()
            db.refresh(default_plantation)

            # Diary observations are intentionally never fabricated or seeded.
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
