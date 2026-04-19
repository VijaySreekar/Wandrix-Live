from app.core.config import get_settings
from app.integrations.mapbox.client import create_mapbox_client
from app.integrations.open_meteo.client import create_open_meteo_client
from app.schemas.trip_planning import TripConfiguration, WeatherDetail


WMO_WEATHER_LABELS = {
    0: "Clear skies expected.",
    1: "Mostly clear conditions.",
    2: "Partly cloudy conditions.",
    3: "Overcast skies likely.",
    45: "Foggy conditions expected.",
    48: "Fog and frost possible.",
    51: "Light drizzle possible.",
    53: "Moderate drizzle possible.",
    55: "Dense drizzle expected.",
    61: "Light rain possible.",
    63: "Rain likely during part of the day.",
    65: "Heavy rain risk in the forecast.",
    71: "Light snowfall possible.",
    73: "Snow showers possible.",
    75: "Heavy snowfall risk in the forecast.",
    80: "Light showers expected.",
    81: "Showers likely during the day.",
    82: "Heavy showers likely during the day.",
    95: "Thunderstorm risk in the forecast.",
}


def enrich_weather_from_open_meteo(configuration: TripConfiguration) -> list[WeatherDetail]:
    if not _can_search_weather(configuration):
        return []

    latitude, longitude = _resolve_coordinates(configuration.to_location or "")
    if latitude is None or longitude is None:
        return []

    query_params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
    }
    query_params.update(_weather_window_params(configuration))

    with create_open_meteo_client() as client:
        response = client.get("/forecast", params=query_params)
        response.raise_for_status()
        payload = response.json()

    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []

    weather_items: list[WeatherDetail] = []
    for index, day_value in enumerate(dates):
        code = codes[index] if index < len(codes) else None
        summary = WMO_WEATHER_LABELS.get(code, "Forecast available for this day.")
        weather_items.append(
            WeatherDetail(
                id=f"weather_live_{index + 1}",
                day_label=f"Day {index + 1}",
                summary=summary,
                high_c=_safe_int(max_temps, index),
                low_c=_safe_int(min_temps, index),
                notes=[
                    f"Forecast date: {day_value}",
                    f"Location: {configuration.to_location}",
                ],
            )
        )

    return weather_items


def _resolve_coordinates(location_name: str) -> tuple[float | None, float | None]:
    settings = get_settings()
    with create_mapbox_client() as client:
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


def _can_search_weather(configuration: TripConfiguration) -> bool:
    return bool(configuration.selected_modules.weather and configuration.to_location)


def _safe_int(values: list, index: int) -> int | None:
    if index >= len(values):
        return None

    value = values[index]
    if isinstance(value, (int, float)):
        return int(round(value))

    return None


def _weather_window_params(configuration: TripConfiguration) -> dict[str, object]:
    if configuration.start_date and configuration.end_date:
        return {
            "start_date": configuration.start_date.isoformat(),
            "end_date": configuration.end_date.isoformat(),
        }

    return {
        "forecast_days": 4,
    }
