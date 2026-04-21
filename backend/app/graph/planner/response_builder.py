from app.graph.planner.turn_models import TripTurnUpdate
from app.schemas.conversation import ConversationBoardAction, PlannerProfileContext
from app.schemas.trip_conversation import (
    PlannerConfirmationStatus,
    PlannerFinalizedVia,
    TripConversationState,
    TripFieldKey,
)
from app.schemas.trip_planning import TripConfiguration


def build_assistant_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    brief_confirmed: bool,
    fallback_text: str | None,
    profile_context: dict,
    board_action: dict | None,
    confirmation_status: PlannerConfirmationStatus,
    finalized_via: PlannerFinalizedVia | None,
    confirmation_transition: str = "none",
    locked_without_reopen: bool = False,
    quick_plan_started: bool = False,
    provider_activation: dict | None = None,
) -> str:
    profile = (
        PlannerProfileContext.model_validate(profile_context)
        if profile_context
        else PlannerProfileContext()
    )
    greeting_name = _get_greeting_name(profile)

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if confirmation_transition == "finalized":
        return _sanitize_assistant_text(
            _build_plan_finalized_response(
                configuration=configuration,
                greeting_name=greeting_name,
                finalized_via=finalized_via,
            )
        )

    if confirmation_transition == "reopened":
        return _sanitize_assistant_text(
            _build_reopen_planning_response(
                configuration=configuration,
                greeting_name=greeting_name,
            )
        )

    if locked_without_reopen and confirmation_status == "finalized":
        return _sanitize_assistant_text(
            _build_finalized_lock_response(
                configuration=configuration,
                greeting_name=greeting_name,
            )
        )

    if _requested_advanced_plan(action, llm_update, conversation, quick_plan_started):
        return _sanitize_assistant_text(
            _build_advanced_planning_fallback_response(
                configuration=configuration,
                greeting_name=greeting_name,
            )
        )

    if _requested_quick_plan(action, llm_update, conversation, quick_plan_started):
        return _sanitize_assistant_text(
            _build_quick_plan_response(
                configuration=configuration,
                greeting_name=greeting_name,
            )
        )

    if conversation.planning_mode == "quick" and not quick_plan_started:
        return _sanitize_assistant_text(
            _build_quick_plan_waiting_response(
                configuration=configuration,
                greeting_name=greeting_name,
                provider_activation=provider_activation or {},
            )
        )

    if brief_confirmed and confirmation_status != "finalized":
        return _sanitize_assistant_text(
            _build_trip_brief_confirmation_response(
                configuration=configuration,
                greeting_name=greeting_name,
                profile=profile,
            )
        )

    if conversation.suggestion_board.mode == "planning_mode_choice":
        return _sanitize_assistant_text(
            _build_planning_mode_choice_response(
                configuration=configuration,
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

    if conversation.suggestion_board.mode == "decision_cards" and conversation.decision_cards:
        return _sanitize_assistant_text(
            _build_decision_cards_response(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
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
            "If you are not actually leaving from around there, tell me your real departure point and I will switch the shortlist. "
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
        if memory.source not in {"user_explicit", "board_action"}
    ]

    if conversation.phase == "opening":
        greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
        profile_soft_start = _build_profile_soft_start_line(
            profile=profile,
            configuration=configuration,
        )
        return _sanitize_assistant_text(
            (
                f"{greeting_prefix}I am ready to shape this with you. "
                "Tell me where you want to go, roughly when, and where you would leave from, "
                "and I will keep the early draft soft until the trip direction is clear."
                f"{' ' + profile_soft_start if profile_soft_start else ''}"
            )
        )

    if conversation.phase in {"collecting_requirements", "shaping_trip"}:
        return _sanitize_assistant_text(
            _build_progress_response(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
                inferred_fields=inferred_fields,
                open_questions=open_questions,
                profile=profile,
            )
        )

    if conversation.phase == "enriching_modules":
        return _sanitize_assistant_text(
            (
                f"I have enough shape to start planning around {route_summary}. "
                "I will use soft assumptions where needed, pull in the relevant modules carefully, "
                "and call out anything that still needs a decision."
            )
        )

    base_response = (
        f"The trip is now coherent enough to review around {route_summary}. "
        "I can keep refining the choices with you or turn this into a clearer trip summary next."
    )
    if conversation.planning_mode == "quick" and confirmation_status != "finalized":
        base_response += (
            " If you want to confirm this plan, say so here and I'll lock it down. "
            "That will finalize the current trip, save the brochure-ready version in Saved Trips, and keep it ready for download there."
        )
    return _sanitize_assistant_text(base_response)


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
    route_summary = next(
        (item.value for item in board.have_details if item.id == "route" and item.value),
        "the working route",
    )
    have_lines = [
        _format_checklist_line(item.label, item.value)
        for item in board.have_details
    ]
    need_lines = [
        _format_checklist_line(item.label, item.value)
        for item in board.need_details
    ]
    intro_line = _build_details_intro(
        action=action,
        configuration=configuration,
        llm_update=llm_update,
        route_summary=route_summary,
    )
    section_lines = []
    if have_lines:
        section_lines.append("Here's what I have so far:")
        section_lines.extend(have_lines)
    if need_lines:
        section_lines.append("To move this forward, I still need:")
        section_lines.extend(need_lines)
    else:
        section_lines.append(
            "If all of that looks right, confirm here in chat and I will move ahead. If you want to tweak anything first, you can edit it on the board."
        )
    bullet_lines = "\n".join(section_lines)
    return (
        f"{greeting_prefix}{intro_line} "
        "If anything looks off, just correct me. You can keep replying here in chat, or use the board on the right if that is quicker.\n"
        f"{bullet_lines}"
    )


def _build_trip_brief_confirmation_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
    profile: PlannerProfileContext,
) -> str:
    route = " -> ".join(
        part for part in [configuration.from_location, configuration.to_location] if part
    )
    timing_bits = [
        configuration.travel_window,
        configuration.trip_length,
    ]
    timing = ", ".join(bit for bit in timing_bits if bit)
    greeting_prefix = f"Perfect, {greeting_name}. " if greeting_name else "Perfect. "
    profile_soft_start = _build_profile_soft_start_line(
        profile=profile,
        configuration=configuration,
    )
    return (
        f"{greeting_prefix}I have {route or 'this trip brief'} locked in as the working direction now. "
        f"{'I will plan around ' + timing + '. ' if timing else ''}"
        "You can let me spin up a Quick Plan next, or wait for Advanced Planning once that mode is ready."
        f"{' ' + profile_soft_start if profile_soft_start else ''}"
    )


def _build_decision_cards_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    primary_card = conversation.decision_cards[0]
    follow_up_titles = [card.title for card in conversation.decision_cards[1:3]]
    next_choice_line = (
        f"The strongest next choice is {primary_card.title.lower()}."
        if primary_card.title
        else "The board has the next useful choice ready."
    )
    secondary_line = (
        f" After that, we can look at {' and '.join(title.lower() for title in follow_up_titles)}."
        if follow_up_titles
        else ""
    )
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}I have enough context to stop asking filler questions for {destination}. "
        f"{next_choice_line} {primary_card.description} "
        f"I can already sketch a strong first direction for {destination} once you choose that.{secondary_line}"
    )


