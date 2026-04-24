from datetime import datetime, timezone
from uuid import uuid4

from app.graph.planner.board_action_merge import apply_board_action_updates
from app.graph.planner.conversation_state import (
    build_conversation_state,
    build_status,
    compute_missing_fields_with_context,
    detect_confirmed_field_corrections,
    is_trip_brief_confirmed,
)
from app.graph.planner.draft_merge import derive_trip_title, merge_trip_configuration
from app.graph.planner.location_context import resolve_planner_location_context
from app.graph.planner.quick_plan import generate_quick_plan_draft
from app.graph.planner.provider_enrichment import build_module_outputs, build_timeline
from app.graph.planner.response_builder import build_assistant_response
from app.graph.planner.turn_models import TripOpenQuestionUpdate, TripTurnUpdate
from app.graph.planner.understanding import generate_llm_trip_update
from app.graph.state import PlanningGraphState
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    CheckpointConversationMessage,
    ConversationFieldMemory,
    PlannerAdvancedAnchor,
    PlannerAdvancedStep,
    PlannerConfirmationStatus,
    PlannerFinalizedVia,
    PlannerIntent,
    TripConversationState,
)
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TimelineItem, TripConfiguration, TripModuleOutputs


def process_trip_turn(state: PlanningGraphState) -> PlanningGraphState:
    trip_draft = {**state.get("trip_draft", {})}
    previous_configuration = TripConfiguration.model_validate(
        trip_draft.get("configuration", {})
    )
    existing_timeline = [
        TimelineItem.model_validate(item)
        for item in trip_draft.get("timeline", [])
    ]
    existing_module_outputs = TripModuleOutputs.model_validate(
        trip_draft.get("module_outputs", {})
    )
    current_status = TripDraftStatus.model_validate(trip_draft.get("status", {}))
    current_conversation = TripConversationState.model_validate(
        trip_draft.get("conversation", {})
    )
    resolved_location_context = resolve_planner_location_context(
        current_location_context=state.get("current_location_context", {}),
        profile_context=state.get("profile_context", {}),
    )
    raw_messages = [
        CheckpointConversationMessage.model_validate(message).model_dump(mode="json")
        for message in state.get("raw_messages", [])
    ]
    user_input = state.get("user_input", "").strip()
    now = datetime.now(timezone.utc)
    turn_id = f"turn_{uuid4().hex[:10]}"
    current_conversation = _hydrate_conversation_memory_from_status(
        conversation=current_conversation,
        status=current_status,
        configuration=previous_configuration,
    )

    llm_update = generate_llm_trip_update(
        user_input=user_input,
        title=trip_draft.get("title") or "Trip planner",
        configuration=previous_configuration,
        status=current_status,
        conversation=current_conversation,
        profile_context=state.get("profile_context", {}),
        current_location_context=resolved_location_context.model_dump(mode="json")
        if resolved_location_context
        else {},
        board_action=state.get("board_action", {}),
        raw_messages=raw_messages,
    )
    llm_update = apply_board_action_updates(
        llm_update,
        board_action=state.get("board_action", {}),
    )
    current_confirmation_status = (
        current_status.confirmation_status
        if getattr(current_status, "confirmation_status", None)
        else current_conversation.confirmation_status
    )
    reopen_requested = _is_reopen_requested(
        llm_update=llm_update,
        board_action=state.get("board_action", {}),
    )
    locked_without_reopen = (
        current_confirmation_status == "finalized" and not reopen_requested
    )
    effective_input_update = (
        _prepare_locked_turn_update(llm_update)
        if locked_without_reopen
        else llm_update
    )

    next_configuration = (
        previous_configuration.model_copy(deep=True)
        if locked_without_reopen
        else merge_trip_configuration(previous_configuration, effective_input_update)
    )
    corrected_fields = detect_confirmed_field_corrections(
        previous_configuration=previous_configuration,
        next_configuration=next_configuration,
        llm_update=effective_input_update,
    )
    brief_confirmed = is_trip_brief_confirmed(
        current_conversation,
        effective_input_update,
        state.get("board_action", {}),
        corrected_fields=corrected_fields,
    )
    planning_mode, planning_mode_status = _resolve_next_planning_mode(
        current_conversation=current_conversation,
        llm_update=effective_input_update,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
    )
    planning_mode_choice_required = _should_require_planning_mode_choice(
        current_conversation=current_conversation,
        llm_update=effective_input_update,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
        user_input=user_input,
    )
    advanced_anchor = _resolve_advanced_anchor(
        current_conversation=current_conversation,
        board_action=state.get("board_action", {}),
        llm_update=effective_input_update,
        planning_mode=planning_mode,
        brief_confirmed=brief_confirmed,
    )
    advanced_step = _resolve_advanced_step(
        current_conversation=current_conversation,
        planning_mode=planning_mode,
        configuration=next_configuration,
        brief_confirmed=brief_confirmed,
        board_action=state.get("board_action", {}),
        llm_update=effective_input_update,
        advanced_anchor=advanced_anchor,
    )
    preserve_existing_quick_plan = _should_preserve_existing_quick_plan(
        current_conversation=current_conversation,
        llm_update=effective_input_update,
        board_action=state.get("board_action", {}),
    )
    effective_llm_update = _prepare_effective_llm_update(
        llm_update=effective_input_update,
        preserve_existing_quick_plan=preserve_existing_quick_plan,
    )
    if (
        planning_mode == "quick"
        and next_configuration.selected_modules.weather
        and not any(
            "weather" in goal.lower() and "warm" in goal.lower()
            for goal in effective_llm_update.active_goals
        )
    ):
        effective_llm_update.active_goals = [
            "Default the weather planning toward warmer, sunnier pacing unless the user says otherwise.",
            *effective_llm_update.active_goals,
        ]
    provider_activation = _evaluate_provider_activation(
        current_conversation=current_conversation,
        llm_update=effective_llm_update,
        configuration=next_configuration,
        brief_confirmed=brief_confirmed,
        planning_mode=planning_mode,
    )
    effective_llm_update = _apply_provider_activation_clarifications(
        llm_update=effective_llm_update,
        provider_activation=provider_activation,
    )
    should_enrich_modules = provider_activation["quick_plan_ready"]
    should_enrich_advanced_stay_hotels = _should_enrich_advanced_stay_hotels(
        current_conversation=current_conversation,
        board_action=state.get("board_action", {}),
        configuration=next_configuration,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
    )
    should_enrich_advanced_activities = _should_enrich_advanced_activities(
        configuration=next_configuration,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
    )
    should_enrich_advanced_flights = _should_enrich_advanced_flights(
        configuration=next_configuration,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
    )
    allowed_modules = set(provider_activation["allowed_modules"])
    if locked_without_reopen or preserve_existing_quick_plan:
        module_outputs = existing_module_outputs
        timeline = existing_timeline
    else:
        module_outputs = (
            build_module_outputs(
                next_configuration,
                previous_configuration,
                existing_module_outputs,
                allowed_modules=(
                    allowed_modules
                    if should_enrich_modules
                    else {"activities", "weather"}
                    if should_enrich_advanced_activities
                    else {"flights"}
                    if should_enrich_advanced_flights
                    else {"hotels"}
                    if should_enrich_advanced_stay_hotels
                    else set()
                ),
            )
            if (
                should_enrich_modules
                or should_enrich_advanced_stay_hotels
                or should_enrich_advanced_activities
                or should_enrich_advanced_flights
            )
            else existing_module_outputs
        )
        effective_preview = effective_llm_update.timeline_preview
        include_derived_when_preview_present = True
        if planning_mode == "quick" and should_enrich_modules:
            quick_plan_draft = generate_quick_plan_draft(
                title=_resolve_trip_title(
                    current_title=trip_draft.get("title"),
                    llm_title=effective_input_update.title,
                    configuration=next_configuration,
                ),
                configuration=next_configuration,
                module_outputs=module_outputs,
                conversation=current_conversation,
            )
            if quick_plan_draft.timeline_preview:
                effective_preview = quick_plan_draft.timeline_preview
                include_derived_when_preview_present = False
            if quick_plan_draft.board_summary:
                effective_llm_update.last_turn_summary = quick_plan_draft.board_summary
        if should_enrich_advanced_activities and planning_mode == "advanced":
            timeline = existing_timeline
        else:
            timeline = build_timeline(
                configuration=next_configuration,
                llm_preview=effective_preview,
                module_outputs=module_outputs,
                include_derived_when_preview_present=include_derived_when_preview_present,
            )
    confirmation_status, finalized_at, finalized_via, confirmation_transition = (
        _resolve_confirmation_state(
            current_status=current_status,
            current_conversation=current_conversation,
            llm_update=effective_llm_update,
            board_action=state.get("board_action", {}),
            planning_mode=planning_mode,
            advanced_step=advanced_step,
            timeline=timeline,
            now=now,
        )
    )

    provisional_conversation = build_conversation_state(
        current=current_conversation,
        previous_configuration=previous_configuration,
        next_configuration=next_configuration,
        llm_update=effective_llm_update,
        module_outputs=module_outputs,
        assistant_response="",
        turn_id=turn_id,
        user_message=user_input,
        now=now,
        resolved_location_context=resolved_location_context,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
        planning_mode=planning_mode,
        planning_mode_status=planning_mode_status,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        planning_mode_choice_required=planning_mode_choice_required,
        confirmation_status=confirmation_status,
        finalized_at=finalized_at,
        finalized_via=finalized_via,
        record_memory=False,
        provider_activation=provider_activation,
    )
    assistant_response = build_assistant_response(
        configuration=next_configuration,
        conversation=provisional_conversation,
        llm_update=effective_llm_update,
        brief_confirmed=brief_confirmed,
        fallback_text=effective_input_update.assistant_response,
        locked_without_reopen=locked_without_reopen,
        quick_plan_started=should_enrich_modules,
        provider_activation=provider_activation,
        profile_context=state.get("profile_context", {}),
        board_action=state.get("board_action", {}),
        planning_mode_choice_required=planning_mode_choice_required,
        confirmation_status=confirmation_status,
        finalized_via=finalized_via,
        confirmation_transition=confirmation_transition,
    )
    next_conversation = build_conversation_state(
        current=current_conversation,
        previous_configuration=previous_configuration,
        next_configuration=next_configuration,
        llm_update=effective_llm_update,
        module_outputs=module_outputs,
        assistant_response=assistant_response,
        turn_id=turn_id,
        user_message=user_input,
        now=now,
        resolved_location_context=resolved_location_context,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
        planning_mode=planning_mode,
        planning_mode_status=planning_mode_status,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        planning_mode_choice_required=planning_mode_choice_required,
        confirmation_status=confirmation_status,
        finalized_at=finalized_at,
        finalized_via=finalized_via,
        provider_activation=provider_activation,
    )
    timeline = _merge_selected_flight_timeline(
        timeline=timeline,
        conversation=next_conversation,
        configuration=next_configuration,
        planning_mode=planning_mode,
    )
    timeline = _merge_hidden_activity_timeline(
        timeline=timeline,
        conversation=next_conversation,
        planning_mode=planning_mode,
    )
    next_status = build_status(
        current=current_status,
        configuration=next_configuration,
        conversation=next_conversation,
        module_outputs=module_outputs,
        now=now,
        resolved_location_context=resolved_location_context,
        confirmation_status=confirmation_status,
        finalized_at=finalized_at,
        finalized_via=finalized_via,
    )

    updated_messages = list(raw_messages)
    if user_input:
        updated_messages.append(
            CheckpointConversationMessage(
                role="user",
                content=user_input,
                created_at=now,
            ).model_dump(mode="json")
        )
    elif state.get("board_action", {}):
        updated_messages.append(
            CheckpointConversationMessage(
                role="system",
                content=_build_board_action_audit_message(state.get("board_action", {})),
                created_at=now,
            ).model_dump(mode="json")
        )
    updated_messages.append(
        CheckpointConversationMessage(
            role="assistant",
            content=assistant_response,
            created_at=now,
        ).model_dump(mode="json")
    )

    return {
        "trip_draft": {
            "title": _resolve_trip_title(
                current_title=trip_draft.get("title"),
                llm_title=effective_input_update.title,
                configuration=next_configuration,
            ),
            "configuration": next_configuration.model_dump(mode="json"),
            "timeline": [item.model_dump(mode="json") for item in timeline],
            "module_outputs": module_outputs.model_dump(mode="json"),
            "status": next_status.model_dump(mode="json"),
            "conversation": next_conversation.model_dump(mode="json"),
        },
        "assistant_response": assistant_response,
        "raw_messages": updated_messages,
        "metadata": {
            **state.get("metadata", {}),
            "graph_bootstrapped": True,
            "turn_processed": True,
            "turn_id": turn_id,
            "planner_observability": _build_planner_observability_snapshot(
                configuration=next_configuration,
                conversation=next_conversation,
                provider_activation=provider_activation,
                advanced_stay_hotels_ready=should_enrich_advanced_stay_hotels,
                corrected_fields=corrected_fields,
                locked_without_reopen=locked_without_reopen,
                preserve_existing_quick_plan=preserve_existing_quick_plan,
            ),
        },
    }


