from app.graph.planner.turn_models import TripTurnUpdate
from app.schemas.conversation import ConversationBoardAction, PlannerProfileContext
from app.schemas.trip_conversation import TripConversationState, TripFieldKey
from app.schemas.trip_planning import TripConfiguration


def build_assistant_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    fallback_text: str | None,
    profile_context: dict,
    board_action: dict | None,
) -> str:
    profile = (
        PlannerProfileContext.model_validate(profile_context)
        if profile_context
        else PlannerProfileContext()
    )
    greeting_name = _get_greeting_name(profile)

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if (action and action.type == "confirm_trip_brief") or llm_update.confirmed_trip_brief:
        return _sanitize_assistant_text(
            _build_trip_brief_confirmation_response(configuration)
        )

    if conversation.phase == "awaiting_confirmation":
        return _sanitize_assistant_text(
            _build_final_confirmation_prompt(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
            )
        )

    if conversation.suggestion_board.mode == "details_collection":
        return _sanitize_assistant_text(
            _build_details_collection_response(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
                llm_update=llm_update,
                action=action,
            )
        )

    if (
        conversation.suggestion_board.mode == "destination_suggestions"
        and conversation.suggestion_board.cards
    ):
        destination_names = ", ".join(
            card.destination_name for card in conversation.suggestion_board.cards[:4]
        )
        greeting_prefix = f"Hey {greeting_name}. " if greeting_name else ""
        source_line = (
            f"{conversation.suggestion_board.source_context.rstrip('.!?')}. "
            if conversation.suggestion_board.source_context
            else ""
        )
        correction_line = (
            "If you're not actually leaving from around there, tell me your real departure point and I'll switch the shortlist. "
            if conversation.suggestion_board.source_context
            else ""
        )
        return _sanitize_assistant_text(
            f"{greeting_prefix}{source_line}"
            f"Here are four destination directions that fit what you asked for: {destination_names}. "
            f"{correction_line}"
            "Pick one on the board if one stands out, or tell me the destination you already have in mind."
        )

    if fallback_text and fallback_text.strip():
        return _sanitize_assistant_text(fallback_text)

    route_summary = (
        f"{configuration.from_location or 'your origin'} to "
        f"{configuration.to_location or 'your destination'}"
    )
    open_questions = [
        question.question.rstrip("?")
        for question in conversation.open_questions
        if question.status == "open"
    ]
    inferred_fields = [
        field
        for field, memory in conversation.memory.field_memory.items()
        if memory.source != "user_explicit"
    ]

    if conversation.phase == "opening":
        greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
        return _sanitize_assistant_text(
            (
            f"{greeting_prefix}I'm ready to shape this with you. "
            "Tell me where you want to go, roughly when, and where you'd leave from, "
            "and I'll keep the early draft soft until the trip direction is clear."
            )
        )

    if conversation.phase in {"collecting_requirements", "shaping_trip"}:
        summary = _build_trip_shape_summary(configuration)
        inferred_summary = _build_inferred_summary(inferred_fields)
        follow_up = " ".join(f"{question}?" for question in open_questions[:2])
        return _sanitize_assistant_text(f"{summary} {inferred_summary} {follow_up}")

    if conversation.phase == "enriching_modules":
        return _sanitize_assistant_text(
            (
            f"I've got enough shape to start planning around {route_summary}. "
            "I'll keep using soft assumptions where needed, pull in the relevant modules carefully, "
            "and call out anything that still needs a decision."
            )
        )

    return _sanitize_assistant_text(
        (
        f"The trip is now coherent enough to review around {route_summary}. "
        "I can keep refining the choices with you or turn this into a clearer trip summary next."
    )
    )


def _sanitize_assistant_text(text: str) -> str:
    sanitized = (
        text.replace("**", "")
        .replace("__", "")
        .replace("`", "")
        .replace("###", "")
        .replace("##", "")
    )
    lines = [" ".join(line.split()) for line in sanitized.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _build_details_collection_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
    llm_update: TripTurnUpdate,
    action: ConversationBoardAction | None,
) -> str:
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    board = conversation.suggestion_board
    from_summary = next(
        (
            item.value
            for item in board.highlighted_details
            if item.id == "from_location" and item.value
        ),
        configuration.from_location or "your current origin",
    )
    to_summary = next(
        (
            item.value
            for item in board.highlighted_details
            if item.id == "to_location" and item.value
        ),
        configuration.to_location or "that destination",
    )
    known_lines = [
        _format_checklist_line(item.label, item.value, known=True)
        for item in board.highlighted_details
        if item.id != "route"
    ]
    missing_lines = [
        _format_checklist_line(item.label, item.value, known=False)
        for item in board.missing_details
    ]
    bullet_lines = "\n".join([*known_lines, *missing_lines])
    intro_line = _build_details_intro(
        action=action,
        configuration=configuration,
        llm_update=llm_update,
        from_summary=from_summary,
        to_summary=to_summary,
    )
    return (
        f"{greeting_prefix}{intro_line} "
        "Before I shape this properly, I still need a few trip details from you. "
        "You can keep sending them here in chat, or use the board on the right to fill them in and confirm them in one go.\n"
        f"{bullet_lines}"
    )


