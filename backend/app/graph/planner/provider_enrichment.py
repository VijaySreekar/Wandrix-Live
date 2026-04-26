from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
from app.services.providers.hotels import HOTEL_SEARCH_RESULT_LIMIT, enrich_hotels
from app.services.providers.location_lookup import (
    Coordinates,
    resolve_destination_coordinates,
)
from app.services.providers.weather import enrich_weather_from_open_meteo


@dataclass(frozen=True)
class ProviderEnrichmentOptions:
    request_timeout_seconds: float | None = None
    parallel: bool = False
    flight_allow_live_fallback: bool = True
    flight_parameter_sets_limit: int | None = None
    hotel_result_limit: int | None = None
    hotel_rate_lookup_limit: int | None = None
    hotel_include_llm_fallback: bool = True
    activity_category_limit: int | None = None


def build_module_outputs(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
    options: ProviderEnrichmentOptions | None = None,
) -> TripModuleOutputs:
    enrichment_options = options or ProviderEnrichmentOptions()
    shared_destination_coordinates = _resolve_shared_destination_coordinates(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules=allowed_modules,
        options=enrichment_options,
    )

    if enrichment_options.parallel:
        return _build_module_outputs_parallel(
            configuration=configuration,
            previous_configuration=previous_configuration,
            existing_module_outputs=existing_module_outputs,
            shared_destination_coordinates=shared_destination_coordinates,
            allowed_modules=allowed_modules,
            options=enrichment_options,
        )

    return TripModuleOutputs(
        flights=_build_flight_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            allowed_modules=allowed_modules,
            options=enrichment_options,
        ),
        hotels=_build_hotel_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            allowed_modules=allowed_modules,
            options=enrichment_options,
        ),
        weather=_build_weather_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            shared_destination_coordinates,
            allowed_modules=allowed_modules,
            options=enrichment_options,
        ),
        activities=_build_activity_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            shared_destination_coordinates,
            allowed_modules=allowed_modules,
            options=enrichment_options,
        ),
    )


def build_timeline(
    *,
    configuration: TripConfiguration,
    llm_preview: list[ProposedTimelineItem],
    module_outputs: TripModuleOutputs,
    include_derived_when_preview_present: bool = True,
    include_derived_modules_when_preview_present: set[str] | None = None,
) -> list[TimelineItem]:
    preview_items = _refine_preview_timeline(
        [_to_timeline_item(item) for item in llm_preview],
        configuration=configuration,
        module_outputs=module_outputs,
    )
    derived_items = _build_derived_timeline(configuration, module_outputs)
    if preview_items and not include_derived_when_preview_present:
        if include_derived_modules_when_preview_present:
            visible_anchors = [
                item
                for item in derived_items
                if item.source_module in include_derived_modules_when_preview_present
                and not _preview_already_has_logistics_anchor(item, preview_items)
            ]
            return _merge_timeline_items(preview_items, visible_anchors)[:16]
        return preview_items[:16]
    return _merge_timeline_items(preview_items, derived_items)[:16]


def has_any_module_output(module_outputs: TripModuleOutputs) -> bool:
    return any(
        [
            module_outputs.flights,
            module_outputs.hotels,
            module_outputs.weather,
            module_outputs.activities,
        ]
    )


def _build_module_outputs_parallel(
    *,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    shared_destination_coordinates: Coordinates | None,
    allowed_modules: set[str] | None,
    options: ProviderEnrichmentOptions,
) -> TripModuleOutputs:
    tasks = {
        "flights": lambda: _build_flight_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            allowed_modules=allowed_modules,
            options=options,
        ),
        "hotels": lambda: _build_hotel_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            allowed_modules=allowed_modules,
            options=options,
        ),
        "weather": lambda: _build_weather_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            shared_destination_coordinates,
            allowed_modules=allowed_modules,
            options=options,
        ),
        "activities": lambda: _build_activity_outputs(
            configuration,
            previous_configuration,
            existing_module_outputs,
            shared_destination_coordinates,
            allowed_modules=allowed_modules,
            options=options,
        ),
    }
    results: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_name = {
            executor.submit(task): name for name, task in tasks.items()
        }
        for future, name in future_to_name.items():
            try:
                results[name] = future.result()
            except Exception:
                results[name] = getattr(existing_module_outputs, name)

    return TripModuleOutputs(
        flights=results.get("flights", existing_module_outputs.flights),
        hotels=results.get("hotels", existing_module_outputs.hotels),
        weather=results.get("weather", existing_module_outputs.weather),
        activities=results.get("activities", existing_module_outputs.activities),
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
    options: ProviderEnrichmentOptions | None = None,
) -> list[FlightDetail]:
    enrichment_options = options or ProviderEnrichmentOptions()
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
        if enrichment_options == ProviderEnrichmentOptions():
            live_flights = enrich_flights(configuration)
        else:
            live_flights = enrich_flights(
                configuration,
                timeout=enrichment_options.request_timeout_seconds,
                allow_live_fallback=enrichment_options.flight_allow_live_fallback,
                parameter_sets_limit=enrichment_options.flight_parameter_sets_limit,
            )
    except Exception:
        live_flights = []
    return live_flights or existing_module_outputs.flights


