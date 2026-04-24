from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from app.core.config import get_settings
from app.integrations.mapbox.client import create_mapbox_client


@dataclass(frozen=True)
class MovementEstimate:
    minutes: int
    distance_meters: int
    source: str


def estimate_travel_duration_minutes(
    *,
    origin_latitude: float | None,
    origin_longitude: float | None,
    destination_latitude: float | None,
    destination_longitude: float | None,
) -> MovementEstimate | None:
    if None in {
        origin_latitude,
        origin_longitude,
        destination_latitude,
        destination_longitude,
    }:
        return None

    fallback = _heuristic_estimate(
        origin_latitude=float(origin_latitude),
        origin_longitude=float(origin_longitude),
        destination_latitude=float(destination_latitude),
        destination_longitude=float(destination_longitude),
    )

    settings = get_settings()
    if not settings.mapbox_access_token:
        return fallback

    try:
        with create_mapbox_client() as client:
            response = client.get(
                (
                    "/directions/v5/mapbox/walking/"
                    f"{origin_longitude},{origin_latitude};"
                    f"{destination_longitude},{destination_latitude}"
                ),
                params={
                    "access_token": settings.mapbox_access_token,
                    "alternatives": "false",
                    "geometries": "geojson",
                    "overview": "false",
                    "steps": "false",
                },
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return fallback

    routes = payload.get("routes") or []
    if not isinstance(routes, list) or not routes:
        return fallback

    first_route = routes[0] or {}
    duration_seconds = first_route.get("duration")
    distance_meters = first_route.get("distance")
    if not isinstance(duration_seconds, (int, float)):
        return fallback

    return MovementEstimate(
        minutes=max(5, int(round(float(duration_seconds) / 60.0))),
        distance_meters=(
            int(round(float(distance_meters)))
            if isinstance(distance_meters, (int, float))
            else fallback.distance_meters
        ),
        source="mapbox",
    )


def _heuristic_estimate(
    *,
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> MovementEstimate:
    distance_km = _haversine_km(
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
    )
    buffered_distance_km = max(distance_km * 1.25, 0.2)
    minutes = max(8, int(round((buffered_distance_km / 4.5) * 60.0)))
    return MovementEstimate(
        minutes=minutes,
        distance_meters=int(round(distance_km * 1000.0)),
        source="heuristic",
    )


def _haversine_km(
    *,
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    radius_km = 6371.0
    lat1 = radians(origin_latitude)
    lon1 = radians(origin_longitude)
    lat2 = radians(destination_latitude)
    lon2 = radians(destination_longitude)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    haversine = (
        sin(delta_lat / 2.0) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2.0) ** 2
    )
    return 2.0 * radius_km * asin(sqrt(haversine))
