import time
from typing import Any, Optional, Tuple
from threading import Lock


class WeatherCache:
    """
    Thread-safe in-memory cache with TTL.
    Supports graceful fallback to stale cache if external API is unreachable.
    """
    def __init__(self, default_ttl_seconds: int = 1800):
        self.default_ttl = default_ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    @staticmethod
    def make_key(lat: float, lon: float) -> str:
        # Round to 3 decimals (~110m resolution)
        return f"{round(float(lat), 3)}:{round(float(lon), 3)}"

    def get(self, key: str, allow_stale: bool = False) -> Tuple[Optional[Any], bool]:
        """
        Returns (data, is_stale).
        If allow_stale is True, returns expired entry if available.
        Otherwise returns None if missing or expired.
        """
        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None, False

            data = entry["data"]
            expires_at = entry["expires_at"]

            if now <= expires_at:
                return data, False
            elif allow_stale:
                return data, True
            else:
                return None, False

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        with self._lock:
            self._store[key] = {
                "data": data,
                "cached_at": now,
                "expires_at": now + ttl
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._store)


# Global instance
weather_cache = WeatherCache(default_ttl_seconds=1800)
