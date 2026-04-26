from app.core.config import get_settings
from app.integrations.mapbox.client import create_mapbox_client
from app.schemas.location_search import (
    LocationSearchKind,
    LocationSearchResponse,
    LocationSearchSuggestion,
)


MAPBOX_ALLOWED_TYPES = "place,locality,district,region,country"


def search_locations(*, query: str, kind: LocationSearchKind) -> LocationSearchResponse:
    normalized_query = query.strip()
    if len(normalized_query) < 2:
        return LocationSearchResponse(items=[])

    settings = get_settings()
    with create_mapbox_client() as client:
        response = client.get(
            "/search/geocode/v6/forward",
            params={
                "q": normalized_query,
                "limit": 6,
                "types": MAPBOX_ALLOWED_TYPES,
                "autocomplete": "true",
                "language": "en",
                "access_token": settings.mapbox_access_token,
            },
        )
        response.raise_for_status()
        payload = response.json()

    features = payload.get("features") or []
    suggestions: list[LocationSearchSuggestion] = []
    seen: set[str] = set()

    for feature in features:
        suggestion = _normalize_feature(feature, kind)
        if suggestion is None:
            continue

        dedupe_key = suggestion.label.strip().lower()
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        suggestions.append(suggestion)

    return LocationSearchResponse(items=suggestions)


def _normalize_feature(
    feature: dict,
    kind: LocationSearchKind,
) -> LocationSearchSuggestion | None:
    properties = feature.get("properties") or {}
    name = properties.get("name")

    if not isinstance(name, str) or not name.strip():
        return None

    context = properties.get("context") or {}
    place = _read_context_name(context, "place")
    region = _read_context_name(context, "region")
    country = _read_context_name(context, "country")

    label = (place or name).strip()
    detail_parts = [
        part
        for part in [region, country]
        if isinstance(part, str) and part.strip() and part.strip().lower() != label.lower()
    ]
    detail = ", ".join(dict.fromkeys(detail_parts)) or None

    mapbox_id = feature.get("id")
    identifier = (
        mapbox_id
        if isinstance(mapbox_id, str) and mapbox_id.strip()
        else f"{kind}:{label.lower()}"
    )

    return LocationSearchSuggestion(
        id=identifier,
        label=label,
        detail=detail,
    )


def _read_context_name(context: dict, key: str) -> str | None:
    entry = context.get(key) or {}
    name = entry.get("name") if isinstance(entry, dict) else None
    return name if isinstance(name, str) and name.strip() else None