def _hydrate_conversation_memory_from_status(
    *,
    conversation: TripConversationState,
    status: TripDraftStatus,
    configuration: TripConfiguration,
) -> TripConversationState:
    if not status.confirmed_fields and not status.inferred_fields:
        return conversation

    next_conversation = conversation.model_copy(deep=True)
    field_memory = dict(next_conversation.memory.field_memory)

    for field in status.confirmed_fields:
        if field in field_memory:
            continue
        value = _get_configuration_value(configuration, field)
        if not _snapshot_value_has_signal(field, value):
            continue
        field_memory[field] = ConversationFieldMemory(
            field=field,
            value=value,
            confidence_level="high",
            confidence=None,
            source="user_explicit",
        )

    for field in status.inferred_fields:
        if field in field_memory:
            continue
        value = _get_configuration_value(configuration, field)
        if not _snapshot_value_has_signal(field, value):
            continue
        field_memory[field] = ConversationFieldMemory(
            field=field,
            value=value,
            confidence_level="medium",
            confidence=None,
            source="user_inferred",
        )

    next_conversation.memory.field_memory = field_memory
    return next_conversation


def _get_configuration_value(
    configuration: TripConfiguration,
    field: str,
):
    if field == "adults":
        return configuration.travelers.adults
    if field == "children":
        return configuration.travelers.children
    if field == "activity_styles":
        return configuration.activity_styles
    if field == "selected_modules":
        return configuration.selected_modules.model_dump(mode="json")
    return getattr(configuration, field)


