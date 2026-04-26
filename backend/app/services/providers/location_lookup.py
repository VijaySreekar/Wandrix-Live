from app.core.config import get_settings
from app.integrations.mapbox.client import create_mapbox_client


Coordinates = tuple[float | None, float | None]


def resolve_destination_coordinates(
    location_name: str,
    *,
    timeout: float | None = None,
) -> Coordinates:
    settings = get_settings()
    with create_mapbox_client(timeout=timeout) as client:
        response = client.get(
            "/search/geocode/v6/forward",
            params={
                "q": location_name,
                "limit": 1,
                "access_token": settings.mapbox_access_token,
            },
        )
        response.raise_for_status()
        payload = response.json()

    features = payload.get("features") or []
    if not features:
        return None, None

    first_feature = features[0]
    coordinates = (first_feature.get("geometry") or {}).get("coordinates") or []
    if len(coordinates) < 2:
        return None, None

    longitude = coordinates[0]
    latitude = coordinates[1]
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None, None

    return float(latitude), float(longitude)


def reverse_geocode_coordinates(*, latitude: float, longitude: float) -> dict[str, str | None]:
    settings = get_settings()
    with create_mapbox_client() as client:
        response = client.get(
            "/search/geocode/v6/reverse",
            params={
                "longitude": longitude,
                "latitude": latitude,
                "limit": 1,
                "access_token": settings.mapbox_access_token,
            },
        )
        response.raise_for_status()
        payload = response.json()

    features = payload.get("features") or []
    if not features:
        return {"city": None, "region": None, "country": None, "summary": None}

    feature = features[0]
    properties = feature.get("properties") or {}
    context = properties.get("context") or {}
    city = _read_context_value(context, "place") or properties.get("name")
    region = _read_context_value(context, "region")
    country = _read_context_value(context, "country")

    summary = ", ".join(
        dict.fromkeys([part for part in [city, region, country] if isinstance(part, str) and part])
    )

    return {
        "city": city if isinstance(city, str) else None,
        "region": region if isinstance(region, str) else None,
        "country": country if isinstance(country, str) else None,
        "summary": summary or None,
    }


def _read_context_value(context: dict, key: str) -> str | None:
    entry = context.get(key) or {}
    name = entry.get("name") if isinstance(entry, dict) else None
    return name if isinstance(name, str) else None