def _build_planning_mode_choice_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    route = " -> ".join(
        part for part in [configuration.from_location, configuration.to_location] if part
    )
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    return (
        f"{greeting_prefix}the trip brief is ready around {route or 'this route'}. "
        "You can choose Quick Plan now if you want a fast first draft itinerary, and you can keep refining it in chat afterwards. "
        "Advanced Planning is visible on the board too, but it is still in development."
    )


def _build_quick_plan_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Great, {greeting_name}. " if greeting_name else "Great. "
    destination = configuration.to_location or "the trip"
    return (
        f"{greeting_prefix}I have started a Quick Plan for {destination} and built a first draft itinerary. "
        "Treat this as a working version, not a locked final plan. "
        "You can now keep refining the flights, pacing, hotels, activities, or budget directly in chat. "
        "If you want to confirm this plan, say so here and I'll lock it down. "
        "That will finalize the current trip plan and save the brochure-ready version in Saved Trips, where you can open it and download the brochure later."
    )


def _build_advanced_planning_fallback_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Got it, {greeting_name}. " if greeting_name else "Got it. "
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}Advanced Planning is not available yet, so I am defaulting to Quick Plan for {destination} and building the first itinerary draft now. "
        "Once it appears on the board, you can keep refining it with me in chat. "
        "When it looks right, confirm it here and I'll save the brochure-ready version in Saved Trips."
    )