def _resolve_trip_title(
    *,
    current_title: object,
    llm_title: str | None,
    configuration: TripConfiguration,
) -> str:
    if llm_title and llm_title.strip():
        return llm_title.strip()

    derived_title = derive_trip_title(configuration)
    if isinstance(current_title, str) and current_title.strip() and current_title != "Trip planner":
        return current_title

    return derived_title


def _resolve_next_planning_mode(
    *,
    current_conversation: TripConversationState,
    llm_update,
    board_action: dict,
    brief_confirmed: bool,
) -> tuple[str | None, str]:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    current_mode = current_conversation.planning_mode
    current_status = current_conversation.planning_mode_status

    if action and action.type == "select_quick_plan":
        return ("quick", "selected")
    if action and action.type == "select_advanced_plan":
        return ("advanced", "selected")
    if llm_update.requested_planning_mode == "quick" and _chat_planning_mode_request_is_actionable(
        current_conversation=current_conversation,
        brief_confirmed=brief_confirmed,
    ):
        return ("quick", "selected")
    if llm_update.requested_planning_mode == "advanced" and _chat_planning_mode_request_is_actionable(
        current_conversation=current_conversation,
        brief_confirmed=brief_confirmed,
    ):
        return ("advanced", "selected")
    if current_mode == "quick":
        return ("quick", current_status or "selected")
    if current_mode == "advanced":
        return ("advanced", current_status or "selected")
    if not brief_confirmed:
        return (None, "not_selected")
    return (None, "not_selected")


