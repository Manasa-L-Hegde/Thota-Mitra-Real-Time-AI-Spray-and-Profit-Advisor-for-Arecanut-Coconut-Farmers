import pytest
from datetime import date, timedelta

from app.models.schemas import (
    NormalizedWeatherData,
    DailyWeather,
    HourlyWeather,
    RiskLevel,
    SprayRecommendation,
)
from app.services.risk_engine import RiskEngine


def build_mock_weather(
    daily_specs: list[dict],
    hourly_dry_streak: int = 6
) -> NormalizedWeatherData:
    """
    Helper to generate deterministic weather objects for unit testing.
    daily_specs: list of dicts with keys:
      - is_past (bool)
      - rain_mm (float)
      - rh_pct (float)
      - cloud_pct (float)
      - wind_kmh (float)
      - rain_prob (float)
    """
    today = date(2026, 7, 15)  # Mid-monsoon test date
    daily_items = []
    hourly_items = []

    for idx, spec in enumerate(daily_specs):
        d = today + timedelta(days=idx - 3)
        d_str = d.isoformat()
        is_past = spec.get("is_past", idx < 3)

        daily_items.append(
            DailyWeather(
                date=d_str,
                is_past=is_past,
                temperature_max_c=27.0,
                temperature_min_c=22.0,
                precipitation_sum_mm=spec["rain_mm"],
                precipitation_probability_max=spec.get("rain_prob", 50.0),
                avg_relative_humidity_pct=spec["rh_pct"],
                avg_cloud_cover_pct=spec["cloud_pct"],
                max_wind_speed_kmh=spec["wind_kmh"],
                is_rainy_day=(spec["rain_mm"] >= 2.5)
            )
        )

        # Generate 24 hourly readings
        for h in range(24):
            # If during daytime 06:00 - 18:00
            is_rainy_hour = (spec["rain_mm"] > 0) and not (6 <= h < 6 + hourly_dry_streak)
            hourly_items.append(
                HourlyWeather(
                    time=f"{d_str}T{h:02d}:00",
                    temperature_c=24.5,
                    relative_humidity_pct=spec["rh_pct"],
                    precipitation_mm=2.0 if is_rainy_hour else 0.0,
                    cloud_cover_pct=spec["cloud_pct"],
                    wind_speed_kmh=spec["wind_kmh"]
                )
            )

    return NormalizedWeatherData(
        latitude=13.6934,
        longitude=75.2427,
        timezone="Asia/Kolkata",
        past_days_count=3,
        forecast_days_count=len(daily_specs) - 3,
        cached=False,
        is_stale_fallback=False,
        fetched_at="2026-07-15T06:00:00Z",
        hourly=hourly_items,
        daily=daily_items,
        disclaimer="Test sample"
    )


