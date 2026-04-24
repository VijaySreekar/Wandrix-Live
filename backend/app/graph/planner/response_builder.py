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
    planning_mode_choice_required: bool = False,
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
                conversation=conversation,
                greeting_name=greeting_name,
                finalized_via=finalized_via,
                advanced_finalization=_is_advanced_finalization_request(
                    action=action,
                    llm_update=llm_update,
                ),
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

    if planning_mode_choice_required and conversation.planning_mode is None:
        return _sanitize_assistant_text(
            _build_planning_mode_gate_response(
                configuration=configuration,
                greeting_name=greeting_name,
            )
        )

    if _requested_advanced_plan(action, llm_update, conversation):
        return _sanitize_assistant_text(
            _build_advanced_plan_selected_response(
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

    if (
        conversation.planning_mode == "advanced"
        and conversation.advanced_step == "resolve_dates"
    ):
        return _sanitize_assistant_text(
            _build_advanced_date_resolution_response(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
                action=action,
            )
        )

    if conversation.planning_mode == "advanced" and conversation.advanced_step == "choose_anchor":
        return _sanitize_assistant_text(
            _build_advanced_choose_anchor_response(
                configuration=configuration,
                greeting_name=greeting_name,
            )
        )

    if conversation.planning_mode == "advanced" and conversation.advanced_step == "review":
        return _sanitize_assistant_text(
            _build_advanced_review_response(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
            )
        )

    if conversation.planning_mode == "advanced" and conversation.advanced_step == "anchor_flow":
        return _sanitize_assistant_text(
            _build_advanced_anchor_flow_response(
                configuration=configuration,
                conversation=conversation,
                greeting_name=greeting_name,
                action=action,
                llm_update=llm_update,
                fallback_text=fallback_text,
            )
        )

    if brief_confirmed and confirmation_status != "finalized":
        return _sanitize_assistant_text(
            _build_trip_brief_confirmation_response(
                configuration=configuration,
                greeting_name=greeting_name,
                profile=profile,
                planning_mode=conversation.planning_mode,
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

    unresolved_destinations = _unresolved_destination_options(
        conversation=conversation,
        llm_update=llm_update,
    )
    if (
        conversation.suggestion_board.mode == "helper"
        and configuration.to_location is None
        and len(unresolved_destinations) >= 2
    ):
        greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
        if len(unresolved_destinations) == 2:
            destination_line = (
                f"{unresolved_destinations[0]} and {unresolved_destinations[1]} are both still live options."
            )
        else:
            destination_line = (
                f"{', '.join(unresolved_destinations[:-1])}, and {unresolved_destinations[-1]} are all still live options."
            )
        return _sanitize_assistant_text(
            f"{greeting_prefix}{destination_line} "
            "I do not need to force the destination yet. "
            "Pick one when you are ready, or tell me to keep comparing them and I will stay broad a little longer."
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
        greeting_prefix = f"Hey {greeting_name}, " if greeting_name else "Hi, "
        profile_soft_start = _build_profile_soft_start_line(
            profile=profile,
            configuration=configuration,
        )
        return _sanitize_assistant_text(
            (
                f"{greeting_prefix}I'm Wandrix, and I can help shape anything from a rough travel idea to a polished trip plan. "
                "Tell me where you want to go, roughly when, or even just the kind of trip you want, "
                "and I will keep the early draft soft until the direction is clear."
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
    advanced_guidance = (
        "This is the shared brief-building step for Advanced Planning, so once these details are solid I'll move into the first anchor choice instead of drafting the itinerary right away. "
        if conversation.planning_mode == "advanced"
        else ""
    )
    flexible_departure_guidance = (
        "You do not need to lock the departure point yet if it is still flexible for now. "
        if configuration.from_location_flexible
        else ""
    )
    return (
        f"{greeting_prefix}{intro_line} "
        f"{advanced_guidance}"
        f"{flexible_departure_guidance}"
        "If anything looks off, just correct me. You can keep replying here in chat, or use the board on the right if that is quicker.\n"
        f"{bullet_lines}"
    )


def _build_trip_brief_confirmation_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
    profile: PlannerProfileContext,
    planning_mode: str | None,
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
    if planning_mode == "advanced":
        closing_line = (
            "Advanced Planning is selected, so I'll keep this guided and move into the next decision step instead of drafting the itinerary right away."
        )
    elif planning_mode == "quick":
        closing_line = (
            "Quick Plan is selected, so I'll build the draft itinerary as soon as the remaining blockers are resolved."
        )
    else:
        closing_line = (
            "Choose Quick Plan for a fast draft, or Advanced Planning for a more guided flow."
        )

    return (
        f"{greeting_prefix}I have {route or 'this trip brief'} locked in as the working direction now. "
        f"{'I will plan around ' + timing + '. ' if timing else ''}"
        f"{closing_line}"
        f"{' ' + profile_soft_start if profile_soft_start else ''}"
    )


def _build_planning_mode_gate_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Before I proceed, {greeting_name}, " if greeting_name else "Before I proceed, "
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}choose how you want Wandrix to plan {destination}. "
        "Pick Quick Plan if you want the fastest route to a first draft itinerary, or Advanced Planning if you want a more guided step-by-step flow. "
        "I've kept your message as the working starting point either way."
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
        "Choose Quick Plan if you want the fastest route to a first draft itinerary, or Advanced Planning if you want to keep this more guided and step by step."
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


def _build_advanced_plan_selected_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Got it, {greeting_name}. " if greeting_name else "Got it. "
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}Advanced Planning is selected for {destination}. "
        "I'll keep collecting the brief with you in the shared brief-building step, then move into the guided anchor choice once the trip is ready for the next decision."
    )


def _build_advanced_choose_anchor_response(
    *,
    configuration: TripConfiguration,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Perfect, {greeting_name}. " if greeting_name else "Perfect. "
    destination = configuration.to_location or "this trip"
    return (
        f"{greeting_prefix}The brief for {destination} is strong enough to move into Advanced Planning properly now. "
        "Instead of drafting the itinerary right away, the next step is choosing what should lead the trip first: flights, stay, trip style, or activities."
    )


def _build_advanced_date_resolution_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
    action: ConversationBoardAction | None,
) -> str:
    greeting_prefix = f"Perfect, {greeting_name}. " if greeting_name else "Perfect. "
    date_resolution = conversation.advanced_date_resolution
    timing_text = date_resolution.source_timing_text or configuration.travel_window or "the rough timing you gave me"
    trip_length_text = date_resolution.source_trip_length_text or configuration.trip_length
    selected_start = date_resolution.selected_start_date
    selected_end = date_resolution.selected_end_date
    selected_reason = date_resolution.selection_rationale

    if (
        action
        and action.type in {"select_date_option", "pick_dates_for_me"}
        and selected_start
        and selected_end
    ):
        window_label = _format_date_window(selected_start, selected_end)
        why_line = (
            f" I chose it because {selected_reason.lower()}."
            if selected_reason
            else ""
        )
        return (
            f"{greeting_prefix}I'll use {window_label} as the current working trip window for now.{why_line} "
            "If that still looks right, confirm it on the board and then I’ll move into the first real Advanced Planning anchor."
        )

    if selected_start and selected_end and date_resolution.selection_status == "confirmed":
        return (
            f"{greeting_prefix}Great, the working trip window is locked in. "
            "Now we can move into the first Advanced Planning anchor with much stronger timing underneath it."
        )

    timing_line = (
        f"You said {timing_text}"
        if not trip_length_text
        else f"You said {timing_text} for {trip_length_text}"
    )
    weekend_line = (
        " I translated that into concrete weekend windows so the rest of the planning can stay practical."
        if "weekend" in timing_text.lower() or (trip_length_text and "weekend" in trip_length_text.lower())
        else " I narrowed that into three workable date windows so the next planning step is grounded in something concrete."
    )
    return (
        f"{greeting_prefix}{timing_line}.{weekend_line} "
        "Pick the date window that feels right, or use Pick for me and I’ll choose the strongest one and explain why before we proceed."
    )


def _build_advanced_anchor_flow_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
    fallback_text: str | None,
) -> str:
    greeting_prefix = f"Perfect, {greeting_name}. " if greeting_name else "Perfect. "
    destination = configuration.to_location or "this trip"
    if conversation.advanced_anchor == "activities":
        return _build_advanced_activities_response(
            configuration=configuration,
            conversation=conversation,
            greeting_prefix=greeting_prefix,
            action=action,
            llm_update=llm_update,
            fallback_text=fallback_text,
        )
    if conversation.advanced_anchor == "stay":
        return _build_advanced_stay_response(
            configuration=configuration,
            conversation=conversation,
            greeting_prefix=greeting_prefix,
            action=action,
        )
    if conversation.advanced_anchor == "flight":
        return _build_advanced_flights_response(
            configuration=configuration,
            conversation=conversation,
            greeting_prefix=greeting_prefix,
            action=action,
            llm_update=llm_update,
        )
    if conversation.advanced_anchor == "trip_style":
        return _build_advanced_trip_style_response(
            configuration=configuration,
            conversation=conversation,
            greeting_prefix=greeting_prefix,
            action=action,
            llm_update=llm_update,
        )
    advanced_anchor = conversation.advanced_anchor
    anchor_label = (
        advanced_anchor.replace("_", " ") if advanced_anchor else "that planning anchor"
    )
    return (
        f"{greeting_prefix}We'll lead {destination} with {anchor_label} first. "
        "I'll keep this in Advanced Planning mode and use that choice as the first deeper planning path."
    )


def _build_advanced_flights_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_prefix: str,
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
) -> str:
    destination = configuration.to_location or "this trip"
    flight_planning = conversation.flight_planning

    if flight_planning.results_status == "blocked" and flight_planning.missing_requirements:
        missing = ", ".join(flight_planning.missing_requirements)
        return (
            f"{greeting_prefix}Flights are the next planning branch, but I still need {missing} before I can shape working outbound and return choices. "
            "Once that is in place, the board will switch from route readiness into selectable flight options."
        )

    if (
        action
        and action.type == "select_flight_strategy"
        and flight_planning.selected_strategy
    ) or any(update.action == "select_strategy" for update in llm_update.requested_flight_updates):
        strategy_label = _flight_strategy_label(
            flight_planning.selected_strategy or "best_timing"
        )
        return (
            f"{greeting_prefix}I set the flight posture to {strategy_label}. "
            "Now choose the outbound and return options that Wandrix should treat as working planning inputs."
        )

    if (
        action
        and action.type in {"select_outbound_flight", "select_return_flight"}
    ) or any(update.action in {"select_outbound", "select_return"} for update in llm_update.requested_flight_updates):
        summary = (
            flight_planning.selection_summary
            or "That flight choice is saved as a working planning input."
        )
        return (
            f"{greeting_prefix}{summary} "
            "This is still only a planning input, and it gives the rest of Advanced Planning a clearer travel shape."
        )

    if (
        action and action.type in {"keep_flights_open", "confirm_flight_selection"}
    ) or any(update.action in {"confirm", "keep_open"} for update in llm_update.requested_flight_updates):
        next_anchor = _recommend_advanced_anchor_after_flights(
            configuration=configuration,
            conversation=conversation,
        )
        next_anchor_label = next_anchor.replace("_", " ")
        completion = (
            flight_planning.completion_summary
            or "Flights now have enough working shape for downstream planning."
        )
        timing_line = " ".join(
            note
            for note in [
                flight_planning.arrival_day_impact_summary,
                flight_planning.departure_day_impact_summary,
            ]
            if note
        )
        return (
            f"{greeting_prefix}{completion}"
            f"{' ' + timing_line if timing_line else ''} "
            f"The board is back to the remaining planning choices, and the cleanest next move is {next_anchor_label}."
        )

    if flight_planning.results_status == "placeholder":
        return (
            f"{greeting_prefix}We’re choosing the working flight shape for {destination}. "
            "Exact inventory is thin, so the board is showing planning placeholders instead of treating any schedule as final."
        )

    option_count = len(flight_planning.outbound_options) + len(flight_planning.return_options)
    return (
        f"{greeting_prefix}We’re choosing which flight shape Wandrix should build around for {destination}. "
        f"The board has {option_count} working option{'s' if option_count != 1 else ''} split across outbound and return, plus strategy cards for the tradeoff."
    )


def _build_advanced_trip_style_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_prefix: str,
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
) -> str:
    destination = configuration.to_location or "this trip"
    trip_style_planning = conversation.trip_style_planning
    primary = trip_style_planning.selected_primary_direction
    accent = trip_style_planning.selected_accent
    primary_label = (
        _trip_direction_primary_label(primary) if primary else "balanced"
    )
    accent_line = (
        f" with a {_trip_direction_accent_label(accent)} accent" if accent else ""
    )

    if action and action.type == "select_trip_style_direction_primary" and primary:
        return (
            f"{greeting_prefix}I’ve moved {destination} toward a {primary_label} direction. "
            "You can still add or change the accent before confirming it as the working trip character."
        )

    if action and action.type == "select_trip_style_direction_accent" and accent:
        return (
            f"{greeting_prefix}I added a { _trip_direction_accent_label(accent) } accent to the trip direction. "
            "That will change how activities are ranked once you confirm this working character."
        )

    if action and action.type == "clear_trip_style_direction_accent":
        return (
            f"{greeting_prefix}I cleared the optional accent, so the trip is back to a cleaner {primary_label} direction. "
            "You can leave it that way or add another accent before confirming."
        )

    if (
        action and action.type in {"confirm_trip_style_direction", "keep_current_trip_style_direction"}
    ) or any(update.action in {"confirm", "keep_current"} for update in llm_update.requested_trip_style_direction_updates):
        influence_line = (
            f" {trip_style_planning.downstream_influence_summary}"
            if trip_style_planning.downstream_influence_summary
            else ""
        )
        return (
            f"{greeting_prefix}{destination} is now set as a {primary_label}{accent_line} trip.{influence_line} "
            "Next, choose the day pace so Activities knows whether to keep the days slow, balanced, or full."
        )

    if action and action.type == "select_trip_style_pace":
        pace_label = _trip_pace_label(trip_style_planning.selected_pace)
        return (
            f"{greeting_prefix}I set the working pace to {pace_label.lower()}. "
            "That will shape how many flexible activity ideas Wandrix auto-places into each day."
        )

    if (
        action and action.type in {"confirm_trip_style_pace", "keep_current_trip_style_pace"}
    ) or any(update.action in {"confirm", "keep_current"} for update in llm_update.requested_trip_style_pace_updates):
        pace_label = _trip_pace_label(trip_style_planning.selected_pace).lower()
        pace_line = (
            f" {trip_style_planning.pace_downstream_influence_summary}"
            if trip_style_planning.pace_downstream_influence_summary
            else ""
        )
        return (
            f"{greeting_prefix}{destination} is now set as a {primary_label}{accent_line} trip at a {pace_label} pace.{pace_line} "
            "Last step: choose the final tie-breakers so Activities knows how to resolve close calls."
        )

    if action and action.type == "set_trip_style_tradeoff":
        return (
            f"{greeting_prefix}I updated that Trip Style tie-breaker. "
            "These tradeoffs will shape ranking when two good activity options are close, without becoming hard constraints."
        )

    if (
        action and action.type in {"confirm_trip_style_tradeoffs", "keep_current_trip_style_tradeoffs"}
    ) or any(update.action in {"confirm", "keep_current"} for update in llm_update.requested_trip_style_tradeoff_updates):
        next_anchor = _recommend_advanced_anchor_after_trip_style(
            configuration=configuration,
            conversation=conversation,
        )
        next_anchor_label = next_anchor.replace("_", " ")
        tradeoff_line = (
            f" {trip_style_planning.tradeoff_downstream_influence_summary}"
            if trip_style_planning.tradeoff_downstream_influence_summary
            else ""
        )
        return (
            f"{greeting_prefix}Trip Style is now complete for {destination}.{tradeoff_line} "
            f"The board is back to the remaining planning choices now, and the cleanest next move is {next_anchor_label}."
        )

    if trip_style_planning.substep == "tradeoffs":
        tradeoff_line = (
            f" {trip_style_planning.tradeoff_rationale}"
            if trip_style_planning.tradeoff_rationale
            else ""
        )
        return (
            f"{greeting_prefix}The direction and pace are set for {destination}. "
            f"Now we’re choosing the final tie-breakers before Activities opens.{tradeoff_line}"
        )

    if trip_style_planning.substep == "pace":
        pace_line = (
            f" {trip_style_planning.pace_rationale}"
            if trip_style_planning.pace_rationale
            else ""
        )
        return (
            f"{greeting_prefix}The direction is set as {primary_label}{accent_line}. "
            f"Now we’re choosing how full the days should feel before Activities opens.{pace_line}"
        )

    if primary and trip_style_planning.selection_status in {"selected", "completed"}:
        influence_line = (
            f" {trip_style_planning.downstream_influence_summary}"
            if trip_style_planning.downstream_influence_summary
            else ""
        )
        return (
            f"{greeting_prefix}We’re deciding what kind of trip {destination} should feel like before the activities branch gets deeper. "
            f"Right now it is leaning {primary_label}{accent_line}.{influence_line} "
            "Use the board to lock the main direction first, then add an accent only if it genuinely changes how the days should feel."
        )

    return (
        f"{greeting_prefix}We’re setting the character of {destination} before we open activities in depth. "
        "Pick the main direction first, add an accent only if it matters, and then confirm it so Wandrix can rank the experiences around that feel."
    )


def _build_advanced_activities_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_prefix: str,
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
    fallback_text: str | None,
) -> str:
    destination = configuration.to_location or "this trip"
    activity_planning = conversation.activity_planning
    stay_planning = conversation.stay_planning
    visible_candidates = activity_planning.visible_candidates
    essentials = [
        candidate.title
        for candidate in visible_candidates
        if candidate.disposition == "essential"
    ]
    event_count = sum(1 for candidate in visible_candidates if candidate.kind == "event")
    lead_event = next(
        (
            candidate
            for candidate in visible_candidates
            if candidate.kind == "event" and candidate.start_at is not None
        ),
        None,
    )
    stay_label = (
        stay_planning.selected_hotel_name
        or stay_planning.selected_stay_direction
    )
    requested_review_scopes = {
        resolution.scope for resolution in llm_update.requested_review_resolutions
    }
    latest_schedule_note = (
        activity_planning.schedule_notes[0]
        if activity_planning.schedule_notes
        else None
    )

    if action and action.type == "rebuild_activity_day_plan":
        schedule_line = (
            f" I refreshed the draft days and kept {activity_planning.schedule_summary.lower()}."
            if activity_planning.schedule_summary
            else ""
        )
        note_line = f" {latest_schedule_note}" if latest_schedule_note else ""
        return (
            f"{greeting_prefix}I rebuilt the activities draft around the current picks.{schedule_line}{note_line} "
            "The board now shows what feels fixed, what is still flexible, and what is sitting in reserve."
        )

    if action and action.type in {
        "move_activity_candidate_to_day",
        "move_activity_candidate_earlier",
        "move_activity_candidate_later",
        "pin_activity_candidate_daypart",
        "send_activity_candidate_to_reserve",
        "restore_activity_candidate_from_reserve",
    }:
        title = action.activity_candidate_title or "that pick"
        note_line = f" {latest_schedule_note}" if latest_schedule_note else ""
        if action.type == "move_activity_candidate_to_day" and action.activity_target_day_index:
            action_line = f"I moved {title} onto Day {action.activity_target_day_index} and rebalanced the rest of that draft lightly around it."
        elif action.type == "pin_activity_candidate_daypart" and action.activity_target_daypart:
            action_line = f"I pinned {title} toward the {action.activity_target_daypart} and kept the neighboring plans flexible around that choice."
        elif action.type == "move_activity_candidate_earlier":
            action_line = f"I pulled {title} earlier in the day and softened the surrounding timing to keep the plan workable."
        elif action.type == "move_activity_candidate_later":
            action_line = f"I pushed {title} later in the day and adjusted the surrounding timing so the draft still flows cleanly."
        elif action.type == "send_activity_candidate_to_reserve":
            action_line = f"I moved {title} into reserve so it stays visible without being forced into the active days."
        else:
            action_line = f"I brought {title} back into the active draft and let the rest of the day plan settle around it again."
        return (
            f"{greeting_prefix}{action_line}{note_line} "
            "The board is keeping explicit edits in place while it reshapes the surrounding gaps and transfers."
        )

    if llm_update.requested_activity_schedule_edits:
        title = llm_update.requested_activity_schedule_edits[0].candidate_title
        note_line = f" {latest_schedule_note}" if latest_schedule_note else ""
        return (
            f"{greeting_prefix}I updated the draft around {title} and kept your edit as the thing to respect first.{note_line} "
            "The board is now showing the revised day shape, reserve picks, and any fixed event timing that still has to stay locked."
        )

    if (
        "stay" in requested_review_scopes
        and stay_planning.selection_status == "selected"
        and stay_planning.compatibility_status == "fit"
    ):
        stay_direction_label = stay_planning.selected_stay_direction or "the current stay direction"
        return (
            f"{greeting_prefix}Got it — I'll keep {stay_direction_label} as the working base for {destination}, even though the current trip shape had put it under review. "
            "The rest of the plan stays intact, and I will only reopen that review if the trip changes enough to create a meaningfully different conflict."
        )

    if (
        "hotel" in requested_review_scopes
        and stay_planning.selected_hotel_name
        and stay_planning.hotel_selection_status == "selected"
        and stay_planning.hotel_compatibility_status == "fit"
    ):
        return (
            f"{greeting_prefix}Got it — I'll keep {stay_planning.selected_hotel_name} as the working hotel for {destination}, even though the current trip shape had put it under review. "
            "The rest of the plan stays intact, and I will only reopen that hotel review if later activity or event changes create a meaningfully different conflict."
        )

    if action and action.type == "keep_current_stay_choice":
        stay_direction_label = stay_planning.selected_stay_direction or "the current stay direction"
        return (
            f"{greeting_prefix}Got it — I'll keep {stay_direction_label} as the working base for {destination}, even though the current trip shape is putting it under some strain. "
            "The rest of the plan stays intact, and I will only reopen that review if the trip shifts enough to create a meaningfully different conflict."
        )

    if action and action.type == "keep_current_hotel_choice" and stay_planning.selected_hotel_name:
        return (
            f"{greeting_prefix}Got it — I'll keep {stay_planning.selected_hotel_name} as the working hotel for {destination}, even though the current trip shape is putting it under some strain. "
            "The rest of the plan stays intact, and I will only reopen that hotel review if later activity or event changes create a meaningfully different conflict."
        )

    if (
        action and action.type == "select_stay_option"
        and stay_planning.selection_status == "selected"
        and stay_planning.compatibility_status == "fit"
        and stay_planning.selected_stay_direction
    ) or (
        llm_update.requested_stay_option_title
        and stay_planning.selection_status == "selected"
        and stay_planning.compatibility_status == "fit"
        and stay_planning.selected_stay_direction
    ):
        return (
            f"{greeting_prefix}I’ve switched the working stay direction to {stay_planning.selected_stay_direction} and kept the rest of the trip intact. "
            "That clears the current stay review, so we’re back to shaping the days with the same draft plan still in place."
        )

    if (
        (action and action.type == "select_stay_hotel")
        or llm_update.requested_stay_hotel_name
    ) and (
        stay_planning.selected_hotel_name
        and stay_planning.hotel_selection_status == "selected"
        and stay_planning.hotel_compatibility_status == "fit"
    ):
        return (
            f"{greeting_prefix}I’ve switched the working hotel to {stay_planning.selected_hotel_name} and kept the rest of the trip intact. "
            "That clears the current hotel review, so we can keep building from the same main experiences."
        )

    if stay_planning.selection_status == "needs_review" or stay_planning.compatibility_status in {
        "strained",
        "conflicted",
    }:
        review_reason = (
            stay_planning.compatibility_notes[0]
            if stay_planning.compatibility_notes
            else "the current activities plan is pulling against the saved base"
        )
        stay_direction_label = stay_planning.selected_stay_direction or "the current stay direction"
        reopened_line = (
            " again"
            if stay_planning.accepted_stay_review_summary
            else ""
        )
        return (
            f"{greeting_prefix}The trip in {destination} is now leaning in a way that puts {stay_direction_label} under review{reopened_line} because {review_reason} "
            "Activities are still leading this step, so I’m keeping that stay visible instead of silently replacing it, and the board is switching into stay review so we can decide whether the base or the trip shape should move."
        )

    if (
        stay_planning.selected_hotel_name
        and (
            stay_planning.hotel_selection_status == "needs_review"
            or stay_planning.hotel_compatibility_status in {"strained", "conflicted"}
        )
    ):
        review_reason = (
            stay_planning.hotel_compatibility_notes[0]
            if stay_planning.hotel_compatibility_notes
            else "the current activities plan is weakening the hotel fit"
        )
        reopened_line = (
            " again"
            if stay_planning.accepted_hotel_review_summary
            else ""
        )
        return (
            f"{greeting_prefix}The trip in {destination} is now leaning in a way that puts {stay_planning.selected_hotel_name} under review{reopened_line} because {review_reason} "
            "I’m keeping the current hotel visible instead of silently swapping it out, and the board is moving into hotel review so we can decide whether the hotel or the trip shape should change."
        )

    if activity_planning.completion_status == "completed":
        next_anchor = _recommend_advanced_anchor_after_activities(
            configuration=configuration,
            conversation=conversation,
        )
        next_anchor_label = next_anchor.replace("_", " ")
        completion_line = (
            activity_planning.completion_summary
            or "The main experiences now have enough shape for us to move on."
        )
        personalization_line = _build_completion_personalization_line(
            fallback_text=fallback_text,
            completion_summary=completion_line,
        )
        return (
            f"{greeting_prefix}{completion_line}"
            f"{' ' + personalization_line if personalization_line else ''} "
            "The board is now back to the remaining planning choices now that this part of the trip feels settled. "
            f"The cleanest next move is {next_anchor_label}."
        )

    stay_line = (
        f" I am also using {stay_label} as extra context while I rank the shortlist."
        if stay_label
        else ""
    )
    event_line = (
        f" I also mixed in {event_count} live event option{'s' if event_count != 1 else ''} where the timing fits."
        if event_count
        else ""
    )
    schedule_line = (
        f" I have already drafted {activity_planning.schedule_summary.lower()}."
        if activity_planning.schedule_status == "ready" and activity_planning.schedule_summary
        else ""
    )
    reserve_line = (
        f" {len(activity_planning.unscheduled_candidate_ids)} pick{'s are' if len(activity_planning.unscheduled_candidate_ids) != 1 else ' is'} still sitting in reserve instead of being forced into the day plan."
        if activity_planning.unscheduled_candidate_ids
        else ""
    )

    if essentials:
        essential_text = ", ".join(essentials[:2])
        return (
            f"{greeting_prefix}We’re now deciding which experiences should really shape {destination}, not just collecting a loose list of ideas."
            f"{stay_line}{event_line}{schedule_line}{reserve_line} "
            f"So far, {essential_text} {'are' if len(essentials) > 1 else 'is'} helping lead the trip. "
            "Use Shape trip, Keep option, Skip, and the schedule controls on the board and I’ll keep the draft days responsive to those decisions."
        )

    if lead_event and visible_candidates and visible_candidates[0].id == lead_event.id:
        return (
            f"{greeting_prefix}{lead_event.title} is currently acting like the strongest time-specific moment in {destination}."
            f"{stay_line}{event_line}{schedule_line}{reserve_line} "
            "The board is treating that event as the lead moment and clustering the supporting options around it."
        )

    candidate_count = len(visible_candidates)
    return (
        f"{greeting_prefix}We’re now narrowing {destination} down to the experiences most worth building around, so the trip can start taking on a real shape."
        f"{stay_line}{event_line}{schedule_line}{reserve_line} "
        f"The board currently has {candidate_count} strong option{'s' if candidate_count != 1 else ''}. "
        "Use Shape trip for the strongest picks, Keep option for the ones you still want in the mix, Skip for anything that does not belong, and the schedule controls whenever you want to reshape a day directly."
    )