def _should_require_planning_mode_choice(
    *,
    current_conversation: TripConversationState,
    llm_update,
    board_action: dict,
    brief_confirmed: bool,
    user_input: str,
) -> bool:
    if current_conversation.planning_mode in {"quick", "advanced"}:
        return False

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type in {"select_quick_plan", "select_advanced_plan"}:
        return False

    if llm_update.requested_planning_mode in {"quick", "advanced"} and _chat_planning_mode_request_is_actionable(
        current_conversation=current_conversation,
        brief_confirmed=brief_confirmed,
    ):
        return False

    if brief_confirmed:
        return bool(user_input.strip() or current_conversation.memory.turn_summaries)

    if user_input.strip() and _has_trip_signal_for_mode_gate(llm_update):
        return True

    return False


def _has_trip_signal_for_mode_gate(llm_update: TripTurnUpdate) -> bool:
    return bool(
        llm_update.to_location
        or llm_update.from_location
        or llm_update.from_location_flexible
        or llm_update.travel_window
        or llm_update.trip_length
        or llm_update.start_date
        or llm_update.end_date
        or llm_update.weather_preference
        or llm_update.activity_styles
        or llm_update.custom_style
        or llm_update.destination_suggestions
        or llm_update.mentioned_options
    )


def _chat_planning_mode_request_is_actionable(
    *,
    current_conversation: TripConversationState,
    brief_confirmed: bool,
) -> bool:
    if brief_confirmed:
        return True

    return bool(
        current_conversation.memory.turn_summaries
        or current_conversation.memory.field_memory
        or current_conversation.last_turn_summary
    )


def _should_preserve_existing_quick_plan(
    *,
    current_conversation: TripConversationState,
    llm_update,
    board_action: dict,
) -> bool:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    requested_advanced = bool(
        (action and action.type == "select_advanced_plan")
        or llm_update.requested_planning_mode == "advanced"
    )
    return current_conversation.planning_mode == "quick" and requested_advanced


def _prepare_effective_llm_update(
    *,
    llm_update,
    preserve_existing_quick_plan: bool,
):
    if not preserve_existing_quick_plan:
        return llm_update

    effective_update = llm_update.model_copy(deep=True)
    effective_update.timeline_preview = []
    effective_update.last_turn_summary = (
        "Advanced Planning is selected, so Wandrix kept the current Quick Plan draft in place while moving into the guided flow."
    )
    return effective_update