def _build_hotel_outputs(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
    options: ProviderEnrichmentOptions | None = None,
) -> list[HotelStayDetail]:
    enrichment_options = options or ProviderEnrichmentOptions()
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
        if enrichment_options == ProviderEnrichmentOptions():
            live_hotels = enrich_hotels(configuration)
        else:
            live_hotels = enrich_hotels(
                configuration,
                timeout=enrichment_options.request_timeout_seconds,
                result_limit=(
                    enrichment_options.hotel_result_limit
                    if enrichment_options.hotel_result_limit is not None
                    else HOTEL_SEARCH_RESULT_LIMIT
                ),
                rate_lookup_limit=enrichment_options.hotel_rate_lookup_limit,
                include_llm_fallback=enrichment_options.hotel_include_llm_fallback,
            )
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
    options: ProviderEnrichmentOptions | None = None,
) -> list[WeatherDetail]:
    enrichment_options = options or ProviderEnrichmentOptions()
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
        if enrichment_options.request_timeout_seconds is None:
            live_weather = enrich_weather_from_open_meteo(
                configuration,
                shared_destination_coordinates,
            )
        else:
            live_weather = enrich_weather_from_open_meteo(
                configuration,
                shared_destination_coordinates,
                timeout=enrichment_options.request_timeout_seconds,
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
    options: ProviderEnrichmentOptions | None = None,
) -> list[ActivityDetail]:
    enrichment_options = options or ProviderEnrichmentOptions()
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
        if (
            enrichment_options.request_timeout_seconds is None
            and enrichment_options.activity_category_limit is None
        ):
            live_activities = enrich_activities_from_geoapify(
                configuration,
                shared_destination_coordinates,
            )
        else:
            live_activities = enrich_activities_from_geoapify(
                configuration,
                shared_destination_coordinates,
                timeout=enrichment_options.request_timeout_seconds,
                category_limit=enrichment_options.activity_category_limit,
            )
    except Exception:
        live_activities = []
    return live_activities or existing_module_outputs.activities


