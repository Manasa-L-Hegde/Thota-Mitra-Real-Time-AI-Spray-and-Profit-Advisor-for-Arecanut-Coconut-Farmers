import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from app.services.weather_service import WeatherService
from app.core.config import settings
from app.core.cache import weather_cache


@pytest.fixture(autouse=True)
def clean_cache():
    weather_cache.clear()
    yield
    weather_cache.clear()


def test_weather_cache_and_force_refresh():
    # Isolate this cache-behaviour test from API tests that may have requested
    # the default plantation coordinates earlier in the same test session.
    weather_cache.clear()

    async def _run():
        service = WeatherService()

        # Sample raw payload resembling Open-Meteo
        sample_raw = {
            "timezone": "Asia/Kolkata",
            "elevation": 590.0,
            "hourly": {
                "time": ["2026-07-12T00:00", "2026-07-12T01:00"],
                "temperature_2m": [24.0, 23.5],
                "relative_humidity_2m": [90.0, 92.0],
                "precipitation": [0.0, 0.5],
                "cloud_cover": [80.0, 85.0],
                "wind_speed_10m": [10.0, 11.0]
            },
            "daily": {
                "time": ["2026-07-12"],
                "temperature_2m_max": [27.0],
                "temperature_2m_min": [22.0],
                "precipitation_sum": [0.5],
                "precipitation_probability_max": [40.0],
                "wind_speed_10m_max": [11.0]
            }
        }

        # Test mode disables external weather by default. This unit test supplies
        # a mock response, so it explicitly enables the fetch branch.
        with patch.object(settings, "ENABLE_LIVE_WEATHER", True), patch.object(service, "_fetch_open_meteo", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_raw

            # First call: should call Open-Meteo
            w1 = await service.get_normalized_weather(13.1234, 75.5678)
            assert mock_fetch.call_count == 1
            assert w1.cached is False

            # Second call: should serve from cache without re-fetching
            w2 = await service.get_normalized_weather(13.1234, 75.5678)
            assert mock_fetch.call_count == 1
            assert w2.cached is True

            # Third call with force_refresh=True: should fetch again
            w3 = await service.get_normalized_weather(13.1234, 75.5678, force_refresh=True)
            assert mock_fetch.call_count == 2
            assert w3.cached is False

    asyncio.run(_run())


def test_graceful_fallback_when_api_fails():
    async def _run():
        service = WeatherService()

        # Simulate network failure on cold start
        with patch.object(service, "_fetch_open_meteo", side_effect=Exception("Connection timed out")):
            w = await service.get_normalized_weather(13.6934, 75.2427)
            # Should gracefully return offline fallback without crashing
            assert w is not None
            assert w.is_stale_fallback is True
            assert "Offline" in w.data_source or "Connection timed out" in w.data_source
            assert len(w.daily) == 10
            assert len(w.hourly) == 240

    asyncio.run(_run())
