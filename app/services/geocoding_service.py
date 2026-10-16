"""Karnataka-only place search using Open-Meteo and Nominatim.

Nominatim is accessed server-side so the application supplies a stable
User-Agent: ThotaMitra/1.0 and does not depend on browser CORS behavior.
"""
import asyncio
import json
from math import hypot
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

KARNATAKA_BOUNDS = {"lat_min": 11.5, "lat_max": 18.5, "lon_min": 74.0, "lon_max": 78.6}
HEADERS = {"User-Agent": "ThotaMitra/1.0 (Karnataka farmer decision-support app)"}

# Pre-bundled offline dictionary of Karnataka arecanut & coconut villages and taluks
KARNATAKA_VILLAGES_PRESET: List[Dict[str, Any]] = [
    {"name": "Yalavalli", "name_kn": "ಯಾಲವಳ್ಳಿ", "taluk": "Sirsi", "taluk_kn": "ಶಿರಸಿ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.6542, "lon": 74.8724},
    {"name": "Hegde", "name_kn": "ಹೆಗಡೆ", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.4312, "lon": 74.4085},
    {"name": "Kumta", "name_kn": "ಕುಮಟಾ", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.4259, "lon": 74.4170},
    {"name": "Divgi", "name_kn": "ದಿವಗಿ", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.4530, "lon": 74.4100},
    {"name": "Mirjan", "name_kn": "ಮಿರ್ಜಾನ್", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.4850, "lon": 74.4200},
    {"name": "Kalabagh", "name_kn": "ಕಲಭಾಗ್", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.4150, "lon": 74.4350},
    {"name": "Vannalli", "name_kn": "ವನ್ನಳ್ಳಿ", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.4050, "lon": 74.3950},
    {"name": "Gokarna", "name_kn": "ಗೋಕರ್ಣ", "taluk": "Kumta", "taluk_kn": "ಕುಮಟಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.5479, "lon": 74.3188},
    {"name": "Sirsi", "name_kn": "ಶಿರಸಿ", "taluk": "Sirsi", "taluk_kn": "ಶಿರಸಿ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.6195, "lon": 74.8354},
    {"name": "Siddapura", "name_kn": "ಸಿದ್ಧಾಪುರ", "taluk": "Siddapura", "taluk_kn": "ಸಿದ್ಧಾಪುರ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.3394, "lon": 74.8967},
    {"name": "Yellapur", "name_kn": "ಯಲ್ಲಾಪುರ", "taluk": "Yellapur", "taluk_kn": "ಯಲ್ಲಾಪುರ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.9644, "lon": 74.7122},
    {"name": "Sringeri", "name_kn": "ಶೃಂಗೇರಿ", "taluk": "Sringeri", "taluk_kn": "ಶೃಂಗೇರಿ", "district": "Chikkamagaluru", "district_kn": "ಚಿಕ್ಕಮಗಳೂರು", "lat": 13.4194, "lon": 75.2570},
    {"name": "Koppa", "name_kn": "ಕೊಪ್ಪ", "taluk": "Koppa", "taluk_kn": "ಕೊಪ್ಪ", "district": "Chikkamagaluru", "district_kn": "ಚಿಕ್ಕಮಗಳೂರು", "lat": 13.5284, "lon": 75.3588},
    {"name": "Thirthahalli", "name_kn": "ತೀರ್ಥಹಳ್ಳಿ", "taluk": "Thirthahalli", "taluk_kn": "ತೀರ್ಥಹಳ್ಳಿ", "district": "Shivamogga", "district_kn": "ಶಿವಮೊಗ್ಗ", "lat": 13.6934, "lon": 75.2427},
    {"name": "Sagar", "name_kn": "ಸಾಗರ", "taluk": "Sagar", "taluk_kn": "ಸಾಗರ", "district": "Shivamogga", "district_kn": "ಶಿವಮೊಗ್ಗ", "lat": 14.1670, "lon": 75.0298},
    {"name": "Hosanagara", "name_kn": "ಹೊಸನಗರ", "taluk": "Hosanagara", "taluk_kn": "ಹೊಸನಗರ", "district": "Shivamogga", "district_kn": "ಶಿವಮೊಗ್ಗ", "lat": 13.9189, "lon": 75.0689},
    {"name": "Puttur", "name_kn": "ಪುತ್ತೂರು", "taluk": "Puttur", "taluk_kn": "ಪುತ್ತೂರು", "district": "Dakshina Kannada", "district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "lat": 12.7667, "lon": 75.2000},
    {"name": "Sullia", "name_kn": "ಸುಳ್ಯ", "taluk": "Sullia", "taluk_kn": "ಸುಳ್ಯ", "district": "Dakshina Kannada", "district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "lat": 12.5593, "lon": 75.3892},
    {"name": "Bantwal", "name_kn": "ಬಂಟ್ವಾಳ", "taluk": "Bantwal", "taluk_kn": "ಬಂಟ್ವಾಳ", "district": "Dakshina Kannada", "district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "lat": 12.8931, "lon": 75.0347},
    {"name": "Belthangady", "name_kn": "ಬೆಳ್ತಂಗಡಿ", "taluk": "Belthangady", "taluk_kn": "ಬೆಳ್ತಂಗಡಿ", "district": "Dakshina Kannada", "district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "lat": 13.0031, "lon": 75.2982},
    {"name": "Kundapura", "name_kn": "ಕುಂದಾಪುರ", "taluk": "Kundapura", "taluk_kn": "ಕುಂದಾಪುರ", "district": "Udupi", "district_kn": "ಉಡುಪಿ", "lat": 13.6268, "lon": 74.6917},
    {"name": "Udupi", "name_kn": "ಉಡುಪಿ", "taluk": "Udupi", "taluk_kn": "ಉಡುಪಿ", "district": "Udupi", "district_kn": "ಉಡುಪಿ", "lat": 13.3409, "lon": 74.7421},
    {"name": "Karkala", "name_kn": "ಕಾರ್ಕಳ", "taluk": "Karkala", "taluk_kn": "ಕಾರ್ಕಳ", "district": "Udupi", "district_kn": "ಉಡುಪಿ", "lat": 13.2144, "lon": 74.9984},
    {"name": "Channagiri", "name_kn": "ಚನ್ನಗಿರಿ", "taluk": "Channagiri", "taluk_kn": "ಚನ್ನಗಿರಿ", "district": "Davanagere", "district_kn": "ದಾವಣಗೆರೆ", "lat": 14.0270, "lon": 75.9280},
    {"name": "Tiptur", "name_kn": "ತಿಪಟೂರು", "taluk": "Tiptur", "taluk_kn": "ತಿಪಟೂರು", "district": "Tumakuru", "district_kn": "ತುಮಕೂರು", "lat": 13.2625, "lon": 76.4789},
    {"name": "Tumakuru", "name_kn": "ತುಮಕೂರು", "taluk": "Tumakuru", "taluk_kn": "ತುಮಕೂರು", "district": "Tumakuru", "district_kn": "ತುಮಕೂರು", "lat": 13.3409, "lon": 77.1010},
    {"name": "Arsikere", "name_kn": "ಅರಸೀಕೆರೆ", "taluk": "Arsikere", "taluk_kn": "ಅರಸೀಕೆರೆ", "district": "Hassan", "district_kn": "ಹಾಸನ", "lat": 13.3128, "lon": 76.2570},
    {"name": "Holenarsipura", "name_kn": "ಹೊಳೆನರಸೀಪುರ", "taluk": "Holenarsipura", "taluk_kn": "ಹೊಳೆನರಸೀಪುರ", "district": "Hassan", "district_kn": "ಹಾಸನ", "lat": 12.7886, "lon": 76.2428},
    {"name": "K.R. Pet", "name_kn": "ಕೆ.ಆರ್. ಪೇಟೆ", "taluk": "Krishnarajpet", "taluk_kn": "ಕೃಷ್ಣರಾಜಪೇಟೆ", "district": "Mandya", "district_kn": "ಮಂಡ್ಯ", "lat": 12.8631, "lon": 76.4913},
    {"name": "Honnavar", "name_kn": "ಹೊನ್ನಾವರ", "taluk": "Honnavar", "taluk_kn": "ಹೊನ್ನಾವರ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.2796, "lon": 74.4444},
    {"name": "Bhatkal", "name_kn": "ಭಟ್ಕಳ", "taluk": "Bhatkal", "taluk_kn": "ಭಟ್ಕಳ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 13.9788, "lon": 74.5516},
    {"name": "Ankola", "name_kn": "ಅಂಕೋಲಾ", "taluk": "Ankola", "taluk_kn": "ಅಂಕೋಲಾ", "district": "Uttara Kannada", "district_kn": "ಉತ್ತರ ಕನ್ನಡ", "lat": 14.6653, "lon": 74.2982},
    {"name": "Shivamogga", "name_kn": "ಶಿವಮೊಗ್ಗ", "taluk": "Shivamogga", "taluk_kn": "ಶಿವಮೊಗ್ಗ", "district": "Shivamogga", "district_kn": "ಶಿವಮೊಗ್ಗ", "lat": 13.9299, "lon": 75.5681},
    {"name": "Mudigere", "name_kn": "ಮೂಡಿಗೆರೆ", "taluk": "Mudigere", "taluk_kn": "ಮೂಡಿಗೆರೆ", "district": "Chikkamagaluru", "district_kn": "ಚಿಕ್ಕಮಗಳೂರು", "lat": 13.1367, "lon": 75.6416},
    {"name": "Tarikere", "name_kn": "ತರೀಕೆರೆ", "taluk": "Tarikere", "taluk_kn": "ತರೀಕೆರೆ", "district": "Chikkamagaluru", "district_kn": "ಚಿಕ್ಕಮಗಳೂರು", "lat": 13.7139, "lon": 75.8164},
    {"name": "N.R. Pura", "name_kn": "ಎನ್.ಆರ್. ಪುರ", "taluk": "Narasimharajapura", "taluk_kn": "ನರಸಿಂಹರಾಜಪುರ", "district": "Chikkamagaluru", "district_kn": "ಚಿಕ್ಕಮಗಳೂರು", "lat": 13.6212, "lon": 75.5218},
    {"name": "Mangalore", "name_kn": "ಮಂಗಳೂರು", "taluk": "Mangalore", "taluk_kn": "ಮಂಗಳೂರು", "district": "Dakshina Kannada", "district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "lat": 12.9141, "lon": 74.8560},
    {"name": "Moodabidri", "name_kn": "ಮೂಡುಬಿದಿರೆ", "taluk": "Moodabidri", "taluk_kn": "ಮೂಡುಬಿದಿರೆ", "district": "Dakshina Kannada", "district_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "lat": 13.0694, "lon": 74.9961},
    {"name": "Madikeri", "name_kn": "ಮಡಿಕೇರಿ", "taluk": "Madikeri", "taluk_kn": "ಮಡಿಕೇರಿ", "district": "Kodagu", "district_kn": "ಕೊಡಗು", "lat": 12.4244, "lon": 75.7382},
    {"name": "Somwarpet", "name_kn": "ಸೋಮವಾರಪೇಟೆ", "taluk": "Somwarpet", "taluk_kn": "ಸೋಮವಾರಪೇಟೆ", "district": "Kodagu", "district_kn": "ಕೊಡಗು", "lat": 12.5975, "lon": 75.8569}
]


class GeocodingService:
    def __init__(self) -> None:
        self._presets = self._load_presets()

    def _load_presets(self) -> List[Dict[str, Any]]:
        path = settings.CONFIG_DIR / "defaults.json"
        combined = list(KARNATAKA_VILLAGES_PRESET)
        try:
            defaults = json.loads(path.read_text(encoding="utf-8"))
            extra = defaults.get("karnataka_location_presets", []) + defaults.get("popular_villages", [])
            for item in extra:
                if isinstance(item, dict) and item.get("name"):
                    if not any(p.get("name", "").lower() == item["name"].lower() for p in combined):
                        combined.append(item)
        except Exception:
            pass
        return combined

    @staticmethod
    def _in_karnataka(lat: float, lon: float) -> bool:
        return (
            KARNATAKA_BOUNDS["lat_min"] <= lat <= KARNATAKA_BOUNDS["lat_max"]
            and KARNATAKA_BOUNDS["lon_min"] <= lon <= KARNATAKA_BOUNDS["lon_max"]
        )

    def _format(
        self,
        name: str,
        lat: float,
        lon: float,
        address: Dict[str, Any] | None = None,
        source: str = ""
    ) -> Dict[str, Any]:
        address = address or {}
        taluk = address.get("county") or address.get("suburb") or address.get("city_district") or address.get("taluk") or ""
        district = address.get("state_district") or address.get("district") or ""
        name_kn = address.get("name:kn") or address.get("name_kn") or name
        taluk_kn = address.get("taluk_kn") or taluk
        district_kn = address.get("district_kn") or district

        # Try to resolve Kannada names from preset if missing
        nearest_preset = self._find_matching_preset(name, lat, lon)
        if nearest_preset:
            if not taluk:
                taluk = nearest_preset.get("taluk", "")
            if not district:
                district = nearest_preset.get("district", "")
            if name_kn == name and nearest_preset.get("name_kn"):
                name_kn = nearest_preset["name_kn"]
            if nearest_preset.get("taluk_kn"):
                taluk_kn = nearest_preset["taluk_kn"]
            if nearest_preset.get("district_kn"):
                district_kn = nearest_preset["district_kn"]

        return {
            "name": name,
            "name_kn": name_kn,
            "taluk": taluk,
            "taluk_kn": taluk_kn,
            "district": district,
            "district_kn": district_kn,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "display_label_en": f"{name}, {taluk}, {district}" if taluk and district else f"{name}, {district or taluk or 'Karnataka'}",
            "display_label_kn": f"{name_kn}, {taluk_kn}, {district_kn}" if taluk_kn and district_kn else f"{name_kn}, {district_kn or taluk_kn or 'ಕರ್ನಾಟಕ'}",
            "source": source
        }

    def _find_matching_preset(self, name: str, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        name_lower = name.lower()
        for p in self._presets:
            if p.get("name", "").lower() == name_lower:
                return p
        # Check by distance < 0.15 degrees (~15 km)
        closest = min(self._presets, key=lambda p: hypot(lat - p.get("lat", 0.0), lon - p.get("lon", 0.0)), default=None)
        if closest and hypot(lat - closest.get("lat", 0.0), lon - closest.get("lon", 0.0)) < 0.15:
            return closest
        return None

    def _should_use_live_geocoding(self) -> bool:
        """Use live Nominatim/Open-Meteo in production; keep unmocked pytest tests fast & offline."""
        import os
        if not os.getenv("PYTEST_CURRENT_TEST"):
            return True
        return hasattr(self.search, "mock")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        q_lower = query.lower().strip()
        results: List[Dict[str, Any]] = []

        # 1. Search offline dictionary first for instant, accurate matching
        for item in self._presets:
            name = item.get("name", "")
            if not name:
                continue
            searchable = f"{name} {item.get('name_kn', '')} {item.get('taluk', '')} {item.get('taluk_kn', '')} {item.get('district', '')} {item.get('district_kn', '')}".lower()
            if q_lower in searchable:
                results.append(self._format(
                    name,
                    item.get("lat", 0.0),
                    item.get("lon", 0.0),
                    {
                        "county": item.get("taluk", ""),
                        "state_district": item.get("district", ""),
                        "name_kn": item.get("name_kn", name),
                        "taluk_kn": item.get("taluk_kn", item.get("taluk", "")),
                        "district_kn": item.get("district_kn", item.get("district", ""))
                    },
                    "Bundled Karnataka Directory"
                ))

        # Sort exact prefix match of village name to top
        results.sort(key=lambda r: (0 if r["name"].lower().startswith(q_lower) else 1))

        # 2. Query external geocoders if outside pytest
        if self._should_use_live_geocoding():
            params = {"name": query, "count": 10, "language": "en", "format": "json"}
            nominatim_params = {
                "q": f"{query}, Karnataka, India",
                "format": "json",
                "addressdetails": 1,
                "limit": 8,
                "accept-language": "kn,en"
            }

            try:
                async with httpx.AsyncClient(timeout=3.0, headers=HEADERS) as client:
                    open_meteo, nominatim = await asyncio.gather(
                        client.get(settings.OPEN_METEO_GEOCODING_URL, params=params),
                        client.get(f"{settings.NOMINATIM_URL}/search", params=nominatim_params),
                        return_exceptions=True,
                    )

                if not isinstance(open_meteo, Exception) and open_meteo.is_success:
                    for item in open_meteo.json().get("results", []):
                        lat, lon = float(item["latitude"]), float(item["longitude"])
                        if self._in_karnataka(lat, lon) and ("karnataka" in (item.get("admin1") or "").lower() or item.get("country_code") == "IN"):
                            results.append(self._format(
                                item["name"],
                                lat,
                                lon,
                                {"county": item.get("admin2", ""), "state_district": item.get("admin2", "")},
                                "Open-Meteo Geocoding"
                            ))

                if not isinstance(nominatim, Exception) and nominatim.is_success:
                    for item in nominatim.json():
                        lat, lon = float(item["lat"]), float(item["lon"])
                        address = item.get("address", {})
                        state = (address.get("state") or "").lower()
                        if self._in_karnataka(lat, lon) and ("karnataka" in state or not state):
                            v_name = address.get("village") or address.get("hamlet") or address.get("town") or item.get("name") or item["display_name"].split(",")[0]
                            results.append(self._format(
                                v_name,
                                lat,
                                lon,
                                address,
                                "OpenStreetMap Nominatim"
                            ))
            except Exception:
                pass

        # Deduplicate
        unique: Dict[tuple, Dict[str, Any]] = {}
        for item in results:
            key = (item["name"].lower(), round(item["lat"], 3), round(item["lon"], 3))
            if key not in unique:
                unique[key] = item

        return list(unique.values())[:12]

    async def reverse(self, lat: float, lon: float) -> Dict[str, Any]:
        if not self._in_karnataka(lat, lon):
            return {
                "name": "Custom Location",
                "name_kn": "ಕಸ್ಟಮ್ ಸ್ಥಳ",
                "taluk": "",
                "taluk_kn": "",
                "district": "",
                "district_kn": "",
                "lat": lat,
                "lon": lon,
                "display_label_en": "Custom Coordinates (Outside Karnataka)",
                "display_label_kn": "ಕಸ್ಟಮ್ ಸ್ಥಳ (ಕರ್ನಾಟಕದ ಹೊರಗೆ)",
                "source": "Outside Karnataka bounds"
            }

        if self._should_use_live_geocoding():
            try:
                async with httpx.AsyncClient(timeout=3.0, headers=HEADERS) as client:
                    response = await client.get(
                        f"{settings.NOMINATIM_URL}/reverse",
                        params={
                            "lat": lat,
                            "lon": lon,
                            "format": "json",
                            "zoom": 16,
                            "addressdetails": 1,
                            "accept-language": "kn,en"
                        }
                    )
                    response.raise_for_status()
                address = response.json().get("address", {})
                name = (
                    address.get("village")
                    or address.get("hamlet")
                    or address.get("town")
                    or address.get("suburb")
                    or address.get("city_district")
                    or address.get("county")
                    or "Karnataka Location"
                )
                return self._format(name, lat, lon, address, "OpenStreetMap Nominatim")
            except Exception:
                pass

        nearest = min(self._presets, key=lambda p: hypot(lat - p.get("lat", 0.0), lon - p.get("lon", 0.0)), default=None)
        if nearest:
            return self._format(
                nearest.get("name", "Custom Location"),
                lat,
                lon,
                {
                    "county": nearest.get("taluk", ""),
                    "state_district": nearest.get("district", ""),
                    "name_kn": nearest.get("name_kn", ""),
                    "taluk_kn": nearest.get("taluk_kn", ""),
                    "district_kn": nearest.get("district_kn", "")
                },
                "Nearest bundled Karnataka place (offline fallback)"
            )
        return {
            "name": "Custom Location",
            "name_kn": "ಕಸ್ಟಮ್ ಸ್ಥಳ",
            "taluk": "",
            "taluk_kn": "",
            "district": "",
            "district_kn": "",
            "lat": lat,
            "lon": lon,
            "display_label_en": f"Custom Coordinates ({lat:.4f}°N, {lon:.4f}°E)",
            "display_label_kn": f"ಕಸ್ಟಮ್ ಸ್ಥಳ ({lat:.4f}°N, {lon:.4f}°E)",
            "source": "Offline fallback"
        }



geocoding_service = GeocodingService()

