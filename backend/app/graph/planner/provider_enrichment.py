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
from app.services.providers.flights import enrich_flights
from app.services.providers.hotels import enrich_hotels
from app.services.providers.location_lookup import (
    Coordinates,
    resolve_destination_coordinates,
)
from app.services.providers.weather import enrich_weather_from_open_meteo


def build_module_outputs(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
) -> TripModuleOutputs:
    shared_destination_coordinates = _resolve_shared_destination_coordinates(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules=allowed_modules,
    )

    return TripModuleOutputs(
        flights=_build_flight_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            allowed_modules=allowed_modules,
        ),
        hotels=_build_hotel_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            allowed_modules=allowed_modules,
        ),
        weather=_build_weather_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            shared_destination_coordinates,
            allowed_modules=allowed_modules,
        ),
        activities=_build_activity_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            shared_destination_coordinates,
            allowed_modules=allowed_modules,
        ),
    )


def build_timeline(
    *,
    configuration: TripConfiguration,
    llm_preview: list[ProposedTimelineItem],
    module_outputs: TripModuleOutputs,
    include_derived_when_preview_present: bool = True,
) -> list[TimelineItem]:
    preview_items = _refine_preview_timeline(
        [_to_timeline_item(item) for item in llm_preview],
        configuration=configuration,
        module_outputs=module_outputs,
    )
    derived_items = _build_derived_timeline(configuration, module_outputs)
    if preview_items and not include_derived_when_preview_present:
        return _merge_timeline_items(preview_items, derived_items)[:12]
    return _merge_timeline_items(preview_items, derived_items)[:12]


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
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
) -> list[FlightDetail]:
    if not configuration.selected_modules.flights:
        return []
    if allowed_modules is not None and "flights" not in allowed_modules:
        return existing_module_outputs.flights
    current_ready = _is_flight_search_ready(configuration)
    previous_ready = _is_flight_search_ready(previous_configuration)

    if not current_ready:
        return existing_module_outputs.flights
    if (
        previous_ready
        and existing_module_outputs.flights
        and not _did_flight_inputs_change(
            previous_configuration,
            configuration,
        )
    ):
        return existing_module_outputs.flights
    try:
        live_flights = enrich_flights(configuration)
    except Exception:
        live_flights = []
    return live_flights or existing_module_outputs.flights


def _build_hotel_outputs(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
) -> list[HotelStayDetail]:
    if not configuration.selected_modules.hotels:
        return []
    if allowed_modules is not None and "hotels" not in allowed_modules:
        return existing_module_outputs.hotels
    if not _is_hotel_search_ready(configuration):
        return existing_module_outputs.hotels
    if (
        _is_hotel_search_ready(previous_configuration)
        and existing_module_outputs.hotels
        and _hotel_outputs_are_rich_enough(
            existing_module_outputs.hotels,
            configuration=configuration,
        )
        and not _did_hotel_inputs_change(
            previous_configuration,
            configuration,
        )
    ):
        return existing_module_outputs.hotels
    try:
        live_hotels = enrich_hotels(configuration)
    except Exception:
        live_hotels = []
    return live_hotels or existing_module_outputs.hotels


def _hotel_outputs_are_rich_enough(
    hotels: list[HotelStayDetail],
    *,
    configuration: TripConfiguration,
) -> bool:
    if not hotels:
        return False

    # Older caches were often only the first 4 provider results. Refresh those
    # into the deeper hotel workspace rather than freezing a thin shortlist.
    if len(hotels) < 6:
        return False

    # Older cached hotel outputs only carried names and notes, which now
    # produce weak board cards with random fallback imagery and no pricing.
    # Refresh those caches even when the trip inputs have not changed.
    has_any_hotel_image = any(bool(hotel.image_url) for hotel in hotels)
    if not has_any_hotel_image:
        return False

    if configuration.start_date and configuration.end_date:
        has_any_live_rate = any(
            hotel.nightly_rate_amount is not None for hotel in hotels
        )
        if not has_any_live_rate:
            return False

    return True


