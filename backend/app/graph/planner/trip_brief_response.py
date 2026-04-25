"""Chat framing for the structured trip brief.

This module does not extract trip facts from natural language. It prefers the
LLM-authored assistant response, then falls back to formatting validated draft
state when that response repeats known-bad checklist phrasing.
"""

from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import PlannerChecklistItem, TripConversationState
from app.schemas.trip_planning import TripConfiguration
from app.utils.currency import format_currency_amount


FULL_MODULE_SCOPE = {"flights", "weather", "activities", "hotels"}

STEP_DETAIL_IDS: dict[str, tuple[str, ...]] = {
    "modules": ("modules",),
    "route": ("route",),
    "timing": ("timing", "trip_length", "weather"),
    "travellers": ("travellers",),
    "vibe": ("trip_style",),
    "budget": ("budget",),
}

DETAIL_LABELS: dict[str, str] = {
    "route": "route",
    "timing": "timing",
    "trip_length": "trip length",
    "weather": "weather preference",
    "travellers": "travellers",
    "trip_style": "trip style",
    "budget": "budget",
    "modules": "trip scope",
}


def build_details_collection_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
    action: ConversationBoardAction | None,
    fallback_text: str | None = None,
) -> str:
    llm_response = _clean_llm_brief_response(fallback_text)
    if llm_response:
        return llm_response

    board = conversation.suggestion_board
    primary_gap = _select_primary_gap(conversation)

    sentences = [
        _build_brief_lede(
            configuration=configuration,
            greeting_name=greeting_name,
            action=action,
        )
    ]

    known_context = _build_known_context_sentence(configuration, board.have_details)
    if known_context:
        sentences.append(known_context)

    if conversation.planning_mode == "advanced":
        sentences.append(
            "For Advanced Planning, this brief becomes the shared starting point; once it is solid, I'll move to the first anchor choice."
        )

    if configuration.from_location_flexible and (
        not primary_gap or primary_gap.id != "route"
    ):
        sentences.append(
            "I'll leave the departure point flexible unless you decide to pin it down."
        )

    if primary_gap:
        if primary_gap.id == "modules":
            summary = _build_brief_summary_sentence(configuration)
            if summary:
                sentences.append(summary)
        sentences.append(_build_primary_gap_sentence(primary_gap, configuration))
        sentences.append("You can type it here or use the brief on the right.")
        remaining = _build_remaining_gap_sentence(board.need_details, primary_gap)
        if remaining:
            sentences.append(remaining)
    else:
        sentences.append("If this looks right, confirm the brief and I'll move ahead.")

    return " ".join(sentence for sentence in sentences if sentence)


def _build_brief_lede(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
    action: ConversationBoardAction | None,
) -> str:
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    shape = _build_trip_shape_phrase(configuration)

    if action and action.type == "confirm_trip_details":
        return f"{greeting_prefix}nice, those brief edits are in. {shape}"

    if action and action.type == "select_destination_suggestion":
        return f"{greeting_prefix}{shape}"

    return f"{greeting_prefix}{shape}"


def _build_trip_shape_phrase(configuration: TripConfiguration) -> str:
    route = _build_route_phrase(configuration)
    timing = _build_timing_phrase(configuration)

    if route and timing:
        return f"{route} {timing} is taking shape."
    if route:
        return f"{route} is the working direction."
    if timing:
        return f"This trip {timing} is taking shape."
    return "The trip brief is taking shape."


def _build_route_phrase(configuration: TripConfiguration) -> str | None:
    if configuration.from_location and configuration.to_location:
        return f"{configuration.from_location} to {configuration.to_location}"
    if configuration.to_location:
        return configuration.to_location
    if configuration.from_location:
        return f"Starting from {configuration.from_location}"
    return None


def _build_timing_phrase(configuration: TripConfiguration) -> str | None:
    timing_bits: list[str] = []
    if configuration.travel_window:
        timing_bits.append(_format_travel_window(configuration.travel_window))
    elif configuration.start_date and configuration.end_date:
        timing_bits.append(
            f"from {configuration.start_date.isoformat()} to {configuration.end_date.isoformat()}"
        )
    elif configuration.start_date:
        timing_bits.append(f"from {configuration.start_date.isoformat()}")
    elif configuration.end_date:
        timing_bits.append(f"by {configuration.end_date.isoformat()}")

    if configuration.trip_length:
        timing_bits.append(f"for {configuration.trip_length}")

    return " ".join(timing_bits) if timing_bits else None