def _resolve_shared_destination_coordinates(
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str] | None = None,
    options: ProviderEnrichmentOptions | None = None,
) -> Coordinates | None:
    enrichment_options = options or ProviderEnrichmentOptions()
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
        if enrichment_options.request_timeout_seconds is None:
            return resolve_destination_coordinates(configuration.to_location)
        return resolve_destination_coordinates(
            configuration.to_location,
            timeout=enrichment_options.request_timeout_seconds,
        )
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
        departure_time = _align_flight_departure_time(flight, configuration)
        timeline.append(
            TimelineItem(
                id=f"timeline_{flight.id}",
                type="flight",
                title=(
                    "Outbound flight option"
                    if flight.direction == "outbound"
                    else "Return flight option"
                ),
                day_label=_flight_day_label(flight, configuration),
                start_at=departure_time,
                end_at=_align_flight_arrival_time(
                    flight,
                    aligned_departure_time=departure_time,
                ),
                timing_source="provider_exact"
                if departure_time or flight.arrival_time
                else None,
                timing_note=None
                if departure_time or flight.arrival_time
                else "Flight timing still needs a live schedule check.",
                location_label=f"{flight.departure_airport} to {flight.arrival_airport}",
                summary=flight.duration_text,
                details=_build_flight_timeline_details(flight),
                source_module="flights",
            )
        )

    for hotel in module_outputs.hotels:
        check_in_time = _hotel_check_in_time(hotel, configuration)
        check_out_time = _hotel_check_out_time(hotel, configuration)
        timing_source = "provider_exact" if hotel.check_in else "planner_estimate"
        timeline.append(
            TimelineItem(
                id=f"timeline_{hotel.id}",
                type="hotel",
                title=hotel.hotel_name,
                day_label=_day_label_for_datetime(check_in_time, configuration),
                start_at=check_in_time,
                end_at=check_out_time,
                timing_source=timing_source if check_in_time else None,
                timing_note=None
                if hotel.check_in
                else "Planner-estimated check-in timing for the accepted trip.",
                location_label=hotel.area,
                summary="Stay anchor",
                details=_build_hotel_timeline_details(hotel),
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

    timeline.sort(
        key=lambda item: (
            _day_sort_value(item.day_label),
            _datetime_sort_value(item.start_at),
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


def _preview_already_has_logistics_anchor(
    derived_item: TimelineItem,
    preview_items: list[TimelineItem],
) -> bool:
    if derived_item.source_module not in {"flights", "hotels"}:
        return False

    for preview_item in preview_items:
        if preview_item.source_module != derived_item.source_module:
            continue
        if preview_item.type != derived_item.type:
            continue
        if derived_item.type == "hotel":
            return True
        if derived_item.type == "flight" and preview_item.day_label == derived_item.day_label:
            return True
    return False


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
        item = _normalize_preview_item(item, module_outputs=module_outputs)
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
        timing_source=item.timing_source,
        timing_note=item.timing_note,
        location_label=item.location_label,
        summary=item.summary,
        details=item.details,
        source_module=item.source_module,
    )


def _normalize_preview_item(
    item: TimelineItem,
    *,
    module_outputs: TripModuleOutputs,
) -> TimelineItem:
    if item.type != "flight" or item.source_module == "flights":
        return item

    details = [detail for detail in item.details if not _is_provider_source_note(detail)]
    if not module_outputs.flights:
        details = [
            *details,
            "Flight option still needs selection before exact timings are final.",
        ]

    return item.model_copy(
        update={
            "type": "transfer",
            "details": details[:4],
        }
    )


def _preview_item_conflicts_with_provider_anchor(
    preview_item: TimelineItem,
    provider_anchors: list[TimelineItem],
) -> bool:
    if preview_item.start_at and preview_item.end_at:
        return False

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


def _build_flight_timeline_details(flight: FlightDetail) -> list[str]:
    details: list[str] = []
    if flight.price_text:
        details.append(f"Estimated fare: {flight.price_text}.")
    stop_detail = _flight_stop_detail(flight)
    if stop_detail:
        details.append(stop_detail)
    if flight.layover_summary and flight.layover_summary not in details:
        details.append(flight.layover_summary)
    if flight.inventory_source == "cached":
        details.append("Use this as a planning option until live schedules are checked.")
    elif flight.inventory_notice:
        details.append(flight.inventory_notice)
    return details[:4]


def _flight_stop_detail(flight: FlightDetail) -> str | None:
    if flight.stop_count is None:
        return None
    if flight.stop_count == 0:
        return "Direct route."
    if flight.stop_details_available:
        return (
            "1 stop with connection detail available."
            if flight.stop_count == 1
            else f"{flight.stop_count} stops with connection detail available."
        )
    return (
        "1 stop; connection airport is not supplied yet."
        if flight.stop_count == 1
        else f"{flight.stop_count} stops; connection airports are not supplied yet."
    )


def _build_hotel_timeline_details(hotel: HotelStayDetail) -> list[str]:
    return [note for note in hotel.notes if not _is_provider_source_note(note)][:3]


def _is_provider_source_note(note: str) -> bool:
    normalized = note.strip().lower()
    return (
        normalized.startswith("tripadvisor:")
        or "rapidapi" in normalized
        or "cached hotel search result" in normalized
        or normalized.startswith("source:")
    )


def _flight_day_label(
    flight: FlightDetail,
    configuration: TripConfiguration,
) -> str | None:
    if not configuration.start_date:
        return _day_label_for_datetime(flight.departure_time, configuration)
    if flight.direction == "outbound":
        return "Day 1"
    if flight.direction == "return" and configuration.end_date:
        day_number = max((configuration.end_date - configuration.start_date).days + 1, 1)
        return f"Day {day_number}"
    return _day_label_for_datetime(flight.departure_time, configuration)


def _align_flight_departure_time(
    flight: FlightDetail,
    configuration: TripConfiguration,
) -> datetime | None:
    target_date = None
    if flight.direction == "outbound":
        target_date = configuration.start_date
    elif flight.direction == "return":
        target_date = configuration.end_date
    if flight.departure_time is None or target_date is None:
        return flight.departure_time
    return flight.departure_time.replace(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
    )


def _align_flight_arrival_time(
    flight: FlightDetail,
    *,
    aligned_departure_time: datetime | None,
) -> datetime | None:
    if flight.arrival_time is None or aligned_departure_time is None:
        return flight.arrival_time
    day_delta = (
        (flight.arrival_time.date() - flight.departure_time.date()).days
        if flight.departure_time
        else 0
    )
    target_date = aligned_departure_time.date()
    if day_delta > 0:
        target_date = target_date + timedelta(days=day_delta)
    return flight.arrival_time.replace(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
    )


def _hotel_check_in_time(
    hotel: HotelStayDetail,
    configuration: TripConfiguration,
) -> datetime | None:
    if hotel.check_in:
        return hotel.check_in
    if configuration.start_date:
        return datetime.combine(
            configuration.start_date,
            datetime.min.time(),
        ).replace(hour=15, minute=30, tzinfo=timezone.utc)
    return None


def _hotel_check_out_time(
    hotel: HotelStayDetail,
    configuration: TripConfiguration,
) -> datetime | None:
    if hotel.check_out:
        return hotel.check_out
    if configuration.end_date:
        return datetime.combine(
            configuration.end_date,
            datetime.min.time(),
        ).replace(hour=11, minute=0, tzinfo=timezone.utc)
    return None


def _day_sort_value(day_label: str | None) -> int:
    if not day_label or not day_label.lower().startswith("day "):
        return 999
    try:
        return int(day_label.split(" ", 1)[1])
    except ValueError:
        return 999


def _datetime_sort_value(value: datetime | None) -> float:
    if value is None:
        return float("inf")
    return value.timestamp()


def _day_label_for_datetime(
    value: datetime | None,
    configuration: TripConfiguration,
) -> str | None:
    if value is None or configuration.start_date is None:
        return None

    offset = (value.date() - configuration.start_date).days + 1
    return f"Day {max(offset, 1)}"
