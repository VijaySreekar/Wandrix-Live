from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.config import get_settings
from app.graph.planner.board_action_merge import apply_board_action_updates
from app.graph.planner.brief_intelligence import review_trip_brief_intelligence
from app.graph.planner.conversation_state import (
    build_conversation_state,
    build_status,
    compute_missing_fields_with_context,
    detect_confirmed_field_corrections,
    is_trip_brief_confirmed,
)
from app.graph.planner.destination_discovery_review import (
    review_destination_discovery_update,
)
from app.graph.planner.draft_merge import derive_trip_title, merge_trip_configuration
from app.graph.planner.location_context import resolve_planner_location_context
from app.graph.planner.profile_origin_review import review_profile_origin_update
from app.graph.planner.quick_plan_dossier import (
    QuickPlanReadiness,
    build_quick_plan_dossier,
    evaluate_quick_plan_readiness,
)
from app.graph.planner.quick_plan_dates import apply_quick_plan_working_dates
from app.graph.planner.quick_plan_budget import estimate_quick_plan_budget
from app.graph.planner.quick_plan_generation import (
    run_quick_plan_generation,
    run_quick_plan_repair,
)
from app.graph.planner.quick_plan_quality_review import review_quick_plan_quality
from app.graph.planner.quick_plan_repair_orchestrator import (
    run_quick_plan_repair_loop,
)
from app.graph.planner.quick_plan_review import review_quick_plan_generation
from app.graph.planner.provider_enrichment import build_module_outputs, build_timeline
from app.graph.planner.response_builder import build_assistant_response
from app.graph.planner.timing_intake import sanitize_timing_update
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
from app.schemas.trip_planning import (
    TimelineItem,
    TripBudgetEstimate,
    TripConfiguration,
    TripModuleOutputs,
)

