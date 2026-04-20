from datetime import datetime, timezone
from uuid import uuid4

from app.graph.planner.board_action_merge import apply_board_action_updates
from app.graph.planner.conversation_state import (
    build_conversation_state,
    build_status,
    compute_missing_fields_with_context,
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
    brief_confirmed = is_trip_brief_confirmed(
        current_conversation,
        effective_input_update,
        state.get("board_action", {}),
    )
    planning_mode, planning_mode_status = _resolve_next_planning_mode(
        current_conversation=current_conversation,
        llm_update=effective_input_update,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
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
        brief_confirmed
        and not next_configuration.from_location
        and resolved_location_context
        and resolved_location_context.summary
    ):
        next_configuration.from_location = resolved_location_context.summary
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
    should_enrich_modules = (
        brief_confirmed
        and planning_mode == "quick"
        and not compute_missing_fields_with_context(
            next_configuration,
            resolved_location_context,
        )
    )
    if locked_without_reopen or preserve_existing_quick_plan:
        module_outputs = existing_module_outputs
        timeline = existing_timeline
    else:
        module_outputs = (
            build_module_outputs(
                next_configuration,
                previous_configuration,
                existing_module_outputs,
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
        confirmation_status=confirmation_status,
        finalized_at=finalized_at,
        finalized_via=finalized_via,
        record_memory=False,
    )
    assistant_response = build_assistant_response(
        configuration=next_configuration,
        conversation=provisional_conversation,
        llm_update=effective_llm_update,
        fallback_text=effective_input_update.assistant_response,
        locked_without_reopen=locked_without_reopen,
        profile_context=state.get("profile_context", {}),
        board_action=state.get("board_action", {}),
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
        if value in (None, "", [], {}):
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
        if value in (None, "", [], {}):
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
    if not brief_confirmed:
        return (current_conversation.planning_mode, current_conversation.planning_mode_status)

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    current_mode = current_conversation.planning_mode
    current_status = current_conversation.planning_mode_status

    if action and action.type == "select_quick_plan":
        return ("quick", "selected")
    if action and action.type == "select_advanced_plan":
        return ("quick", "advanced_unavailable_fallback")
    if llm_update.requested_planning_mode == "quick":
        return ("quick", "selected")
    if llm_update.requested_planning_mode == "advanced":
        return ("quick", "advanced_unavailable_fallback")
    if current_mode == "quick":
        return ("quick", current_status or "selected")
    if current_mode == "advanced":
        return ("advanced", current_status or "selected")
    return (None, "not_selected")


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
        "Advanced Planning is still in development, so Wandrix kept the current Quick Plan draft in place."
    )
    return effective_update


def _prepare_locked_turn_update(llm_update) -> TripTurnUpdate:
    return TripTurnUpdate(planner_intent=llm_update.planner_intent)


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