def _resolve_advanced_step(
    *,
    current_conversation: TripConversationState,
    planning_mode: str | None,
    configuration: TripConfiguration,
    brief_confirmed: bool,
    board_action: dict,
    llm_update: TripTurnUpdate,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> PlannerAdvancedStep | None:
    if planning_mode != "advanced":
        return None

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    prior_advanced_step = current_conversation.advanced_step

    if action and action.type == "revise_advanced_review_section" and action.advanced_anchor:
        return "anchor_flow"

    if (
        prior_advanced_step == "review"
        and advanced_anchor is not None
        and llm_update.requested_advanced_anchor is not None
    ):
        return "anchor_flow"

    if (
        not brief_confirmed
        and prior_advanced_step
        not in {"resolve_dates", "choose_anchor", "anchor_flow", "review"}
    ):
        return "intake"

    if llm_update.requested_advanced_review:
        return "review"

    if llm_update.requested_advanced_finalization:
        return "review"

    if _advanced_review_is_ready(
        conversation=current_conversation,
        configuration=configuration,
    ):
        return "review"

    if prior_advanced_step in {"anchor_flow", "review"}:
        return prior_advanced_step

    if (
        brief_confirmed
        and advanced_anchor is None
        and _needs_advanced_date_resolution(configuration=configuration)
    ):
        return "resolve_dates"

    if (
        action
        and action.type == "select_advanced_anchor"
        and advanced_anchor
    ) or advanced_anchor:
        return "anchor_flow"

    if advanced_anchor and current_conversation.advanced_step == "anchor_flow":
        return "anchor_flow"

    return "choose_anchor"


def _needs_advanced_date_resolution(*, configuration: TripConfiguration) -> bool:
    if configuration.start_date and configuration.end_date:
        return False

    if not configuration.travel_window and not configuration.trip_length:
        return False

    return True


def _resolve_advanced_anchor(
    *,
    current_conversation: TripConversationState,
    board_action: dict,
    llm_update,
    planning_mode: str | None,
    brief_confirmed: bool,
) -> PlannerAdvancedAnchor | None:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "revise_advanced_review_section" and action.advanced_anchor:
        return action.advanced_anchor
    if action and action.type == "select_advanced_anchor" and action.advanced_anchor:
        return action.advanced_anchor

    if (
        planning_mode == "advanced"
        and (
            brief_confirmed
            or current_conversation.advanced_step in {"choose_anchor", "anchor_flow", "review"}
        )
        and llm_update.requested_advanced_anchor is not None
    ):
        return llm_update.requested_advanced_anchor

    return current_conversation.advanced_anchor


def _advanced_review_is_ready(
    *,
    conversation: TripConversationState,
    configuration: TripConfiguration,
) -> bool:
    if conversation.planning_mode != "advanced":
        return False
    required: set[PlannerAdvancedAnchor] = set()
    if configuration.selected_modules.flights:
        required.add("flight")
    if configuration.selected_modules.hotels:
        required.add("stay")
    if configuration.selected_modules.activities:
        required.update({"trip_style", "activities"})
    if not required:
        return False

    completed: set[PlannerAdvancedAnchor] = set()
    if conversation.flight_planning.selection_status in {"completed", "kept_open"}:
        completed.add("flight")
    if conversation.stay_planning.selected_hotel_id:
        completed.add("stay")
    if conversation.trip_style_planning.substep == "completed":
        completed.add("trip_style")
    if conversation.activity_planning.completion_status == "completed":
        completed.add("activities")
    return required.issubset(completed)


def _prepare_locked_turn_update(llm_update) -> TripTurnUpdate:
    return TripTurnUpdate(planner_intent=llm_update.planner_intent)


def _evaluate_provider_activation(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    brief_confirmed: bool,
    planning_mode: str | None,
) -> dict:
    scope_explicit = configuration.selected_modules != TripConfiguration().selected_modules
    destination_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="to_location",
    )
    origin_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="from_location",
    )
    origin_flexibility_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="from_location_flexible",
    )
    timing_snapshots = [
        _projected_field_snapshot(
            current_conversation=current_conversation,
            llm_update=llm_update,
            configuration=configuration,
            field=field,
        )
        for field in ["start_date", "end_date", "travel_window", "trip_length"]
    ]
    adults_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="adults",
    )
    traveler_flexibility_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="travelers_flexible",
    )

    destination_ready = _is_destination_ready(destination_snapshot)
    timing_ready = _is_timing_ready(timing_snapshots)
    origin_ready = _is_origin_ready(
        origin_snapshot,
        origin_flexibility_snapshot=origin_flexibility_snapshot,
    )
    traveler_ready = _is_traveler_ready(adults_snapshot)

    reliability_blockers: list[dict] = []
    if not brief_confirmed:
        base_reasons = ["trip brief is not confirmed yet"]
    elif planning_mode != "quick":
        base_reasons = ["quick planning is not active"]
    elif not scope_explicit:
        base_reasons = ["module scope is still implicit"]
        reliability_blockers.append(
            _provider_reliability_blocker(
                category="module_scope",
                field="selected_modules",
                reason=base_reasons[0],
                snapshot=None,
            )
        )
    elif not destination_ready:
        base_reasons = ["destination is not reliable enough yet"]
        reliability_blockers.append(
            _provider_reliability_blocker(
                category="destination",
                field="to_location",
                reason=base_reasons[0],
                snapshot=destination_snapshot,
            )
        )
    elif not timing_ready:
        base_reasons = ["timing is not reliable enough yet"]
        reliability_blockers.append(
            _provider_reliability_blocker(
                category="timing",
                field=_best_timing_snapshot(timing_snapshots)["field"],
                reason=base_reasons[0],
                snapshot=_best_timing_snapshot(timing_snapshots),
            )
        )
    else:
        base_reasons = []

    allowed_modules: list[str] = []
    blocked_modules: dict[str, list[str]] = {}
    for module_name, enabled in configuration.selected_modules.model_dump(mode="json").items():
        if not enabled:
            continue

        blockers = list(base_reasons)
        if not blockers and module_name == "flights" and not origin_ready:
            blockers.append("departure point is not reliable enough yet")
            reliability_blockers.append(
                _provider_reliability_blocker(
                    category="origin",
                    field="from_location",
                    reason=blockers[0],
                    snapshot=origin_snapshot,
                )
            )
        if not blockers and module_name in {"flights", "hotels"} and not traveler_ready:
            blockers.append("traveller count is not reliable enough yet")
            reliability_blockers.append(
                _provider_reliability_blocker(
                    category="travellers",
                    field="adults",
                    reason=blockers[0],
                    snapshot=adults_snapshot,
                )
            )

        if blockers:
            blocked_modules[module_name] = blockers
            continue

        allowed_modules.append(module_name)

    return {
        "brief_confirmed": brief_confirmed,
        "planning_mode": planning_mode,
        "scope_explicit": scope_explicit,
        "destination_ready": destination_ready,
        "timing_ready": timing_ready,
        "origin_ready": origin_ready,
        "traveler_ready": traveler_ready,
        "quick_plan_ready": bool(allowed_modules),
        "allowed_modules": allowed_modules,
        "blocked_modules": blocked_modules,
        "reliability_blockers": _dedupe_provider_reliability_blockers(
            reliability_blockers
        ),
        "next_reliability_question": _next_provider_reliability_question(
            reliability_blockers
        ),
        "field_readiness": {
            "destination": destination_snapshot,
            "origin": origin_snapshot,
            "origin_flexibility": origin_flexibility_snapshot,
            "travellers": adults_snapshot,
            "traveller_flexibility": traveler_flexibility_snapshot,
            "timing": timing_snapshots,
        },
    }


