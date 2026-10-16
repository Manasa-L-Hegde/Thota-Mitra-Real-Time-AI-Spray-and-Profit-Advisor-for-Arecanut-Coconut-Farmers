import json
import csv
import io
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings

DEFAULTS_PATH = settings.CONFIG_DIR / "defaults.json"


class MandiService:
    def __init__(self, defaults_path: Path = DEFAULTS_PATH):
        self.defaults_path = defaults_path
        self._cached_prices: List[Dict[str, Any]] = []
        self._market_catalog: List[Dict[str, Any]] = []
        self._load_reference_prices()

    def _load_reference_prices(self):
        try:
            if self.defaults_path.exists():
                with open(self.defaults_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cached_prices = data.get("mandi_prices_reference", [])
                    self._market_catalog = data.get("karnataka_mandi_catalog", [])
            else:
                self._cached_prices = self._get_fallback_prices()
        except Exception:
            self._cached_prices = self._get_fallback_prices()

    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        return [
            {"market": "Kundapura APMC", "district": "Udupi", "commodity": "Arecanut", "modal_price_per_quintal": 44000.0, "date": "2026", "source": "Agmarknet via data.gov.in / ACROP Kundapura"},
            {"market": "Mangalore APMC", "district": "Dakshina Kannada", "commodity": "Arecanut", "modal_price_per_quintal": 35367.0, "date": "2026-08-01", "source": "Agmarknet via data.gov.in / ACROP Mangalore"},
            {"market": "Holenarsipura APMC", "district": "Hassan", "commodity": "Arecanut", "modal_price_per_quintal": 20000.0, "date": "2026-06-24", "source": "Agmarknet via data.gov.in / ACROP Hassan"},
            {"market": "K.R. Pet APMC", "district": "Mandya", "commodity": "Coconut", "modal_price_per_quintal": 17000.0, "date": "2026-06-19", "source": "Agmarknet via data.gov.in / ACROP Mandya"}
        ]

    def get_prices(self, commodity: Optional[str] = None) -> List[Dict[str, Any]]:
        # Live data is deliberately opt-in: the public API needs a configured
        # resource id/key and schema can vary by dataset.  Any error falls back
        # to the cited snapshot rather than inventing a current price.
        if not self._cached_prices:
            self._load_reference_prices()
        live_prices = self._fetch_live_prices()
        prices_by_market = {p["market"].lower(): p for p in self._cached_prices}
        prices_by_market.update({p["market"].lower(): p for p in live_prices})
        # Catalog entries deliberately have no numeric price until Agmarknet
        # reports one; the UI prompts for a farmer-entered live/custom rate.
        for market in self._market_catalog:
            key = market["market"].lower()
            if key not in prices_by_market:
                prices_by_market[key] = {
                    **market,
                    "modal_price_per_quintal": None,
                    "date": None,
                    "source": "No live price reported — enter local rate",
                    "price_status": "CUSTOM_RATE_REQUIRED"
                }
        prices = list(prices_by_market.values())
        
        if commodity:
            c_lower = commodity.lower()
            return [p for p in prices if c_lower in p.get("commodity", "").lower()]
        return prices

    def _fetch_live_prices(self) -> List[Dict[str, Any]]:
        if os.getenv("PYTEST_CURRENT_TEST") or not (settings.ENABLE_LIVE_AGMARKNET and settings.AGMARKNET_RESOURCE_ID and settings.AGMARKNET_API_KEY):
            return []
        try:
            import httpx
            url = f"https://api.data.gov.in/resource/{settings.AGMARKNET_RESOURCE_ID}"
            response = httpx.get(url, params={"api-key": settings.AGMARKNET_API_KEY, "format": "json", "limit": 100}, timeout=3.0)
            response.raise_for_status()
            records = response.json().get("records", [])
            live = []
            for record in records:
                price = record.get("modal_price") or record.get("Modal Price")
                market, commodity = record.get("market") or record.get("Market"), record.get("commodity") or record.get("Commodity")
                if price and market and commodity:
                    live.append({"market": market, "district": record.get("district") or record.get("District", ""), "commodity": commodity, "modal_price_per_quintal": float(str(price).replace(",", "")), "date": record.get("arrival_date") or datetime.now(timezone.utc).date().isoformat(), "source": "Live Agmarknet via data.gov.in", "price_status": "LIVE_AGMARKNET"})
            return live
        except Exception:
            return []

    def get_price_for_market(self, market_name: str) -> Optional[Dict[str, Any]]:
        prices = self.get_prices()
        for p in prices:
            if market_name.lower() in p["market"].lower():
                return p
        return prices[0] if prices else None

    def import_csv(self, csv_content: str) -> int:
        """Parses user-uploaded CSV with columns: Market, District, Commodity, Modal_Price, Date"""
        reader = csv.DictReader(io.StringIO(csv_content))
        new_entries = []
        for row in reader:
            try:
                price_val = float(row.get("Modal_Price") or row.get("price") or row.get("modal_price_per_quintal") or 0.0)
                if price_val > 0:
                    entry = {
                        "market": row.get("Market") or row.get("market") or "Custom Mandi",
                        "district": row.get("District") or row.get("district") or "Karnataka",
                        "commodity": row.get("Commodity") or row.get("commodity") or "Arecanut",
                        "modal_price_per_quintal": price_val,
                        "date": row.get("Date") or row.get("date") or "2026",
                        "source": "Farmer CSV Import"
                    }
                    new_entries.append(entry)
            except Exception:
                continue

        if new_entries:
            self._cached_prices = new_entries + self._cached_prices
        return len(new_entries)


mandi_service = MandiService()
