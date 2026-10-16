from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.database import Base


class PlantationProfile(Base):
    __tablename__ = "plantation_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="My Plantation")
    owner_name = Column(String(100), default="Manasa Hegde")
    village = Column(String(100), default="Thirthahalli, Shivamogga")
    latitude = Column(Float, default=13.6934)
    longitude = Column(Float, default=75.2427)
    total_acres = Column(Float, default=3.0)
    bearing_trees = Column(Integer, default=1725)
    crop_type = Column(String(50), default="arecanut")
    last_sprayed_date = Column(String(20), nullable=True)  # YYYY-MM-DD
    spray_rounds_done = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    scenarios = relationship("CostScenario", back_populates="plantation", cascade="all, delete-orphan")
    diary_entries = relationship("FarmDiaryEntry", back_populates="plantation", cascade="all, delete-orphan")


class CostScenario(Base):
    __tablename__ = "cost_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    plantation_id = Column(Integer, ForeignKey("plantation_profiles.id"), nullable=True)
    scenario_name = Column(String(100), default="2026 Monsoon Budget")
    acres = Column(Float, default=1.0)
    trees_per_acre = Column(Integer, default=575)
    labour_wage_per_day = Column(Float, default=650.0)
    spray_rounds = Column(Integer, default=3)
    spray_cost_per_round = Column(Float, default=10350.0)  # 575 trees * 18/tree
    manure_fertilizer_cost = Column(Float, default=35000.0)
    harvest_labour_cost = Column(Float, default=45000.0)
    expected_yield_kg = Column(Float, default=2730.0)  # ~4.75 kg * 575 trees
    selling_price_per_qtl = Column(Float, default=44000.0)
    
    # Calculated outputs
    total_cost = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    profit_per_acre = Column(Float, default=0.0)
    break_even_price_per_qtl = Column(Float, default=0.0)
    break_even_price_per_kg = Column(Float, default=0.0)
    labour_cost_pct = Column(Float, default=70.0)
    spraying_cost_pct = Column(Float, default=20.0)
    plain_insight_en = Column(Text, default="")
    plain_insight_kn = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)

    plantation = relationship("PlantationProfile", back_populates="scenarios")


class FarmDiaryEntry(Base):
    __tablename__ = "farm_diary_entries"

    id = Column(Integer, primary_key=True, index=True)
    plantation_id = Column(Integer, ForeignKey("plantation_profiles.id"), nullable=True)
    entry_date = Column(String(20), index=True)  # YYYY-MM-DD
    event_type = Column(String(50), index=True)  # fruit_rot_seen, sprayed, harvest, monkey_damage, fertilizer
    severity = Column(String(20), default="None")  # None, Low, Moderate, Severe
    affected_trees_count = Column(Integer, default=0)
    notes = Column(Text, default="")
    photo_url = Column(String(255), nullable=True)
    weather_risk_score_at_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plantation = relationship("PlantationProfile", back_populates="diary_entries")