def _build_quick_plan_waiting_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
    provider_activation: dict,
) -> str:
    greeting_prefix = f"Got it, {greeting_name}. " if greeting_name else "Got it. "
    destination = configuration.to_location or "this trip"
    blockers = provider_activation.get("blocked_modules", {})
    blocker_text = next(
        (
            blockers[module_name][0]
            for module_name in ["flights", "hotels", "activities", "weather"]
            if blockers.get(module_name)
        ),
        "a few core details are still soft",
    )
    return (
        f"{greeting_prefix}Quick Plan is selected for {destination}, but I am not triggering live planning yet because {blocker_text}. "
        "I will keep the brief structured and move into the first draft as soon as the remaining blocker is resolved."
    )


def _build_plan_finalized_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
    finalized_via: PlannerFinalizedVia | None,
) -> str:
    greeting_prefix = f"Locked in, {greeting_name}. " if greeting_name else "Locked in. "
    destination = configuration.to_location or "this trip"
    via_line = (
        "I used the board confirmation to finalize it. "
        if finalized_via == "board"
        else "I finalized it from your chat confirmation. "
    )
    return (
        f"{greeting_prefix}{via_line}"
        f"The current plan for {destination} is now finalized and the brochure-ready version is saved in Saved Trips. "
        "You can open it there, review the details, and download the brochure when you need it. "
        "If you want to change anything later, just ask me to reopen planning and I will unlock it."
    )


def _build_reopen_planning_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Absolutely, {greeting_name}. " if greeting_name else "Absolutely. "
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}I have reopened planning for {destination}. "
        "The finalized lock is off now, so we can keep refining the trip in chat and update the board before you save a new brochure-ready version."
    )


def _build_finalized_lock_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Just so you know, {greeting_name}, " if greeting_name else "Just so you know, "
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}{destination} is currently finalized, so I have kept the saved plan locked. "
        "If you want to make changes, ask me to reopen planning first and I will unlock it before we edit anything."
    )


def _format_checklist_line(label: str, value: str | None) -> str:
    detail = value or "Tell me this in chat or confirm it on the board."
    return f"- {label}: {detail}"


def _build_details_intro(
    *,
    action: ConversationBoardAction | None,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    route_summary: str,
) -> str:
    if action and action.type == "select_destination_suggestion":
        return (
            f"I can see {route_summary} as the strongest direction so far, and we can still change any part of it."
        )

    if action and action.type == "confirm_trip_details":
        return (
            f"Nice, I have pulled those board details into the working brief for {route_summary}."
        )

    captured = _describe_captured_fields(configuration, llm_update)
    if captured:
        return f"I have added {captured} around {route_summary}."

    return f"I have {route_summary} as the working route so far."


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
        return "I do not want to lock the wrong details too early."

    return f"I can already start shaping this as {' '.join(parts)}."


def _build_progress_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
    inferred_fields: list[TripFieldKey],
    open_questions: list[str],
    profile: PlannerProfileContext,
) -> str:
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    working_shape = _build_working_shape_description(configuration)
    confirmed_line = (
        f"{greeting_prefix}I now have {working_shape} as the working shape."
        if working_shape
        else f"{greeting_prefix}I have enough signal to keep shaping this without pretending the brief is fully locked."
    )
    provisional_line = _build_provisional_detail_line(inferred_fields)
    profile_soft_start = _build_profile_soft_start_line(
        profile=profile,
        configuration=configuration,
    )
    next_question_line = (
        f"The main thing I'd confirm next is: {open_questions[0]}?"
        if open_questions
        else "If that still looks right, I can tighten the next pass from here."
    )

    if conversation.phase == "shaping_trip":
        destination = configuration.to_location or "this trip"
        return (
            f"{confirmed_line} {provisional_line} "
            f"{profile_soft_start + ' ' if profile_soft_start else ''}"
            f"I can already sketch a strong first direction for {destination} and refine the rest with you after. "
            f"{next_question_line}"
        )

    return (
        f"{confirmed_line} {provisional_line} "
        f"{profile_soft_start + ' ' if profile_soft_start else ''}"
        f"{next_question_line}"
    )


