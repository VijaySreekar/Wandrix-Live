from datetime import date

from app.integrations.open_meteo.client import create_open_meteo_client
from app.schemas.trip_planning import TripConfiguration, WeatherDetail
from app.services.providers.location_lookup import (
    Coordinates,
    resolve_destination_coordinates,
)


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


def enrich_weather_from_open_meteo(
    configuration: TripConfiguration,
    coordinates: Coordinates | None = None,
    *,
    timeout: float | None = None,
) -> list[WeatherDetail]:
    if not _can_search_weather(configuration):
        return []

    latitude, longitude = coordinates or resolve_destination_coordinates(
        configuration.to_location or "",
    )
    if latitude is None or longitude is None:
        return []

    query_params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
    }
    query_params.update(_weather_window_params(configuration))

    if timeout is None:
        client_context = create_open_meteo_client()
    else:
        client_context = create_open_meteo_client(timeout=timeout)

    with client_context as client:
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
        high_c = _safe_int(max_temps, index)
        low_c = _safe_int(min_temps, index)
        condition_tags = _condition_tags_for_code(code)
        weather_items.append(
            WeatherDetail(
                id=f"weather_live_{index + 1}",
                day_label=f"Day {index + 1}",
                summary=summary,
                forecast_date=_parse_forecast_date(day_value),
                weather_code=code if isinstance(code, int) else None,
                condition_tags=condition_tags,
                temperature_band=_temperature_band(high_c, low_c),
                weather_risk_level=_weather_risk_level(
                    condition_tags=condition_tags,
                    high_c=high_c,
                    low_c=low_c,
                ),
                high_c=high_c,
                low_c=low_c,
                notes=[
                    f"Forecast date: {day_value}",
                    f"Location: {configuration.to_location}",
                ],
            )
        )

    return weather_items


def _condition_tags_for_code(code: object) -> list[str]:
    if not isinstance(code, int):
        return []
    if code == 0:
        return ["clear"]
    if code in {1, 2}:
        return ["clear", "mild"]
    if code == 3:
        return ["cloudy"]
    if code in {45, 48}:
        return ["fog"]
    if code in {51, 53, 55, 61, 63, 65, 80, 81, 82}:
        tags = ["rain"]
        if code in {65, 82}:
            tags.append("heavy_rain")
        return tags
    if code in {71, 73, 75}:
        return ["snow"]
    if code == 95:
        return ["storm", "rain"]
    return []


def _temperature_band(high_c: int | None, low_c: int | None) -> str | None:
    if high_c is None and low_c is None:
        return None
    if high_c is not None and high_c >= 30:
        return "hot"
    if high_c is not None and high_c >= 24:
        return "warm"
    if low_c is not None and low_c <= 2:
        return "cold"
    if high_c is not None and high_c <= 10:
        return "cool"
    return "mild"


def _weather_risk_level(
    *,
    condition_tags: list[str],
    high_c: int | None,
    low_c: int | None,
) -> str:
    if any(tag in condition_tags for tag in ["storm", "heavy_rain", "snow"]):
        return "high"
    if any(tag in condition_tags for tag in ["rain", "fog"]):
        return "medium"
    if high_c is not None and high_c >= 30:
        return "medium"
    if low_c is not None and low_c <= 2:
        return "medium"
    return "low"


def _parse_forecast_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


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