def _format_date_window(start_date, end_date) -> str:
    if start_date.year == end_date.year:
        return f"{start_date.strftime('%d %b')} to {end_date.strftime('%d %b %Y')}"
    return f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"


def _build_advanced_stay_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_prefix: str,
    action: ConversationBoardAction | None,
) -> str:
    destination = configuration.to_location or "this trip"
    stay_planning = conversation.stay_planning
    selected_option = next(
        (
            option
            for option in stay_planning.recommended_stay_options
            if option.id == stay_planning.selected_stay_option_id
        ),
        None,
    )
    selected_hotel = next(
        (
            hotel
            for hotel in stay_planning.recommended_hotels
            if hotel.id == stay_planning.selected_hotel_id
        ),
        None,
    )

    if stay_planning.selection_status == "needs_review" or stay_planning.compatibility_status in {
        "strained",
        "conflicted",
    }:
        review_reason = (
            stay_planning.compatibility_notes[0]
            if stay_planning.compatibility_notes
            else "newer trip decisions are putting the current stay under strain"
        )
        stay_label = selected_option.title if selected_option else "the current stay direction"
        recommended_alternative = next(
            (
                option.title
                for option in stay_planning.recommended_stay_options
                if option.recommended and option.id != stay_planning.selected_stay_option_id
            ),
            None,
        )
        alternative_line = (
            f" Right now, {recommended_alternative} is leading the replacement options."
            if recommended_alternative
            else ""
        )
        return (
            f"{greeting_prefix}{stay_label} is still the working stay direction for {destination}, "
            f"but it needs a second look because {review_reason}. "
            "I'll keep it visible on the board, explain the tension clearly, and suggest a stronger stay strategy instead of silently replacing it."
            f"{alternative_line}"
        )

    if (
        stay_planning.hotel_selection_status == "needs_review"
        or stay_planning.hotel_compatibility_status in {"strained", "conflicted"}
    ) and selected_hotel:
        review_reason = (
            stay_planning.hotel_compatibility_notes[0]
            if stay_planning.hotel_compatibility_notes
            else "later trip choices are putting this hotel under strain"
        )
        recommended_hotel = next(
            (
                hotel.hotel_name
                for hotel in stay_planning.recommended_hotels
                if hotel.recommended and hotel.id != stay_planning.selected_hotel_id
            ),
            None,
        )
        alternative_line = (
            f" Right now, {recommended_hotel} is leading the replacement options."
            if recommended_hotel
            else ""
        )
        return (
            f"{greeting_prefix}{selected_hotel.hotel_name} is still the working hotel inside {selected_option.title.lower() if selected_option else 'the current stay direction'}, "
            f"but it needs review because {review_reason}. "
            "I'll keep the stay direction visible, show why the hotel fit has weakened, and suggest a better hotel inside the same strategy if needed."
            f"{alternative_line}"
        )

    if selected_hotel and selected_option:
        assumption_line = (
            f" It is currently supporting {', '.join(stay_planning.hotel_selection_assumptions[:2]).lower()}."
            if stay_planning.hotel_selection_assumptions
            else ""
        )
        next_anchor = _recommend_advanced_anchor_after_stay(
            configuration=configuration,
            conversation=conversation,
        )
        next_anchor_label = next_anchor.replace("_", " ")
        return (
            f"{greeting_prefix}{selected_hotel.hotel_name} is a strong choice inside {selected_option.title.lower()}, so I'll use it as the working hotel for now. "
            "That still is not a booking, so I can revise it later if activities, timing, or routing make a different hotel stronger."
            f" Next, the cleanest move is {next_anchor_label}."
            " The board now shows the remaining planning anchors again, with stay marked completed and moved out of the way."
            " If anything about this hotel feels off, tell me what you want changed and I'll reshape it."
            f"{assumption_line}"
        )

    if selected_option and stay_planning.hotel_results_status == "blocked":
        return (
            f"{greeting_prefix}{selected_option.title} is still the working stay direction for {destination}. "
            "I can keep discussing hotel fit inside that base, but exact hotel comparison needs fixed dates before I shape the final hotel recommendations."
        )

    if selected_option and stay_planning.hotel_results_status == "empty":
        return (
            f"{greeting_prefix}I couldn't shape a strong hotel set inside {selected_option.title.lower()} yet. "
            "Give me a little more signal on budget, vibe, or area and I'll rebuild the recommendations."
        )

    if selected_option and stay_planning.recommended_hotels:
        hotel_count = stay_planning.hotel_total_results or len(
            stay_planning.recommended_hotels
        )
        recommendation_line = next(
            (
                hotel.hotel_name
                for hotel in stay_planning.recommended_hotels
                if hotel.recommended
            ),
            stay_planning.recommended_hotels[0].hotel_name,
        )
        return (
            f"{greeting_prefix}{selected_option.title} is now the working stay direction for {destination}. "
            f"I've moved straight into {hotel_count} hotel recommendations inside that base, led by {recommendation_line}. "
            "The board keeps them compact by default, but you can open any card for more detail. "
            "Tell me in chat if you want the list to skew calmer, livelier, cheaper, or more central, and I'll reshape it."
        )

    if selected_option:
        assumption_line = (
            f" I'm currently building around it for {', '.join(stay_planning.selection_assumptions[:2]).lower()}."
            if stay_planning.selection_assumptions
            else ""
        )
        return (
            f"{greeting_prefix}We'll build {destination} around {selected_option.title.lower()} first. "
            "That is a working stay direction rather than a hotel selection, so I can still review it later if activities, flights, or trip style pull the trip in a different direction."
            f"{assumption_line}"
        )

    return (
        f"{greeting_prefix}We'll lead {destination} with stay first. "
        "The board now has four stay strategies to compare, each framed as an area direction rather than a hotel lock. "
        "Pick the one that feels most right, and I'll use it as the first working stay decision for the trip."
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
    next_question = (provider_activation.get("next_reliability_question") or {}).get(
        "question"
    )
    question_line = f" The key thing to confirm is: {next_question}" if next_question else ""
    return (
        f"{greeting_prefix}Quick Plan is selected for {destination}, but I am not triggering live planning yet because {blocker_text}. "
        "I will keep the brief structured and move into the first draft as soon as the remaining blocker is resolved."
        f"{question_line}"
    )


def _build_plan_finalized_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
    finalized_via: PlannerFinalizedVia | None,
    advanced_finalization: bool = False,
) -> str:
    greeting_prefix = f"Locked in, {greeting_name}. " if greeting_name else "Locked in. "
    destination = configuration.to_location or "this trip"
    via_line = (
        "I used the board confirmation to finalize it. "
        if finalized_via == "board"
        else "I finalized it from your chat confirmation. "
    )
    plan_label = "reviewed Advanced plan" if advanced_finalization else "current plan"
    conflict_line = (
        f" I also saved {len(conversation.planner_conflicts)} planning caution"
        f"{'s' if len(conversation.planner_conflicts) != 1 else ''} with the brochure notes."
        if conversation.planner_conflicts
        else ""
    )
    return (
        f"{greeting_prefix}{via_line}"
        f"The {plan_label} for {destination} is now finalized and the brochure-ready version is saved in Saved Trips. "
        "You can open it there, review the details, and download the brochure when you need it. "
        f"{conflict_line} "
        "If you want to change anything later, just ask me to reopen planning and I will unlock it."
    )


