from datetime import datetime

from app.core.config import get_settings
from app.integrations.ticketmaster.client import create_ticketmaster_client
from app.schemas.trip_planning import TripConfiguration
from app.services.providers.location_lookup import resolve_destination_coordinates


def enrich_events_from_ticketmaster(
    configuration: TripConfiguration,
) -> list[dict[str, object]]:
    settings = get_settings()
    if not _can_search_events(configuration, settings):
        return []

    params = {
        "apikey": settings.ticketmaster_consumer_key,
        "keyword": _build_keyword(configuration),
        "city": configuration.to_location,
        "size": 6,
        "sort": "date,asc",
    }
    if configuration.start_date:
        params["startDateTime"] = (
            datetime.combine(configuration.start_date, datetime.min.time()).isoformat()
            + "Z"
        )
    if configuration.end_date:
        params["endDateTime"] = (
            datetime.combine(configuration.end_date, datetime.max.time()).isoformat()
            + "Z"
        )

    try:
        with create_ticketmaster_client() as client:
            response = client.get("/events.json", params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return []

    embedded = payload.get("_embedded") or {}
    events = embedded.get("events") or []
    normalized: list[dict[str, object]] = []
    used_ids: set[str] = set()

    for event in events:
        event_id = event.get("id")
        name = event.get("name")
        if not isinstance(event_id, str) or not isinstance(name, str):
            continue
        if event_id in used_ids:
            continue

        venue_label = _extract_venue_label(event)
        venue_name = _extract_venue_name(event)
        timing = _extract_event_timing(event)
        summary = _extract_summary(event, venue_label)
        latitude, longitude = _extract_event_coordinates(
            event,
            configuration=configuration,
            venue_label=venue_label,
        )
        image_url = _extract_event_image_url(event)
        availability_text = _extract_availability_text(event)
        price_text = _extract_price_text(event)
        status_text = _extract_status_text(event)
        normalized.append(
            {
                "id": f"ticketmaster_{event_id}",
                "kind": "event",
                "title": name.strip(),
                "venue_name": venue_name,
                "location_label": venue_label,
                "summary": summary,
                "source_label": "Ticketmaster",
                "source_url": event.get("url"),
                "image_url": image_url,
                "availability_text": availability_text,
                "price_text": price_text,
                "status_text": status_text,
                "latitude": latitude,
                "longitude": longitude,
                "estimated_duration_minutes": _estimate_event_duration_minutes(timing),
                "start_at": timing.get("start_at"),
                "end_at": timing.get("end_at"),
            }
        )
        used_ids.add(event_id)

        if len(normalized) >= 6:
            break

    return normalized


def _can_search_events(configuration: TripConfiguration, settings) -> bool:
    if not configuration.selected_modules.activities:
        return False
    if not configuration.to_location:
        return False
    if not settings.ticketmaster_consumer_key:
        return False
    return bool(configuration.start_date or configuration.end_date or configuration.travel_window)


def _build_keyword(configuration: TripConfiguration) -> str | None:
    if configuration.custom_style and configuration.custom_style.strip():
        return configuration.custom_style.strip()
    if configuration.activity_styles:
        return configuration.activity_styles[0].replace("_", " ")
    return None


def _extract_venue_label(event: dict[str, object]) -> str | None:
    embedded = event.get("_embedded") or {}
    venues = embedded.get("venues") or []
    if not isinstance(venues, list) or not venues:
        return None
    primary = venues[0] or {}
    city = ((primary.get("city") or {}) if isinstance(primary, dict) else {}).get("name")
    venue_name = primary.get("name") if isinstance(primary, dict) else None
    parts = [
        part.strip()
        for part in [venue_name, city]
        if isinstance(part, str) and part.strip()
    ]
    return ", ".join(parts) if parts else None


def _extract_venue_name(event: dict[str, object]) -> str | None:
    embedded = event.get("_embedded") or {}
    venues = embedded.get("venues") or []
    if not isinstance(venues, list) or not venues:
        return None
    primary = venues[0] or {}
    venue_name = primary.get("name") if isinstance(primary, dict) else None
    return venue_name.strip() if isinstance(venue_name, str) and venue_name.strip() else None


def _extract_event_timing(event: dict[str, object]) -> dict[str, datetime | None]:
    dates = event.get("dates") or {}
    start = dates.get("start") if isinstance(dates, dict) else {}
    end = dates.get("end") if isinstance(dates, dict) else {}
    if not isinstance(start, dict):
        start = {}
    if not isinstance(end, dict):
        end = {}
    return {
        "start_at": _parse_event_datetime(start.get("dateTime")),
        "end_at": _parse_event_datetime(end.get("dateTime")),
    }


def _extract_event_coordinates(
    event: dict[str, object],
    *,
    configuration: TripConfiguration,
    venue_label: str | None,
) -> tuple[float | None, float | None]:
    embedded = event.get("_embedded") or {}
    venues = embedded.get("venues") or []
    if isinstance(venues, list) and venues:
        primary = venues[0] or {}
        location = primary.get("location") if isinstance(primary, dict) else None
        if isinstance(location, dict):
            longitude = _parse_coordinate(location.get("longitude"))
            latitude = _parse_coordinate(location.get("latitude"))
            if latitude is not None and longitude is not None:
                return latitude, longitude

    search_query_parts = [
        part.strip()
        for part in [venue_label, configuration.to_location]
        if isinstance(part, str) and part.strip()
    ]
    if not search_query_parts:
        return None, None

    try:
        return resolve_destination_coordinates(", ".join(dict.fromkeys(search_query_parts)))
    except Exception:
        return None, None


def _parse_coordinate(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _parse_event_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _estimate_event_duration_minutes(timing: dict[str, datetime | None]) -> int:
    start_at = timing.get("start_at")
    end_at = timing.get("end_at")
    if start_at and end_at:
        duration_minutes = int((end_at - start_at).total_seconds() // 60)
        if duration_minutes >= 30:
            return min(duration_minutes, 240)
    return 120


def _extract_event_image_url(event: dict[str, object]) -> str | None:
    images = event.get("images") or []
    if not isinstance(images, list):
        return None
    scored: list[tuple[int, str]] = []
    for image in images:
        if not isinstance(image, dict):
            continue
        image_url = image.get("url")
        if not isinstance(image_url, str) or not image_url.strip():
            continue
        ratio = image.get("ratio")
        width = image.get("width")
        score = 0
        if ratio == "16_9":
            score += 3
        if isinstance(width, int):
            score += min(width, 2000) // 400
        scored.append((score, image_url.strip()))
    if not scored:
        return None
    return max(scored, key=lambda item: item[0])[1]


def _extract_availability_text(event: dict[str, object]) -> str | None:
    sales = event.get("sales") or {}
    public_sales = sales.get("public") if isinstance(sales, dict) else None
    if isinstance(public_sales, dict):
        start = _parse_event_datetime(public_sales.get("startDateTime"))
        end = _parse_event_datetime(public_sales.get("endDateTime"))
        if start and end:
            return f"Public sale window: {start.strftime('%d %b')} to {end.strftime('%d %b')}."
        if start:
            return f"Public sale started {start.strftime('%d %b')}."
    return None


def _extract_price_text(event: dict[str, object]) -> str | None:
    ranges = event.get("priceRanges") or []
    if not isinstance(ranges, list) or not ranges:
        return None
    primary = ranges[0] or {}
    if not isinstance(primary, dict):
        return None
    minimum = primary.get("min")
    maximum = primary.get("max")
    currency = primary.get("currency")
    if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)):
        if isinstance(currency, str) and currency.strip():
            return f"{currency.strip()} {minimum:.0f}-{maximum:.0f}"
        return f"{minimum:.0f}-{maximum:.0f}"
    return None


def _extract_status_text(event: dict[str, object]) -> str | None:
    dates = event.get("dates") or {}
    status = dates.get("status") if isinstance(dates, dict) else None
    if not isinstance(status, dict):
        return None
    status_code = status.get("code")
    status_name = status.get("name")
    if isinstance(status_name, str) and status_name.strip():
        return status_name.strip()
    if isinstance(status_code, str) and status_code.strip():
        return status_code.replace("_", " ").title()
    return None


def _extract_summary(event: dict[str, object], venue_label: str | None) -> str | None:
    classifications = event.get("classifications") or []
    segment_name = None
    genre_name = None
    if isinstance(classifications, list) and classifications:
        primary = classifications[0] or {}
        if isinstance(primary, dict):
            segment = primary.get("segment") or {}
            genre = primary.get("genre") or {}
            segment_name = segment.get("name") if isinstance(segment, dict) else None
            genre_name = genre.get("name") if isinstance(genre, dict) else None

    summary_parts = [
        part.strip()
        for part in [segment_name, genre_name, venue_label]
        if isinstance(part, str) and part.strip()
    ]
    if not summary_parts:
        return None
    return " | ".join(summary_parts[:3])
