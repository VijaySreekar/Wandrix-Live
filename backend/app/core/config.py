import os
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


ROOT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_description: str
    app_version: str
    api_v1_prefix: str
    frontend_origin: str
    local_frontend_origin: str
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str | None
    codex_lb_base_url: str
    codex_lb_api_key: str
    openai_model: str
    langsmith_tracing: bool
    langsmith_api_key: str | None
    langsmith_project: str
    database_url: str
    amadeus_env: str
    amadeus_client_id: str
    amadeus_client_secret: str
    amadeus_base_url: str
    weather_provider: str
    open_meteo_base_url: str
    map_provider: str
    mapbox_base_url: str
    mapbox_access_token: str
    activities_provider: str
    poi_provider: str
    geoapify_base_url: str
    geoapify_api_key: str
    events_provider: str
    ticketmaster_base_url: str
    ticketmaster_consumer_key: str
    ticketmaster_consumer_secret: str
    travel_content_provider: str
    wikimedia_travel_base_url: str


@lru_cache
def get_settings() -> Settings:
    amadeus_env = os.getenv("AMADEUS_ENV", "test")
    amadeus_base_url = (
        "https://api.amadeus.com"
        if amadeus_env == "production"
        else "https://test.api.amadeus.com"
    )

    return Settings(
        app_name="Wandrix API",
        app_description="FastAPI backend for the Wandrix travel package generator.",
        app_version="0.1.0",
        api_v1_prefix="/api/v1",
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
        local_frontend_origin="http://127.0.0.1:3000",
        supabase_url=os.getenv(
            "SUPABASE_URL",
            "https://your-project-ref.supabase.co",
        ),
        supabase_publishable_key=os.getenv("SUPABASE_PUBLISHABLE_KEY", ""),
        supabase_secret_key=os.getenv("SUPABASE_SECRET_KEY") or None,
        codex_lb_base_url=os.getenv(
            "CODEX_LB_BASE_URL",
            "https://your-codex-lb-instance.com/v1",
        ),
        codex_lb_api_key=os.getenv("CODEX_LB_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        langsmith_tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY") or None,
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "wandrix"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/wandrix",
        ),
        amadeus_env=amadeus_env,
        amadeus_client_id=os.getenv("AMADEUS_CLIENT_ID", ""),
        amadeus_client_secret=os.getenv("AMADEUS_CLIENT_SECRET", ""),
        amadeus_base_url=os.getenv("AMADEUS_BASE_URL", amadeus_base_url),
        weather_provider=os.getenv("WEATHER_PROVIDER", "open-meteo"),
        open_meteo_base_url=os.getenv(
            "OPEN_METEO_BASE_URL",
            "https://api.open-meteo.com/v1",
        ),
        map_provider=os.getenv("MAP_PROVIDER", "mapbox"),
        mapbox_base_url=os.getenv("MAPBOX_BASE_URL", "https://api.mapbox.com"),
        mapbox_access_token=os.getenv("MAPBOX_ACCESS_TOKEN", ""),
        activities_provider=os.getenv("ACTIVITIES_PROVIDER", "ai"),
        poi_provider=os.getenv("POI_PROVIDER", "geoapify"),
        geoapify_base_url=os.getenv("GEOAPIFY_BASE_URL", "https://api.geoapify.com/v2"),
        geoapify_api_key=os.getenv("GEOAPIFY_API_KEY", ""),
        events_provider=os.getenv("EVENTS_PROVIDER", "ticketmaster"),
        ticketmaster_base_url=os.getenv(
            "TICKETMASTER_BASE_URL",
            "https://app.ticketmaster.com/discovery/v2",
        ),
        ticketmaster_consumer_key=os.getenv("TICKETMASTER_CONSUMER_KEY", ""),
        ticketmaster_consumer_secret=os.getenv("TICKETMASTER_CONSUMER_SECRET", ""),
        travel_content_provider=os.getenv("TRAVEL_CONTENT_PROVIDER", "wikimedia"),
        wikimedia_travel_base_url=os.getenv(
            "WIKIMEDIA_TRAVEL_BASE_URL",
            "https://api.wikimedia.org/wiki/Travel",
        ),
    )


def get_sqlalchemy_database_url() -> str:
    database_url = get_settings().database_url

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url
