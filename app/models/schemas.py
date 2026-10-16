from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class SprayRecommendation(str, Enum):
    GOOD = "GOOD"
    AVOID = "AVOID"
    MONITOR = "MONITOR"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class HourlyWeather(BaseModel):
    time: str
    temperature_c: float
    relative_humidity_pct: float
    precipitation_mm: float
    cloud_cover_pct: float
    wind_speed_kmh: float


class DailyWeather(BaseModel):
    date: str
    is_past: bool
    temperature_max_c: float
    temperature_min_c: float
    precipitation_sum_mm: float
    precipitation_probability_max: Optional[float] = 0.0
    avg_relative_humidity_pct: float
    avg_cloud_cover_pct: float
    max_wind_speed_kmh: float
    is_rainy_day: bool


class NormalizedWeatherData(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    elevation: Optional[float] = 0.0
    past_days_count: int
    forecast_days_count: int
    cached: bool = False
    is_stale_fallback: bool = False
    fetched_at: str
    data_source: str = "Open-Meteo Weather API (https://api.open-meteo.com/v1/forecast)"
    source: str = "Open-Meteo Live API"
    hourly: List[HourlyWeather]
    daily: List[DailyWeather]
    disclaimer: str = "Weather data provided for advisory guidance only."


class FactorScore(BaseModel):
    factor_id: str
    factor_name_en: str
    factor_name_kn: str
    weight: float
    raw_value: float
    unit: str
    normalized_score: float = Field(..., ge=0.0, le=100.0)
    weighted_contribution: float
    rule_applied: str
    explanation_en: str
    explanation_kn: str


class RiskAssessment(BaseModel):
    crop: str
    crop_name_kn: str
    target_disease_en: str
    target_disease_kn: str
    pathogen: str
    total_risk_score: int = Field(..., ge=0, le=100)
    # Preferred terminology. Legacy fields remain for backwards-compatible clients.
    conducive_conditions_index: int = Field(..., ge=0, le=100)
    index_label_en: str = "Conducive-Conditions Index (Heuristic — Pending Field Validation)"
    index_label_kn: str = "ಹವಾಮಾನ ಅನುಕೂಲಕರ ಸೂಚ್ಯಂಕ (ಅಂದಾಜು — ಕ್ಷೇತ್ರ ಪರಿಶೀಲನೆ ಬಾಕಿ)"
    methodology: str = "HEURISTIC_TO_BE_VALIDATED"
    risk_level: RiskLevel
    risk_label_en: str
    risk_label_kn: str
    badge_color: str
    consecutive_rainy_days: int
    action_summary_en: str
    action_summary_kn: str
    factors: List[FactorScore]
    rules_source: str
    rules_version: str
    rules_status: str
    disclaimer: str


class DailySprayDecision(BaseModel):
    date: str
    day_name: str
    recommendation: SprayRecommendation
    badge_color: str
    summary_en: str
    summary_kn: str
    rain_expected_mm: float
    rain_probability_pct: float
    max_wind_kmh: float
    dry_window_hours: int
    rules_applied: List[str]
    rule_source: str


class SprayPlannerResponse(BaseModel):
    crop: str
    plantation_location: Dict[str, float]
    forecast_days_count: int
    decisions: List[DailySprayDecision]
    data_source: str
    rules_reference: str
    disclaimer: str


class DashboardSummaryResponse(BaseModel):
    location: Dict[str, Any]
    weather: NormalizedWeatherData
    risk: RiskAssessment
    spray_plan: SprayPlannerResponse
    disclaimer: str
