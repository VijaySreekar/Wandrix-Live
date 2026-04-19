from datetime import date, datetime, timezone
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
    configuration = TripConfiguration.model_validate(trip_draft.get("configuration", {}))
    status = TripDraftStatus.model_validate(trip_draft.get("status", {}))
    existing_module_outputs = TripModuleOutputs.model_validate(
        trip_draft.get("module_outputs", {})
    )

    llm_update = _generate_llm_trip_update(
        user_input=state.get("user_input", ""),
        configuration=configuration,
        title=trip_draft.get("title") or "Trip planner",
        status=status,
        profile_context=state.get("profile_context", {}),
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
            "used_llm_extraction": True,
        },
    }


def _generate_llm_trip_update(
    *,
    user_input: str,
    configuration: TripConfiguration,
    title: str,
    status: TripDraftStatus,
    profile_context: dict,
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

Saved profile context:
{profile_context}

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

    return existing_module_outputs.flights


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

    return existing_module_outputs.hotels


def _build_weather_outputs(
    configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> list[WeatherDetail]:
    if not configuration.selected_modules.weather:
        return []

    live_weather = _try_live_weather_enrichment(configuration)
    if live_weather:
        return live_weather

    return existing_module_outputs.weather


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

    return existing_module_outputs.activities


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
            "I do not want to lock the wrong trip details from that message. "
            f"Right now the draft still looks like {route_summary}. "
            f"Please clarify these next: {', '.join(missing_fields)}."
        )

    return (
        f"I kept the draft aligned around {route_summary}. "
        "If you want, I can now turn that into a more concrete plan."
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

def _day_label_for_datetime(
    value: datetime | None,
    configuration: TripConfiguration,
) -> str | None:
    if value is None or configuration.start_date is None:
        return None

    offset = (value.date() - configuration.start_date).days + 1
    return f"Day {max(offset, 1)}"
