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
from app.graph.planner.turn_models import TripTurnUpdate
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
        brief_confirmed=brief_confirmed,
        board_action=state.get("board_action", {}),
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
    should_enrich_modules = provider_activation["quick_plan_ready"]
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
                allowed_modules=allowed_modules,
            )
            if should_enrich_modules
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
    user_input: str,
) -> bool:
    if current_conversation.planning_mode in {"quick", "advanced"}:
        return False

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type in {"select_quick_plan", "select_advanced_plan"}:
        return False

    if llm_update.requested_planning_mode in {"quick", "advanced"} and _chat_planning_mode_request_is_actionable(
        current_conversation=current_conversation,
        brief_confirmed=False,
    ):
        return False

    if user_input.strip():
        return True

    return bool(current_conversation.memory.turn_summaries)


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
    brief_confirmed: bool,
    board_action: dict,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> PlannerAdvancedStep | None:
    if planning_mode != "advanced":
        return None

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    prior_advanced_step = current_conversation.advanced_step

    if (
        not brief_confirmed
        and prior_advanced_step not in {"choose_anchor", "anchor_flow", "review"}
    ):
        return "intake"

    if prior_advanced_step in {"anchor_flow", "review"}:
        return prior_advanced_step

    if (
        action
        and action.type == "select_advanced_anchor"
        and advanced_anchor
    ) or advanced_anchor:
        return "anchor_flow"

    if advanced_anchor and current_conversation.advanced_step == "anchor_flow":
        return "anchor_flow"

    return "choose_anchor"


def _resolve_advanced_anchor(
    *,
    current_conversation: TripConversationState,
    board_action: dict,
    llm_update,
    planning_mode: str | None,
    brief_confirmed: bool,
) -> PlannerAdvancedAnchor | None:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
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

    if not brief_confirmed:
        base_reasons = ["trip brief is not confirmed yet"]
    elif planning_mode != "quick":
        base_reasons = ["quick planning is not active"]
    elif not scope_explicit:
        base_reasons = ["module scope is still implicit"]
    elif not destination_ready:
        base_reasons = ["destination is not reliable enough yet"]
    elif not timing_ready:
        base_reasons = ["timing is not reliable enough yet"]
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
        if not blockers and module_name in {"flights", "hotels"} and not traveler_ready:
            blockers.append("traveller count is not reliable enough yet")

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
        "field_readiness": {
            "destination": destination_snapshot,
            "origin": origin_snapshot,
            "origin_flexibility": origin_flexibility_snapshot,
            "travellers": adults_snapshot,
            "traveller_flexibility": traveler_flexibility_snapshot,
            "timing": timing_snapshots,
        },
    }


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


def _resolve_confirmation_state(
    *,
    current_status: TripDraftStatus,
    current_conversation: TripConversationState,
    llm_update,
    board_action: dict,
    planning_mode: str | None,
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

    if action and action.type == "reopen_plan" and current_confirmation_status == "finalized":
        return ("unconfirmed", None, None, "reopened")
    if planner_intent == "reopen_plan" and current_confirmation_status == "finalized":
        return ("unconfirmed", None, None, "reopened")

    if current_confirmation_status == "finalized":
        return ("finalized", current_finalized_at, current_finalized_via, "none")

    if action and action.type == "finalize_quick_plan" and quick_draft_ready:
        return ("finalized", now, "board", "finalized")
    if planner_intent == "confirm_plan" and quick_draft_ready:
        return ("finalized", now, "chat", "finalized")

    return ("unconfirmed", None, None, "none")


def _build_board_action_audit_message(board_action: dict) -> str:
    action = ConversationBoardAction.model_validate(board_action)
    return f"Board action: {action.type}"