def _apply_provider_activation_clarifications(
    *,
    llm_update: TripTurnUpdate,
    provider_activation: dict,
) -> TripTurnUpdate:
    question = provider_activation.get("next_reliability_question")
    if not question:
        return llm_update
    if any(
        existing.question.strip().lower() == question["question"].strip().lower()
        or (question.get("field") and existing.field == question["field"])
        for existing in llm_update.open_question_updates
    ):
        return llm_update
    update = llm_update.model_copy(deep=True)
    update.open_question_updates = [
        TripOpenQuestionUpdate(**question),
        *update.open_question_updates,
    ][:4]
    return update


def _projected_field_snapshot(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    field: str,
) -> dict:
    source_by_field = {item.field: item.source for item in llm_update.field_sources}
    confidence_by_field = {item.field: item.confidence for item in llm_update.field_confidences}
    value = _get_configuration_value(configuration, field)
    memory = current_conversation.memory.field_memory.get(field)

    source = source_by_field.get(field)
    if source is None and memory is not None and memory.value == value:
        source = memory.source

    confidence_level = confidence_by_field.get(field)
    if confidence_level is None and memory is not None and memory.value == value:
        confidence_level = memory.confidence_level

    return {
        "field": field,
        "has_value": _snapshot_value_has_signal(field, value),
        "value": value,
        "source": source,
        "confidence_level": confidence_level,
    }


def _best_timing_snapshot(snapshots: list[dict]) -> dict:
    for field in ["start_date", "travel_window", "trip_length", "end_date"]:
        for snapshot in snapshots:
            if snapshot["field"] == field and snapshot["has_value"]:
                return snapshot
    return snapshots[0] if snapshots else {"field": "travel_window"}


def _provider_reliability_blocker(
    *,
    category: str,
    field: str,
    reason: str,
    snapshot: dict | None,
) -> dict:
    return {
        "category": category,
        "field": field,
        "reason": reason,
        "source": snapshot.get("source") if snapshot else None,
        "confidence_level": snapshot.get("confidence_level") if snapshot else None,
        "has_value": bool(snapshot.get("has_value")) if snapshot else False,
        "value": snapshot.get("value") if snapshot else None,
    }