def _build_final_confirmation_prompt(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    highlighted_details = conversation.suggestion_board.highlighted_details
    recap_lines = [
        _format_checklist_line(item.label, item.value, known=True)
        for item in highlighted_details
        if item.id != "route"
    ]
    recap = "\n".join(recap_lines)
    return (
        f"{greeting_prefix}I’ve got the full working brief in place now. Before I move on, please give this a quick check.\n"
        f"{recap}\n"
        "If this looks right, reply with something like yes, go ahead, or confirm it on the board. If anything needs changing, just tell me what to update."
    )


def _build_trip_brief_confirmation_response(configuration: TripConfiguration) -> str:
    route = " -> ".join(
        part for part in [configuration.from_location, configuration.to_location] if part
    )
    timing_bits = [
        configuration.travel_window,
        configuration.trip_length,
    ]
    timing = ", ".join(bit for bit in timing_bits if bit)
    return (
        f"Perfect. I’ll treat {route or 'this trip brief'} as confirmed and move into the next planning step now. "
        f"{'I’ll plan around ' + timing + '. ' if timing else ''}"
        "If you want to change anything later, you can still do that in chat."
    )


def _format_checklist_line(label: str, value: str | None, *, known: bool) -> str:
    status = "Known" if known else "Still needed"
    detail = value or "Tell me this in chat or confirm it on the board"
    return f"- {label}: {detail} ({status})"


def _build_details_intro(
    *,
    action: ConversationBoardAction | None,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    from_summary: str,
    to_summary: str,
) -> str:
    if action and action.type == "select_destination_suggestion":
        return (
            f"I see you’re leaning toward {to_summary}. I’ll use it as the working destination from {from_summary} for now, and you can still change either part of the route later."
        )

    if action and action.type == "confirm_trip_details":
        return (
            f"Nice — I’ve pulled those board details into the working brief for {from_summary} to {to_summary}."
        )

    captured = _describe_captured_fields(configuration, llm_update)
    if captured:
        return (
            f"I’ve added {captured} for {from_summary} to {to_summary}."
        )

    return f"I’ve got {from_summary} to {to_summary} as the working route so far."


def _describe_captured_fields(
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
) -> str | None:
    changed_fields = [
        field
        for field in [*llm_update.confirmed_fields, *llm_update.inferred_fields]
        if field not in {"from_location", "to_location", "selected_modules"}
    ]
    if not changed_fields:
        return None

    labels: list[str] = []
    for field in changed_fields:
        label = _field_value_label(configuration, field)
        if label and label not in labels:
            labels.append(label)
    if not labels:
        return None
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def _field_value_label(configuration: TripConfiguration, field: TripFieldKey) -> str | None:
    if field == "travel_window" and configuration.travel_window:
        return f"the timing as {configuration.travel_window}"
    if field == "trip_length" and configuration.trip_length:
        return f"the trip length as {configuration.trip_length}"
    if field == "adults" and configuration.travelers.adults is not None:
        return f"{configuration.travelers.adults} adult{'s' if configuration.travelers.adults != 1 else ''}"
    if field == "children" and configuration.travelers.children is not None:
        return f"{configuration.travelers.children} child{'ren' if configuration.travelers.children != 1 else ''}"
    if field == "activity_styles" and configuration.activity_styles:
        return f"the trip style as {', '.join(configuration.activity_styles)}"
    if field == "budget_posture" and configuration.budget_posture:
        return f"the budget as {_format_budget_posture(configuration.budget_posture)}"
    if field == "budget_gbp" and configuration.budget_gbp is not None:
        return f"the budget at about GBP {configuration.budget_gbp:.0f}"
    return None


def _format_modules(selected_modules: dict[str, bool]) -> str:
    modules = [name for name, enabled in selected_modules.items() if enabled]
    return ", ".join(modules) if modules else ""


def _format_travelers(*, adults: int | None, children: int | None) -> str:
    parts: list[str] = []
    if adults is not None:
        parts.append(f"{adults} adult{'s' if adults != 1 else ''}")
    if children is not None:
        parts.append(f"{children} child{'ren' if children != 1 else ''}")
    return " and ".join(parts)


def _format_budget_posture(value: object | None) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.replace("_", "-")


def _get_greeting_name(profile: PlannerProfileContext) -> str | None:
    if profile.first_name and profile.first_name.strip():
        return profile.first_name.strip()

    if profile.display_name and profile.display_name.strip():
        return profile.display_name.strip().split(" ")[0]

    return None


def _build_trip_shape_summary(configuration: TripConfiguration) -> str:
    parts: list[str] = []
    if configuration.to_location:
        parts.append(f"a trip centered on {configuration.to_location}")
    if configuration.activity_styles:
        parts.append(f"with a {', '.join(configuration.activity_styles[:2])} feel")
    if configuration.travel_window:
        parts.append(f"around {configuration.travel_window}")
    if configuration.trip_length:
        parts.append(f"for {configuration.trip_length}")

    if not parts:
        return "I don't want to lock the wrong details too early."

    return f"I can already start shaping this as {' '.join(parts)}."


def _build_inferred_summary(inferred_fields: list[TripFieldKey]) -> str:
    labels = [_field_label(field) for field in inferred_fields[:2]]
    if not labels:
        return "I'm keeping anything uncertain soft instead of pretending it's confirmed."
    if len(labels) == 1:
        return f"I'm still treating {labels[0]} as provisional."
    return f"I'm still treating {labels[0]} and {labels[1]} as provisional."


def _field_label(field: TripFieldKey) -> str:
    return {
        "from_location": "your departure point",
        "to_location": "the destination",
        "start_date": "the travel window",
        "end_date": "the trip length",
        "travel_window": "the rough travel timing",
        "trip_length": "the rough trip length",
        "budget_posture": "the budget posture",
        "budget_gbp": "the budget posture",
        "adults": "the traveler count",
        "children": "the child traveler count",
        "activity_styles": "the trip style",
        "selected_modules": "the active planning modules",
    }[field]
