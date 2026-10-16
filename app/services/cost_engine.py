import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.config import settings

DEFAULTS_PATH = settings.CONFIG_DIR / "defaults.json"


class CostProfitEngine:
    def __init__(self, defaults_path: Path = DEFAULTS_PATH):
        self.defaults_path = defaults_path
        self._defaults = self._load_defaults()

    def _load_defaults(self) -> Dict[str, Any]:
        if self.defaults_path.exists():
            try:
                with open(self.defaults_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_reference_defaults(self) -> Dict[str, Any]:
        return self._defaults.get("plantation_defaults", {})

    def calculate_cost_and_profit(
        self,
        acres: float = 1.0,
        trees_per_acre: int = 575,
        labour_wage_per_day: float = 650.0,
        spray_rounds: int = 3,
        spray_cost_per_round: Optional[float] = None,
        manure_fertilizer_cost: float = 35000.0,
        harvest_labour_cost: float = 45000.0,
        expected_yield_kg: Optional[float] = None,
        selling_price_per_qtl: float = 44000.0,
        crop: str = "arecanut"
    ) -> Dict[str, Any]:
        """
        Calculates complete plantation economics, break-even thresholds,
        and plain-language agronomic insights.
        """
        total_trees = round(acres * trees_per_acre)

        # Default spray cost: ₹18 per tree per round (Deccan Herald CPCRI baseline)
        if spray_cost_per_round is None or spray_cost_per_round <= 0:
            spray_cost_per_round = total_trees * 18.0

        total_spray_cost = spray_rounds * spray_cost_per_round
        total_manure_cost = acres * manure_fertilizer_cost
        total_harvest_cost = acres * harvest_labour_cost

        # Other maintenance labour (weeding, drainage, desuckering ~ 25 mandays/acre)
        other_labour_days = 25 * acres
        other_labour_cost = other_labour_days * labour_wage_per_day

        total_cultivation_cost = (
            total_spray_cost +
            total_manure_cost +
            total_harvest_cost +
            other_labour_cost
        )

        cost_per_acre = total_cultivation_cost / max(0.1, acres)
        cost_per_tree = total_cultivation_cost / max(1, total_trees)

        # Default yield: 4.75 kg dry chali per bearing tree
        if expected_yield_kg is None or expected_yield_kg <= 0:
            expected_yield_kg = total_trees * 4.75

        # Yield in quintals (1 quintal = 100 kg)
        expected_yield_qtl = expected_yield_kg / 100.0

        # Revenue
        total_revenue = expected_yield_qtl * selling_price_per_qtl
        revenue_per_acre = total_revenue / max(0.1, acres)

        # Profit / Loss
        net_profit = total_revenue - total_cultivation_cost
        profit_per_acre = net_profit / max(0.1, acres)

        # Break-even price
        if expected_yield_qtl > 0:
            break_even_price_per_qtl = round(total_cultivation_cost / expected_yield_qtl, 2)
            break_even_price_per_kg = round(break_even_price_per_qtl / 100.0, 2)
        else:
            break_even_price_per_qtl = 0.0
            break_even_price_per_kg = 0.0

        # Percentage breakdown
        spray_pct = round((total_spray_cost / max(1.0, total_cultivation_cost)) * 100.0, 1)
        manure_pct = round((total_manure_cost / max(1.0, total_cultivation_cost)) * 100.0, 1)
        harvest_pct = round((total_harvest_cost / max(1.0, total_cultivation_cost)) * 100.0, 1)
        labour_other_pct = round((other_labour_cost / max(1.0, total_cultivation_cost)) * 100.0, 1)

        # Total labour components (spray labour + harvest + maintenance)
        approx_total_labour_pct = round(harvest_pct + labour_other_pct + (spray_pct * 0.6), 1)

        # Plain language insight
        selling_price_kg = selling_price_per_qtl / 100.0
        profit_margin_pct = round((net_profit / max(1.0, total_revenue)) * 100.0, 1) if total_revenue > 0 else 0.0

        if net_profit >= 0:
            insight_en = (
                f"Labour and spraying account for {approx_total_labour_pct}% of your total cultivation cost. "
                f"Your break-even price is ₹{break_even_price_per_qtl:,.0f}/quintal (₹{break_even_price_per_kg:.0f}/kg). "
                f"At the current mandi price of ₹{selling_price_per_qtl:,.0f}/qtl, your estimated net profit is ₹{profit_per_acre:,.0f} per acre "
                f"({profit_margin_pct}% margin)."
            )
            insight_kn = (
                f"ಕೂಲಿ ಮತ್ತು ಸಿಂಪರಣೆ ವೆಚ್ಚವು ಒಟ್ಟು ವೆಚ್ಚದ ಶೇ. {approx_total_labour_pct} ರಷ್ಟಾಗಿದೆ. "
                f"ನಿಮ್ಮ ಖರ್ಚು ಸರಿದೂಗಿಸುವ ಬೆಲೆ (Break-even) ಪ್ರತಿ ಕ್ವಿಂಟಾಲ್‌ಗೆ ₹{break_even_price_per_qtl:,.0f} (ಪ್ರತಿ ಕೆ.ಜಿ.ಗೆ ₹{break_even_price_per_kg:.0f}). "
                f"ಮಾರುಕಟ್ಟೆ ದರ ₹{selling_price_per_qtl:,.0f} ಪ್ರಕಾರ, ಎಕರೆಗೆ ಅಂದಾಜು ನಿವ್ವಳ ಲಾಭ ₹{profit_per_acre:,.0f}."
            )
        else:
            insight_en = (
                f"Loss alert: Current costs exceed revenue by ₹{abs(profit_per_acre):,.0f} per acre. "
                f"You need at least ₹{break_even_price_per_qtl:,.0f}/qtl to break even."
            )
            insight_kn = (
                f"ಎಚ್ಚರಿಕೆ: ಎಕರೆಗೆ ₹{abs(profit_per_acre):,.0f} ನಷ್ಟವಾಗುವ ಸಂಭವವಿದೆ. "
                f"ಖರ್ಚು ಸರಿಹೊಂದಲು ಕ್ವಿಂಟಾಲ್‌ಗೆ ಕನಿಷ್ಠ ₹{break_even_price_per_qtl:,.0f} ಬೆಲೆ ಬೇಕು."
            )

        return {
            "inputs": {
                "acres": acres,
                "trees_per_acre": trees_per_acre,
                "total_trees": total_trees,
                "labour_wage_per_day": labour_wage_per_day,
                "spray_rounds": spray_rounds,
                "spray_cost_per_round": round(spray_cost_per_round, 2),
                "manure_fertilizer_cost": manure_fertilizer_cost,
                "harvest_labour_cost": harvest_labour_cost,
                "expected_yield_kg": round(expected_yield_kg, 1),
                "expected_yield_qtl": round(expected_yield_qtl, 2),
                "selling_price_per_qtl": selling_price_per_qtl
            },
            "financial_summary": {
                "total_cultivation_cost": round(total_cultivation_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2),
                "cost_per_tree": round(cost_per_tree, 2),
                "total_revenue": round(total_revenue, 2),
                "revenue_per_acre": round(revenue_per_acre, 2),
                "net_profit": round(net_profit, 2),
                "profit_per_acre": round(profit_per_acre, 2),
                "break_even_price_per_qtl": break_even_price_per_qtl,
                "break_even_price_per_kg": break_even_price_per_kg,
                "profit_margin_pct": profit_margin_pct,
                "is_profitable": net_profit >= 0
            },
            "cost_breakdown": {
                "spraying_cost": round(total_spray_cost, 2),
                "spraying_pct": spray_pct,
                "manure_fertilizer_cost": round(total_manure_cost, 2),
                "manure_pct": manure_pct,
                "harvest_labour_cost": round(total_harvest_cost, 2),
                "harvest_pct": harvest_pct,
                "maintenance_labour_cost": round(other_labour_cost, 2),
                "maintenance_labour_pct": labour_other_pct,
                "combined_labour_pct": approx_total_labour_pct
            },
            "plain_insights": {
                "en": insight_en,
                "kn": insight_kn
            },
            "disclaimer": "Economics calculator based on user inputs and published regional averages. Actual farm profits depend on grade quality, weather losses, and market fluctuations."
        }


cost_engine = CostProfitEngine()