class TestRiskEngine:

    @pytest.fixture
    def engine(self):
        return RiskEngine()

    def test_risk_rules_metadata_and_notice(self, engine):
        """Ensure rules file contains the mandatory heuristic status notice and disclaimer."""
        rules = engine.rules
        assert "_meta" in rules
        meta = rules["_meta"]
        assert "validate against" in meta["status"].lower()
        assert "disclaimer" in meta
        assert "crop_profiles" in rules
        assert "arecanut" in rules["crop_profiles"]
        assert "coconut" in rules["crop_profiles"]

    def test_high_risk_koleroga_scenario(self, engine):
        """
        Severe monsoon outbreak scenario:
        - 4 consecutive heavy rain days
        - 94% humidity
        - 90% cloud cover
        - 24°C favorable temperature
        Should result in HIGH risk score (>= 70).
        """
        specs = [
            {"is_past": True, "rain_mm": 35.0, "rh_pct": 94.0, "cloud_pct": 90.0, "wind_kmh": 14.0},
            {"is_past": True, "rain_mm": 42.0, "rh_pct": 95.0, "cloud_pct": 95.0, "wind_kmh": 16.0},
            {"is_past": True, "rain_mm": 28.0, "rh_pct": 93.0, "cloud_pct": 88.0, "wind_kmh": 12.0},
            {"is_past": False, "rain_mm": 25.0, "rh_pct": 92.0, "cloud_pct": 85.0, "wind_kmh": 15.0},
        ]
        weather = build_mock_weather(specs)
        assessment = engine.assess_risk(weather, crop="arecanut")

        assert assessment.total_risk_score >= 70
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.consecutive_rainy_days >= 3
        assert assessment.badge_color == "#D32F2F"
        assert len(assessment.factors) == 4

        # Validate that explanations and rules are populated
        rain_factor = next(f for f in assessment.factors if f.factor_id == "consecutive_rain")
        assert "consecutive_rain >=" in rain_factor.rule_applied
        assert rain_factor.raw_value >= 3.0

    def test_low_risk_dry_sunny_scenario(self, engine):
        """
        Pre-monsoon / dry sunny break scenario:
        - 0 consecutive rainy days
        - 62% humidity
        - 25% cloud cover (sunny UV)
        - 31°C canopy temperature
        Should result in LOW risk score (< 40).
        """
        specs = [
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 60.0, "cloud_pct": 20.0, "wind_kmh": 8.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 62.0, "cloud_pct": 25.0, "wind_kmh": 7.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 64.0, "cloud_pct": 30.0, "wind_kmh": 9.0},
            {"is_past": False, "rain_mm": 0.0, "rh_pct": 61.0, "cloud_pct": 20.0, "wind_kmh": 8.0},
        ]
        weather = build_mock_weather(specs)
        assessment = engine.assess_risk(weather, crop="arecanut")

        assert assessment.total_risk_score < 40
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.consecutive_rainy_days == 0
        assert assessment.badge_color == "#2E7D32"

    def test_medium_risk_scenario(self, engine):
        """
        Intermediate conditions:
        - 2 consecutive rain days
        - 83% humidity
        - 65% cloud cover
        Should result in MEDIUM risk score (40 - 69).
        """
        specs = [
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 75.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 5.0, "rh_pct": 82.0, "cloud_pct": 65.0, "wind_kmh": 11.0},
            {"is_past": True, "rain_mm": 8.0, "rh_pct": 84.0, "cloud_pct": 70.0, "wind_kmh": 12.0},
            {"is_past": False, "rain_mm": 4.0, "rh_pct": 83.0, "cloud_pct": 65.0, "wind_kmh": 10.0},
        ]
        weather = build_mock_weather(specs)
        assessment = engine.assess_risk(weather, crop="arecanut")

        assert 40 <= assessment.total_risk_score <= 69
        assert assessment.risk_level == RiskLevel.MEDIUM

    def test_spray_planner_avoid_heavy_rain(self, engine):
        """Heavy rain day must be marked AVOID with transparent reason."""
        specs = [
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            # Forecast Day 1: heavy rain
            {"is_past": False, "rain_mm": 18.0, "rh_pct": 92.0, "cloud_pct": 90.0, "wind_kmh": 14.0, "rain_prob": 90.0},
        ]
        weather = build_mock_weather(specs, hourly_dry_streak=1)
        plan = engine.plan_spray_windows(weather, crop="arecanut")

        assert len(plan.decisions) == 1
        decision = plan.decisions[0]
        assert decision.recommendation == SprayRecommendation.AVOID
        assert "wash off" in decision.summary_en.lower()
        assert decision.badge_color == "#D32F2F"

    def test_spray_planner_avoid_high_wind(self, engine):
        """High wind day (>20 km/h) even without rain must be marked AVOID due to spray drift."""
        specs = [
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            # Forecast Day 1: 0 rain but 26 km/h wind
            {"is_past": False, "rain_mm": 0.0, "rh_pct": 65.0, "cloud_pct": 30.0, "wind_kmh": 26.0, "rain_prob": 10.0},
        ]
        weather = build_mock_weather(specs, hourly_dry_streak=10)
        plan = engine.plan_spray_windows(weather, crop="arecanut")

        decision = plan.decisions[0]
        assert decision.recommendation == SprayRecommendation.AVOID
        assert "wind" in decision.summary_en.lower()

    def test_spray_planner_good_window(self, engine):
        """Dry day with calm winds and 6h dry window must be marked GOOD."""
        specs = [
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            # Forecast Day 1: clear break
            {"is_past": False, "rain_mm": 0.2, "rh_pct": 68.0, "cloud_pct": 35.0, "wind_kmh": 9.0, "rain_prob": 15.0},
        ]
        weather = build_mock_weather(specs, hourly_dry_streak=7)
        plan = engine.plan_spray_windows(weather, crop="arecanut")

        decision = plan.decisions[0]
        assert decision.recommendation == SprayRecommendation.GOOD
        assert decision.badge_color == "#2E7D32"
        assert decision.dry_window_hours >= 4

    def test_spray_planner_monitor_marginal(self, engine):
        """Marginal day with scattered shower (1.8mm, 45% prob) must be marked MONITOR."""
        specs = [
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            {"is_past": True, "rain_mm": 0.0, "rh_pct": 70.0, "cloud_pct": 50.0, "wind_kmh": 10.0},
            # Forecast Day 1: marginal
            {"is_past": False, "rain_mm": 1.8, "rh_pct": 75.0, "cloud_pct": 55.0, "wind_kmh": 12.0, "rain_prob": 45.0},
        ]
        weather = build_mock_weather(specs, hourly_dry_streak=3)
        plan = engine.plan_spray_windows(weather, crop="arecanut")

        decision = plan.decisions[0]
        assert decision.recommendation == SprayRecommendation.MONITOR
        assert decision.badge_color == "#ED6C02"
