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
from app.graph.planner.understanding import generate_llm_trip_update
from app.graph.state import PlanningGraphState
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import CheckpointConversationMessage, TripConversationState
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

    next_configuration = merge_trip_configuration(previous_configuration, llm_update)
    brief_confirmed = is_trip_brief_confirmed(
        current_conversation,
        llm_update,
        state.get("board_action", {}),
    )
    planning_mode, planning_mode_status = _resolve_next_planning_mode(
        current_conversation=current_conversation,
        llm_update=llm_update,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
    )
    preserve_existing_quick_plan = _should_preserve_existing_quick_plan(
        current_conversation=current_conversation,
        llm_update=llm_update,
        board_action=state.get("board_action", {}),
    )
    effective_llm_update = _prepare_effective_llm_update(
        llm_update=llm_update,
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
    if preserve_existing_quick_plan:
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
                    llm_title=llm_update.title,
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
        record_memory=False,
    )
    assistant_response = build_assistant_response(
        configuration=next_configuration,
        conversation=provisional_conversation,
        llm_update=effective_llm_update,
        fallback_text=llm_update.assistant_response,
        profile_context=state.get("profile_context", {}),
        board_action=state.get("board_action", {}),
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
    )
    next_status = build_status(
        current=current_status,
        configuration=next_configuration,
        conversation=next_conversation,
        module_outputs=module_outputs,
        now=now,
        resolved_location_context=resolved_location_context,
    )

    updated_messages = [
        *raw_messages,
        CheckpointConversationMessage(
            role="user",
            content=user_input,
            created_at=now,
        ).model_dump(mode="json"),
        CheckpointConversationMessage(
            role="assistant",
            content=assistant_response,
            created_at=now,
        ).model_dump(mode="json"),
    ]

    return {
        "trip_draft": {
            "title": _resolve_trip_title(
                current_title=trip_draft.get("title"),
                llm_title=llm_update.title,
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
