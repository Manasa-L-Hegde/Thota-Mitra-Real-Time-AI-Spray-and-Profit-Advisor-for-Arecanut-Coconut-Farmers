import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


class Settings:
    PROJECT_NAME: str = "Thota Mitra (ತೋಟ ಮಿತ್ರ)"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    BASE_DIR: Path = BASE_DIR
    DOCS_CORPUS_DIR: Path = BASE_DIR / "docs_corpus"
    
    # Host & Port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Weather APIs
    OPEN_METEO_FORECAST_URL: str = os.getenv(
        "OPEN_METEO_FORECAST_URL", "https://api.open-meteo.com/v1/forecast"
    )
    OPEN_METEO_ARCHIVE_URL: str = os.getenv(
        "OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive"
    )
    OPEN_METEO_GEOCODING_URL: str = os.getenv(
        "OPEN_METEO_GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1/search"
    )
    NOMINATIM_URL: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
    # Optional data.gov.in resource id and API key.  Without both, the app uses
    # the dated, verified reference records in config/defaults.json.
    AGMARKNET_RESOURCE_ID: str = os.getenv("AGMARKNET_RESOURCE_ID", "")
    AGMARKNET_API_KEY: str = os.getenv("AGMARKNET_API_KEY", os.getenv("DATA_GOV_IN_API_KEY", ""))
    # Backward-compatible alias for earlier deployments.
    DATA_GOV_IN_API_KEY: str = AGMARKNET_API_KEY
    ENABLE_LIVE_AGMARKNET: bool = os.getenv("ENABLE_LIVE_AGMARKNET", "1") == "1"
    # Live weather is the normal app mode. WeatherService suppresses it for
    # unmocked pytest requests so tests never depend on external HTTP.
    ENABLE_LIVE_WEATHER: bool = os.getenv("ENABLE_LIVE_WEATHER", "1") == "1"
    
    # Cache TTL (30 minutes = 1800 seconds)
    WEATHER_CACHE_TTL_SECONDS: int = int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "1800"))
    
    # Default Karnataka plantation location: Thirthahalli, Malnad arecanut belt
    DEFAULT_LATITUDE: float = float(os.getenv("DEFAULT_LATITUDE", "13.6934"))
    DEFAULT_LONGITUDE: float = float(os.getenv("DEFAULT_LONGITUDE", "75.2427"))
    DEFAULT_VILLAGE: str = os.getenv("DEFAULT_VILLAGE", "Thirthahalli, Shivamogga")
    
    # Risk configuration path
    CONFIG_DIR: Path = BASE_DIR / "config"
    RISK_RULES_PATH: Path = CONFIG_DIR / "risk_rules.json"


settings = Settings()