def _format_travel_window(value: str) -> str:
    cleaned = " ".join(value.split())
    lowered = cleaned.lower()
    if lowered.startswith(("around ", "about ", "roughly ")):
        return cleaned
    if lowered.startswith(("early ", "mid ", "mid-", "late ")):
        return f"in {cleaned}"
    return f"around {cleaned}"


def _build_known_context_sentence(
    configuration: TripConfiguration,
    have_details: list[PlannerChecklistItem],
) -> str | None:
    noted: list[str] = []
    if configuration.weather_preference:
        noted.append(f"{configuration.weather_preference} weather")

    style = _format_trip_style(configuration)
    if style:
        noted.append(f"a {style} style")

    travellers = _detail_value(have_details, "travellers")
    if travellers:
        noted.append(travellers)

    budget = _format_budget_context(configuration)
    if budget:
        noted.append(budget)

    sentences: list[str] = []
    if noted:
        sentences.append(f"I've got {_join_natural(noted)} noted.")

    scope_sentence = _build_module_scope_sentence(configuration)
    if scope_sentence:
        sentences.append(scope_sentence)

    return " ".join(sentences) if sentences else None


def _format_trip_style(configuration: TripConfiguration) -> str | None:
    values = [*configuration.activity_styles]
    if configuration.custom_style:
        values.append(configuration.custom_style)
    return _join_natural(values) if values else None


def _format_budget_context(configuration: TripConfiguration) -> str | None:
    if configuration.budget_amount is not None:
        return (
            f"a budget around "
            f"{format_currency_amount(configuration.budget_amount, configuration.budget_currency)}"
        )
    if configuration.budget_posture:
        posture = configuration.budget_posture.replace("_", "-")
        if configuration.budget_currency:
            return f"a {posture} budget in {configuration.budget_currency}"
        return f"a {posture} budget"
    if configuration.budget_currency:
        return f"{configuration.budget_currency} as the budget currency"
    return None


def _build_module_scope_sentence(configuration: TripConfiguration) -> str | None:
    active_modules = _active_modules(configuration)
    if not active_modules:
        return None
    if set(active_modules) == FULL_MODULE_SCOPE:
        return "I'll keep the full trip scope available for now."
    return f"I'll keep this focused on {_join_natural(active_modules)}."


def _select_primary_gap(
    conversation: TripConversationState,
) -> PlannerChecklistItem | None:
    need_details = conversation.suggestion_board.need_details
    if not need_details:
        return None

    suggested_step = conversation.suggestion_board.suggested_step
    if suggested_step:
        for detail_id in STEP_DETAIL_IDS.get(suggested_step, ()):
            matching_detail = _find_detail(need_details, detail_id)
            if matching_detail:
                return matching_detail

    return need_details[0]


def _build_primary_gap_sentence(
    gap: PlannerChecklistItem,
    configuration: TripConfiguration,
) -> str:
    if gap.id == "route":
        if (
            configuration.selected_modules.flights
            and not configuration.from_location
            and not configuration.from_location_flexible
        ):
            return (
                "The next useful detail is your departure point, because flights are still in scope."
            )
        if not configuration.to_location:
            return "The next useful detail is the destination."
        return "The next useful detail is the route setup."

    if gap.id == "travellers":
        return (
            "The next useful detail is who is travelling, so the plan can size flights, stays, and activities properly."
        )

    if gap.id == "trip_style":
        return (
            "The next useful detail is the trip style, so the plan knows what to optimize for."
        )

    if gap.id == "budget":
        return (
            "The next useful detail is the budget posture or amount, especially for flights and stays."
        )

    if gap.id == "modules":
        return (
            "The last open choice is planning scope: confirm flights, hotels, activities, and weather, or tell me the narrower mix you want."
        )

    if gap.id == "timing":
        return "The next useful detail is the rough travel window."

    if gap.id == "trip_length":
        return "The next useful detail is how long to plan for."

    if gap.id == "weather":
        return "The next useful detail is the weather preference."

    return f"The next useful detail is {gap.label.lower()}."


def _build_remaining_gap_sentence(
    need_details: list[PlannerChecklistItem],
    primary_gap: PlannerChecklistItem,
) -> str | None:
    remaining = [
        _detail_label(detail)
        for detail in need_details
        if detail.id != primary_gap.id
    ]
    if not remaining:
        return None

    if len(remaining) > 4:
        return "After that, we can tidy up the remaining brief details."

    return f"After that, we can tidy up {_join_natural(remaining)}."