def _build_profile_soft_start_line(
    *,
    profile: PlannerProfileContext,
    configuration: TripConfiguration,
) -> str | None:
    if configuration.from_location:
        return None

    home_base = _profile_home_base_summary(profile)
    if not home_base:
        return None

    return (
        f"If it helps, I can use your saved home base around {home_base} as a starting point, "
        "but only if that's right for this trip."
    )


def _profile_home_base_summary(profile: PlannerProfileContext) -> str | None:
    return (
        profile.location_summary
        or profile.home_city
        or profile.home_airport
        or profile.home_country
    )


def _build_working_shape_description(configuration: TripConfiguration) -> str | None:
    parts: list[str] = []
    if configuration.to_location:
        parts.append(configuration.to_location)
    timing = _build_timing_description(configuration)
    if timing:
        parts.append(timing)
    if configuration.activity_styles:
        parts.append(f"with a {', '.join(configuration.activity_styles[:2])} direction")
    elif _active_module_count(configuration) < 4:
        parts.append(f"focused on {_format_selected_modules(configuration)}")
    if configuration.budget_posture:
        parts.append(f"with a {_format_budget_posture(configuration.budget_posture)} budget posture")
    return ", ".join(part for part in parts if part) or None


def _build_timing_description(configuration: TripConfiguration) -> str | None:
    bits: list[str] = []
    if configuration.travel_window:
        bits.append(f"around {configuration.travel_window}")
    elif configuration.start_date and configuration.end_date:
        bits.append(
            f"from {configuration.start_date.isoformat()} to {configuration.end_date.isoformat()}"
        )
    elif configuration.start_date:
        bits.append(f"from {configuration.start_date.isoformat()}")
    if configuration.trip_length:
        bits.append(f"for {configuration.trip_length}")
    return " ".join(bits) if bits else None


def _build_provisional_detail_line(inferred_fields: list[TripFieldKey]) -> str:
    labels = [_field_label(field) for field in inferred_fields[:2]]
    if not labels:
        return "I am not leaning on hidden assumptions here."
    if len(labels) == 1:
        return f"I'm still treating {labels[0]} as provisional."
    return f"I'm still treating {labels[0]} and {labels[1]} as provisional."


def _active_module_count(configuration: TripConfiguration) -> int:
    return sum(
        1
        for enabled in configuration.selected_modules.model_dump(mode="json").values()
        if enabled
    )


def _format_selected_modules(configuration: TripConfiguration) -> str:
    modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]
    return ", ".join(modules)


def _build_inferred_summary(inferred_fields: list[TripFieldKey]) -> str:
    labels = [_field_label(field) for field in inferred_fields[:2]]
    if not labels:
        return "I am keeping anything uncertain soft instead of pretending it is confirmed."
    if len(labels) == 1:
        return f"I am still treating {labels[0]} as provisional."
    return f"I am still treating {labels[0]} and {labels[1]} as provisional."


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


def _requested_quick_plan(
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
    conversation: TripConversationState,
    quick_plan_started: bool,
) -> bool:
    return bool(
        quick_plan_started
        and
        conversation.planning_mode == "quick"
        and conversation.planning_mode_status == "selected"
        and (
            (action and action.type == "select_quick_plan")
            or llm_update.requested_planning_mode == "quick"
        )
    )


def _requested_advanced_plan(
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
    conversation: TripConversationState,
    quick_plan_started: bool,
) -> bool:
    return bool(
        quick_plan_started
        and
        conversation.planning_mode == "quick"
        and conversation.planning_mode_status == "advanced_unavailable_fallback"
        and (
            (action and action.type == "select_advanced_plan")
            or llm_update.requested_planning_mode == "advanced"
        )
    )
