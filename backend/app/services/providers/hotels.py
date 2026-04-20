from datetime import UTC, datetime, time

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.integrations.llm.client import create_chat_model
from app.integrations.rapidapi.client import create_rapidapi_client
from app.schemas.trip_planning import HotelStayDetail, TripConfiguration
from app.services.provider_usage_service import record_provider_usage


XOTELO_PROVIDER_KEY = "xotelo"
XOTELO_PROVIDER_HOST = "xotelo-hotel-prices.p.rapidapi.com"


class LlmHotelSuggestionItem(BaseModel):
    hotel_name: str
    area: str | None = None
    notes: list[str] = Field(default_factory=list)


class LlmHotelSuggestionResponse(BaseModel):
    suggestions: list[LlmHotelSuggestionItem] = Field(default_factory=list, max_length=3)


def enrich_hotels(configuration: TripConfiguration) -> list[HotelStayDetail]:
    if not _can_search_hotels(configuration):
        return []

    try:
        rapidapi_hotels = enrich_hotels_from_xotelo(configuration)
    except Exception:
        rapidapi_hotels = []

    if rapidapi_hotels:
        return rapidapi_hotels

    try:
        return enrich_hotels_from_llm(configuration)
    except Exception:
        return []


def enrich_hotels_from_xotelo(
    configuration: TripConfiguration,
) -> list[HotelStayDetail]:
    settings = get_settings()
    if not settings.rapidapi_key or not configuration.to_location:
        return []

    query = configuration.to_location.strip()
    if not query:
        return []

    with create_rapidapi_client(
        base_url=settings.rapidapi_xotelo_base_url,
        host=XOTELO_PROVIDER_HOST,
    ) as client:
        response = client.get(
            "/api/search",
            params={
                "location_type": "accommodation",
                "query": query,
            },
        )
        succeeded = response.is_success
        record_provider_usage(
            provider_key=XOTELO_PROVIDER_KEY,
            succeeded=succeeded,
            quota_limit=1000,
            last_status=str(response.status_code),
        )
        response.raise_for_status()
        payload = response.json()

    result = payload.get("result") or {}
    hotel_candidates = result.get("list") or []
    if not isinstance(hotel_candidates, list) or not hotel_candidates:
        return []

    return [
        _map_xotelo_hotel(candidate, configuration, index)
        for index, candidate in enumerate(hotel_candidates[:3], start=1)
    ]


def enrich_hotels_from_llm(
    configuration: TripConfiguration,
) -> list[HotelStayDetail]:
    prompt = f"""
You are Wandrix's hotel suggestion fallback.

Generate 3 hotel stay suggestions for the destination and trip profile below.

Rules:
- These are fallback planning suggestions, not live inventory.
- Do not invent exact prices, real-time availability, or fake booking claims.
- Prefer area guidance and stay style over brand-name certainty.
- Keep notes useful, grounded, and short.
- If a well-known hotel is mentioned, it must be plausible for the destination.

Trip configuration:
{configuration.model_dump(mode="json")}
""".strip()

    model = create_chat_model(temperature=0.2)
    structured_model = model.with_structured_output(
        LlmHotelSuggestionResponse,
        method="json_schema",
    )
    response = structured_model.invoke(
        [
            (
                "system",
                "Create hotel stay suggestions for a travel planner using structured output.",
            ),
            ("human", prompt),
        ]
    )

    return [
        HotelStayDetail(
            id=f"llm_hotel_{index}",
            hotel_name=suggestion.hotel_name,
            area=suggestion.area,
            check_in=_to_check_in(configuration),
            check_out=_to_check_out(configuration),
            notes=[
                "AI-suggested stay option used because no cached provider results were available.",
                *suggestion.notes,
            ],
        )
        for index, suggestion in enumerate(response.suggestions[:3], start=1)
    ]


def _map_xotelo_hotel(
    candidate: dict,
    configuration: TripConfiguration,
    index: int,
) -> HotelStayDetail:
    notes = [
        "Cached hotel search result from Xotelo via RapidAPI.",
    ]

    street_address = candidate.get("street_address")
    if isinstance(street_address, str) and street_address.strip():
        notes.append(street_address.strip())

    tripadvisor_url = candidate.get("url")
    if isinstance(tripadvisor_url, str) and tripadvisor_url.strip():
        notes.append(f"TripAdvisor: {tripadvisor_url.strip()}")

    short_place_name = candidate.get("short_place_name")
    if isinstance(short_place_name, str) and short_place_name.strip():
        notes.append(f"Area fit: {short_place_name.strip()}")

    return HotelStayDetail(
        id=f"xotelo_hotel_{candidate.get('location_id') or index}",
        hotel_name=_coerce_text(candidate.get("name"), fallback="Hotel option"),
        area=_coerce_text(candidate.get("place_name")),
        check_in=_to_check_in(configuration),
        check_out=_to_check_out(configuration),
        notes=notes,
    )


def _can_search_hotels(configuration: TripConfiguration) -> bool:
    return bool(configuration.to_location and _has_timing_signal(configuration))


def _has_timing_signal(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )


def _to_check_in(configuration: TripConfiguration) -> datetime | None:
    if not configuration.start_date:
        return None
    return datetime.combine(configuration.start_date, time(hour=15), tzinfo=UTC)


def _to_check_out(configuration: TripConfiguration) -> datetime | None:
    if not configuration.end_date:
        return None
    return datetime.combine(configuration.end_date, time(hour=11), tzinfo=UTC)


def _coerce_text(value: object, *, fallback: str | None = None) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return fallback
