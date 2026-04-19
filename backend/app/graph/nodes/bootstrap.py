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
    PlannerDecisionCard,
    PlanningModuleKey,
    TripFieldKey,
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
    start_date: date | None = Field(
        default=None,
        description=(
            "Only use this when the user gave an explicit calendar date or fixed date range. "
            "Leave null for rough timing like 'late January', 'spring', or '4 or 5 nights'."
        ),
    )
    end_date: date | None = Field(
        default=None,
        description=(
            "Only use this when the user gave an explicit calendar date or fixed date range. "
            "Leave null for rough timing like 'late January', 'spring', or '4 or 5 nights'."
        ),
    )
    budget_gbp: float | None = None
    adults: int | None = Field(default=None, ge=1)
    children: int | None = Field(default=None, ge=0)
    selected_modules: TripModuleSelectionUpdate = Field(default_factory=TripModuleSelectionUpdate)
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    confirmed_fields: list[TripFieldKey] = Field(default_factory=list)
    inferred_fields: list[TripFieldKey] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    decision_cards: list[PlannerDecisionCard] = Field(default_factory=list)
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
    confirmed_fields, inferred_fields = _merge_field_signals(
        configuration=configuration,
        status=status,
        llm_update=llm_update,
    )
    open_questions = _merge_open_questions(
        configuration=configuration,
        llm_update=llm_update,
        missing_fields=missing_fields,
    )
    decision_cards = _merge_decision_cards(
        llm_update=llm_update,
        missing_fields=missing_fields,
    )
    phase = "planning" if not missing_fields else "collecting_requirements"
    status.phase = phase
    status.missing_fields = missing_fields
    status.confirmed_fields = confirmed_fields
    status.inferred_fields = inferred_fields
    status.open_questions = open_questions if missing_fields else []
    status.decision_cards = decision_cards if missing_fields else []
    status.brochure_ready = phase == "planning"
    status.last_updated_at = datetime.now(timezone.utc)

    assistant_response = (
        llm_update.assistant_response.strip()
        if llm_update.assistant_response.strip()
        else _build_fallback_response(
            configuration,
            missing_fields,
            open_questions,
            inferred_fields,
        )
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
- Treat rough timing like "late January", "end of January", "spring", or "4 or 5 nights" as flexible timing, not exact calendar dates. Keep start_date and end_date unset unless the user gave a concrete date or fixed range.
- Infer traveler counts from clear natural phrasing when the user names the group in plain language. Examples: "me and my partner", "me and my mum", "me and my sister", or "the two of us" should update adults to 2 unless children are mentioned.
- Use confirmed_fields for details the user clearly stated in this turn.
- Use inferred_fields for soft assumptions or best-effort readings that should stay provisional.
- If something important is still unclear, add 1 or 2 short open_questions instead of silently locking a weak guess.
- If the user has given enough signal to compare likely directions, include 1 to 3 decision_cards with concrete options that would help them answer quickly.
- Keep decision card options short, specific, and grounded in the user's stated pace, season, budget posture, and geography. Prefer real candidate destinations or timing choices over generic placeholders.
- If the user provided enough detail, produce a small high-level timeline preview with 2 to 5 items.
- If enough signal already exists, let assistant_response propose a provisional trip direction before asking follow-up questions.
- Keep assistant_response concise, warm, and specific about what changed and what is still missing.
- Prefer structured travel-planning language over generic chatbot language.

Allowed field keys for confirmed_fields and inferred_fields:
["from_location", "to_location", "start_date", "end_date", "budget_gbp", "adults", "children", "activity_styles", "selected_modules"]

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


def _merge_field_signals(
    *,
    configuration: TripConfiguration,
    status: TripDraftStatus,
    llm_update: TripTurnUpdate,
) -> tuple[list[TripFieldKey], list[TripFieldKey]]:
    available_fields = _collect_available_fields(configuration)
    confirmed = {
        field
        for field in [*status.confirmed_fields, *llm_update.confirmed_fields]
        if field in available_fields
    }
    inferred = {
        field
        for field in [*status.inferred_fields, *llm_update.inferred_fields]
        if field in available_fields and field not in confirmed
    }

    return sorted(confirmed), sorted(inferred)


def _collect_available_fields(configuration: TripConfiguration) -> set[TripFieldKey]:
    available_fields: set[TripFieldKey] = set()

    if configuration.from_location:
        available_fields.add("from_location")
    if configuration.to_location:
        available_fields.add("to_location")
    if configuration.start_date:
        available_fields.add("start_date")
    if configuration.end_date:
        available_fields.add("end_date")
    if configuration.budget_gbp is not None:
        available_fields.add("budget_gbp")
    if configuration.travelers.adults > 0:
        available_fields.add("adults")
    if configuration.travelers.children > 0:
        available_fields.add("children")
    if configuration.activity_styles:
        available_fields.add("activity_styles")
    if configuration.selected_modules != TripConfiguration().selected_modules:
        available_fields.add("selected_modules")

    return available_fields


def _merge_open_questions(
    *,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    missing_fields: list[str],
) -> list[str]:
    seen: set[str] = set()
    merged_questions: list[str] = []

    for question in [*llm_update.open_questions, *_build_default_open_questions(configuration, missing_fields)]:
        cleaned = question.strip()
        normalized = cleaned.lower()
        if not cleaned or normalized in seen:
            continue
        seen.add(normalized)
        merged_questions.append(cleaned)

    return merged_questions[:2]


def _merge_decision_cards(
    *,
    llm_update: TripTurnUpdate,
    missing_fields: list[str],
) -> list[PlannerDecisionCard]:
    if not missing_fields:
        return []

    merged_cards: list[PlannerDecisionCard] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()

    for card in llm_update.decision_cards:
        title = card.title.strip()
        description = card.description.strip()
        options = [option.strip() for option in card.options if option.strip()]

        if not title or not description:
            continue

        key = (title.lower(), tuple(option.lower() for option in options))
        if key in seen:
            continue

        seen.add(key)
        merged_cards.append(
            PlannerDecisionCard(
                title=title,
                description=description,
                options=options[:4],
            )
        )

    return merged_cards[:3]


def _derive_title(configuration: TripConfiguration) -> str:
    if configuration.to_location:
        return f"{configuration.to_location} trip"
    return "Trip planner"


def _build_fallback_response(
    configuration: TripConfiguration,
    missing_fields: list[str],
    open_questions: list[str],
    inferred_fields: list[TripFieldKey],
) -> str:
    route_summary = f"{configuration.from_location or 'TBD'} to {configuration.to_location or 'TBD'}"
    if missing_fields:
        trip_shape = _build_trip_shape_summary(configuration)
        inferred_summary = _build_inferred_summary(inferred_fields)
        follow_up = " ".join(question.rstrip("?") + "?" for question in open_questions[:2])

        return (
            f"{trip_shape} "
            f"Right now the draft still looks like {route_summary}. "
            f"{inferred_summary} "
            f"{follow_up}".strip()
        )

    return (
        f"I kept the draft aligned around {route_summary}. "
        "If you want, I can now turn that into a more concrete day-by-day plan."
    )


def _build_trip_shape_summary(configuration: TripConfiguration) -> str:
    parts: list[str] = []

    if configuration.to_location:
        parts.append(f"a trip centered on {configuration.to_location}")
    if configuration.activity_styles:
        style_summary = ", ".join(configuration.activity_styles[:2])
        parts.append(f"with a {style_summary} feel")

    if not parts:
        return "I do not want to lock the wrong trip details from that message."

    return f"I can already start shaping this as {' '.join(parts)}."


def _build_inferred_summary(inferred_fields: list[TripFieldKey]) -> str:
    visible_fields = [_field_label(field) for field in inferred_fields[:2]]
    if not visible_fields:
        return "I want to keep anything uncertain soft instead of pretending it is confirmed."

    if len(visible_fields) == 1:
        return f"I am still treating {visible_fields[0]} as provisional so I do not over-commit too early."

    return (
        f"I am still treating {visible_fields[0]} and {visible_fields[1]} as provisional "
        "so I do not over-commit too early."
    )


def _build_default_open_questions(
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> list[str]:
    question_map: dict[str, str] = {
        "from_location": "Where would you be flying or traveling from?",
        "to_location": "Where do you want this trip to take place?",
        "start_date": "What rough travel window are you thinking about?",
        "end_date": (
            "How long do you want to stay?"
            if configuration.start_date
            else "Roughly how many days or nights should I plan around?"
        ),
    }
    return [question_map[field] for field in missing_fields if field in question_map]


def _field_label(field: TripFieldKey) -> str:
    return {
        "from_location": "your departure point",
        "to_location": "the destination",
        "start_date": "the travel window",
        "end_date": "the trip length",
        "budget_gbp": "the budget",
        "adults": "the adult traveler count",
        "children": "the child traveler count",
        "activity_styles": "the trip style",
        "selected_modules": "the planning modules",
    }[field]


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