def _build_weather_outputs(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    shared_destination_coordinates: Coordinates | None,
    allowed_modules: set[str] | None = None,
) -> list[WeatherDetail]:
    if not configuration.selected_modules.weather:
        return []
    if allowed_modules is not None and "weather" not in allowed_modules:
        return existing_module_outputs.weather
    current_ready = _is_weather_search_ready(configuration)
    previous_ready = _is_weather_search_ready(previous_configuration)

    if not current_ready:
        return existing_module_outputs.weather
    if (
        previous_ready
        and existing_module_outputs.weather
        and not _did_weather_inputs_change(
            previous_configuration,
            configuration,
        )
    ):
        return existing_module_outputs.weather
    try:
        live_weather = enrich_weather_from_open_meteo(
            configuration,
            shared_destination_coordinates,
        )
    except Exception:
        live_weather = []
    return live_weather or existing_module_outputs.weather


def _build_activity_outputs(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    shared_destination_coordinates: Coordinates | None,
    allowed_modules: set[str] | None = None,
) -> list[ActivityDetail]:
    if not configuration.selected_modules.activities:
        return []
    if allowed_modules is not None and "activities" not in allowed_modules:
        return existing_module_outputs.activities
    current_ready = _is_activity_search_ready(configuration)
    previous_ready = _is_activity_search_ready(previous_configuration)

    if not current_ready:
        return existing_module_outputs.activities
    if (
        previous_ready
        and existing_module_outputs.activities
        and not _did_activity_inputs_change(
            previous_configuration,
            configuration,
        )
    ):
        return existing_module_outputs.activities
    try:
        live_activities = enrich_activities_from_geoapify(
            configuration,
            shared_destination_coordinates,
        )
    except Exception:
        live_activities = []
    return live_activities or existing_module_outputs.activities


def _resolve_shared_destination_coordinates(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
) -> Coordinates | None:
    weather_needs_refresh = (
        configuration.selected_modules.weather
        and (allowed_modules is None or "weather" in allowed_modules)
        and _is_weather_search_ready(configuration)
        and (
            not _is_weather_search_ready(previous_configuration)
            or _did_weather_inputs_change(previous_configuration, configuration)
            or not existing_module_outputs.weather
        )
    )
    activity_needs_refresh = (
        configuration.selected_modules.activities
        and (allowed_modules is None or "activities" in allowed_modules)
        and _is_activity_search_ready(configuration)
        and (
            not _is_activity_search_ready(previous_configuration)
            or _did_activity_inputs_change(previous_configuration, configuration)
            or not existing_module_outputs.activities
        )
    )

    if not (weather_needs_refresh or activity_needs_refresh):
        return None

    if not configuration.to_location:
        return None

    try:
        return resolve_destination_coordinates(configuration.to_location)
    except Exception:
        return None


def _is_flight_search_ready(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.from_location
        and configuration.to_location
        and _has_timing_signal(configuration)
    )


def _is_hotel_search_ready(configuration: TripConfiguration) -> bool:
    return bool(configuration.to_location and _has_timing_signal(configuration))


def _is_weather_search_ready(configuration: TripConfiguration) -> bool:
    return bool(configuration.to_location and _has_timing_signal(configuration))


def _is_activity_search_ready(configuration: TripConfiguration) -> bool:
    return bool(configuration.to_location and _has_timing_signal(configuration))


def _did_flight_inputs_change(
    previous_configuration: TripConfiguration,
    configuration: TripConfiguration,
) -> bool:
    return (
        previous_configuration.from_location != configuration.from_location
        or previous_configuration.to_location != configuration.to_location
        or previous_configuration.start_date != configuration.start_date
        or previous_configuration.end_date != configuration.end_date
        or previous_configuration.travel_window != configuration.travel_window
        or previous_configuration.trip_length != configuration.trip_length
    )


def _did_hotel_inputs_change(
    previous_configuration: TripConfiguration,
    configuration: TripConfiguration,
) -> bool:
    return (
        previous_configuration.to_location != configuration.to_location
        or previous_configuration.start_date != configuration.start_date
        or previous_configuration.end_date != configuration.end_date
        or previous_configuration.travel_window != configuration.travel_window
        or previous_configuration.trip_length != configuration.trip_length
    )