def _dedupe_provider_reliability_blockers(blockers: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for blocker in blockers:
        key = (blocker["category"], blocker["reason"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(blocker)
    return deduped


def _next_provider_reliability_question(blockers: list[dict]) -> dict | None:
    for blocker in _dedupe_provider_reliability_blockers(blockers):
        question = _provider_reliability_question(blocker)
        if question:
            return question
    return None


def _provider_reliability_question(blocker: dict) -> dict | None:
    category = blocker.get("category")
    if category == "module_scope":
        return {
            "question": "Which planning areas should I include in the live draft right now?",
            "field": "selected_modules",
            "step": "modules",
            "priority": 1,
            "why": "Live planning waits until the active planning areas are explicit.",
        }
    if category == "destination":
        return {
            "question": "Which destination should I treat as definite for live planning?",
            "field": "to_location",
            "step": "route",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    if category == "timing":
        return {
            "question": "Should I use this timing as the working search window?",
            "field": blocker.get("field") or "travel_window",
            "step": "timing",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    if category == "origin":
        return {
            "question": "Where should I search flights from?",
            "field": "from_location",
            "step": "route",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    if category == "travellers":
        return {
            "question": "How many travelers should I use for live flight and hotel checks?",
            "field": "adults",
            "step": "travellers",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    return None


def _provider_reliability_question_reason(blocker: dict) -> str:
    if not blocker.get("has_value"):
        return "Live provider checks need this before Wandrix can search responsibly."
    source = blocker.get("source")
    confidence = blocker.get("confidence_level")
    if source == "profile_default":
        return "This currently comes from profile memory, so Wandrix needs trip-specific confirmation before live checks."
    if confidence == "low":
        return "This is only a low-confidence working assumption, so Wandrix should confirm it before live checks."
    return "This detail is still provisional, so Wandrix should confirm it before live checks."


def _is_destination_ready(snapshot: dict) -> bool:
    if not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {"medium", "high"}:
        return True
    return False


def _is_origin_ready(
    snapshot: dict,
    *,
    origin_flexibility_snapshot: dict | None = None,
) -> bool:
    if origin_flexibility_snapshot and origin_flexibility_snapshot["has_value"]:
        return False
    if not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {"medium", "high"}:
        return True
    return False


def _is_timing_ready(snapshots: list[dict]) -> bool:
    for snapshot in snapshots:
        if not snapshot["has_value"]:
            continue
        if snapshot["source"] in {"user_explicit", "board_action"}:
            return True
        if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {"medium", "high"}:
            return True
    return False


def _is_traveler_ready(snapshot: dict) -> bool:
    if not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {"medium", "high"}:
        return True
    return False


def _build_planner_observability_snapshot(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    provider_activation: dict,
    advanced_stay_hotels_ready: bool,
    corrected_fields: list[str],
    locked_without_reopen: bool,
    preserve_existing_quick_plan: bool,
) -> dict:
    latest_turn_summary = (
        conversation.memory.turn_summaries[-1]
        if conversation.memory.turn_summaries
        else None
    )
    return {
        "phase": conversation.phase,
        "planning_mode": conversation.planning_mode,
        "planning_mode_status": conversation.planning_mode_status,
        "confirmation_status": conversation.confirmation_status,
        "last_turn_summary": conversation.last_turn_summary,
        "open_question_count": len(
            [question for question in conversation.open_questions if question.status == "open"]
        ),
        "changed_fields": list(latest_turn_summary.changed_fields) if latest_turn_summary else [],
        "corrected_fields": corrected_fields,
        "locked_without_reopen": locked_without_reopen,
        "preserved_existing_quick_plan": preserve_existing_quick_plan,
        "configuration_snapshot": {
            "from_location": configuration.from_location,
            "from_location_flexible": configuration.from_location_flexible,
            "to_location": configuration.to_location,
            "travel_window": configuration.travel_window,
            "trip_length": configuration.trip_length,
            "adults": configuration.travelers.adults,
            "children": configuration.travelers.children,
            "travelers_flexible": configuration.travelers_flexible,
            "selected_modules": configuration.selected_modules.model_dump(mode="json"),
        },
        "provider_activation": provider_activation,
        "advanced_stay_hotels_ready": advanced_stay_hotels_ready,
    }


def _get_configuration_value(
    configuration: TripConfiguration,
    field: str,
):
    if field == "adults":
        return configuration.travelers.adults
    if field == "children":
        return configuration.travelers.children
    if field == "activity_styles":
        return configuration.activity_styles
    if field == "selected_modules":
        return configuration.selected_modules.model_dump(mode="json")
    return getattr(configuration, field)


def _snapshot_value_has_signal(field: str, value: object) -> bool:
    if field in {"from_location_flexible", "travelers_flexible"}:
        return value is True
    if field == "adults":
        return isinstance(value, int) and value > 0
    return value not in (None, "", [], {})


def _is_reopen_requested(*, llm_update, board_action: dict) -> bool:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    return bool(
        (action and action.type == "reopen_plan")
        or getattr(llm_update, "planner_intent", "none") == "reopen_plan"
    )


def _should_enrich_advanced_stay_hotels(
    *,
    current_conversation: TripConversationState,
    board_action: dict,
    configuration: TripConfiguration,
    planning_mode: str | None,
    advanced_step: PlannerAdvancedStep | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> bool:
    if planning_mode != "advanced" or advanced_step != "anchor_flow" or advanced_anchor != "stay":
        return False
    if not configuration.selected_modules.hotels:
        return False
    if not configuration.to_location:
        return False
    if not (
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    ):
        return False

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "select_stay_option" and action.stay_option_id:
        return True
    if action and action.type == "select_stay_hotel" and action.stay_hotel_id:
        return True

    return bool(current_conversation.stay_planning.selected_stay_option_id)


def _should_enrich_advanced_activities(
    *,
    configuration: TripConfiguration,
    planning_mode: str | None,
    advanced_step: PlannerAdvancedStep | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> bool:
    if (
        planning_mode != "advanced"
        or advanced_step != "anchor_flow"
        or advanced_anchor != "activities"
    ):
        return False
    if not configuration.selected_modules.activities:
        return False
    if not configuration.to_location:
        return False
    return bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )


def _should_enrich_advanced_flights(
    *,
    configuration: TripConfiguration,
    planning_mode: str | None,
    advanced_step: PlannerAdvancedStep | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> bool:
    if (
        planning_mode != "advanced"
        or advanced_step != "anchor_flow"
        or advanced_anchor != "flight"
    ):
        return False
    if not configuration.selected_modules.flights:
        return False
    return bool(
        configuration.from_location
        and configuration.to_location
        and configuration.start_date
        and configuration.end_date
        and (configuration.travelers.adults or configuration.travelers_flexible)
    )


def _resolve_confirmation_state(
    *,
    current_status: TripDraftStatus,
    current_conversation: TripConversationState,
    llm_update,
    board_action: dict,
    planning_mode: str | None,
    advanced_step: PlannerAdvancedStep | None,
    timeline: list[TimelineItem],
    now: datetime,
) -> tuple[
    PlannerConfirmationStatus,
    datetime | None,
    PlannerFinalizedVia | None,
    str,
]:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    current_confirmation_status = (
        current_status.confirmation_status
        if getattr(current_status, "confirmation_status", None)
        else current_conversation.confirmation_status
    )
    current_finalized_at = (
        current_status.finalized_at
        if getattr(current_status, "finalized_at", None)
        else current_conversation.finalized_at
    )
    current_finalized_via = (
        current_status.finalized_via
        if getattr(current_status, "finalized_via", None)
        else current_conversation.finalized_via
    )
    planner_intent: PlannerIntent = getattr(llm_update, "planner_intent", "none")
    quick_draft_ready = planning_mode == "quick" and len(timeline) > 0
    advanced_review_ready = planning_mode == "advanced" and advanced_step == "review"
    chat_advanced_finalization_ready = (
        advanced_review_ready
        and current_conversation.advanced_step == "review"
        and llm_update.requested_advanced_finalization
    )

    if action and action.type == "reopen_plan" and current_confirmation_status == "finalized":
        return ("unconfirmed", None, None, "reopened")
    if planner_intent == "reopen_plan" and current_confirmation_status == "finalized":
        return ("unconfirmed", None, None, "reopened")

    if current_confirmation_status == "finalized":
        return ("finalized", current_finalized_at, current_finalized_via, "none")

    if action and action.type == "finalize_quick_plan" and quick_draft_ready:
        return ("finalized", now, "board", "finalized")
    if action and action.type == "finalize_advanced_plan" and advanced_review_ready:
        return ("finalized", now, "board", "finalized")
    if planner_intent == "confirm_plan" and quick_draft_ready:
        return ("finalized", now, "chat", "finalized")
    if chat_advanced_finalization_ready:
        return ("finalized", now, "chat", "finalized")

    return ("unconfirmed", None, None, "none")


def _build_board_action_audit_message(board_action: dict) -> str:
    action = ConversationBoardAction.model_validate(board_action)
    if (
        action.type == "select_trip_style_direction_primary"
        and action.trip_style_direction_primary
    ):
        return (
            "Board action: set trip direction to "
            f"{action.trip_style_direction_primary}."
        )
    if (
        action.type == "select_trip_style_direction_accent"
        and action.trip_style_direction_accent
    ):
        return (
            "Board action: set trip accent to "
            f"{action.trip_style_direction_accent}."
        )
    if action.type == "confirm_trip_style_direction":
        return "Board action: confirmed the current trip direction."
    if action.type == "select_trip_style_pace" and action.trip_style_pace:
        return f"Board action: set trip pace to {action.trip_style_pace}."
    if action.type == "confirm_trip_style_pace":
        return "Board action: confirmed the current trip pace."
    if (
        action.type == "set_trip_style_tradeoff"
        and action.trip_style_tradeoff_axis
        and action.trip_style_tradeoff_value
    ):
        return (
            "Board action: set trip style tradeoff "
            f"{action.trip_style_tradeoff_axis} to {action.trip_style_tradeoff_value}."
        )
    if action.type == "confirm_trip_style_tradeoffs":
        return "Board action: confirmed the current trip style tradeoffs."
    if (
        action.type == "set_activity_candidate_disposition"
        and action.activity_candidate_title
        and action.activity_candidate_disposition
    ):
        return (
            f"Board action: set {action.activity_candidate_title} to "
            f"{action.activity_candidate_disposition}."
        )
    if action.type == "rebuild_activity_day_plan":
        return "Board action: rebuild the activity day plan."
    if action.type == "select_stay_hotel" and action.stay_hotel_name:
        return f"Board action: selected hotel {action.stay_hotel_name}."
    if action.type == "select_stay_option" and action.stay_option_id:
        return f"Board action: selected stay option {action.stay_option_id}."
    if action.type == "select_advanced_anchor" and action.advanced_anchor:
        return f"Board action: start advanced planning with {action.advanced_anchor}."
    if action.type == "finalize_advanced_plan":
        return "Board action: finalize the reviewed Advanced plan."
    return f"Board action: {action.type}"


def _merge_hidden_activity_timeline(
    *,
    timeline: list[TimelineItem],
    conversation: TripConversationState,
    planning_mode: str | None,
) -> list[TimelineItem]:
    if planning_mode != "advanced":
        return timeline

    preserved_items = [
        item
        for item in timeline
        if not (
            item.source_module == "activities"
            and item.type in {"activity", "event", "transfer"}
        )
    ]
    scheduled_activity_items = [
        TimelineItem(
            id=block.id,
            type=block.type,
            title=block.title,
            day_label=block.day_label,
            start_at=block.start_at,
            end_at=block.end_at,
            venue_name=block.venue_name,
            location_label=block.location_label,
            summary=block.summary,
            details=[
                detail
                for detail in block.details
                if not detail.startswith("coords:")
            ],
            source_label=block.source_label,
            source_url=block.source_url,
            image_url=block.image_url,
            availability_text=block.availability_text,
            price_text=block.price_text,
            status_text=block.status_text,
            source_module="activities",
            status="draft",
        )
        for block in conversation.activity_planning.timeline_blocks
    ]
    return [*preserved_items, *scheduled_activity_items]


def _merge_selected_flight_timeline(
    *,
    timeline: list[TimelineItem],
    conversation: TripConversationState,
    configuration: TripConfiguration,
    planning_mode: str | None,
) -> list[TimelineItem]:
    if planning_mode != "advanced":
        return timeline

    preserved_items = [
        item for item in timeline if item.source_module != "flights" and item.type != "flight"
    ]
    flight_planning = conversation.flight_planning
    if flight_planning.selection_status != "completed":
        return preserved_items

    selected_flights = [
        flight
        for flight in [
            flight_planning.selected_outbound_flight,
            flight_planning.selected_return_flight,
        ]
        if flight is not None
    ]
    selected_items = [
        TimelineItem(
            id=f"timeline_selected_{flight.id}",
            type="flight",
            title="Outbound flight" if flight.direction == "outbound" else "Return flight",
            day_label=_flight_day_label(flight, configuration),
            start_at=flight.departure_time,
            end_at=flight.arrival_time,
            location_label=f"{flight.departure_airport} to {flight.arrival_airport}",
            summary=flight.duration_text or flight.summary,
            details=[
                detail
                for detail in [
                    flight.summary,
                    *flight.tradeoffs,
                    "Working planning flight, not a final schedule.",
                ]
                if detail
            ][:6],
            source_module="flights",
            status="draft",
        )
        for flight in selected_flights
    ]
    return [*preserved_items, *selected_items]


def _flight_day_label(
    flight,
    configuration: TripConfiguration,
) -> str | None:
    departure_time = getattr(flight, "departure_time", None)
    if not departure_time or not configuration.start_date:
        return None
    day_number = max((departure_time.date() - configuration.start_date).days + 1, 1)
    return f"Day {day_number}"
