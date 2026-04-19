from datetime import datetime, timezone
from uuid import uuid4

from app.graph.planner.turn_models import ProposedTimelineItem
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TimelineItem,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services.providers.activities import enrich_activities_from_geoapify
from app.services.providers.flights import enrich_flights_from_amadeus
from app.services.providers.weather import enrich_weather_from_open_meteo


def build_module_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    return TripModuleOutputs(
        flights=_build_flight_outputs(configuration, existing_module_outputs),
        hotels=_build_hotel_outputs(configuration, existing_module_outputs),
        weather=_build_weather_outputs(configuration, existing_module_outputs),
        activities=_build_activity_outputs(configuration, existing_module_outputs),
    )


def build_timeline(
    *,
    configuration: TripConfiguration,
    llm_preview: list[ProposedTimelineItem],
    module_outputs: TripModuleOutputs,
) -> list[TimelineItem]:
    preview_items = [_to_timeline_item(item) for item in llm_preview]
    derived_items = _build_derived_timeline(configuration, module_outputs)
    return _merge_timeline_items(preview_items, derived_items)[:10]


def has_any_module_output(module_outputs: TripModuleOutputs) -> bool:
    return any(
        [
            module_outputs.flights,
            module_outputs.hotels,
            module_outputs.weather,
            module_outputs.activities,
        ]
    )


def _has_timing_signal(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )


def _build_flight_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[FlightDetail]:
    if not configuration.selected_modules.flights:
        return []
    if not (
        configuration.from_location
        and configuration.to_location
        and _has_timing_signal(configuration)
    ):
        return existing_module_outputs.flights
    try:
        live_flights = enrich_flights_from_amadeus(configuration)
    except Exception:
        live_flights = []
    return live_flights or existing_module_outputs.flights


def _build_hotel_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[HotelStayDetail]:
    if not configuration.selected_modules.hotels:
        return []
    if not (configuration.to_location and _has_timing_signal(configuration)):
        return existing_module_outputs.hotels
    return existing_module_outputs.hotels


def _build_weather_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[WeatherDetail]:
    if not configuration.selected_modules.weather:
        return []
    if not (configuration.to_location and _has_timing_signal(configuration)):
        return existing_module_outputs.weather
    try:
        live_weather = enrich_weather_from_open_meteo(configuration)
    except Exception:
        live_weather = []
    return live_weather or existing_module_outputs.weather


def _build_activity_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[ActivityDetail]:
    if not configuration.selected_modules.activities:
        return []
    if not (configuration.to_location and _has_timing_signal(configuration)):
        return existing_module_outputs.activities
    try:
        live_activities = enrich_activities_from_geoapify(configuration)
    except Exception:
        live_activities = []
    return live_activities or existing_module_outputs.activities


def _build_derived_timeline(
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> list[TimelineItem]:
    timeline: list[TimelineItem] = []

    for flight in module_outputs.flights:
        timeline.append(
            TimelineItem(
                id=f"timeline_{flight.id}",
                type="flight",
                title="Outbound flight" if flight.direction == "outbound" else "Return flight",
                day_label=_day_label_for_datetime(flight.departure_time, configuration),
                start_at=flight.departure_time,
                end_at=flight.arrival_time,
                location_label=f"{flight.departure_airport} to {flight.arrival_airport}",
                summary=flight.duration_text,
                details=flight.notes,
                source_module="flights",
            )
        )

    for hotel in module_outputs.hotels:
        timeline.append(
            TimelineItem(
                id=f"timeline_{hotel.id}",
                type="hotel",
                title=hotel.hotel_name,
                day_label=_day_label_for_datetime(hotel.check_in, configuration),
                start_at=hotel.check_in,
                end_at=hotel.check_out,
                location_label=hotel.area,
                summary="Recommended stay window",
                details=hotel.notes,
                source_module="hotels",
            )
        )

    for activity in module_outputs.activities:
        timeline.append(
            TimelineItem(
                id=f"timeline_{activity.id}",
                type="activity",
                title=activity.title,
                day_label=activity.day_label,
                location_label=configuration.to_location,
                summary=activity.notes[0] if activity.notes else None,
                details=activity.notes,
                source_module="activities",
            )
        )

    for weather in module_outputs.weather:
        timeline.append(
            TimelineItem(
                id=f"timeline_{weather.id}",
                type="weather",
                title="Weather pacing note",
                day_label=weather.day_label,
                location_label=configuration.to_location,
                summary=weather.summary,
                details=weather.notes,
                source_module="weather",
            )
        )

    timeline.sort(
        key=lambda item: (
            item.start_at or datetime.max.replace(tzinfo=timezone.utc),
            item.day_label or "Day 99",
        )
    )
    return timeline


def _merge_timeline_items(
    preview_items: list[TimelineItem],
    derived_items: list[TimelineItem],
) -> list[TimelineItem]:
    seen_keys: set[tuple[str, str | None, str | None]] = set()
    merged_items: list[TimelineItem] = []

    for item in [*preview_items, *derived_items]:
        key = (item.title.lower(), item.day_label, item.source_module)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged_items.append(item)

    return merged_items


def _to_timeline_item(item: ProposedTimelineItem) -> TimelineItem:
    return TimelineItem(
        id=f"tl_{uuid4().hex[:10]}",
        type=item.type,
        title=item.title,
        day_label=item.day_label,
        location_label=item.location_label,
        summary=item.summary,
        details=item.details,
        source_module=item.source_module,
    )


def _day_label_for_datetime(
    value: datetime | None,
    configuration: TripConfiguration,
) -> str | None:
    if value is None or configuration.start_date is None:
        return None

    offset = (value.date() - configuration.start_date).days + 1
    return f"Day {max(offset, 1)}"
