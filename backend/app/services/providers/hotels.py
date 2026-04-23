from datetime import UTC, datetime, time

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.integrations.llm.client import create_chat_model
from app.integrations.rapidapi.client import create_rapidapi_client
from app.schemas.trip_planning import HotelStayDetail, TripConfiguration
from app.services.provider_usage_service import record_provider_usage


XOTELO_PROVIDER_KEY = "xotelo"
XOTELO_PROVIDER_HOST = "xotelo-hotel-prices.p.rapidapi.com"
HOTEL_SEARCH_RESULT_LIMIT = 24


class LlmHotelSuggestionItem(BaseModel):
    hotel_name: str
    area: str | None = None
    notes: list[str] = Field(default_factory=list)


class LlmHotelSuggestionResponse(BaseModel):
    suggestions: list[LlmHotelSuggestionItem] = Field(default_factory=list, max_length=12)


def enrich_hotels(configuration: TripConfiguration) -> list[HotelStayDetail]:
    if not _can_search_hotels(configuration):
        return []

    try:
        rapidapi_hotels = enrich_hotels_from_xotelo(configuration)
    except Exception:
        rapidapi_hotels = []

    if rapidapi_hotels:
        if len(rapidapi_hotels) >= 4:
            return rapidapi_hotels
        try:
            llm_hotels = enrich_hotels_from_llm(configuration)
        except Exception:
            llm_hotels = []
        return _merge_hotel_recommendations(rapidapi_hotels, llm_hotels)

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
            _map_xotelo_hotel(client, candidate, configuration, index)
            for index, candidate in enumerate(
                hotel_candidates[:HOTEL_SEARCH_RESULT_LIMIT],
                start=1,
            )
        ]


def enrich_hotels_from_llm(
    configuration: TripConfiguration,
) -> list[HotelStayDetail]:
    prompt = f"""
You are Wandrix's hotel suggestion fallback.

Generate 12 hotel stay suggestions for the destination and trip profile below.

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
        for index, suggestion in enumerate(response.suggestions[:12], start=1)
    ]


def _map_xotelo_hotel(
    client,
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

    rate_snapshot = _fetch_xotelo_rate_snapshot(
        client=client,
        hotel_key=_coerce_text(candidate.get("hotel_key")),
        configuration=configuration,
    )

    return HotelStayDetail(
        id=f"xotelo_hotel_{candidate.get('location_id') or index}",
        hotel_name=_coerce_text(candidate.get("name"), fallback="Hotel option"),
        hotel_key=_coerce_text(candidate.get("hotel_key")),
        area=_derive_hotel_area_label(candidate),
        address=_coerce_text(street_address),
        image_url=_coerce_text(candidate.get("image")),
        source_url=_coerce_text(tripadvisor_url),
        source_label="TripAdvisor" if tripadvisor_url else None,
        nightly_rate_amount=rate_snapshot["rate"],
        nightly_rate_currency=rate_snapshot["currency"],
        nightly_tax_amount=rate_snapshot["tax"],
        rate_provider_name=rate_snapshot["provider"],
        check_in=_to_check_in(configuration),
        check_out=_to_check_out(configuration),
        notes=notes,
    )


def _derive_hotel_area_label(candidate: dict) -> str | None:
    street_address = _coerce_text(candidate.get("street_address"))
    short_place_name = _coerce_text(candidate.get("short_place_name"))
    place_name = _coerce_text(candidate.get("place_name"))

    for value in (street_address, short_place_name, place_name):
        if not value:
            continue
        ward = _extract_ward_label(value)
        if ward:
            return ward

    return short_place_name or place_name


def _extract_ward_label(value: str) -> str | None:
    normalized = " ".join(value.replace("/", " ").split())
    for chunk in [part.strip() for part in normalized.split(",")]:
        lower = chunk.lower()
        if lower.endswith("-ku") or " ward" in lower:
            return chunk
    return None


def _fetch_xotelo_rate_snapshot(
    *,
    client,
    hotel_key: str | None,
    configuration: TripConfiguration,
) -> dict[str, float | str | None]:
    if not hotel_key or not _has_exact_stay_dates(configuration):
        return {
            "rate": None,
            "currency": None,
            "tax": None,
            "provider": None,
        }

    response = client.get(
        "/api/rates",
        params={
            "hotel_key": hotel_key,
            "chk_in": configuration.start_date.isoformat(),
            "chk_out": configuration.end_date.isoformat(),
            "currency": "GBP",
        },
    )
    succeeded = response.is_success
    record_provider_usage(
        provider_key=XOTELO_PROVIDER_KEY,
        succeeded=succeeded,
        quota_limit=1000,
        last_status=str(response.status_code),
    )
    if not succeeded:
        return {
            "rate": None,
            "currency": None,
            "tax": None,
            "provider": None,
        }

    payload = response.json()
    result = payload.get("result") or {}
    rates = result.get("rates") or []
    if not isinstance(rates, list) or not rates:
        return {
            "rate": None,
            "currency": _coerce_text(result.get("currency"), fallback="GBP"),
            "tax": None,
            "provider": None,
        }

    ranked_rates = []
    for item in rates:
        if not isinstance(item, dict):
            continue
        rate_value = _coerce_number(item.get("rate"))
        if rate_value is None:
            continue
        ranked_rates.append(
            {
                "rate": rate_value,
                "currency": _coerce_text(result.get("currency"), fallback="GBP"),
                "tax": _coerce_number(item.get("tax")),
                "provider": _coerce_text(item.get("name")),
            }
        )

    if not ranked_rates:
        return {
            "rate": None,
            "currency": _coerce_text(result.get("currency"), fallback="GBP"),
            "tax": None,
            "provider": None,
        }

    ranked_rates.sort(key=lambda item: item["rate"])
    return ranked_rates[0]


def _can_search_hotels(configuration: TripConfiguration) -> bool:
    return bool(configuration.to_location and _has_timing_signal(configuration))


def _has_timing_signal(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )


def _has_exact_stay_dates(configuration: TripConfiguration) -> bool:
    return bool(configuration.start_date and configuration.end_date)


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


def _coerce_number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        number = float(value)
        if number >= 0:
            return number
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
        if number >= 0:
            return number
    return None


def _merge_hotel_recommendations(
    provider_hotels: list[HotelStayDetail],
    fallback_hotels: list[HotelStayDetail],
) -> list[HotelStayDetail]:
    merged: list[HotelStayDetail] = []
    seen_names: set[str] = set()

    for hotel in [*provider_hotels, *fallback_hotels]:
        normalized_name = hotel.hotel_name.strip().lower()
        if not normalized_name or normalized_name in seen_names:
            continue
        seen_names.add(normalized_name)
        merged.append(hotel)
        if len(merged) >= 12:
            break

    return merged