LAST_TURN_SUMMARY_MAX_LENGTH = 400


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
    existing_budget_estimate = (
        TripBudgetEstimate.model_validate(trip_draft.get("budget_estimate"))
        if trip_draft.get("budget_estimate")
        else None
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
    llm_update = review_destination_discovery_update(
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
        llm_update=llm_update,
    )
    llm_update = review_profile_origin_update(
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
        llm_update=llm_update,
    )
    llm_update = review_trip_brief_intelligence(
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
        llm_update=llm_update,
    )
    llm_update = apply_board_action_updates(
        llm_update,
        board_action=state.get("board_action", {}),
    )
    llm_update = sanitize_timing_update(llm_update)
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
    if not brief_confirmed and _quick_plan_selection_confirms_complete_brief(
        llm_update=effective_input_update,
        configuration=next_configuration,
        board_action=state.get("board_action", {}),
        corrected_fields=corrected_fields,
    ):
        effective_input_update = effective_input_update.model_copy(
            update={"confirmed_trip_brief": True}
        )
        brief_confirmed = True
    planning_mode, planning_mode_status = _resolve_next_planning_mode(
        current_conversation=current_conversation,
        llm_update=effective_input_update,
        configuration=next_configuration,
        board_action=state.get("board_action", {}),
        brief_confirmed=brief_confirmed,
    )
    planning_mode_choice_required = _should_require_planning_mode_choice(
        current_conversation=current_conversation,
        llm_update=effective_input_update,
        configuration=next_configuration,
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
    quick_plan_date_decision = None
    if (
        planning_mode == "quick"
        and (brief_confirmed or planning_mode_status == "selected")
        and not locked_without_reopen
        and not preserve_existing_quick_plan
    ):
        (
            next_configuration,
            effective_llm_update,
            quick_plan_date_decision,
        ) = apply_quick_plan_working_dates(
            configuration=next_configuration,
            llm_update=effective_llm_update,
            conversation=current_conversation,
        )
    provider_activation = _evaluate_provider_activation(
        current_conversation=current_conversation,
        llm_update=effective_llm_update,
        configuration=next_configuration,
        brief_confirmed=brief_confirmed,
        planning_mode=planning_mode,
        board_action=state.get("board_action", {}),
    )
    if quick_plan_date_decision is not None:
        provider_activation["quick_plan_working_dates"] = quick_plan_date_decision.model_dump(
            mode="json"
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
    quick_plan_dossier = None
    quick_plan_review = None
    quick_plan_repair_attempted = False
    quick_plan_repair_goal = "not_attempted"
    quick_plan_first_review = None
    quick_plan_final_review = None
    quick_plan_first_quality_review = None
    quick_plan_final_quality_review = None
    quick_plan_stage_one_only = get_settings().quick_plan_stage_one_only
    if provider_activation["quick_plan_ready"]:
        quick_plan_dossier = build_quick_plan_dossier(
            current_conversation=current_conversation,
            llm_update=effective_llm_update,
            configuration=next_configuration,
            readiness=QuickPlanReadiness.model_validate(
                provider_activation["quick_plan_readiness"]
            ),
            provider_activation=provider_activation,
            raw_messages=raw_messages,
            user_input=user_input,
            board_action=state.get("board_action", {}),
            working_date_decision=quick_plan_date_decision,
        )
    if locked_without_reopen or preserve_existing_quick_plan:
        module_outputs = existing_module_outputs
        timeline = existing_timeline
        budget_estimate = existing_budget_estimate
    else:
        quick_plan_built = False
        quick_plan_has_preview = False
        accepted_quick_plan = None
        budget_estimate = existing_budget_estimate
        if planning_mode == "quick" and should_enrich_modules and quick_plan_stage_one_only:
            quick_plan_attempt = None
            accepted_quick_plan = None
            module_outputs = existing_module_outputs
            timeline = existing_timeline
            provider_activation["quick_plan_acceptance"] = {
                "accepted": False,
                "final_visible": False,
                "review_status": None,
                "completeness_status": None,
                "quality_status": None,
                "repair_attempted": False,
                "accepted_modules": [],
                "assumptions": quick_plan_dossier.assumptions
                if quick_plan_dossier is not None
                else [],
                "final_completeness_review": None,
                "final_quality_review": None,
                "repair_metadata": {
                    "stage_one_only": True,
                    "stopped_reason": "stage_one_flights_only",
                },
                "intelligence_metadata": {},
                "intelligence_metadata_present": False,
            }
            provider_activation["quick_plan_build"] = {
                "status": "running",
                "active_stage": "flights",
                "completed_stages": ["brief"],
                "failed_stage": None,
                "message": "Brief saved. Finding flight options for the first Quick Plan board.",
            }
            effective_llm_update.last_turn_summary = _clamp_last_turn_summary(
                "Quick Plan started with the confirmed brief. Flight options are being added to the live board first."
            )
        elif planning_mode == "quick" and should_enrich_modules:
            trip_title = _resolve_trip_title(
                current_title=trip_draft.get("title"),
                llm_title=effective_input_update.title,
                configuration=next_configuration,
            )
            repair_loop_result = run_quick_plan_repair_loop(
                dossier=quick_plan_dossier,
                configuration=next_configuration,
                previous_configuration=previous_configuration,
                existing_module_outputs=existing_module_outputs,
                trip_title=trip_title,
                conversation=current_conversation,
                run_generation=run_quick_plan_generation,
                run_repair=run_quick_plan_repair,
                review_completeness=review_quick_plan_generation,
                review_quality=review_quick_plan_quality,
            )
            quick_plan_attempt = repair_loop_result.attempt
            accepted_quick_plan = repair_loop_result.accepted_plan
            quick_plan_first_review = repair_loop_result.first_completeness_review
            quick_plan_final_review = repair_loop_result.final_completeness_review
            quick_plan_first_quality_review = repair_loop_result.first_quality_review
            quick_plan_final_quality_review = repair_loop_result.final_quality_review
            quick_plan_repair_metadata = repair_loop_result.repair_metadata
            quick_plan_repair_attempted = bool(
                quick_plan_repair_metadata.get("repair_attempted")
            )
            quick_plan_repair_goal = quick_plan_repair_metadata.get(
                "repair_goal",
                "not_attempted",
            )
            quick_plan_completeness_payload = (
                quick_plan_final_review.model_dump(mode="json")
                if quick_plan_final_review
                else None
            )
            quick_plan_quality_payload = (
                quick_plan_final_quality_review.model_dump(mode="json")
                if quick_plan_final_quality_review
                else None
            )
            provider_activation["quick_plan_completeness_review"] = (
                quick_plan_completeness_payload
            )
            provider_activation["quick_plan_review"] = quick_plan_completeness_payload
            provider_activation["quick_plan_quality_review"] = quick_plan_quality_payload
            provider_activation["quick_plan_quality_specialists"] = (
                (quick_plan_quality_payload or {}).get("specialist_results", [])
            )
            provider_activation["quick_plan_strategy"] = (
                quick_plan_attempt.strategy_brief.model_dump(mode="json")
                if quick_plan_attempt.strategy_brief
                else None
            )
            provider_activation["quick_plan_provider_brief"] = (
                quick_plan_attempt.provider_brief.model_dump(mode="json")
                if quick_plan_attempt.provider_brief
                else None
            )
            provider_activation["quick_plan_day_architecture"] = (
                quick_plan_attempt.day_architecture.model_dump(mode="json")
                if quick_plan_attempt.day_architecture
                else None
            )
            provider_activation["quick_plan_repair"] = quick_plan_repair_metadata
            provider_activation["quick_plan_acceptance"] = {
                "accepted": accepted_quick_plan is not None,
                "final_visible": accepted_quick_plan is not None,
                "review_status": quick_plan_final_review.status
                if quick_plan_final_review
                else None,
                "completeness_status": quick_plan_final_review.status
                if quick_plan_final_review
                else None,
                "quality_status": quick_plan_final_quality_review.status
                if quick_plan_final_quality_review
                else None,
                "repair_attempted": quick_plan_repair_attempted,
                "accepted_modules": quick_plan_dossier.readiness.allowed_modules
                if accepted_quick_plan is not None and quick_plan_dossier is not None
                else [],
                "assumptions": accepted_quick_plan.assumptions
                if accepted_quick_plan is not None
                else [],
                "final_completeness_review": accepted_quick_plan.final_completeness_review
                if accepted_quick_plan is not None
                else None,
                "final_quality_review": accepted_quick_plan.final_quality_review
                if accepted_quick_plan is not None
                else None,
                "repair_metadata": accepted_quick_plan.repair_metadata
                if accepted_quick_plan is not None
                else quick_plan_repair_metadata,
                "intelligence_metadata": accepted_quick_plan.intelligence_metadata
                if accepted_quick_plan is not None
                else {},
                "intelligence_metadata_present": bool(
                    accepted_quick_plan
                    and any(
                        accepted_quick_plan.intelligence_metadata.get(key)
                        for key in [
                            "strategy_brief",
                            "provider_brief",
                            "day_architecture",
                        ]
                    )
                ),
            }
            module_outputs = (
                accepted_quick_plan.module_outputs
                if accepted_quick_plan is not None
                else existing_module_outputs
            )
        else:
            quick_plan_attempt = None
            accepted_quick_plan = None
            module_outputs = (
                build_module_outputs(
                    next_configuration,
                    previous_configuration,
                    existing_module_outputs,
                    allowed_modules=(
                        {"activities", "weather"}
                        if should_enrich_advanced_activities
                        else {"flights"}
                        if should_enrich_advanced_flights
                        else {"hotels"}
                        if should_enrich_advanced_stay_hotels
                        else set()
                    ),
                )
                if (
                    should_enrich_advanced_stay_hotels
                    or should_enrich_advanced_activities
                    or should_enrich_advanced_flights
                )
                else existing_module_outputs
            )
        effective_preview = effective_llm_update.timeline_preview
        include_derived_when_preview_present = True
        include_derived_modules_when_preview_present = None
        timeline_module_outputs = module_outputs
        if accepted_quick_plan is not None:
            timeline_module_outputs = accepted_quick_plan.timeline_module_outputs
            effective_preview = accepted_quick_plan.timeline_preview
            include_derived_when_preview_present = False
            include_derived_modules_when_preview_present = {"flights", "hotels"}
            budget_estimate = estimate_quick_plan_budget(
                configuration=next_configuration,
                module_outputs=accepted_quick_plan.timeline_module_outputs,
            )
            quick_plan_has_preview = True
            if accepted_quick_plan.generation_attempt.draft.board_summary:
                effective_llm_update.last_turn_summary = _clamp_last_turn_summary(
                    accepted_quick_plan.generation_attempt.draft.board_summary
                )
        elif quick_plan_final_quality_review is not None:
            effective_llm_update.last_turn_summary = _clamp_last_turn_summary(
                quick_plan_final_quality_review.assistant_summary
                or effective_llm_update.last_turn_summary
            )
        elif quick_plan_review is not None:
            effective_llm_update.last_turn_summary = _clamp_last_turn_summary(
                quick_plan_review.assistant_summary
                or effective_llm_update.last_turn_summary
            )
        if should_enrich_advanced_activities and planning_mode == "advanced":
            timeline = existing_timeline
        elif (
            planning_mode == "quick"
            and quick_plan_attempt is not None
            and not quick_plan_has_preview
        ):
            timeline = existing_timeline
        else:
            timeline = build_timeline(
                configuration=next_configuration,
                llm_preview=effective_preview,
                module_outputs=timeline_module_outputs,
                include_derived_when_preview_present=include_derived_when_preview_present,
                include_derived_modules_when_preview_present=include_derived_modules_when_preview_present,
            )
            if planning_mode == "quick" and quick_plan_has_preview:
                quick_plan_built = _has_quick_plan_itinerary_items(timeline)
        should_enrich_modules = should_enrich_modules and quick_plan_built
    quick_plan_finalization = _evaluate_quick_plan_finalization(
        current_conversation=current_conversation,
        planning_mode=planning_mode,
        timeline=timeline,
        module_outputs=module_outputs,
        provider_activation=provider_activation,
    )
    provider_activation["quick_plan_finalization"] = quick_plan_finalization
    confirmation_status, finalized_at, finalized_via, confirmation_transition = (
        _resolve_confirmation_state(
            current_status=current_status,
            current_conversation=current_conversation,
            llm_update=effective_llm_update,
            board_action=state.get("board_action", {}),
            planning_mode=planning_mode,
            advanced_step=advanced_step,
            timeline=timeline,
            quick_plan_brochure_eligible=quick_plan_finalization.get(
                "brochure_eligible", False
            ),
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
            "budget_estimate": budget_estimate.model_dump(mode="json")
            if budget_estimate
            else None,
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


def _has_quick_plan_itinerary_items(timeline: list[TimelineItem]) -> bool:
    return any(
        item.type not in {"hotel", "note"} or bool(item.day_label)
        for item in timeline
    )


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
    configuration: TripConfiguration,
    board_action: dict,
    brief_confirmed: bool,
) -> tuple[str | None, str]:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    current_mode = current_conversation.planning_mode
    current_status = current_conversation.planning_mode_status

    if action and action.type == "select_quick_plan" and brief_confirmed:
        return ("quick", "selected")
    if action and action.type == "select_advanced_plan":
        return ("advanced", "selected")
    if llm_update.requested_planning_mode == "quick" and _chat_planning_mode_request_is_actionable(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        brief_confirmed=brief_confirmed,
    ):
        return ("quick", "selected")
    if llm_update.requested_planning_mode == "advanced" and _chat_planning_mode_request_is_actionable(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
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
    configuration: TripConfiguration,
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
        llm_update=llm_update,
        configuration=configuration,
        brief_confirmed=brief_confirmed,
    ):
        return False

    return bool(
        brief_confirmed and (user_input.strip() or current_conversation.memory.turn_summaries)
    )


def _quick_plan_selection_confirms_complete_brief(
    *,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    board_action: dict,
    corrected_fields: list[str],
) -> bool:
    if corrected_fields:
        return False

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    quick_plan_selected = bool(
        (action and action.type == "select_quick_plan")
        or llm_update.requested_planning_mode == "quick"
    )
    if not quick_plan_selected:
        return False

    return _current_brief_is_complete_for_quick_plan(configuration)


def _current_brief_is_complete_for_quick_plan(
    configuration: TripConfiguration,
) -> bool:
    if not configuration.to_location:
        return False

    has_exact_dates = bool(configuration.start_date and configuration.end_date)
    has_working_window = bool(
        (configuration.travel_window or configuration.start_date)
        and (configuration.trip_length or configuration.end_date)
    )
    if not (has_exact_dates or has_working_window):
        return False

    selected_modules = configuration.selected_modules
    if selected_modules.flights and not configuration.from_location:
        return False
    if selected_modules.flights and configuration.from_location_flexible:
        return False
    if (
        (selected_modules.flights or selected_modules.hotels)
        and not configuration.travelers.adults
    ):
        return False

    return True


def _chat_planning_mode_request_is_actionable(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    brief_confirmed: bool,
) -> bool:
    if not brief_confirmed:
        return False
    if is_trip_brief_confirmed(
        current_conversation,
        TripTurnUpdate(),
        {},
    ):
        return True
    if llm_update.requested_planning_mode == "advanced":
        return True

    return llm_update.requested_planning_mode == "quick"


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
    finalizing_quick_plan = bool(
        (action and action.type == "finalize_quick_plan")
        or llm_update.planner_intent == "confirm_plan"
    )
    return current_conversation.planning_mode == "quick" and (
        requested_advanced or finalizing_quick_plan
    )


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


def _clamp_last_turn_summary(summary: str | None) -> str | None:
    if summary is None:
        return None
    if len(summary) <= LAST_TURN_SUMMARY_MAX_LENGTH:
        return summary
    return summary[: LAST_TURN_SUMMARY_MAX_LENGTH - 1].rstrip() + "…"


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
    board_action: dict,
) -> dict:
    return evaluate_quick_plan_readiness(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        brief_confirmed=brief_confirmed,
        planning_mode=planning_mode,
        board_action=board_action,
    )


def _is_selected_module_scope_explicit(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
) -> bool:
    if configuration.selected_modules != TripConfiguration().selected_modules:
        return True
    if "selected_modules" in {
        *llm_update.confirmed_fields,
        *llm_update.inferred_fields,
    }:
        return True

    memory = current_conversation.memory.field_memory.get("selected_modules")
    if memory is None:
        return False
    return memory.value == configuration.selected_modules.model_dump(mode="json")


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
        if snapshot["source"] == "assistant_derived" and snapshot["confidence_level"] in {"medium", "high"}:
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


def _evaluate_quick_plan_finalization(
    *,
    current_conversation: TripConversationState,
    planning_mode: str | None,
    timeline: list[TimelineItem],
    module_outputs: TripModuleOutputs,
    provider_activation: dict,
) -> dict:
    existing = current_conversation.quick_plan_finalization
    acceptance = provider_activation.get("quick_plan_acceptance") or {}
    acceptance_present = "accepted" in acceptance
    accepted_this_turn = bool(acceptance.get("accepted"))
    accepted = accepted_this_turn if acceptance_present else bool(existing.accepted)
    review_result = (
        acceptance.get("final_completeness_review")
        or provider_activation.get("quick_plan_completeness_review")
        or provider_activation.get("quick_plan_review")
        if acceptance_present
        else existing.review_result
    ) or {}
    quality_result = (
        acceptance.get("final_quality_review")
        or provider_activation.get("quick_plan_quality_review")
        if acceptance_present
        else existing.quality_result
    ) or {}
    review_status = (
        acceptance.get("completeness_status") or acceptance.get("review_status")
        if acceptance_present
        else existing.review_status
    )
    quality_status = (
        acceptance.get("quality_status")
        if acceptance_present
        else existing.quality_status
    )
    accepted_modules = (
        list(acceptance.get("accepted_modules") or [])
        if accepted_this_turn
        else list(existing.accepted_modules)
    )
    assumptions = (
        list(acceptance.get("assumptions") or [])
        if accepted_this_turn
        else list(existing.assumptions)
    )
    intelligence_summary = (
        _build_quick_plan_intelligence_summary(
            acceptance=acceptance,
            module_outputs=module_outputs,
            timeline=timeline,
            accepted_modules=accepted_modules,
            assumptions=assumptions,
        )
        if accepted_this_turn
        else dict(existing.intelligence_summary)
    )

    blocked_reasons: list[str] = []
    if planning_mode != "quick":
        blocked_reasons.append("Quick Plan is not the active planning mode.")
    if not accepted:
        blocked_reasons.append("Quick Plan has not produced a reviewed and accepted board plan yet.")
    if review_status != "complete":
        blocked_reasons.append("Quick Plan has not passed the completeness review.")
    if quality_status != "pass":
        blocked_reasons.append("Quick Plan has not passed the quality review.")
    if not timeline:
        blocked_reasons.append("The accepted Quick Plan does not have itinerary rows to save.")

    accepted_module_set = set(accepted_modules)
    if "flights" in accepted_module_set:
        flight_directions = {flight.direction for flight in module_outputs.flights}
        flight_anchor_count = sum(
            1
            for item in timeline
            if item.type == "flight" or item.source_module == "flights"
        )
        if not {"outbound", "return"}.issubset(flight_directions):
            blocked_reasons.append("The accepted Quick Plan is missing outbound or return flight details.")
        if flight_anchor_count < 2:
            blocked_reasons.append("The accepted Quick Plan is missing visible flight anchors.")
    if "hotels" in accepted_module_set:
        has_stay_anchor = any(
            item.type == "hotel" or item.source_module == "hotels"
            for item in timeline
        )
        if not module_outputs.hotels:
            blocked_reasons.append("The accepted Quick Plan is missing stay details.")
        if not has_stay_anchor:
            blocked_reasons.append("The accepted Quick Plan is missing a visible stay anchor.")
    if "activities" in accepted_module_set:
        has_activity = bool(module_outputs.activities) or any(
            item.type in {"activity", "event"} or item.source_module == "activities"
            for item in timeline
        )
        if not has_activity:
            blocked_reasons.append("The accepted Quick Plan is missing planned activities.")

    untimed_rows = [
        item.title
        for item in timeline
        if item.type in {"flight", "hotel", "activity", "event", "meal", "transfer"}
        and (item.start_at is None or item.end_at is None)
    ]
    if untimed_rows:
        blocked_reasons.append("The accepted Quick Plan still has visible rows without usable timing.")

    deduped_reasons = list(dict.fromkeys(blocked_reasons))
    return {
        "accepted": accepted,
        "review_status": review_status,
        "quality_status": quality_status,
        "brochure_eligible": accepted and not deduped_reasons,
        "accepted_modules": accepted_modules,
        "assumptions": assumptions,
        "blocked_reasons": deduped_reasons,
        "review_result": review_result,
        "quality_result": quality_result,
        "intelligence_summary": intelligence_summary if accepted else {},
        "final_visible": accepted and not deduped_reasons,
    }


def _build_quick_plan_intelligence_summary(
    *,
    acceptance: dict,
    module_outputs: TripModuleOutputs,
    timeline: list[TimelineItem],
    accepted_modules: list[str],
    assumptions: list[dict[str, Any]],
) -> dict[str, Any]:
    if not acceptance.get("accepted"):
        return {}

    intelligence = acceptance.get("intelligence_metadata") or {}
    strategy = intelligence.get("strategy_brief") or {}
    provider_brief = intelligence.get("provider_brief") or {}
    day_architecture = intelligence.get("day_architecture") or {}
    completeness_review = acceptance.get("final_completeness_review") or {}
    quality_review = acceptance.get("final_quality_review") or {}
    accepted_module_set = set(accepted_modules)
    excluded_modules = [
        {
            "module": module,
            "reason": "Excluded by request",
        }
        for module in ["flights", "hotels", "activities", "weather"]
        if module not in accepted_module_set
    ]
    timing_sources = {item.timing_source for item in timeline if item.timing_source}
    provider_exact_count = sum(
        1 for item in timeline if item.timing_source == "provider_exact"
    )
    planner_estimate_count = sum(
        1 for item in timeline if item.timing_source == "planner_estimate"
    )

    provider_notes: list[str] = []
    if "flights" in accepted_module_set:
        provider_notes.append(
            "Flight anchors are provider-backed."
            if module_outputs.flights
            else "Flight scope is accepted with honest planning anchors."
        )
    if "hotels" in accepted_module_set:
        provider_notes.append(
            "Stay anchor is provider-backed."
            if module_outputs.hotels
            else "Stay scope is accepted with an area-based planning anchor."
        )
    if "activities" in accepted_module_set and module_outputs.activities:
        provider_notes.append("Activity ideas are grounded in accepted module outputs.")
    if "weather" in accepted_module_set and module_outputs.weather:
        provider_notes.append("Weather context is included in the accepted plan.")
    provider_notes.extend(provider_brief.get("fact_safety_caveats") or [])
    provider_notes.extend(
        f"Missing provider fact kept as caveat: {fact}"
        for fact in provider_brief.get("missing_provider_facts") or []
    )

    assumption_notes = [
        _format_quick_plan_assumption(assumption)
        for assumption in assumptions
        if _format_quick_plan_assumption(assumption)
    ]

    return {
        "plan_rationale": strategy.get("trip_thesis")
        or "This Quick Plan was accepted after private completeness and quality review.",
        "plan_fit": {
            "user_intent": strategy.get("user_intent") or [],
            "pacing_rules": strategy.get("pacing_rules") or [],
            "quality_bar": strategy.get("quality_bar") or [],
        },
        "accepted_module_scope": accepted_modules,
        "excluded_modules": excluded_modules,
        "day_architecture_highlights": [
            {
                "day_label": day.get("day_label"),
                "theme": day.get("theme"),
                "geography_focus": day.get("geography_focus"),
                "pacing_target": day.get("pacing_target"),
            }
            for day in (day_architecture.get("days") or [])[:10]
            if day.get("day_label")
        ],
        "provider_confidence_notes": list(dict.fromkeys(provider_notes))[:8],
        "timing_confidence": {
            "sources": sorted(timing_sources),
            "provider_exact_count": provider_exact_count,
            "planner_estimate_count": planner_estimate_count,
        },
        "assumption_notes": assumption_notes[:8],
        "review_outcome": {
            "completeness_status": completeness_review.get("status"),
            "quality_status": quality_review.get("status"),
            "quality_scores": quality_review.get("scorecard") or {},
        },
    }


def _format_quick_plan_assumption(assumption: dict[str, Any]) -> str | None:
    label = assumption.get("label") or assumption.get("type") or assumption.get("key")
    value = assumption.get("value") or assumption.get("description")
    if label and value:
        return f"{label}: {value}"
    if value:
        return str(value)
    if label:
        return str(label).replace("_", " ")
    return None


def _resolve_confirmation_state(
    *,
    current_status: TripDraftStatus,
    current_conversation: TripConversationState,
    llm_update,
    board_action: dict,
    planning_mode: str | None,
    advanced_step: PlannerAdvancedStep | None,
    timeline: list[TimelineItem],
    quick_plan_brochure_eligible: bool,
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
    quick_draft_ready = planning_mode == "quick" and quick_plan_brochure_eligible
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

    if action and action.type == "finalize_quick_plan":
        if quick_draft_ready:
            return ("finalized", now, "board", "finalized")
        return ("unconfirmed", None, None, "quick_plan_blocked")
    if action and action.type == "finalize_advanced_plan" and advanced_review_ready:
        return ("finalized", now, "board", "finalized")
    if planner_intent == "confirm_plan" and planning_mode == "quick":
        if quick_draft_ready:
            return ("finalized", now, "chat", "finalized")
        return ("unconfirmed", None, None, "quick_plan_blocked")
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
    if not configuration.start_date:
        return None
    direction = getattr(flight, "direction", None)
    if direction == "outbound":
        day_number = 1
    elif direction == "return" and configuration.end_date:
        day_number = max((configuration.end_date - configuration.start_date).days + 1, 1)
    else:
        departure_time = getattr(flight, "departure_time", None)
        if not departure_time:
            return None
        day_number = max((departure_time.date() - configuration.start_date).days + 1, 1)
    return f"Day {day_number}"
