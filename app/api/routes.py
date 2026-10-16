import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.db_models import PlantationProfile, CostScenario, FarmDiaryEntry
from app.services.weather_service import weather_service
from app.services.risk_engine import risk_engine
from app.services.cost_engine import cost_engine
from app.services.mandi_service import mandi_service
from app.services.advisory_service import advisory_service
from app.services.geocoding_service import geocoding_service
from app.models.schemas import (
    NormalizedWeatherData,
    RiskAssessment,
    SprayPlannerResponse,
    DashboardSummaryResponse
)

router = APIRouter(prefix="/api", tags=["Thota Mitra Endpoints"])


@router.get("/geocode/search", summary="Karnataka village/taluk autocomplete")
async def geocode_search(q: str = Query(..., min_length=2, max_length=120)):
    return {"results": await geocoding_service.search(q)}


@router.get("/geocode/reverse", summary="Karnataka village identity for map pins")
async def geocode_reverse(lat: float = Query(...), lon: float = Query(...)):
    return await geocoding_service.reverse(lat, lon)


# --- WEATHER & RISK (PHASE 1) ---

@router.get("/weather", response_model=NormalizedWeatherData, summary="Normalized 10-day weather")
async def get_weather(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    force_refresh: bool = Query(False)
):
    latitude = lat if lat is not None else settings.DEFAULT_LATITUDE
    longitude = lon if lon is not None else settings.DEFAULT_LONGITUDE
    try:
        return await weather_service.get_normalized_weather(latitude, longitude, force_refresh=force_refresh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather: {str(exc)}")


@router.get("/risk", response_model=RiskAssessment, summary="Conducive-Conditions Index (Heuristic — Pending Field Validation)")
async def get_disease_risk(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    crop: str = Query("arecanut")
):
    latitude = lat if lat is not None else settings.DEFAULT_LATITUDE
    longitude = lon if lon is not None else settings.DEFAULT_LONGITUDE
    weather = await weather_service.get_normalized_weather(latitude, longitude)
    return risk_engine.assess_risk(weather, crop=crop)


@router.get("/spray-plan", response_model=SprayPlannerResponse, summary="7-Day Spray Window Planner")
async def get_spray_planner(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    crop: str = Query("arecanut")
):
    latitude = lat if lat is not None else settings.DEFAULT_LATITUDE
    longitude = lon if lon is not None else settings.DEFAULT_LONGITUDE
    weather = await weather_service.get_normalized_weather(latitude, longitude)
    return risk_engine.plan_spray_windows(weather, crop=crop)


@router.get("/dashboard", response_model=DashboardSummaryResponse, summary="Integrated Dashboard")
async def get_dashboard(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    crop: str = Query("arecanut"),
    db: Session = Depends(get_db)
):
    latitude = lat if lat is not None else settings.DEFAULT_LATITUDE
    longitude = lon if lon is not None else settings.DEFAULT_LONGITUDE

    weather = await weather_service.get_normalized_weather(latitude, longitude)
    risk = risk_engine.assess_risk(weather, crop=crop)
    plan = risk_engine.plan_spray_windows(weather, crop=crop)

    # Fetch profile from DB if available
    profile = db.query(PlantationProfile).first()
    village = profile.village if profile and lat is None else ("Thirthahalli, Shivamogga" if lat is None else "Custom Coordinates")

    location_info = {
        "latitude": latitude,
        "longitude": longitude,
        "village": village,
        "state": "Karnataka",
        "region": "Malnad & Coastal Belt",
        "spray_schedule": risk_engine.rules.get("schedule_engine", {})
    }

    return DashboardSummaryResponse(
        location=location_info,
        weather=weather,
        risk=risk,
        spray_plan=plan,
        disclaimer=risk.disclaimer
    )


@router.get("/rules", summary="Active Risk Rules & Thresholds")
async def get_rules():
    return risk_engine.rules


@router.get("/defaults", summary="Sourced Reference Defaults (config/defaults.json)")
async def get_defaults():
    import json
    path = settings.CONFIG_DIR / "defaults.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# --- ADVISORY & RAG (PHASE 3) ---

class AskRequest(BaseModel):
    question: str
    crop: Optional[str] = "arecanut"


@router.post("/ask", summary="RAG Advisory Assistant (strictly from /docs_corpus)")
async def ask_assistant(req: AskRequest):
    if not req.question or len(req.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please provide a valid question.")
    return advisory_service.query(req.question)


# --- MANDI PRICES & PROFIT PLANNER (PHASE 4) ---

@router.get("/mandi/prices", summary="Get APMC Mandi Prices")
async def get_mandi_prices(commodity: Optional[str] = None):
    return mandi_service.get_prices(commodity)


@router.post("/mandi/import-csv", summary="Import custom APMC prices via CSV")
async def import_mandi_csv(file: UploadFile = File(...)):
    content = await file.read()
    try:
        decoded = content.decode("utf-8")
        imported_count = mandi_service.import_csv(decoded)
        return {"status": "success", "imported_rows": imported_count}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(exc)}")


class CostCalcRequest(BaseModel):
    acres: float = 1.0
    trees_per_acre: int = 575
    labour_wage_per_day: float = 650.0
    spray_rounds: int = 3
    spray_cost_per_round: Optional[float] = None
    manure_fertilizer_cost: float = 35000.0
    harvest_labour_cost: float = 45000.0
    expected_yield_kg: Optional[float] = None
    selling_price_per_qtl: float = 44000.0
    scenario_name: Optional[str] = "Default Scenario"


@router.post("/economics/calculate", summary="Calculate Profit/Loss & Break-Even")
async def calculate_economics(req: CostCalcRequest):
    return cost_engine.calculate_cost_and_profit(
        acres=req.acres,
        trees_per_acre=req.trees_per_acre,
        labour_wage_per_day=req.labour_wage_per_day,
        spray_rounds=req.spray_rounds,
        spray_cost_per_round=req.spray_cost_per_round,
        manure_fertilizer_cost=req.manure_fertilizer_cost,
        harvest_labour_cost=req.harvest_labour_cost,
        expected_yield_kg=req.expected_yield_kg,
        selling_price_per_qtl=req.selling_price_per_qtl
    )


@router.post("/economics/save-scenario", summary="Save Cost Scenario to SQLite")
async def save_scenario(req: CostCalcRequest, db: Session = Depends(get_db)):
    calc = cost_engine.calculate_cost_and_profit(
        acres=req.acres,
        trees_per_acre=req.trees_per_acre,
        labour_wage_per_day=req.labour_wage_per_day,
        spray_rounds=req.spray_rounds,
        spray_cost_per_round=req.spray_cost_per_round,
        manure_fertilizer_cost=req.manure_fertilizer_cost,
        harvest_labour_cost=req.harvest_labour_cost,
        expected_yield_kg=req.expected_yield_kg,
        selling_price_per_qtl=req.selling_price_per_qtl
    )

    profile = db.query(PlantationProfile).first()
    scenario = CostScenario(
        plantation_id=profile.id if profile else None,
        scenario_name=req.scenario_name or "Monsoon Scenario",
        acres=req.acres,
        trees_per_acre=req.trees_per_acre,
        labour_wage_per_day=req.labour_wage_per_day,
        spray_rounds=req.spray_rounds,
        spray_cost_per_round=calc["inputs"]["spray_cost_per_round"],
        manure_fertilizer_cost=req.manure_fertilizer_cost,
        harvest_labour_cost=req.harvest_labour_cost,
        expected_yield_kg=calc["inputs"]["expected_yield_kg"],
        selling_price_per_qtl=req.selling_price_per_qtl,
        total_cost=calc["financial_summary"]["total_cultivation_cost"],
        total_revenue=calc["financial_summary"]["total_revenue"],
        net_profit=calc["financial_summary"]["net_profit"],
        profit_per_acre=calc["financial_summary"]["profit_per_acre"],
        break_even_price_per_qtl=calc["financial_summary"]["break_even_price_per_qtl"],
        break_even_price_per_kg=calc["financial_summary"]["break_even_price_per_kg"],
        labour_cost_pct=calc["cost_breakdown"]["combined_labour_pct"],
        spraying_cost_pct=calc["cost_breakdown"]["spraying_pct"],
        plain_insight_en=calc["plain_insights"]["en"],
        plain_insight_kn=calc["plain_insights"]["kn"]
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return {"status": "saved", "scenario_id": scenario.id, "calculated": calc}


@router.get("/economics/scenarios", summary="Get all saved cost scenarios")
async def get_saved_scenarios(db: Session = Depends(get_db)):
    return db.query(CostScenario).order_by(CostScenario.created_at.desc()).all()


# --- PLANTATION PROFILE ---

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_acres: Optional[float] = None
    bearing_trees: Optional[int] = None
    crop_type: Optional[str] = None
    last_sprayed_date: Optional[str] = None
    spray_rounds_done: Optional[int] = None


@router.get("/plantation/profile", summary="Get Plantation Profile")
async def get_plantation_profile(db: Session = Depends(get_db)):
    profile = db.query(PlantationProfile).first()
    if not profile:
        profile = PlantationProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.post("/plantation/profile", summary="Update Plantation Profile")
async def update_plantation_profile(req: ProfileUpdateRequest, db: Session = Depends(get_db)):
    profile = db.query(PlantationProfile).first()
    if not profile:
        profile = PlantationProfile()
        db.add(profile)

    if req.name is not None: profile.name = req.name
    if req.village is not None: profile.village = req.village
    if req.latitude is not None: profile.latitude = req.latitude
    if req.longitude is not None: profile.longitude = req.longitude
    if req.total_acres is not None: profile.total_acres = req.total_acres
    if req.bearing_trees is not None: profile.bearing_trees = req.bearing_trees
    if req.crop_type is not None: profile.crop_type = req.crop_type
    if req.last_sprayed_date is not None: profile.last_sprayed_date = req.last_sprayed_date
    if req.spray_rounds_done is not None: profile.spray_rounds_done = req.spray_rounds_done

    db.commit()
    db.refresh(profile)
    return profile


# --- FARM DIARY (PHASE 5) ---

class DiaryEntryCreate(BaseModel):
    entry_date: str
    event_type: str  # fruit_rot_seen, sprayed, harvest, monkey_damage, fertilizer
    severity: Optional[str] = "None"
    affected_trees_count: Optional[int] = 0
    notes: Optional[str] = ""
    photo_url: Optional[str] = None


@router.get("/diary", summary="List farm diary entries")
async def get_diary_entries(db: Session = Depends(get_db)):
    return db.query(FarmDiaryEntry).order_by(FarmDiaryEntry.entry_date.desc()).all()


@router.post("/diary", summary="Add a farm diary log entry")
async def create_diary_entry(entry: DiaryEntryCreate, db: Session = Depends(get_db)):
    profile = db.query(PlantationProfile).first()
    
    # Optionally pull the current heuristic index snapshot for a diary observation.
    current_risk_score = None
    try:
        lat = profile.latitude if profile else settings.DEFAULT_LATITUDE
        lon = profile.longitude if profile else settings.DEFAULT_LONGITUDE
        weather = await weather_service.get_normalized_weather(lat, lon)
        risk = risk_engine.assess_risk(weather, crop=profile.crop_type if profile else "arecanut")
        current_risk_score = risk.total_risk_score
    except Exception:
        pass

    new_entry = FarmDiaryEntry(
        plantation_id=profile.id if profile else None,
        entry_date=entry.entry_date,
        event_type=entry.event_type,
        severity=entry.severity or "None",
        affected_trees_count=entry.affected_trees_count or 0,
        notes=entry.notes or "",
        photo_url=entry.photo_url,
        weather_risk_score_at_time=current_risk_score
    )
    db.add(new_entry)

    # If it's a spray event, update the plantation profile last_sprayed_date
    if entry.event_type == "sprayed" and profile:
        profile.last_sprayed_date = entry.entry_date
        profile.spray_rounds_done = (profile.spray_rounds_done or 0) + 1

    db.commit()
    db.refresh(new_entry)
    return new_entry


@router.get("/diary/export.csv", summary="Export farm diary to CSV")
async def export_diary_csv(db: Session = Depends(get_db)):
    entries = db.query(FarmDiaryEntry).order_by(FarmDiaryEntry.entry_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Date", "Event_Type", "Severity", "Affected_Trees", "Notes", "Weather_Risk_Score_At_Time", "Logged_At"
    ])
    for e in entries:
        writer.writerow([
            e.id, e.entry_date, e.event_type, e.severity, e.affected_trees_count, e.notes, e.weather_risk_score_at_time, e.created_at
        ])
    output.seek(0)
    return Response(
        # UTF-8 BOM keeps Kannada legible in Excel and common mobile sheet apps.
        content="\ufeff" + output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=thota_mitra_diary.csv"}
    )