def _detail_value(
    details: list[PlannerChecklistItem],
    detail_id: str,
) -> str | None:
    detail = _find_detail(details, detail_id)
    return detail.value if detail and detail.value else None


def _find_detail(
    details: list[PlannerChecklistItem],
    detail_id: str,
) -> PlannerChecklistItem | None:
    return next((detail for detail in details if detail.id == detail_id), None)


def _detail_label(detail: PlannerChecklistItem) -> str:
    return DETAIL_LABELS.get(detail.id, detail.label.lower())


def _active_modules(configuration: TripConfiguration) -> list[str]:
    return [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]


def build_trip_brief_summary_lines(configuration: TripConfiguration) -> list[str]:
    lines: list[str] = []
    route = _build_route_summary(configuration)
    if route:
        lines.append(f"Route: {route}")

    timing = _build_timing_summary(configuration)
    if timing:
        lines.append(f"Timing: {timing}")

    travellers = _build_travellers_summary(configuration)
    if travellers:
        lines.append(f"Travellers: {travellers}")

    trip_focus = _build_trip_focus_summary(configuration)
    if trip_focus:
        lines.append(f"Trip focus: {trip_focus}")

    budget = _format_budget_context(configuration)
    if budget:
        lines.append(f"Budget: {budget}")

    active_modules = _active_modules(configuration)
    if active_modules:
        scope = (
            "flights, hotels, activities, and weather"
            if set(active_modules) == FULL_MODULE_SCOPE
            else _join_natural(active_modules)
        )
        lines.append(f"Planning scope: {scope}")

    return lines


def _build_brief_summary_sentence(configuration: TripConfiguration) -> str | None:
    lines = build_trip_brief_summary_lines(configuration)
    if not lines:
        return None
    return "Here is the brief I am carrying: " + "; ".join(lines) + "."


def _build_route_summary(configuration: TripConfiguration) -> str | None:
    if configuration.from_location and configuration.to_location:
        return f"{configuration.from_location} to {configuration.to_location}"
    if configuration.to_location and configuration.from_location_flexible:
        return f"flexible departure to {configuration.to_location}"
    return configuration.to_location or configuration.from_location


def _build_timing_summary(configuration: TripConfiguration) -> str | None:
    bits: list[str] = []
    if configuration.travel_window:
        bits.append(configuration.travel_window)
    elif configuration.start_date and configuration.end_date:
        bits.append(
            f"{configuration.start_date.isoformat()} to {configuration.end_date.isoformat()}"
        )
    elif configuration.start_date:
        bits.append(configuration.start_date.isoformat())
    elif configuration.end_date:
        bits.append(configuration.end_date.isoformat())
    if configuration.trip_length:
        bits.append(configuration.trip_length)
    if configuration.weather_preference:
        bits.append(f"{configuration.weather_preference} weather")
    return ", ".join(bits) if bits else None


def _build_travellers_summary(configuration: TripConfiguration) -> str | None:
    parts: list[str] = []
    if configuration.travelers.adults is not None and configuration.travelers.adults > 0:
        parts.append(
            f"{configuration.travelers.adults} adult"
            f"{'s' if configuration.travelers.adults != 1 else ''}"
        )
    if configuration.travelers.children is not None and configuration.travelers.children > 0:
        parts.append(
            f"{configuration.travelers.children} child"
            f"{'ren' if configuration.travelers.children != 1 else ''}"
        )
    if parts:
        return _join_natural(parts)
    if configuration.travelers_flexible:
        return "flexible for now"
    return None


def _build_trip_focus_summary(configuration: TripConfiguration) -> str | None:
    style = _format_trip_style(configuration)
    if not style:
        return None
    if configuration.custom_style and not configuration.activity_styles:
        return configuration.custom_style
    return style


def _join_natural(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _clean_llm_brief_response(text: str | None) -> str | None:
    if not text or not text.strip():
        return None
    cleaned = "\n".join(
        " ".join(line.split())
        for line in text.strip().splitlines()
        if line.strip()
    )
    if not cleaned:
        return None

    lowered = cleaned.lower()
    blocked_phrases = (
        "here's what i have so far",
        "to move this forward",
        "tell me this in chat",
        "right-hand checklist",
        "checklist if that is quicker",
        "checklist if that's quicker",
    )
    if any(phrase in lowered for phrase in blocked_phrases):
        return None
    return cleaned