def _did_weather_inputs_change(
    previous_configuration: TripConfiguration,
    configuration: TripConfiguration,
) -> bool:
    return (
        previous_configuration.to_location != configuration.to_location
        or previous_configuration.start_date != configuration.start_date
        or previous_configuration.end_date != configuration.end_date
        or previous_configuration.travel_window != configuration.travel_window
        or previous_configuration.trip_length != configuration.trip_length
    )


def _did_activity_inputs_change(
    previous_configuration: TripConfiguration,
    configuration: TripConfiguration,
) -> bool:
    return (
        previous_configuration.to_location != configuration.to_location
        or previous_configuration.start_date != configuration.start_date
        or previous_configuration.end_date != configuration.end_date
        or previous_configuration.travel_window != configuration.travel_window
        or previous_configuration.trip_length != configuration.trip_length
        or previous_configuration.activity_styles != configuration.activity_styles
    )


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

    prioritized_derived = [
        item
        for item in derived_items
        if item.type in {"flight", "hotel"}
    ]
    remaining_derived = [
        item
        for item in derived_items
        if item.type not in {"flight", "hotel"}
    ]

    for item in [*prioritized_derived, *preview_items, *remaining_derived]:
        key = (item.title.lower(), item.day_label, item.source_module)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged_items.append(item)

    return merged_items


def _refine_preview_timeline(
    preview_items: list[TimelineItem],
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> list[TimelineItem]:
    if not preview_items:
        return []

    provider_anchors = _build_derived_timeline(configuration, module_outputs)
    refined: list[TimelineItem] = []
    seen_generic_keys: set[tuple[str, str | None]] = set()

    for item in preview_items:
        if _preview_item_conflicts_with_provider_anchor(item, provider_anchors):
            continue

        generic_key = _generic_preview_key(item)
        if generic_key is not None:
            if generic_key in seen_generic_keys:
                continue
            seen_generic_keys.add(generic_key)

        refined.append(item)

    return refined


def _to_timeline_item(item: ProposedTimelineItem) -> TimelineItem:
    return TimelineItem(
        id=f"tl_{uuid4().hex[:10]}",
        type=item.type,
        title=item.title,
        day_label=item.day_label,
        start_at=item.start_at,
        end_at=item.end_at,
        location_label=item.location_label,
        summary=item.summary,
        details=item.details,
        source_module=item.source_module,
    )


def _preview_item_conflicts_with_provider_anchor(
    preview_item: TimelineItem,
    provider_anchors: list[TimelineItem],
) -> bool:
    category = _generic_preview_anchor_category(preview_item)
    if category is None:
        return False

    for anchor in provider_anchors:
        if preview_item.day_label and anchor.day_label and preview_item.day_label != anchor.day_label:
            continue
        if category == "arrival" and anchor.type == "flight" and "outbound" in anchor.title.lower():
            return True
        if category == "departure" and anchor.type == "flight" and "return" in anchor.title.lower():
            return True
        if category == "stay" and anchor.type == "hotel":
            return True
    return False


def _generic_preview_key(item: TimelineItem) -> tuple[str, str | None] | None:
    category = _generic_preview_anchor_category(item)
    if category is None:
        return None
    return (category, item.day_label)


def _generic_preview_anchor_category(item: TimelineItem) -> str | None:
    normalized_title = item.title.lower()
    normalized_summary = (item.summary or "").lower()
    normalized_details = " ".join(item.details).lower()
    combined = " ".join([normalized_title, normalized_summary, normalized_details])

    if any(
        phrase in combined
        for phrase in ["arrive", "arrival", "land in", "touch down", "airport transfer"]
    ):
        return "arrival"
    if any(
        phrase in combined
        for phrase in ["depart", "departure", "head home", "return flight", "fly home"]
    ):
        return "departure"
    if any(
        phrase in combined
        for phrase in ["check in", "check-in", "settle into", "hotel arrival", "drop bags"]
    ):
        return "stay"
    if item.type in {"activity", "meal", "note"} and any(
        phrase in normalized_title
        for phrase in ["explore the city", "dinner in town", "free time", "sightseeing"]
    ):
        return normalized_title
    return None


def _day_label_for_datetime(
    value: datetime | None,
    configuration: TripConfiguration,
) -> str | None:
    if value is None or configuration.start_date is None:
        return None

    offset = (value.date() - configuration.start_date).days + 1
    return f"Day {max(offset, 1)}"
