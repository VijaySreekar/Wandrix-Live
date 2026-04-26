import os
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
from typing import Final

from dotenv import load_dotenv


ROOT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV_PATH, override=False)

LOCAL_FRONTEND_ORIGIN: Final = "http://127.0.0.1:3000"
PRODUCTION_ENVIRONMENTS: Final = {"production", "prod"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_description: str
    app_version: str
    environment: str
    api_v1_prefix: str
    frontend_origin: str
    frontend_origins: tuple[str, ...]
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str | None
    codex_lb_base_url: str
    codex_lb_api_key: str
    openai_model: str
    quick_plan_model: str
    quick_plan_reasoning_effort: str
    quick_plan_stage_one_only: bool
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
    hotel_provider: str
    rapidapi_key: str | None
    rapidapi_xotelo_base_url: str
    rapidapi_agoda_base_url: str
    rapidapi_hotels_com_base_url: str
    rapidapi_travel_advisor_base_url: str
    events_provider: str
    ticketmaster_base_url: str
    ticketmaster_consumer_key: str
    ticketmaster_consumer_secret: str
    travel_content_provider: str
    wikimedia_travel_base_url: str
    travelpayouts_base_url: str
    travelpayouts_api_token: str | None


@lru_cache
def get_settings() -> Settings:
    environment = _get_environment()
    frontend_origins = _get_frontend_origins(environment)
    amadeus_env = os.getenv("AMADEUS_ENV", "test")
    amadeus_base_url = (
        "https://api.amadeus.com"
        if amadeus_env == "production"
        else "https://test.api.amadeus.com"
    )

    settings = Settings(
        app_name="Wandrix API",
        app_description="FastAPI backend for the Wandrix conversation-first travel planner.",
        app_version="0.1.0",
        environment=environment,
        api_v1_prefix="/api/v1",
        frontend_origin=frontend_origins[0],
        frontend_origins=frontend_origins,
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
        quick_plan_model=os.getenv("QUICK_PLAN_MODEL", "gpt-5.5"),
        quick_plan_reasoning_effort=os.getenv(
            "QUICK_PLAN_REASONING_EFFORT",
            "medium",
        ),
        quick_plan_stage_one_only=os.getenv(
            "QUICK_PLAN_STAGE_ONE_ONLY",
            "true",
        ).lower()
        in {"1", "true", "yes", "on"},
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
        hotel_provider=os.getenv("HOTEL_PROVIDER", "xotelo"),
        rapidapi_key=os.getenv("RAPIDAPI_KEY") or None,
        rapidapi_xotelo_base_url=os.getenv(
            "RAPIDAPI_XOTELO_BASE_URL",
            "https://xotelo-hotel-prices.p.rapidapi.com",
        ),
        rapidapi_agoda_base_url=os.getenv(
            "RAPIDAPI_AGODA_BASE_URL",
            "https://agoda-com.p.rapidapi.com",
        ),
        rapidapi_hotels_com_base_url=os.getenv(
            "RAPIDAPI_HOTELS_COM_BASE_URL",
            "https://hotels-com6.p.rapidapi.com",
        ),
        rapidapi_travel_advisor_base_url=os.getenv(
            "RAPIDAPI_TRAVEL_ADVISOR_BASE_URL",
            "https://travel-advisor.p.rapidapi.com",
        ),
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
        travelpayouts_base_url=os.getenv(
            "TRAVELPAYOUTS_BASE_URL",
            "https://api.travelpayouts.com",
        ),
        travelpayouts_api_token=os.getenv("TRAVELPAYOUTS_API_TOKEN") or None,
    )

    _validate_production_settings(settings)

    return settings


def _get_environment() -> str:
    return (
        os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or "development"
    ).strip().lower()


def _get_frontend_origins(environment: str) -> tuple[str, ...]:
    configured_origins = os.getenv("FRONTEND_ORIGINS") or os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:3000",
    ) or "http://localhost:3000"
    origins = _parse_csv(configured_origins)

    if environment not in PRODUCTION_ENVIRONMENTS:
        origins.append(LOCAL_FRONTEND_ORIGIN)

    deduped: list[str] = []
    for origin in origins:
        normalized_origin = origin.rstrip("/")
        if normalized_origin and normalized_origin not in deduped:
            deduped.append(normalized_origin)

    return tuple(deduped)


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _validate_production_settings(settings: Settings) -> None:
    if settings.environment not in PRODUCTION_ENVIRONMENTS:
        return

    required_values = {
        "FRONTEND_ORIGINS": ",".join(settings.frontend_origins),
        "DATABASE_URL": settings.database_url,
        "SUPABASE_URL": settings.supabase_url,
        "SUPABASE_PUBLISHABLE_KEY": settings.supabase_publishable_key,
        "SUPABASE_SECRET_KEY": settings.supabase_secret_key or "",
        "CODEX_LB_BASE_URL": settings.codex_lb_base_url,
        "CODEX_LB_API_KEY": settings.codex_lb_api_key,
    }
    invalid_names = [
        name
        for name, value in required_values.items()
        if _is_missing_or_placeholder(value)
    ]

    if invalid_names:
        missing = ", ".join(sorted(invalid_names))
        raise RuntimeError(
            f"Production backend configuration is incomplete: {missing}."
        )


def _is_missing_or_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True

    placeholder_markers = (
        "your-",
        "your_",
        "example.com",
        "localhost",
        "127.0.0.1",
    )
    return any(marker in normalized for marker in placeholder_markers)


def get_sqlalchemy_database_url() -> str:
    database_url = get_settings().database_url

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url
