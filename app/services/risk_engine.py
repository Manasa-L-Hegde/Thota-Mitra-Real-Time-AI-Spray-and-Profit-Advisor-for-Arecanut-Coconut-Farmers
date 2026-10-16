import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from app.core.config import settings
from app.models.schemas import (
    RiskAssessment,
    RiskLevel,
    FactorScore,
    SprayRecommendation,
    DailySprayDecision,
    SprayPlannerResponse,
    NormalizedWeatherData,
    DailyWeather
)

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Transparent, rule-based conducive-conditions index and spray window planner.
    Strictly reads agronomic parameters and thresholds from config/risk_rules.json.
    """

    def __init__(self, rules_path: Path = settings.RISK_RULES_PATH):
        self.rules_path = rules_path
        self._rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Failed to load risk rules from {self.rules_path}: {exc}")
            raise RuntimeError(f"Could not load risk rules: {exc}")

    def reload_rules(self) -> None:
        """Allows hot reloading if config/risk_rules.json is edited by the farmer/agronomist."""
        self._rules = self._load_rules()

    @property
    def rules(self) -> Dict[str, Any]:
        return self._rules

    def calculate_consecutive_rainy_days(self, daily: List[DailyWeather]) -> int:
        """
        Calculates consecutive rainy days ending at the present/recent period.
        A day is considered rainy if precipitation_sum_mm >= rainy_day_definition_mm (2.5mm).
        """
        rain_threshold = self._rules.get("rainy_day_definition_mm", 2.5)
        # Find index of today or last past day
        past_and_today = [d for d in daily if d.is_past]
        if not past_and_today and daily:
            past_and_today = [daily[0]]
        
        # Count consecutive rainy days backwards from the most recent known day
        consecutive = 0
        for day in reversed(past_and_today):
            if day.precipitation_sum_mm >= rain_threshold:
                consecutive += 1
            else:
                break
        return consecutive

    def assess_risk(
        self,
        weather: NormalizedWeatherData,
        crop: str = "arecanut"
    ) -> RiskAssessment:
        """
        Computes a heuristic conducive-conditions index (0-100), not disease probability.
        Returns full rule attribution and explanation in English and Kannada.
        """
        crop_profiles = self._rules.get("crop_profiles", {})
        crop_key = crop.lower()
        if crop_key not in crop_profiles:
            crop_key = "arecanut"

        profile = crop_profiles[crop_key]
        weights = profile["weights"]
        thresholds = profile["thresholds"]
        
        # 1. Consecutive rainy days factor
        consecutive_rain = self.calculate_consecutive_rainy_days(weather.daily)
        if consecutive_rain >= thresholds["consecutive_rain_days_high"]:
            rain_norm = 100.0
            rain_exp_en = f"{consecutive_rain} consecutive rainy days (critical threshold: >= {thresholds['consecutive_rain_days_high']} days)."
            rain_exp_kn = f"{consecutive_rain} ನಿರಂತರ ಮಳೆಯ ದಿನಗಳು (ಅಪಾಯದ ಮಿತಿ: >= {thresholds['consecutive_rain_days_high']} ದಿನಗಳು)."
            rain_rule = f"consecutive_rain >= {thresholds['consecutive_rain_days_high']}"
        elif consecutive_rain >= thresholds["consecutive_rain_days_moderate"]:
            rain_norm = 65.0
            rain_exp_en = f"{consecutive_rain} consecutive rainy days (moderate threshold: >= {thresholds['consecutive_rain_days_moderate']} days)."
            rain_exp_kn = f"{consecutive_rain} ನಿರಂತರ ಮಳೆಯ ದಿನಗಳು (ಮಧ್ಯಮ ಮಿತಿ: >= {thresholds['consecutive_rain_days_moderate']} ದಿನಗಳು)."
            rain_rule = f"consecutive_rain >= {thresholds['consecutive_rain_days_moderate']}"
        elif consecutive_rain == 1:
            rain_norm = 35.0
            rain_exp_en = "1 rainy day recorded in the recent window."
            rain_exp_kn = "ಕಳೆದ ದಿನಗಳಲ್ಲಿ 1 ಮಳೆಯ ದಿನ ದಾಖಲಾಗಿದೆ."
            rain_rule = "consecutive_rain == 1"
        else:
            rain_norm = 10.0
            rain_exp_en = "No consecutive rainy days recorded."
            rain_exp_kn = "ನಿರಂತರ ಮಳೆಯ ದಿನಗಳಿಲ್ಲ."
            rain_rule = "consecutive_rain == 0"

        # 2. Relative Humidity factor
        # Look at the most recent 3 days + today
        recent_days = [d for d in weather.daily if d.is_past] or weather.daily[:3]
        avg_rh = sum(d.avg_relative_humidity_pct for d in recent_days) / len(recent_days) if recent_days else 80.0

        if avg_rh >= thresholds["rh_high_pct"]:
            rh_norm = 100.0
            rh_exp_en = f"Average relative humidity is {avg_rh:.1f}%, exceeding high risk threshold ({thresholds['rh_high_pct']}%)."
            rh_exp_kn = f"ಸರಾಸರಿ ಸಾಪೇಕ್ಷ ಆರ್ದ್ರತೆ {avg_rh:.1f}% ಇದ್ದು, ಅಧಿಕ ಅಪಾಯದ ಮಿತಿ ({thresholds['rh_high_pct']}%) ಮೀರಿದೆ."
            rh_rule = f"avg_rh >= {thresholds['rh_high_pct']}%"
        elif avg_rh >= thresholds["rh_moderate_pct"]:
            # Linear scaling between moderate and high
            ratio = (avg_rh - thresholds["rh_moderate_pct"]) / max(1.0, (thresholds["rh_high_pct"] - thresholds["rh_moderate_pct"]))
            rh_norm = 60.0 + (ratio * 40.0)
            rh_exp_en = f"Average relative humidity is {avg_rh:.1f}% (moderate threshold: {thresholds['rh_moderate_pct']}%)."
            rh_exp_kn = f"ಸರಾಸರಿ ಸಾಪೇಕ್ಷ ಆರ್ದ್ರತೆ {avg_rh:.1f}% (ಮಧ್ಯಮ ಮಿತಿ: {thresholds['rh_moderate_pct']}%)."
            rh_rule = f"avg_rh in [{thresholds['rh_moderate_pct']}%, {thresholds['rh_high_pct']}%]"
        else:
            rh_norm = max(0.0, (avg_rh / thresholds["rh_moderate_pct"]) * 50.0)
            rh_exp_en = f"Average relative humidity is {avg_rh:.1f}%, below moderate trigger threshold."
            rh_exp_kn = f"ಸರಾಸರಿ ಸಾಪೇಕ್ಷ ಆರ್ದ್ರತೆ {avg_rh:.1f}% ಇದ್ದು, ಮಿತಿಗಿಂತ ಕಡಿಮೆಯಿದೆ."
            rh_rule = f"avg_rh < {thresholds['rh_moderate_pct']}%"

        # 3. Cloud cover factor
        avg_cloud = sum(d.avg_cloud_cover_pct for d in recent_days) / len(recent_days) if recent_days else 60.0
        if avg_cloud >= thresholds["cloud_cover_high_pct"]:
            cloud_norm = 100.0
            cloud_exp_en = f"Heavy overcast cloud cover ({avg_cloud:.1f}%), blocking sunlight and promoting fungal spores."
            cloud_exp_kn = f"ದಟ್ಟ ಮೋಡ ಕವಿದ ವಾತಾವರಣ ({avg_cloud:.1f}%), ಸೂರ್ಯನ ಬೆಳಕನ್ನು ತಡೆದು ಶಿಲೀಂಧ್ರಕ್ಕೆ ಪೂರಕವಾಗಿದೆ."
            cloud_rule = f"cloud_cover >= {thresholds['cloud_cover_high_pct']}%"
        elif avg_cloud >= thresholds["cloud_cover_moderate_pct"]:
            cloud_norm = 65.0
            cloud_exp_en = f"Partly to mostly cloudy ({avg_cloud:.1f}%)."
            cloud_exp_kn = f"ಭಾಗಶಃ ಮೋಡ ಕವಿದ ವಾತಾವರಣ ({avg_cloud:.1f}%)."
            cloud_rule = f"cloud_cover >= {thresholds['cloud_cover_moderate_pct']}%"
        else:
            cloud_norm = 20.0
            cloud_exp_en = f"Clear sunshine conditions ({avg_cloud:.1f}% cloud cover), UV light suppresses Phytophthora sporangia."
            cloud_exp_kn = f"ಉತ್ತಮ ಬಿಸಿಲು ({avg_cloud:.1f}% ಮೋಡ), ಸೂರ್ಯನ ಬೆಳಕು ಶಿಲೀಂಧ್ರ ಬೀಜಕಗಳನ್ನು ತಡೆಯುತ್ತದೆ."
            cloud_rule = f"cloud_cover < {thresholds['cloud_cover_moderate_pct']}%"

        # 4. Temperature factor (Phytophthora optimal range 20-30°C)
        avg_temp = sum((d.temperature_max_c + d.temperature_min_c) / 2.0 for d in recent_days) / len(recent_days) if recent_days else 25.0
        min_favorable = thresholds["temp_favorable_min_c"]
        max_favorable = thresholds["temp_favorable_max_c"]

        if min_favorable <= avg_temp <= max_favorable:
            temp_norm = 100.0
            temp_exp_en = f"Temperature {avg_temp:.1f}°C is in the prime germination range ({min_favorable}°C - {max_favorable}°C)."
            temp_exp_kn = f"ತಾಪಮಾನ {avg_temp:.1f}°C ಶಿಲೀಂಧ್ರ ಬೆಳವಣಿಗೆಗೆ ಅತ್ಯಂತ ಸೂಕ್ತವಾಗಿದೆ ({min_favorable}°C - {max_favorable}°C)."
            temp_rule = f"temp in [{min_favorable}°C, {max_favorable}°C]"
        else:
            temp_norm = 30.0
            temp_exp_en = f"Temperature {avg_temp:.1f}°C is outside the optimal pathogen growth range."
            temp_exp_kn = f"ತಾಪಮಾನ {avg_temp:.1f}°C ಶಿಲೀಂಧ್ರ ಬೆಳವಣಿಗೆಯ ಸೂಕ್ತ ವ್ಯಾಪ್ತಿಯಿಂದ ಹೊರಗಿದೆ."
            temp_rule = f"temp outside [{min_favorable}°C, {max_favorable}°C]"

        # Composite score calculation
        total_weight = sum(weights.values())
        w_rain = weights["consecutive_rain"]
        w_rh = weights["relative_humidity"]
        w_cloud = weights["cloud_cover"]
        w_temp = weights["temperature"]

        weighted_rain = (rain_norm * w_rain) / total_weight
        weighted_rh = (rh_norm * w_rh) / total_weight
        weighted_cloud = (cloud_norm * w_cloud) / total_weight
        weighted_temp = (temp_norm * w_temp) / total_weight

        total_score = round(weighted_rain + weighted_rh + weighted_cloud + weighted_temp)
        total_score = max(0, min(100, total_score))

        # Risk band determination
        risk_bands = self._rules.get("risk_bands", {})
        if total_score >= risk_bands["high"]["min"]:
            band = risk_bands["high"]
            level = RiskLevel.HIGH
        elif total_score >= risk_bands["medium"]["min"]:
            band = risk_bands["medium"]
            level = RiskLevel.MEDIUM
        else:
            band = risk_bands["low"]
            level = RiskLevel.LOW

        factors = [
            FactorScore(
                factor_id="consecutive_rain",
                factor_name_en="Consecutive Rainy Days",
                factor_name_kn="ನಿರಂತರ ಮಳೆಯ ದಿನಗಳು",
                weight=float(w_rain),
                raw_value=float(consecutive_rain),
                unit="days",
                normalized_score=round(rain_norm, 1),
                weighted_contribution=round(weighted_rain, 1),
                rule_applied=rain_rule,
                explanation_en=rain_exp_en,
                explanation_kn=rain_exp_kn
            ),
            FactorScore(
                factor_id="relative_humidity",
                factor_name_en="Relative Humidity (RH)",
                factor_name_kn="ಸಾಪೇಕ್ಷ ಆರ್ದ್ರತೆ",
                weight=float(w_rh),
                raw_value=round(avg_rh, 1),
                unit="%",
                normalized_score=round(rh_norm, 1),
                weighted_contribution=round(weighted_rh, 1),
                rule_applied=rh_rule,
                explanation_en=rh_exp_en,
                explanation_kn=rh_exp_kn
            ),
            FactorScore(
                factor_id="cloud_cover",
                factor_name_en="Cloud Cover",
                factor_name_kn="ಮೋಡದ ಸಾಂದ್ರತೆ",
                weight=float(w_cloud),
                raw_value=round(avg_cloud, 1),
                unit="%",
                normalized_score=round(cloud_norm, 1),
                weighted_contribution=round(weighted_cloud, 1),
                rule_applied=cloud_rule,
                explanation_en=cloud_exp_en,
                explanation_kn=cloud_exp_kn
            ),
            FactorScore(
                factor_id="temperature",
                factor_name_en="Canopy Temperature",
                factor_name_kn="ತೋಟದ ತಾಪಮಾನ",
                weight=float(w_temp),
                raw_value=round(avg_temp, 1),
                unit="°C",
                normalized_score=round(temp_norm, 1),
                weighted_contribution=round(weighted_temp, 1),
                rule_applied=temp_rule,
                explanation_en=temp_exp_en,
                explanation_kn=temp_exp_kn
            ),
        ]

        meta = self._rules.get("_meta", {})
        return RiskAssessment(
            crop=crop_key,
            crop_name_kn=profile.get("name_kn", "ಅಡಿಕೆ"),
            target_disease_en=profile.get("target_disease_en", "Fruit Rot"),
            target_disease_kn=profile.get("target_disease_kn", "ಕೊಳೆರೋಗ"),
            pathogen=profile.get("pathogen", "Phytophthora meadii"),
            total_risk_score=total_score,
            conducive_conditions_index=total_score,
            methodology="HEURISTIC_TO_BE_VALIDATED",
            risk_level=level,
            risk_label_en=band["label_en"],
            risk_label_kn=band["label_kn"],
            badge_color=band["badge_color"],
            consecutive_rainy_days=consecutive_rain,
            action_summary_en=band["action_summary_en"],
            action_summary_kn=band["action_summary_kn"],
            factors=factors,
            rules_source=meta.get("title", "config/risk_rules.json"),
            rules_version=meta.get("version", "1.0.0"),
            rules_status=meta.get("status", "PLACEHOLDER"),
            disclaimer="Conducive-Conditions Index (Heuristic — Pending Field Validation). CPCRI documents qualitative triggers; numeric weights and thresholds are software heuristics, not CPCRI thresholds. " + meta.get("disclaimer", "Decision support only. Validate against farm conditions.")
        )

    def plan_spray_windows(
        self,
        weather: NormalizedWeatherData,
        crop: str = "arecanut"
    ) -> SprayPlannerResponse:
        """
        Evaluates forecast days and categorizes each day as GOOD, AVOID, or MONITOR
        based on rain, wind, rain probability, and consecutive dry daytime hours.
        """
        spray_rules = self._rules.get("spray_rules", {})
        avoid_cfg = spray_rules.get("avoid", {})
        good_cfg = spray_rules.get("good", {})

        # Evaluate only forecast days (not past days)
        forecast_days = [d for d in weather.daily if not d.is_past]
        if not forecast_days:
            forecast_days = weather.daily[-7:] if len(weather.daily) >= 7 else weather.daily

        decisions: List[DailySprayDecision] = []

        for day in forecast_days:
            # Find daytime hourly rainfall for this date (between 06:00 and 18:00)
            date_str = day.date
            daytime_hours = [
                h for h in weather.hourly
                if h.time.startswith(date_str) and 6 <= int(h.time[11:13]) <= 18
            ]

            # Calculate longest consecutive daytime dry streak (precipitation <= 0.1 mm)
            longest_dry_streak = 0
            current_dry_streak = 0
            for h in daytime_hours:
                if h.precipitation_mm <= 0.1:
                    current_dry_streak += 1
                    if current_dry_streak > longest_dry_streak:
                        longest_dry_streak = current_dry_streak
                else:
                    current_dry_streak = 0

            rain_sum = day.precipitation_sum_mm
            rain_prob = day.precipitation_probability_max or 0.0
            max_wind = day.max_wind_speed_kmh

            # Parse weekday name
            try:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = dt_obj.strftime("%a")
            except Exception:
                day_name = date_str

            applied_rules = []
            rec = SprayRecommendation.MONITOR
            badge_color = "#ED6C02"  # Amber
            summary_en = ""
            summary_kn = ""

            # Check Avoid Conditions First
            if rain_sum >= avoid_cfg.get("max_acceptable_rain_mm", 3.0):
                rec = SprayRecommendation.AVOID
                badge_color = "#D32F2F"
                applied_rules.append(f"rain_sum ({rain_sum}mm) >= threshold ({avoid_cfg.get('max_acceptable_rain_mm')}mm)")
                summary_en = f"Avoid spraying: Rain ({rain_sum} mm) will wash off fungicide before adherence."
                summary_kn = f"ಸಿಂಪರಣೆ ಬೇಡ: ಮಳೆ ({rain_sum} ಮಿ.ಮೀ) ಔಷಧಿಯನ್ನು ತೊಳೆದು ಹಾಕುತ್ತದೆ."
            elif rain_prob >= avoid_cfg.get("max_acceptable_rain_prob_pct", 65.0):
                rec = SprayRecommendation.AVOID
                badge_color = "#D32F2F"
                applied_rules.append(f"rain_prob ({rain_prob}%) >= threshold ({avoid_cfg.get('max_acceptable_rain_prob_pct')}%)")
                summary_en = f"Avoid spraying: High rain probability ({rain_prob:.0f}%) risks wash-off within 4-hour setting window."
                summary_kn = f"ಸಿಂಪರಣೆ ಬೇಡ: ಮಳೆಯ ಸಂಭವನೀಯತೆ ಹೆಚ್ಚಿದೆ ({rain_prob:.0f}%), ಔಷಧಿ ಒಣಗಲು ಸಮಯ ಸಿಗುವುದಿಲ್ಲ."
            elif max_wind >= avoid_cfg.get("max_acceptable_wind_speed_kmh", 20.0):
                rec = SprayRecommendation.AVOID
                badge_color = "#D32F2F"
                applied_rules.append(f"wind ({max_wind}km/h) >= threshold ({avoid_cfg.get('max_acceptable_wind_speed_kmh')}km/h)")
                summary_en = f"Avoid spraying: Strong winds ({max_wind} km/h) cause canopy drift and poor coverage."
                summary_kn = f"ಸಿಂಪರಣೆ ಬೇಡ: ಬಿರುಗಾಳಿ ({max_wind} ಕಿ.ಮೀ/ಗಂ) ಔಷಧಿಯನ್ನು ಮರಗಳ ತುದಿಗೆ ತಲುಪಲು ಬಿಡುವುದಿಲ್ಲ."

            # Check Good Conditions
            elif (
                rain_sum <= good_cfg.get("max_rain_mm", 1.0) and
                rain_prob <= good_cfg.get("max_rain_prob_pct", 30.0) and
                max_wind <= good_cfg.get("max_wind_speed_kmh", 15.0) and
                longest_dry_streak >= good_cfg.get("min_consecutive_dry_hours", 4)
            ):
                rec = SprayRecommendation.GOOD
                badge_color = "#2E7D32"
                applied_rules.append(
                    f"rain ({rain_sum}mm) <= {good_cfg.get('max_rain_mm')}mm, "
                    f"wind ({max_wind}km/h) <= {good_cfg.get('max_wind_speed_kmh')}km/h, "
                    f"dry_streak ({longest_dry_streak}h) >= {good_cfg.get('min_consecutive_dry_hours')}h"
                )
                summary_en = f"Good to spray: Clear break with {longest_dry_streak}h dry window and calm winds ({max_wind} km/h)."
                summary_kn = f"ಔಷಧಿ ಸಿಂಪಡಿಸಲು ಸೂಕ್ತ ಸಮಯ: {longest_dry_streak} ಗಂಟೆ ಒಣ ಹವೆ ಮತ್ತು ಶಾಂತ ಗಾಳಿ ಇದೆ."

            # Otherwise Monitor
            else:
                rec = SprayRecommendation.MONITOR
                badge_color = "#ED6C02"
                applied_rules.append("intermediate conditions (scattered rain / partial dry window)")
                summary_en = f"Monitor weather: Marginal showers expected ({rain_sum} mm, {rain_prob:.0f}% prob). Spray only if morning is clear."
                summary_kn = f"ಹವಾಮಾನ ಗಮನಿಸಿ: ತುಂತುರು ಮಳೆ ಸಾಧ್ಯತೆ ({rain_sum} ಮಿ.ಮೀ). ಬೆಳಿಗ್ಗೆ ಬಿಸಿಲಿದ್ದರೆ ಮಾತ್ರ ಸಿಂಪಡಿಸಿ."

            decisions.append(
                DailySprayDecision(
                    date=date_str,
                    day_name=day_name,
                    recommendation=rec,
                    badge_color=badge_color,
                    summary_en=summary_en,
                    summary_kn=summary_kn,
                    rain_expected_mm=rain_sum,
                    rain_probability_pct=rain_prob,
                    max_wind_kmh=max_wind,
                    dry_window_hours=longest_dry_streak,
                    rules_applied=applied_rules,
                    rule_source="config/risk_rules.json [spray_rules]"
                )
            )

        meta = self._rules.get("_meta", {})
        return SprayPlannerResponse(
            crop=crop,
            plantation_location={"lat": weather.latitude, "lon": weather.longitude},
            forecast_days_count=len(decisions),
            decisions=decisions,
            data_source="Open-Meteo Weather API + config/risk_rules.json",
            rules_reference=meta.get("status", "PLACEHOLDER, validate against CPCRI/UAS guidance"),
            disclaimer=meta.get("disclaimer", "Advisory decision support only. Confirm with field conditions.")
        )


risk_engine = RiskEngine()