def _build_advanced_review_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Absolutely, {greeting_name}. " if greeting_name else "Absolutely. "
    destination = configuration.to_location or "this trip"
    review = conversation.advanced_review_planning
    top_conflict = conversation.planner_conflicts[0] if conversation.planner_conflicts else None
    conflict_line = (
        f" I also found one planning tension to resolve first: {top_conflict.summary}"
        if top_conflict
        else ""
    )
    if review.readiness_status == "needs_review":
        return (
            f"{greeting_prefix}I’ve pulled {destination} into a working trip review. "
            "The board shows what is selected, what is still flexible, and the parts worth checking before you save a brochure-ready version."
            f"{conflict_line}"
        )
    if review.readiness_status == "ready":
        return (
            f"{greeting_prefix}I’ve pulled together the reviewed plan for {destination}. "
            "The board shows the current flights, stay, trip character, experiences, and supporting weather notes, with revision buttons if you want to adjust a section before saving it."
        )
    return (
        f"{greeting_prefix}I’ve opened the working review for {destination}. "
        "Some choices are still flexible; you can revise them, or save the brochure-ready version with those flexible notes captured."
    )


def _is_advanced_finalization_request(
    *,
    action: ConversationBoardAction | None,
    llm_update: TripTurnUpdate,
) -> bool:
    return bool(
        (action and action.type == "finalize_advanced_plan")
        or llm_update.requested_advanced_finalization
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
    if field == "weather_preference" and configuration.weather_preference:
        return f"the weather preference as {configuration.weather_preference}"
    if field == "from_location_flexible" and configuration.from_location_flexible:
        return "the departure as flexible for now"
    if field == "adults" and configuration.travelers.adults is not None and configuration.travelers.adults > 0:
        return f"{configuration.travelers.adults} adult{'s' if configuration.travelers.adults != 1 else ''}"
    if field == "children" and configuration.travelers.children is not None and configuration.travelers.children > 0:
        return f"{configuration.travelers.children} child{'ren' if configuration.travelers.children != 1 else ''}"
    if field == "travelers_flexible" and configuration.travelers_flexible:
        return "the traveller count as flexible for now"
    if field == "activity_styles" and configuration.activity_styles:
        return f"the trip style as {', '.join(configuration.activity_styles)}"
    if field == "custom_style" and configuration.custom_style:
        return f"the custom trip style as {configuration.custom_style}"
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
    if adults is not None and adults > 0:
        parts.append(f"{adults} adult{'s' if adults != 1 else ''}")
    if children is not None and children > 0:
        parts.append(f"{children} child{'ren' if children != 1 else ''}")
    return " and ".join(parts)


def _format_budget_posture(value: object | None) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.replace("_", "-")


def _unresolved_destination_options(
    *,
    conversation: TripConversationState,
    llm_update: TripTurnUpdate,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for option in [*llm_update.mentioned_options, *conversation.memory.mentioned_options]:
        if option.kind != "destination":
            continue
        normalized = " ".join(option.value.strip().lower().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        values.append(option.value)
    return values[:3]


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
    if configuration.custom_style:
        parts.append(f"shaped around {configuration.custom_style}")
    if configuration.travel_window:
        parts.append(f"around {configuration.travel_window}")
    if configuration.trip_length:
        parts.append(f"for {configuration.trip_length}")
    if configuration.weather_preference:
        parts.append(f"with {configuration.weather_preference} weather in mind")

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
    if configuration.custom_style:
        parts.append(f"guided by {configuration.custom_style}")
    if configuration.weather_preference:
        parts.append(f"with a {configuration.weather_preference} weather preference")
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
        "from_location_flexible": "your departure flexibility",
        "to_location": "the destination",
        "start_date": "the travel window",
        "end_date": "the trip length",
        "travel_window": "the rough travel timing",
        "trip_length": "the rough trip length",
        "weather_preference": "the weather preference",
        "budget_posture": "the budget posture",
        "budget_gbp": "the budget posture",
        "adults": "the traveler count",
        "children": "the child traveler count",
        "travelers_flexible": "the traveller count",
        "activity_styles": "the trip style",
        "custom_style": "the custom trip style",
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
) -> bool:
    explicit_mode_selection = bool(action and action.type == "select_advanced_plan")
    chat_mode_selection = bool(
        llm_update.requested_planning_mode == "advanced"
        and llm_update.requested_advanced_anchor is None
        and conversation.advanced_step in {None, "intake"}
    )
    return bool(
        conversation.planning_mode == "advanced"
        and conversation.planning_mode_status == "selected"
        and conversation.advanced_step in {None, "intake"}
        and (explicit_mode_selection or chat_mode_selection)
    )


def _recommend_advanced_anchor_after_stay(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
) -> str:
    if conversation.trip_style_planning.substep == "completed":
        return "activities"
    if configuration.selected_modules.activities:
        if configuration.activity_styles:
            return "activities"
        if configuration.custom_style:
            return "trip_style"
        return "activities"
    if configuration.selected_modules.flights and not configuration.from_location_flexible:
        return "flight"
    return "trip_style"


def _recommend_advanced_anchor_after_trip_style(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
) -> str:
    if configuration.selected_modules.activities and conversation.activity_planning.completion_status != "completed":
        return "activities"
    if configuration.selected_modules.hotels and not conversation.stay_planning.selected_hotel_id:
        return "stay"
    if configuration.selected_modules.flights and not configuration.from_location_flexible:
        return "flight"
    return "activities"


def _recommend_advanced_anchor_after_flights(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
) -> str:
    if configuration.selected_modules.activities and conversation.trip_style_planning.substep != "completed":
        return "trip_style"
    if configuration.selected_modules.activities and conversation.activity_planning.completion_status != "completed":
        return "activities"
    if configuration.selected_modules.hotels and not conversation.stay_planning.selected_hotel_id:
        return "stay"
    return "activities"


def _recommend_advanced_anchor_after_activities(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
) -> str:
    completed_anchors = {"activities"}
    if conversation.stay_planning.selected_hotel_id:
        completed_anchors.add("stay")
    if conversation.trip_style_planning.substep == "completed":
        completed_anchors.add("trip_style")

    active_modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]
    trip_length_text = (configuration.trip_length or "").lower()
    has_short_trip_signal = any(
        signal in trip_length_text for signal in ["weekend", "3 day", "3-night", "3 night"]
    )
    route_is_soft = not configuration.from_location
    route_is_explicitly_flexible = bool(configuration.from_location_flexible)
    hotels_active = "hotels" in active_modules
    flights_active = "flights" in active_modules
    activities_active = "activities" in active_modules

    ranked_candidates: list[str] = []
    if activities_active and configuration.custom_style:
        ranked_candidates.append("trip_style")
    if flights_active and not route_is_explicitly_flexible and (route_is_soft or has_short_trip_signal):
        ranked_candidates.append("flight")
    if hotels_active and "stay" not in completed_anchors:
        ranked_candidates.append("stay")
    ranked_candidates.extend(["stay", "trip_style", "flight", "activities"])

    for candidate in ranked_candidates:
        if candidate not in completed_anchors:
            return candidate
    return "trip_style"


def _trip_direction_primary_label(primary: str | None) -> str:
    return {
        "food_led": "food-led",
        "culture_led": "culture-led",
        "nightlife_led": "nightlife-led",
        "outdoors_led": "outdoors-led",
        "balanced": "balanced",
    }.get(primary or "", "balanced")


def _trip_direction_accent_label(accent: str | None) -> str:
    return {
        "local": "local",
        "classic": "classic",
        "polished": "polished",
        "romantic": "romantic",
        "relaxed": "relaxed",
    }.get(accent or "", "refined")


def _trip_pace_label(pace: str | None) -> str:
    return {
        "slow": "Slow",
        "balanced": "Balanced",
        "full": "Full",
    }.get(pace or "", "Balanced")


def _flight_strategy_label(strategy: str | None) -> str:
    return {
        "smoothest_route": "smoothest route",
        "best_timing": "best timing",
        "best_value": "best value",
        "keep_flexible": "keep flexible",
    }.get(strategy or "", "best timing")


def _build_completion_personalization_line(
    *,
    fallback_text: str | None,
    completion_summary: str,
) -> str | None:
    if not fallback_text or not fallback_text.strip():
        return None

    cleaned = " ".join(fallback_text.strip().split())
    if not cleaned:
        return None

    lowered = cleaned.lower()
    if any(
        phrase in lowered
        for phrase in [
            "activities marked completed",
            "remaining advanced planning anchors",
            "the cleanest next move",
        ]
    ):
        return None

    summary_tokens = {
        token for token in completion_summary.lower().replace(",", " ").split() if len(token) > 4
    }
    cleaned_tokens = {
        token for token in lowered.replace(",", " ").split() if len(token) > 4
    }
    if summary_tokens and cleaned_tokens and len(summary_tokens.intersection(cleaned_tokens)) >= 4:
        return None

    return cleaned.rstrip(".!?") + "."
