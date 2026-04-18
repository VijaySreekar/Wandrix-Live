from datetime import date, datetime, time, timedelta, timezone
import re
from uuid import uuid4

from pydantic import BaseModel, Field

from app.graph.state import PlanningGraphState
from app.integrations.llm.client import create_chat_model
from app.schemas.trip_draft import (
    ActivityDetail,
    ActivityStyle,
    FlightDetail,
    HotelStayDetail,
    PlanningModuleKey,
    TimelineItem,
    TimelineItemType,
    TripConfiguration,
    TripDraftStatus,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services.providers.activities import enrich_activities_from_geoapify
from app.services.providers.flights import enrich_flights_from_amadeus
from app.services.providers.weather import enrich_weather_from_open_meteo


ACTIVITY_STYLE_KEYWORDS = {
    "relaxed": ["relaxed", "slow", "easygoing", "chill"],
    "adventure": ["adventure", "hiking", "surf", "trek", "outdoors"],
    "luxury": ["luxury", "premium", "five-star", "5-star"],
    "family": ["family", "kids", "children"],
    "culture": ["culture", "museum", "history", "heritage"],
    "nightlife": ["nightlife", "bars", "clubs", "late-night"],
    "romantic": ["romantic", "honeymoon", "couple"],
    "food": ["food", "restaurants", "culinary", "dining"],
    "outdoors": ["outdoors", "nature", "parks", "scenic"],
}

MODULE_KEYWORDS = {
    "flights": ["flight", "flights", "plane", "airfare"],
    "hotels": ["hotel", "hotels", "stay", "stays", "accommodation"],
    "weather": ["weather", "temperature", "forecast", "rain"],
    "activities": ["activity", "activities", "things to do", "sightseeing"],
}

ACTIVITY_STYLE_TEMPLATES = {
    "food": ("Market lunch crawl", "Sample local specialties in the city's best food pockets."),
    "culture": ("Museum and old quarter walk", "Anchor the day around heritage streets and one cultural highlight."),
    "relaxed": ("Slow afternoon cafe stretch", "Leave breathing room for coffee, people-watching, and a light stroll."),
    "adventure": ("Outdoor viewpoint run", "Balance the itinerary with a more active scenic outing."),
    "luxury": ("Signature dinner reservation", "Hold space for a premium evening experience."),
    "family": ("Family-friendly city stop", "Keep the pace easy and child-friendly for this block."),
    "nightlife": ("Late evening district wander", "Reserve the evening for bars, music, or a livelier neighborhood."),
    "romantic": ("Golden-hour riverfront walk", "Shape the evening around a slower scenic moment."),
    "outdoors": ("Park and lookout loop", "Use open-air time to break up the denser city schedule."),
}


class TripModuleSelectionUpdate(BaseModel):
    flights: bool | None = None
    weather: bool | None = None
    activities: bool | None = None
    hotels: bool | None = None


class ProposedTimelineItem(BaseModel):
    type: TimelineItemType
    title: str
    day_label: str | None = None
    location_label: str | None = None
    summary: str | None = None
    details: list[str] = Field(default_factory=list)
    source_module: PlanningModuleKey | None = None


class TripTurnUpdate(BaseModel):
    title: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_gbp: float | None = None
    adults: int | None = Field(default=None, ge=1)
    children: int | None = Field(default=None, ge=0)
    selected_modules: TripModuleSelectionUpdate = Field(default_factory=TripModuleSelectionUpdate)
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    timeline_preview: list[ProposedTimelineItem] = Field(default_factory=list)
    assistant_response: str


def process_trip_turn(state: PlanningGraphState) -> PlanningGraphState:
    trip_draft = {
        **state.get("trip_draft", {}),
    }
    configuration = _apply_heuristic_updates(
        TripConfiguration.model_validate(trip_draft.get("configuration", {})),
        state.get("user_input", ""),
    )
    status = TripDraftStatus.model_validate(trip_draft.get("status", {}))
    existing_module_outputs = TripModuleOutputs.model_validate(
        trip_draft.get("module_outputs", {})
    )

    llm_update = _generate_llm_trip_update(
        user_input=state.get("user_input", ""),
        configuration=configuration,
        title=trip_draft.get("title") or "Trip planner",
        status=status,
    )

    configuration = _merge_llm_update_into_configuration(configuration, llm_update)
    title = llm_update.title or _derive_title(configuration)

    module_outputs = _build_module_outputs(configuration, existing_module_outputs)
    timeline = _build_timeline(
        configuration=configuration,
        llm_preview=llm_update.timeline_preview,
        module_outputs=module_outputs,
    )

    missing_fields = _compute_missing_fields(configuration)
    phase = "planning" if not missing_fields else "collecting_requirements"
    status.phase = phase
    status.missing_fields = missing_fields
    status.brochure_ready = phase == "planning"
    status.last_updated_at = datetime.now(timezone.utc)

    assistant_response = (
        llm_update.assistant_response.strip()
        if llm_update.assistant_response.strip()
        else _build_fallback_response(configuration, missing_fields)
    )

    return {
        "trip_draft": {
            "title": title,
            "configuration": configuration.model_dump(mode="json"),
            "timeline": [item.model_dump(mode="json") for item in timeline],
            "module_outputs": module_outputs.model_dump(mode="json"),
            "status": status.model_dump(mode="json"),
        },
        "assistant_response": assistant_response,
        "metadata": {
            **state.get("metadata", {}),
            "graph_bootstrapped": True,
            "turn_processed": True,
            "used_llm_extraction": llm_update.assistant_response != "",
        },
    }


def _apply_heuristic_updates(
    configuration: TripConfiguration,
    user_input: str,
) -> TripConfiguration:
    lowered_input = user_input.lower()

    route_match = re.search(
        r"\bfrom\s+([a-zA-Z][a-zA-Z .'-]{1,80}?)\s+to\s+([a-zA-Z][a-zA-Z .'-]{1,80})\b",
        user_input,
        flags=re.IGNORECASE,
    )
    if route_match:
        configuration.from_location = route_match.group(1).strip().title()
        configuration.to_location = route_match.group(2).strip().title()

    budget_match = re.search(
        r"\b(?:budget|around|under|roughly)\s*[£$€]?\s*([0-9][0-9,]{2,})\b",
        user_input,
        flags=re.IGNORECASE,
    )
    if budget_match:
        configuration.budget_gbp = float(budget_match.group(1).replace(",", ""))

    adults_match = re.search(r"\b(\d+)\s+adults?\b", lowered_input)
    if adults_match:
        configuration.travelers.adults = int(adults_match.group(1))

    children_match = re.search(r"\b(\d+)\s+children?\b", lowered_input)
    if children_match:
        configuration.travelers.children = int(children_match.group(1))

    for style, keywords in ACTIVITY_STYLE_KEYWORDS.items():
        if style in configuration.activity_styles:
            continue
        if any(keyword in lowered_input for keyword in keywords):
            configuration.activity_styles.append(style)

    for module_name, keywords in MODULE_KEYWORDS.items():
        if any(keyword in lowered_input for keyword in keywords):
            setattr(configuration.selected_modules, module_name, True)

    return configuration


def _generate_llm_trip_update(
    *,
    user_input: str,
    configuration: TripConfiguration,
    title: str,
    status: TripDraftStatus,
) -> TripTurnUpdate:
    if not user_input.strip():
        return TripTurnUpdate(assistant_response="")

    prompt = f"""
You are Wandrix's trip-planning extraction engine.

Take the latest user message and update the travel draft conservatively.
Rules:
- Only extract fields that are supported by the user's message or current draft.
- Do not invent exact travel dates unless the user clearly provided them.
- If the user provided enough detail, produce a small high-level timeline preview with 2 to 5 items.
- Keep assistant_response concise, warm, and specific about what changed and what is still missing.
- Prefer structured travel-planning language over generic chatbot language.

Current draft title:
{title}

Current configuration:
{configuration.model_dump(mode="json")}

Current status:
{status.model_dump(mode="json")}

Latest user message:
{user_input}
""".strip()

    try:
        model = create_chat_model(temperature=0.1)
        structured_model = model.with_structured_output(
            TripTurnUpdate,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                (
                    "system",
                    "Extract and refine the Wandrix trip draft using structured output.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return TripTurnUpdate(assistant_response="")


def _merge_llm_update_into_configuration(
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
) -> TripConfiguration:
    if llm_update.from_location:
        configuration.from_location = llm_update.from_location
    if llm_update.to_location:
        configuration.to_location = llm_update.to_location
    if llm_update.start_date:
        configuration.start_date = llm_update.start_date
    if llm_update.end_date:
        configuration.end_date = llm_update.end_date
    if llm_update.budget_gbp is not None:
        configuration.budget_gbp = llm_update.budget_gbp
    if llm_update.adults is not None:
        configuration.travelers.adults = llm_update.adults
    if llm_update.children is not None:
        configuration.travelers.children = llm_update.children

    for module_name, enabled in llm_update.selected_modules.model_dump().items():
        if enabled is not None:
            setattr(configuration.selected_modules, module_name, enabled)

    for style in llm_update.activity_styles:
        if style not in configuration.activity_styles:
            configuration.activity_styles.append(style)

    return configuration


def _build_module_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    return TripModuleOutputs(
        flights=_build_flight_outputs(configuration, existing_module_outputs),
        hotels=_build_hotel_outputs(configuration, existing_module_outputs),
        weather=_build_weather_outputs(configuration, existing_module_outputs),
        activities=_build_activity_outputs(configuration, existing_module_outputs),
    )


def _build_flight_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[FlightDetail]:
    if not configuration.selected_modules.flights:
        return []

    if not configuration.from_location or not configuration.to_location:
        return existing_module_outputs.flights

    live_flights = _try_live_flight_enrichment(configuration)
    if live_flights:
        return live_flights

    flights = [
        FlightDetail(
            id="flight_outbound",
            direction="outbound",
            carrier="Routing placeholder",
            flight_number=None,
            departure_airport=configuration.from_location,
            arrival_airport=configuration.to_location,
            departure_time=_combine_date_and_hour(configuration.start_date, 8),
            arrival_time=_combine_date_and_hour(configuration.start_date, 13),
            duration_text="Approx 5h block",
            notes=[
                "Fallback route placeholder because live flight search did not return a usable offer yet.",
            ],
        )
    ]

    if configuration.end_date:
        flights.append(
            FlightDetail(
                id="flight_return",
                direction="return",
                carrier="Routing placeholder",
                flight_number=None,
                departure_airport=configuration.to_location,
                arrival_airport=configuration.from_location,
                departure_time=_combine_date_and_hour(configuration.end_date, 16),
                arrival_time=_combine_date_and_hour(configuration.end_date, 21),
                duration_text="Approx 5h block",
                notes=[
                    "Fallback return leg placeholder derived from the current travel window.",
                ],
            )
        )

    return flights


def _try_live_flight_enrichment(
    configuration: TripConfiguration,
) -> list[FlightDetail]:
    try:
        return enrich_flights_from_amadeus(configuration)
    except Exception:
        return []


def _build_hotel_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[HotelStayDetail]:
    if not configuration.selected_modules.hotels:
        return []

    if not configuration.to_location:
        return existing_module_outputs.hotels

    return [
        HotelStayDetail(
            id="hotel_primary",
            hotel_name=f"{configuration.to_location} stay shortlist",
            area=f"Central {configuration.to_location}",
            check_in=_combine_date_and_hour(configuration.start_date, 15),
            check_out=_combine_date_and_hour(configuration.end_date, 11),
            notes=[
                "Primary stay placeholder until hotel discovery fills in actual options.",
            ],
        )
    ]


def _build_weather_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[WeatherDetail]:
    if not configuration.selected_modules.weather:
        return []

    live_weather = _try_live_weather_enrichment(configuration)
    if live_weather:
        return live_weather

    travel_dates = _get_travel_dates(configuration)
    if not travel_dates:
        return existing_module_outputs.weather

    weather_items: list[WeatherDetail] = []
    for index, travel_date in enumerate(travel_dates[:4], start=1):
        weather_items.append(
            WeatherDetail(
                id=f"weather_{index}",
                day_label=f"Day {index}",
                summary="Forecast placeholder for pacing activities and transfers.",
                high_c=24,
                low_c=17,
                notes=[
                    "Weather will become more specific once provider-backed forecasts are connected.",
                ],
            )
        )

    return weather_items


def _try_live_weather_enrichment(
    configuration: TripConfiguration,
) -> list[WeatherDetail]:
    try:
        return enrich_weather_from_open_meteo(configuration)
    except Exception:
        return []


def _build_activity_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[ActivityDetail]:
    if not configuration.selected_modules.activities:
        return []

    if not configuration.to_location:
        return existing_module_outputs.activities

    live_activities = _try_live_activity_enrichment(configuration)
    if live_activities:
        return live_activities

    travel_dates = _get_travel_dates(configuration)
    if not travel_dates:
        travel_dates = [None]

    preferred_styles = configuration.activity_styles or ["culture", "food", "relaxed"]
    activity_items: list[ActivityDetail] = []

    for index, style in enumerate(preferred_styles[:3], start=1):
        title, note = ACTIVITY_STYLE_TEMPLATES.get(
            style,
            ("City discovery block", "Use this as a flexible planning block."),
        )
        activity_items.append(
            ActivityDetail(
                id=f"activity_{index}",
                title=title,
                category=style,
                day_label=f"Day {min(index, len(travel_dates))}",
                time_label=_time_label_for_index(index),
                notes=[
                    note,
                    f"Focus the experience around {configuration.to_location}.",
                ],
            )
        )

    return activity_items


def _try_live_activity_enrichment(
    configuration: TripConfiguration,
) -> list[ActivityDetail]:
    try:
        return enrich_activities_from_geoapify(configuration)
    except Exception:
        return []


def _build_timeline(
    *,
    configuration: TripConfiguration,
    llm_preview: list[ProposedTimelineItem],
    module_outputs: TripModuleOutputs,
) -> list[TimelineItem]:
    preview_items = [_to_timeline_item(item) for item in llm_preview]
    derived_items = _build_derived_timeline(configuration, module_outputs)
    merged_items = _merge_timeline_items(preview_items, derived_items)

    return merged_items[:10]


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
                title=(
                    "Outbound flight"
                    if flight.direction == "outbound"
                    else "Return flight"
                ),
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
                summary="Primary hotel stay placeholder for the current trip draft.",
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


def _compute_missing_fields(configuration: TripConfiguration) -> list[str]:
    missing_fields: list[str] = []
    if not configuration.from_location:
        missing_fields.append("from_location")
    if not configuration.to_location:
        missing_fields.append("to_location")
    if not configuration.start_date:
        missing_fields.append("start_date")
    if not configuration.end_date:
        missing_fields.append("end_date")

    return missing_fields


def _derive_title(configuration: TripConfiguration) -> str:
    if configuration.to_location:
        return f"{configuration.to_location} trip"
    return "Trip planner"


def _build_fallback_response(
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> str:
    route_summary = f"{configuration.from_location or 'TBD'} to {configuration.to_location or 'TBD'}"
    if missing_fields:
        return (
            f"I've updated the draft with what I could from your message. "
            f"The route currently looks like {route_summary}. "
            f"I still need: {', '.join(missing_fields)}."
        )

    return (
        f"I've updated the draft for {route_summary}. "
        "The trip has enough core information to move into planning."
    )


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


def _get_travel_dates(configuration: TripConfiguration) -> list[date]:
    if not configuration.start_date:
        return []

    end_date = configuration.end_date or configuration.start_date
    travel_dates: list[date] = []
    current_date = configuration.start_date

    while current_date <= end_date and len(travel_dates) < 7:
        travel_dates.append(current_date)
        current_date += timedelta(days=1)

    return travel_dates


def _combine_date_and_hour(value: date | None, hour: int) -> datetime | None:
    if value is None:
        return None

    return datetime.combine(value, time(hour=hour, minute=0), tzinfo=timezone.utc)


def _day_label_for_datetime(
    value: datetime | None,
    configuration: TripConfiguration,
) -> str | None:
    if value is None or configuration.start_date is None:
        return None

    offset = (value.date() - configuration.start_date).days + 1
    return f"Day {max(offset, 1)}"


def _time_label_for_index(index: int) -> str:
    labels = {
        1: "Morning",
        2: "Afternoon",
        3: "Evening",
    }
    return labels.get(index, "Flexible")
