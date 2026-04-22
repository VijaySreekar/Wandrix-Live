from datetime import datetime
from uuid import uuid4

from app.graph.planner.date_resolution import build_advanced_date_options
from app.graph.planner.details_collection import compute_scope_missing_fields
from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.graph.planner.provider_enrichment import has_any_module_output
from app.graph.planner.suggestion_board import (
    build_advanced_stay_hotel_options,
    build_advanced_stay_options,
    build_default_decision_cards,
    build_destination_mentioned_options,
    build_suggestion_board_state,
)
from app.graph.planner.turn_models import (
    ConversationOptionCandidate,
    TripOpenQuestionUpdate,
    TripTurnUpdate,
)
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    ConversationDecisionEvent,
    ConversationFieldConfidence,
    ConversationFieldMemory,
    ConversationFieldSource,
    ConversationOptionMemory,
    AdvancedDateResolutionState,
    AdvancedStayPlanningSegment,
    AdvancedStayPlanningState,
    PlannerConfirmationStatus,
    PlannerAdvancedStep,
    PlannerAdvancedAnchor,
    PlannerFinalizedVia,
    ConversationQuestion,
    ConversationTurnSummary,
    PlannerPlanningMode,
    PlannerPlanningModeStatus,
    PlannerDecisionCard,
    TripDetailsStepKey,
    TripConversationMemory,
    TripConversationState,
    TripFieldKey,
)
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


def compute_missing_fields(configuration: TripConfiguration) -> list[str]:
    return compute_missing_fields_with_context(configuration)


def compute_missing_fields_with_context(
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
    *,
    planning_mode: PlannerPlanningMode | None = None,
) -> list[str]:
    return compute_scope_missing_fields(
        configuration,
        resolved_location_context,
        allow_flexible_origin=planning_mode == "advanced",
        allow_flexible_travelers=planning_mode == "advanced",
    )


def build_conversation_state(
    *,
    current: TripConversationState,
    previous_configuration: TripConfiguration,
    next_configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    module_outputs: TripModuleOutputs,
    assistant_response: str,
    turn_id: str,
    user_message: str,
    now: datetime,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
    board_action: dict | None = None,
    brief_confirmed: bool = False,
    planning_mode: PlannerPlanningMode | None = None,
    planning_mode_status: PlannerPlanningModeStatus = "not_selected",
    advanced_step: PlannerAdvancedStep | None = None,
    advanced_anchor: PlannerAdvancedAnchor | None = None,
    planning_mode_choice_required: bool = False,
    confirmation_status: PlannerConfirmationStatus = "unconfirmed",
    finalized_at: datetime | None = None,
    finalized_via: PlannerFinalizedVia | None = None,
    record_memory: bool = True,
) -> TripConversationState:
    conversation = current.model_copy(deep=True)
    missing_fields = compute_missing_fields_with_context(
        next_configuration,
        resolved_location_context,
        planning_mode=planning_mode,
    )
    phase = determine_phase(
        configuration=next_configuration,
        missing_fields=missing_fields,
        module_outputs=module_outputs,
        brief_confirmed=brief_confirmed,
        planning_mode=planning_mode,
        confirmation_status=confirmation_status,
    )

    conversation.phase = phase
    conversation.planning_mode = planning_mode
    conversation.planning_mode_status = planning_mode_status
    conversation.advanced_step = advanced_step
    conversation.advanced_anchor = advanced_anchor
    conversation.confirmation_status = confirmation_status
    conversation.finalized_at = finalized_at
    conversation.finalized_via = finalized_via
    conversation.open_questions = merge_open_questions(
        current.open_questions,
        llm_update,
        next_configuration,
        missing_fields,
    )
    conversation.decision_cards = merge_decision_cards(
        current.decision_cards,
        llm_update.decision_cards or build_default_decision_cards(next_configuration),
        phase,
    )
    conversation.last_turn_summary = (
        llm_update.last_turn_summary.strip()
        if llm_update.last_turn_summary and llm_update.last_turn_summary.strip()
        else build_last_turn_summary(
            next_configuration,
            missing_fields,
            planning_mode=planning_mode,
        )
    )
    conversation.active_goals = merge_active_goals(current.active_goals, llm_update.active_goals)
    conversation.advanced_date_resolution = merge_advanced_date_resolution_state(
        current=current.advanced_date_resolution,
        configuration=next_configuration,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        board_action=board_action or {},
    )
    conversation.stay_planning = merge_stay_planning_state(
        current=current.stay_planning,
        configuration=next_configuration,
        module_outputs=module_outputs,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        board_action=board_action or {},
    )
    conversation.suggestion_board = build_suggestion_board_state(
        current=conversation,
        configuration=next_configuration,
        phase=phase,
        llm_update=llm_update,
        resolved_location_context=resolved_location_context,
        board_action=board_action or {},
        brief_confirmed=brief_confirmed,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        planning_mode_choice_required=planning_mode_choice_required,
    )
    if record_memory:
        conversation.memory = merge_conversation_memory(
            current=current.memory,
            previous_configuration=previous_configuration,
            next_configuration=next_configuration,
            llm_update=llm_update,
            decision_cards=conversation.decision_cards,
            assistant_response=assistant_response,
            turn_id=turn_id,
            user_message=user_message,
            phase=phase,
            now=now,
            board_action=board_action or {},
            planning_mode=planning_mode,
            planning_mode_status=planning_mode_status,
            advanced_anchor=advanced_anchor,
            open_questions=conversation.open_questions,
            active_goals=conversation.active_goals,
            last_turn_summary=conversation.last_turn_summary,
        )

    return conversation


def build_status(
    *,
    current: TripDraftStatus,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    module_outputs: TripModuleOutputs,
    now: datetime,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
    confirmation_status: PlannerConfirmationStatus = "unconfirmed",
    finalized_at: datetime | None = None,
    finalized_via: PlannerFinalizedVia | None = None,
) -> TripDraftStatus:
    status = current.model_copy(deep=True)
    status.phase = conversation.phase
    status.confirmation_status = confirmation_status
    status.finalized_at = finalized_at
    status.finalized_via = finalized_via
    status.missing_fields = compute_missing_fields_with_context(
        configuration,
        resolved_location_context,
        planning_mode=conversation.planning_mode,
    )

    confirmed_fields: list[TripFieldKey] = []
    inferred_fields: list[TripFieldKey] = []
    for field, memory in conversation.memory.field_memory.items():
        if not _field_has_value(configuration, field):
            continue
        if _is_confirmed_field_source(memory.source):
            confirmed_fields.append(field)
        else:
            inferred_fields.append(field)

    status.confirmed_fields = sorted(set(confirmed_fields))
    status.inferred_fields = sorted(set(field for field in inferred_fields if field not in confirmed_fields))
    status.brochure_ready = confirmation_status == "finalized"
    status.last_updated_at = now
    return status


def determine_phase(
    *,
    configuration: TripConfiguration,
    missing_fields: list[str],
    module_outputs: TripModuleOutputs,
    brief_confirmed: bool,
    planning_mode: PlannerPlanningMode | None,
    confirmation_status: PlannerConfirmationStatus,
) -> str:
    if confirmation_status == "finalized":
        return "finalized"

    has_route_signal = bool(configuration.from_location or configuration.to_location)
    has_timing_signal = bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )
    core_shape_ready = bool(configuration.to_location and has_timing_signal)
    provider_ready = bool(configuration.to_location and has_timing_signal)

    if provider_ready and has_any_module_output(module_outputs):
        return "reviewing" if not missing_fields else "enriching_modules"
    if brief_confirmed and planning_mode is None:
        return "shaping_trip"
    if _is_early_draft_ready(configuration):
        return "shaping_trip"
    if not has_route_signal and not has_timing_signal:
        return "opening"
    if not core_shape_ready:
        return "collecting_requirements"
    if missing_fields:
        return "collecting_requirements"
    if provider_ready:
        return "enriching_modules"
    return "shaping_trip"


def is_trip_brief_confirmed(
    conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    board_action: dict | None = None,
    corrected_fields: list[TripFieldKey] | None = None,
) -> bool:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "confirm_trip_details":
        return True
    if corrected_fields:
        return False
    if llm_update.confirmed_trip_brief:
        return True
    return _latest_trip_brief_confirmation_state(conversation.memory.decision_history)


def merge_open_questions(
    current_questions: list[ConversationQuestion],
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> list[ConversationQuestion]:
    active_questions: list[ConversationQuestion] = []
    answered_or_dismissed: list[ConversationQuestion] = []
    active_index: dict[tuple[TripFieldKey | None, TripDetailsStepKey | None, str], int] = {}

    for question in current_questions:
        normalized_existing = _normalize_question_text(question.question)
        if question.status == "dismissed":
            answered_or_dismissed.append(question)
            continue
        if _question_is_still_relevant(question, configuration, missing_fields):
            normalized_field = _normalize_question_field_for_missing_state(
                question.field,
                configuration,
                missing_fields,
            )
            refreshed = question.model_copy(
                update={
                    "status": "open",
                    "priority": _resolve_open_question_priority(
                        field=normalized_field,
                        step=question.step,
                        requested_priority=question.priority,
                        configuration=configuration,
                        missing_fields=missing_fields,
                    ),
                    "field": normalized_field,
                    "step": question.step or _default_question_step(normalized_field),
                    "why": question.why
                    or _default_question_reason(normalized_field, question.step),
                }
            )
            key = _question_identity(
                field=refreshed.field,
                step=refreshed.step,
                question=normalized_existing,
            )
            active_index[key] = len(active_questions)
            active_questions.append(refreshed)
            continue
        answered_or_dismissed.append(question.model_copy(update={"status": "answered"}))

    candidate_updates = [
        *_normalize_legacy_open_question_updates(llm_update.open_questions),
        *llm_update.open_question_updates,
        *_build_default_open_questions(configuration, missing_fields),
    ]
    for candidate in candidate_updates:
        question = _build_conversation_question(
            candidate=candidate,
            configuration=configuration,
            missing_fields=missing_fields,
        )
        if question is None:
            continue
        key = _question_identity(
            field=question.field,
            step=question.step,
            question=_normalize_question_text(question.question),
        )
        if key in active_index:
            position = active_index[key]
            existing = active_questions[position]
            if question.priority < existing.priority:
                active_questions[position] = existing.model_copy(
                    update={
                        "question": question.question,
                        "field": question.field,
                        "step": question.step,
                        "priority": question.priority,
                        "why": question.why or existing.why,
                        "status": "open",
                    }
                )
            continue
        active_index[key] = len(active_questions)
        active_questions.append(question)

    active_questions.sort(key=_open_question_sort_key)
    return [*active_questions[:3], *answered_or_dismissed[-3:]]


def merge_decision_cards(
    current_cards: list[PlannerDecisionCard],
    next_cards: list[PlannerDecisionCard],
    phase: str,
) -> list[PlannerDecisionCard]:
    if phase not in {"shaping_trip", "enriching_modules", "reviewing"}:
        return []

    merged_cards: list[PlannerDecisionCard] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()

    for card in [*current_cards, *next_cards]:
        title = card.title.strip()
        description = card.description.strip()
        options = [option.strip() for option in card.options if option.strip()]
        if not _decision_card_is_useful(
            title=title,
            description=description,
            options=options,
        ):
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


def merge_active_goals(current: list[str], next_goals: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for goal in [*next_goals, *current]:
        cleaned = goal.strip()
        normalized = cleaned.lower()
        if not cleaned or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(cleaned)
    return merged[:4]


def merge_conversation_memory(
    *,
    current: TripConversationMemory,
    previous_configuration: TripConfiguration,
    next_configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    decision_cards: list[PlannerDecisionCard],
    assistant_response: str,
    turn_id: str,
    user_message: str,
    phase: str,
    now: datetime,
    board_action: dict,
    planning_mode: PlannerPlanningMode | None,
    planning_mode_status: PlannerPlanningModeStatus,
    advanced_anchor: PlannerAdvancedAnchor | None,
    open_questions: list[ConversationQuestion],
    active_goals: list[str],
    last_turn_summary: str | None,
) -> TripConversationMemory:
    memory = current.model_copy(deep=True)
    confidence_by_field = {
        item.field: item.confidence for item in llm_update.field_confidences
    }
    source_by_field = {item.field: item.source for item in llm_update.field_sources}
    corrected_fields = detect_confirmed_field_corrections(
        previous_configuration=previous_configuration,
        next_configuration=next_configuration,
        llm_update=llm_update,
    )

    for field in sorted(set([*llm_update.confirmed_fields, *llm_update.inferred_fields])):
        value = _get_configuration_value(next_configuration, field)
        if not _field_value_has_signal(field, value):
            if field in {"from_location_flexible", "travelers_flexible"}:
                memory.field_memory.pop(field, None)
            continue
        source = _resolve_field_source(
            field=field,
            llm_update=llm_update,
            source_by_field=source_by_field,
        )
        memory.field_memory[field] = _merge_field_memory_entry(
            previous_entry=memory.field_memory.get(field),
            field=field,
            value=value,
            source=source,
            confidence_level=confidence_by_field.get(field),
            turn_id=turn_id,
            now=now,
        )

        previous_value = _get_configuration_value(previous_configuration, field)
        if (
            previous_value not in (None, "", [], {})
            and previous_value != value
            and _is_confirmed_field_source(source)
        ):
            corrected_option = _field_to_option_candidate(field, previous_value)
            if corrected_option:
                memory.rejected_options = _merge_option_memory(
                    memory.rejected_options,
                    [corrected_option],
                    turn_id,
                    now,
                )

    memory.mentioned_options = _merge_option_memory(
        memory.mentioned_options,
        [
            *llm_update.mentioned_options,
            *build_destination_mentioned_options(llm_update.destination_suggestions),
        ],
        turn_id,
        now,
    )
    memory.rejected_options = _merge_option_memory(
        memory.rejected_options,
        llm_update.rejected_options,
        turn_id,
        now,
    )
    memory.mentioned_options, memory.rejected_options = _reconcile_option_memories(
        mentioned_options=memory.mentioned_options,
        rejected_options=memory.rejected_options,
        next_configuration=next_configuration,
        llm_update=llm_update,
        turn_id=turn_id,
        now=now,
    )
    memory.decision_history = _merge_decision_history(
        current=memory.decision_history,
        decision_cards=decision_cards,
        llm_update=llm_update,
        turn_id=turn_id,
        now=now,
        board_action=board_action,
        previous_configuration=previous_configuration,
        next_configuration=next_configuration,
        corrected_fields=corrected_fields,
        planning_mode=planning_mode,
        planning_mode_status=planning_mode_status,
        advanced_anchor=advanced_anchor,
    )
    memory.turn_summaries = _merge_turn_summaries(
        current=memory.turn_summaries,
        turn_id=turn_id,
        user_message=user_message,
        assistant_message=assistant_response,
        changed_fields=sorted(set([*llm_update.confirmed_fields, *llm_update.inferred_fields])),
        open_questions=open_questions,
        active_goals=active_goals,
        last_turn_summary=last_turn_summary,
        phase=phase,
        now=now,
        board_action=board_action,
    )

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "select_destination_suggestion":
        leading_value = ", ".join(
            [value for value in [action.destination_name, action.country_or_region] if value]
        )
        if leading_value:
            memory.mentioned_options = _merge_option_memory(
                memory.mentioned_options,
                [ConversationOptionCandidate(kind="destination", value=leading_value)],
                turn_id,
                now,
            )
    return memory


def detect_confirmed_field_corrections(
    *,
    previous_configuration: TripConfiguration,
    next_configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
) -> list[TripFieldKey]:
    source_by_field = {item.field: item.source for item in llm_update.field_sources}
    corrected_fields: list[TripFieldKey] = []

    for field in sorted(set([*llm_update.confirmed_fields, *llm_update.inferred_fields])):
        source = _resolve_field_source(
            field=field,
            llm_update=llm_update,
            source_by_field=source_by_field,
        )
        if not _is_confirmed_field_source(source):
            continue

        previous_value = _get_configuration_value(previous_configuration, field)
        next_value = _get_configuration_value(next_configuration, field)
        if previous_value in (None, "", [], {}):
            continue
        if next_value in (None, "", [], {}):
            continue
        if previous_value == next_value:
            continue
        corrected_fields.append(field)

    return corrected_fields


def build_last_turn_summary(
    configuration: TripConfiguration,
    missing_fields: list[str],
    planning_mode: PlannerPlanningMode | None = None,
) -> str:
    destination = configuration.to_location or "the destination"
    if _is_early_draft_ready(configuration) and planning_mode is None:
        return (
            f"The trip for {destination} already has enough shape for a strong first direction, "
            "even though a few details are still open."
        )
    if not missing_fields and planning_mode is None:
        return (
            f"The trip brief for {destination} is ready for a quick first draft, "
            "and advanced planning can come later."
        )
    if missing_fields:
        return f"The trip is leaning toward {destination}, but key planning details are still open."
    return f"The trip shape is stable enough to start building around {destination}."


def _evaluate_stay_compatibility(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    selected_option_id: str,
) -> tuple[str, list[str]]:
    activity_styles = set(configuration.activity_styles)
    custom_style = (configuration.custom_style or "").lower()
    activities = module_outputs.activities

    wants_food = "food" in activity_styles or any(
        token in custom_style for token in ["food", "market", "markets", "dining", "cafe"]
    )
    wants_quiet = any(
        style in activity_styles for style in ["relaxed", "romantic", "luxury"]
    ) or any(token in custom_style for token in ["quiet", "calm", "slow", "easy mornings"])
    wants_nightlife = "nightlife" in activity_styles or any(
        token in custom_style
        for token in ["nightlife", "late night", "late-night", "bars", "cocktails", "club", "party"]
    )
    has_day_trip_signal = "outdoors" in activity_styles or "adventure" in activity_styles or any(
        token in custom_style
        for token in ["day trip", "day-trip", "hike", "hiking", "beach", "coast", "nature"]
    )
    dense_activity_signal = len(activities) >= 5

    severe_notes: list[str] = []
    moderate_notes: list[str] = []

    if selected_option_id == "stay_quiet_local":
        if wants_nightlife:
            severe_notes.append(
                "the trip now leans too heavily on later nights for a quieter local base to stay effortless"
            )
        if dense_activity_signal or has_day_trip_signal:
            moderate_notes.append(
                "the activity anchors now spread across the trip enough that this calmer base may add daily travel friction"
            )
    elif selected_option_id == "stay_food_forward":
        if has_day_trip_signal:
            moderate_notes.append(
                "the trip is now leaning farther toward day-trip or outdoors anchors than this dining-led base naturally supports"
            )
        if dense_activity_signal and not wants_food:
            moderate_notes.append(
                "the plan now looks denser and less food-led, so this neighbourhood-first base may no longer be the clearest fit"
            )
    elif selected_option_id == "stay_central_base":
        if wants_quiet and not dense_activity_signal and not wants_food:
            moderate_notes.append(
                "the trip now sounds gentler and calmer than a busier central base may feel on the ground"
            )
    elif selected_option_id == "stay_connected_hub":
        if wants_food or wants_quiet:
            moderate_notes.append(
                "the trip is now leaning more toward neighbourhood feel than a purely practical hub base"
            )
    elif selected_option_id == "stay_split_strategy":
        if not dense_activity_signal and not has_day_trip_signal:
            moderate_notes.append(
                "the trip no longer looks varied enough to justify the extra friction of splitting the stay"
            )

    if severe_notes:
        return "conflicted", severe_notes[:4]
    if moderate_notes:
        return "strained", moderate_notes[:4]
    return "fit", []


def _evaluate_selected_hotel_compatibility(
    *,
    selected_option_id: str,
    selected_option_title: str,
    selected_hotel,
    stay_compatibility_status: str,
    stay_compatibility_notes: list[str],
) -> tuple[str, list[str]]:
    hotel_text = " ".join(
        part
        for part in [
            selected_hotel.hotel_name,
            selected_hotel.area or "",
            selected_hotel.summary,
            selected_hotel.why_it_fits,
        ]
        if part
    ).lower()

    if stay_compatibility_status == "conflicted":
        return (
            "conflicted",
            [
                "this hotel sits inside a stay direction that no longer fits the broader trip as cleanly"
            ],
        )
    if stay_compatibility_status == "strained":
        return (
            "strained",
            [
                stay_compatibility_notes[0]
                if stay_compatibility_notes
                else "this hotel sits inside a stay direction that is now under strain"
            ],
        )

    if selected_option_id == "stay_quiet_local" and any(
        token in hotel_text for token in ["station", "central", "hub"]
    ):
        return (
            "strained",
            [
                f"{selected_hotel.hotel_name} is more transit-led than the calmer rhythm {selected_option_title.lower()} was meant to protect"
            ],
        )
    if selected_option_id == "stay_food_forward" and any(
        token in hotel_text for token in ["station", "airport", "hub"]
    ):
        return (
            "strained",
            [
                f"{selected_hotel.hotel_name} feels more practical than neighbourhood-led for a food-forward base"
            ],
        )
    if selected_option_id == "stay_connected_hub" and any(
        token in hotel_text for token in ["quiet", "residential", "local"]
    ):
        return (
            "strained",
            [
                f"{selected_hotel.hotel_name} pulls more local and atmospheric than the current transit-first stay strategy"
            ],
        )

    return "fit", []


def merge_stay_planning_state(
    *,
    current: AdvancedStayPlanningState,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    planning_mode: PlannerPlanningMode | None,
    advanced_step: PlannerAdvancedStep | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
    board_action: dict,
) -> AdvancedStayPlanningState:
    stay_planning = current.model_copy(deep=True)

    if planning_mode != "advanced":
        return stay_planning

    if advanced_step != "anchor_flow" or advanced_anchor != "stay":
        return stay_planning

    active_segment = _build_active_stay_segment(configuration)
    stay_planning.active_segment_id = active_segment.id
    stay_planning.segments = _merge_stay_segments(
        current_segments=stay_planning.segments,
        active_segment=active_segment,
    )
    stay_planning.recommended_stay_options = build_advanced_stay_options(
        configuration=configuration,
        segment_id=active_segment.id,
    )

    selected_option = next(
        (
            option
            for option in stay_planning.recommended_stay_options
            if option.id == stay_planning.selected_stay_option_id
        ),
        None,
    )

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "select_stay_option" and action.stay_option_id:
        selected_option = next(
            (
                option
                for option in stay_planning.recommended_stay_options
                if option.id == action.stay_option_id
                and (
                    action.stay_segment_id is None
                    or option.segment_id == action.stay_segment_id
                )
            ),
            None,
        )
        if selected_option is not None:
            strategy_changed = stay_planning.selected_stay_option_id != selected_option.id
            stay_planning.selected_stay_option_id = selected_option.id
            stay_planning.selected_stay_direction = selected_option.title
            stay_planning.selection_status = "selected"
            stay_planning.selection_rationale = selected_option.summary
            stay_planning.selection_assumptions = list(selected_option.best_for[:4])
            stay_planning.hotel_substep = "hotel_shortlist"
            if stay_planning.compatibility_status not in {"strained", "conflicted"}:
                stay_planning.compatibility_status = "fit"
                stay_planning.compatibility_notes = []
            if strategy_changed:
                stay_planning.selected_hotel_id = None
                stay_planning.selected_hotel_name = None
                stay_planning.hotel_selection_status = "none"
                stay_planning.hotel_selection_rationale = None
                stay_planning.hotel_selection_assumptions = []
                stay_planning.hotel_compatibility_status = "fit"
                stay_planning.hotel_compatibility_notes = []

    if selected_option is None and stay_planning.selection_status != "needs_review":
        stay_planning.selected_stay_option_id = None
        stay_planning.selected_stay_direction = None
        stay_planning.selection_status = "none"
        stay_planning.selection_rationale = None
        stay_planning.selection_assumptions = []
        stay_planning.hotel_substep = "strategy_choice"
        stay_planning.recommended_hotels = []
        stay_planning.selected_hotel_id = None
        stay_planning.selected_hotel_name = None
        stay_planning.hotel_selection_status = "none"
        stay_planning.hotel_selection_rationale = None
        stay_planning.hotel_selection_assumptions = []
        stay_planning.hotel_compatibility_status = "fit"
        stay_planning.hotel_compatibility_notes = []
    elif selected_option is not None:
        stay_planning.selected_stay_option_id = selected_option.id
        stay_planning.selected_stay_direction = selected_option.title
        if stay_planning.selection_status == "none":
            stay_planning.selection_status = "selected"
        if not stay_planning.selection_rationale:
            stay_planning.selection_rationale = selected_option.summary
        if not stay_planning.selection_assumptions:
            stay_planning.selection_assumptions = list(selected_option.best_for[:4])
        stay_planning.recommended_hotels = build_advanced_stay_hotel_options(
            configuration=configuration,
            selected_stay_option=selected_option,
            hotels=module_outputs.hotels,
        )
        if stay_planning.recommended_hotels and stay_planning.hotel_substep == "strategy_choice":
            stay_planning.hotel_substep = "hotel_shortlist"

        selected_hotel = next(
            (
                hotel
                for hotel in stay_planning.recommended_hotels
                if hotel.id == stay_planning.selected_hotel_id
            ),
            None,
        )
        if action and action.type == "select_stay_hotel" and action.stay_hotel_id:
            selected_hotel = next(
                (
                    hotel
                    for hotel in stay_planning.recommended_hotels
                    if hotel.id == action.stay_hotel_id
                ),
                None,
            )
            if selected_hotel is not None:
                stay_planning.selected_hotel_id = selected_hotel.id
                stay_planning.selected_hotel_name = selected_hotel.hotel_name
                stay_planning.hotel_selection_status = "selected"
                stay_planning.hotel_selection_rationale = selected_hotel.why_it_fits
                stay_planning.hotel_selection_assumptions = list(
                    selected_option.best_for[:3]
                )
                stay_planning.hotel_compatibility_status = "fit"
                stay_planning.hotel_compatibility_notes = []
                stay_planning.hotel_substep = "hotel_selected"

        if selected_hotel is None and stay_planning.hotel_selection_status != "needs_review":
            stay_planning.selected_hotel_id = None
            stay_planning.selected_hotel_name = None
            stay_planning.hotel_selection_status = "none"
            stay_planning.hotel_selection_rationale = None
            stay_planning.hotel_selection_assumptions = []
            if stay_planning.hotel_compatibility_status not in {"strained", "conflicted"}:
                stay_planning.hotel_compatibility_status = "fit"
                stay_planning.hotel_compatibility_notes = []
            stay_planning.hotel_substep = (
                "hotel_shortlist" if stay_planning.recommended_hotels else "strategy_choice"
            )
        elif selected_hotel is not None:
            stay_planning.selected_hotel_id = selected_hotel.id
            stay_planning.selected_hotel_name = selected_hotel.hotel_name
            if stay_planning.hotel_selection_status == "none":
                stay_planning.hotel_selection_status = "selected"
            if not stay_planning.hotel_selection_rationale:
                stay_planning.hotel_selection_rationale = selected_hotel.why_it_fits
            if not stay_planning.hotel_selection_assumptions:
                stay_planning.hotel_selection_assumptions = list(
                    selected_option.best_for[:3]
                )
            if stay_planning.hotel_substep == "strategy_choice":
                stay_planning.hotel_substep = "hotel_selected"
            elif stay_planning.hotel_substep != "hotel_review":
                stay_planning.hotel_substep = "hotel_selected"

        stay_compatibility_status, stay_compatibility_notes = _evaluate_stay_compatibility(
            configuration=configuration,
            module_outputs=module_outputs,
            selected_option_id=selected_option.id,
        )
        if (
            stay_compatibility_status == "fit"
            and stay_planning.selection_status == "needs_review"
            and stay_planning.compatibility_notes
        ):
            stay_compatibility_status = (
                stay_planning.compatibility_status
                if stay_planning.compatibility_status in {"strained", "conflicted"}
                else "strained"
            )
            stay_compatibility_notes = list(stay_planning.compatibility_notes[:4])
        stay_planning.compatibility_status = stay_compatibility_status
        stay_planning.compatibility_notes = stay_compatibility_notes
        stay_planning.selection_status = (
            "needs_review"
            if stay_compatibility_status in {"strained", "conflicted"}
            else "selected"
        )

        selected_hotel = next(
            (
                hotel
                for hotel in stay_planning.recommended_hotels
                if hotel.id == stay_planning.selected_hotel_id
            ),
            None,
        )
        if selected_hotel is not None:
            hotel_compatibility_status, hotel_compatibility_notes = (
                _evaluate_selected_hotel_compatibility(
                    selected_option_id=selected_option.id,
                    selected_option_title=selected_option.title,
                    selected_hotel=selected_hotel,
                    stay_compatibility_status=stay_compatibility_status,
                    stay_compatibility_notes=stay_compatibility_notes,
                )
            )
            if (
                hotel_compatibility_status == "fit"
                and stay_planning.hotel_selection_status == "needs_review"
                and stay_planning.hotel_compatibility_notes
            ):
                hotel_compatibility_status = (
                    stay_planning.hotel_compatibility_status
                    if stay_planning.hotel_compatibility_status in {"strained", "conflicted"}
                    else "strained"
                )
                hotel_compatibility_notes = list(
                    stay_planning.hotel_compatibility_notes[:4]
                )
            stay_planning.hotel_compatibility_status = hotel_compatibility_status
            stay_planning.hotel_compatibility_notes = hotel_compatibility_notes
            stay_planning.hotel_selection_status = (
                "needs_review"
                if hotel_compatibility_status in {"strained", "conflicted"}
                else "selected"
            )
            stay_planning.hotel_substep = (
                "hotel_review"
                if hotel_compatibility_status in {"strained", "conflicted"}
                else "hotel_selected"
            )

    return stay_planning


def merge_advanced_date_resolution_state(
    *,
    current: AdvancedDateResolutionState,
    configuration: TripConfiguration,
    planning_mode: PlannerPlanningMode | None,
    advanced_step: PlannerAdvancedStep | None,
    board_action: dict,
) -> AdvancedDateResolutionState:
    date_resolution = current.model_copy(deep=True)
    action = ConversationBoardAction.model_validate(board_action) if board_action else None

    if planning_mode != "advanced":
        return date_resolution

    if configuration.start_date and configuration.end_date:
        date_resolution.selected_start_date = configuration.start_date
        date_resolution.selected_end_date = configuration.end_date
        if date_resolution.selection_status != "confirmed":
            date_resolution.selection_status = "confirmed"
        date_resolution.requires_confirmation = False

    if advanced_step != "resolve_dates":
        if action and action.type == "confirm_working_dates":
            if configuration.start_date and configuration.end_date:
                date_resolution.selection_status = "confirmed"
                date_resolution.requires_confirmation = False
        return date_resolution

    if configuration.travel_window:
        date_resolution.source_timing_text = configuration.travel_window
    if configuration.trip_length:
        date_resolution.source_trip_length_text = configuration.trip_length

    date_resolution.recommended_date_options = build_advanced_date_options(configuration)
    valid_option_ids = {
        option.id for option in date_resolution.recommended_date_options
    }
    selected_option = next(
        (
            option
            for option in date_resolution.recommended_date_options
            if option.id == date_resolution.selected_date_option_id
        ),
        None,
    )

    if action and action.type == "pick_dates_for_me":
        selected_option = next(
            (
                option
                for option in date_resolution.recommended_date_options
                if option.recommended
            ),
            date_resolution.recommended_date_options[0]
            if date_resolution.recommended_date_options
            else None,
        )
    elif action and action.type == "select_date_option" and action.date_option_id:
        selected_option = next(
            (
                option
                for option in date_resolution.recommended_date_options
                if option.id == action.date_option_id
            ),
            None,
        )

    if selected_option is None and date_resolution.selected_date_option_id not in valid_option_ids:
        date_resolution.selected_date_option_id = None
        date_resolution.selected_start_date = None
        date_resolution.selected_end_date = None
        date_resolution.selection_status = "none"
        date_resolution.selection_rationale = None
        date_resolution.requires_confirmation = True
        return date_resolution

    if selected_option is not None:
        date_resolution.selected_date_option_id = selected_option.id
        date_resolution.selected_start_date = selected_option.start_date
        date_resolution.selected_end_date = selected_option.end_date
        date_resolution.selection_status = "selected"
        date_resolution.selection_rationale = selected_option.reason
        date_resolution.requires_confirmation = True

    return date_resolution


def _build_active_stay_segment(
    configuration: TripConfiguration,
) -> AdvancedStayPlanningSegment:
    destination = configuration.to_location or "this trip"
    timing_bits = [bit for bit in [configuration.travel_window, configuration.trip_length] if bit]
    summary = (
        f"Primary stay direction for {destination}."
        if not timing_bits
        else f"Primary stay direction for {destination} around {', '.join(timing_bits)}."
    )
    return AdvancedStayPlanningSegment(
        id="segment_primary",
        title=f"{destination} stay",
        destination_name=configuration.to_location,
        summary=summary,
    )


def _merge_stay_segments(
    *,
    current_segments: list[AdvancedStayPlanningSegment],
    active_segment: AdvancedStayPlanningSegment,
) -> list[AdvancedStayPlanningSegment]:
    merged = [active_segment]
    merged.extend(
        segment
        for segment in current_segments
        if segment.id != active_segment.id
    )
    return merged[:4]


def _merge_option_memory(
    current: list[ConversationOptionMemory],
    candidates: list[ConversationOptionCandidate],
    turn_id: str,
    now: datetime,
) -> list[ConversationOptionMemory]:
    merged = list(current)
    index: dict[tuple[str, str], int] = {
        (item.kind, item.value.lower()): position for position, item in enumerate(merged)
    }

    for candidate in candidates:
        cleaned = candidate.value.strip()
        if not cleaned:
            continue
        key = (candidate.kind, cleaned.lower())
        if key in index:
            position = index[key]
            existing = merged[position]
            merged[position] = ConversationOptionMemory(
                kind=existing.kind,
                value=existing.value,
                source_turn_id=turn_id,
                first_seen_at=existing.first_seen_at,
                last_seen_at=now,
            )
            continue

        merged.append(
            ConversationOptionMemory(
                kind=candidate.kind,
                value=cleaned,
                source_turn_id=turn_id,
                first_seen_at=now,
                last_seen_at=now,
            )
        )
        index[key] = len(merged) - 1

    return merged[-12:]


def _reconcile_option_memories(
    *,
    mentioned_options: list[ConversationOptionMemory],
    rejected_options: list[ConversationOptionMemory],
    next_configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    turn_id: str,
    now: datetime,
) -> tuple[list[ConversationOptionMemory], list[ConversationOptionMemory]]:
    active_candidates = list(llm_update.mentioned_options)

    for field in sorted(set([*llm_update.confirmed_fields, *llm_update.inferred_fields])):
        value = _get_configuration_value(next_configuration, field)
        if value in (None, "", [], {}):
            continue
        candidate = _field_to_option_candidate(field, value)
        if candidate is not None:
            active_candidates.append(candidate)

    active_keys = {
        key
        for candidate in active_candidates
        for key in _option_identity_keys(candidate.kind, candidate.value)
    }
    rejected_keys = {
        key
        for option in rejected_options
        for key in _option_identity_keys(option.kind, option.value)
    }

    reconciled_mentioned = [
        option
        for option in mentioned_options
        if not rejected_keys.intersection(_option_identity_keys(option.kind, option.value))
    ]
    reconciled_rejected = [
        option
        for option in rejected_options
        if not active_keys.intersection(_option_identity_keys(option.kind, option.value))
    ]

    refreshed_mentioned = _merge_option_memory(
        reconciled_mentioned,
        active_candidates,
        turn_id,
        now,
    )
    return refreshed_mentioned, reconciled_rejected


def _merge_decision_history(
    *,
    current: list[ConversationDecisionEvent],
    decision_cards: list[PlannerDecisionCard],
    llm_update: TripTurnUpdate,
    turn_id: str,
    now: datetime,
    board_action: dict,
    previous_configuration: TripConfiguration,
    next_configuration: TripConfiguration,
    corrected_fields: list[TripFieldKey],
    planning_mode: PlannerPlanningMode | None,
    planning_mode_status: PlannerPlanningModeStatus,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> list[ConversationDecisionEvent]:
    merged = list(current)
    seen = {
        (item.title.lower(), tuple(option.lower() for option in item.options))
        for item in merged
    }
    existing_advanced_anchor_selections = {
        item.selected_option.lower()
        for item in merged
        if item.title.lower() == "advanced anchor selected" and item.selected_option
    }
    existing_stay_selections = {
        item.selected_option.lower()
        for item in merged
        if item.title.lower() == "stay strategy selected" and item.selected_option
    }
    existing_hotel_selections = {
        item.selected_option.lower()
        for item in merged
        if item.title.lower() == "stay hotel selected" and item.selected_option
    }

    for card in decision_cards:
        key = (card.title.lower(), tuple(option.lower() for option in card.options))
        if key in seen:
            continue
        seen.add(key)
        merged.append(
            ConversationDecisionEvent(
                id=f"decision_{uuid4().hex[:10]}",
                title=card.title,
                description=card.description,
                options=card.options,
                source_turn_id=turn_id,
                resolved_at=now,
            )
        )

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "confirm_trip_details":
        confirmation_key = ("trip details confirmed", tuple())
        if confirmation_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Trip details confirmed",
                    description="The user confirmed the structured trip details from the board.",
                    options=[],
                    selected_option="confirm_trip_details",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    for field in corrected_fields:
        correction_key = ("trip details corrected", (field,))
        if correction_key in seen:
            continue
        merged.append(
            ConversationDecisionEvent(
                id=f"decision_{uuid4().hex[:10]}",
                title="Trip details corrected",
                description=_build_trip_detail_correction_description(
                    field=field,
                    previous_value=_get_configuration_value(previous_configuration, field),
                    next_value=_get_configuration_value(next_configuration, field),
                ),
                options=[field],
                selected_option=field,
                source_turn_id=turn_id,
                resolved_at=now,
            )
        )
        seen.add(correction_key)
    accepted_quick_selection = (
        planning_mode == "quick" and planning_mode_status == "selected"
    )
    accepted_advanced_selection = (
        planning_mode == "advanced" and planning_mode_status == "selected"
    )

    if action and action.type == "select_quick_plan" and accepted_quick_selection:
        selection_key = ("planning mode selected", ("quick",))
        if selection_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Planning mode selected",
                    description="The user chose Quick Plan for a fast first-pass itinerary.",
                    options=["quick"],
                    selected_option="quick",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if action and action.type == "select_advanced_plan" and accepted_advanced_selection:
        selection_key = ("planning mode selected", ("advanced",))
        if selection_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Planning mode selected",
                    description="The user chose Advanced Planning for a more guided trip-building flow.",
                    options=["quick", "advanced"],
                    selected_option="advanced",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if llm_update.confirmed_trip_brief and not (
        action and action.type == "confirm_trip_details"
    ):
        confirmation_key = ("trip details confirmed", tuple())
        if confirmation_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Trip details confirmed",
                    description="The user confirmed the current working trip details in chat.",
                    options=[],
                    selected_option="confirm_trip_details",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if (
        llm_update.requested_planning_mode == "quick"
        and not action
        and accepted_quick_selection
    ):
        selection_key = ("planning mode selected", ("quick",))
        if selection_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Planning mode selected",
                    description="The user asked Wandrix to generate a quick itinerary draft.",
                    options=["quick"],
                    selected_option="quick",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if (
        llm_update.requested_planning_mode == "advanced"
        and not action
        and accepted_advanced_selection
    ):
        selection_key = ("planning mode selected", ("advanced",))
        if selection_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Planning mode selected",
                    description="The user asked for Advanced Planning in chat.",
                    options=["quick", "advanced"],
                    selected_option="advanced",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if action and action.type == "select_advanced_anchor" and advanced_anchor:
        selection_key = ("advanced anchor selected", (advanced_anchor,))
        if advanced_anchor not in existing_advanced_anchor_selections:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Advanced anchor selected",
                    description=(
                        f"The user chose {advanced_anchor.replace('_', ' ')} to lead the next Advanced Planning step."
                    ),
                    options=["flight", "stay", "trip_style", "activities"],
                    selected_option=advanced_anchor,
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
            existing_advanced_anchor_selections.add(advanced_anchor)
    if action and action.type == "select_stay_option" and action.stay_option_id:
        selection_key = ("stay strategy selected", (action.stay_option_id,))
        if action.stay_option_id not in existing_stay_selections:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Stay strategy selected",
                    description="The user chose a working stay direction for the next Advanced Planning step.",
                    options=["working_stay_direction"],
                    selected_option=action.stay_option_id,
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
            existing_stay_selections.add(action.stay_option_id)
    if action and action.type == "select_stay_hotel" and action.stay_hotel_id:
        selection_key = ("stay hotel selected", (action.stay_hotel_id,))
        if action.stay_hotel_id not in existing_hotel_selections:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Stay hotel selected",
                    description="The user chose a working hotel inside the selected stay direction.",
                    options=["working_hotel_choice"],
                    selected_option=action.stay_hotel_id,
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
            existing_hotel_selections.add(action.stay_hotel_id)
    if (
        llm_update.requested_advanced_anchor
        and not action
        and planning_mode == "advanced"
        and planning_mode_status == "selected"
    ):
        selection_key = (
            "advanced anchor selected",
            (llm_update.requested_advanced_anchor,),
        )
        if llm_update.requested_advanced_anchor not in existing_advanced_anchor_selections:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Advanced anchor selected",
                    description=(
                        f"The user chose {llm_update.requested_advanced_anchor.replace('_', ' ')} to lead the next Advanced Planning step."
                    ),
                    options=["flight", "stay", "trip_style", "activities"],
                    selected_option=llm_update.requested_advanced_anchor,
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
            existing_advanced_anchor_selections.add(
                llm_update.requested_advanced_anchor
            )
    if action and action.type == "finalize_quick_plan":
        finalization_key = ("trip plan finalized", ("board",))
        if finalization_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Trip plan finalized",
                    description="The user finalized the quick plan from the board and saved the brochure-ready trip.",
                    options=["board"],
                    selected_option="board",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if action and action.type == "reopen_plan":
        reopen_key = ("planning reopened", ("board",))
        if reopen_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Planning reopened",
                    description="The user reopened the finalized trip from the board so planning could continue.",
                    options=["board"],
                    selected_option="board",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if llm_update.planner_intent == "confirm_plan" and not action:
        finalization_key = ("trip plan finalized", ("chat",))
        if finalization_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Trip plan finalized",
                    description="The user finalized the quick plan in chat and saved the brochure-ready trip.",
                    options=["chat"],
                    selected_option="chat",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    if llm_update.planner_intent == "reopen_plan" and not action:
        reopen_key = ("planning reopened", ("chat",))
        if reopen_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Planning reopened",
                    description="The user reopened the finalized trip in chat so planning could continue.",
                    options=["chat"],
                    selected_option="chat",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )

    return merged[-12:]


def _merge_turn_summaries(
    *,
    current: list[ConversationTurnSummary],
    turn_id: str,
    user_message: str,
    assistant_message: str,
    changed_fields: list[TripFieldKey],
    open_questions: list[ConversationQuestion],
    active_goals: list[str],
    last_turn_summary: str | None,
    phase: str,
    now: datetime,
    board_action: dict | None = None,
) -> list[ConversationTurnSummary]:
    merged = list(current)
    summary_user_message = user_message.strip() or _build_turn_summary_user_message(
        board_action or {}
    )
    open_fields = [
        question.field
        for question in open_questions
        if question.status == "open" and question.field is not None
    ]
    next_open_question = next(
        (
            question.question
            for question in open_questions
            if question.status == "open" and question.question.strip()
        ),
        None,
    )
    summary_text = _build_structured_turn_summary_text(
        changed_fields=changed_fields,
        open_fields=open_fields,
        active_goals=active_goals,
        phase=phase,
        last_turn_summary=last_turn_summary,
    )
    merged.append(
        ConversationTurnSummary(
            turn_id=turn_id,
            user_message=summary_user_message,
            assistant_message=assistant_message.strip(),
            summary_text=summary_text,
            changed_fields=changed_fields,
            open_fields=sorted(set(open_fields)),
            next_open_question=next_open_question,
            active_goal=active_goals[0] if active_goals else None,
            resulting_phase=phase,
            created_at=now,
        )
    )
    return merged[-10:]


def _build_structured_turn_summary_text(
    *,
    changed_fields: list[TripFieldKey],
    open_fields: list[TripFieldKey],
    active_goals: list[str],
    phase: str,
    last_turn_summary: str | None,
) -> str:
    changed_labels = [_field_resume_label(field) for field in changed_fields[:3]]
    open_labels = [_field_resume_label(field) for field in sorted(set(open_fields))[:2]]

    parts: list[str] = []
    if changed_labels:
        parts.append(f"Changed {', '.join(changed_labels)}.")
    elif last_turn_summary and last_turn_summary.strip():
        parts.append(last_turn_summary.strip().rstrip(".") + ".")

    if open_labels:
        parts.append(f"Still resolving {', '.join(open_labels)}.")

    if active_goals:
        parts.append(f"Planner focus: {active_goals[0].strip().rstrip('.')}.")
    else:
        parts.append(f"Planner phase: {phase.replace('_', ' ')}.")

    return " ".join(parts)[:400]


def _build_turn_summary_user_message(board_action: dict) -> str:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action is None:
        return "Planner action recorded."
    if action.type == "finalize_quick_plan":
        return "Board action: confirm the current quick plan."
    if action.type == "reopen_plan":
        return "Board action: reopen planning for this trip."
    if action.type == "confirm_trip_details":
        return "Board action: confirm the current trip details."
    if action.type == "select_quick_plan":
        return "Board action: generate a quick plan."
    if action.type == "select_advanced_plan":
        return "Board action: request advanced planning."
    if action.type == "select_destination_suggestion":
        return "Board action: choose a destination suggestion."
    if action.type == "own_choice":
        return "Board action: continue with a custom destination."
    return f"Board action: {action.type.replace('_', ' ')}."


def _build_default_open_questions(
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> list[TripOpenQuestionUpdate]:
    questions: dict[str, TripOpenQuestionUpdate] = {
        "selected_modules": TripOpenQuestionUpdate(
            question="Which parts of the trip should I actually help with first, and is anything already booked or out of scope?",
            field="selected_modules",
            step="modules",
            why="Module scope changes which providers and follow-up questions Wandrix should activate next.",
        ),
        "from_location": TripOpenQuestionUpdate(
            question="Where are you most likely travelling from for this trip?",
            field="from_location",
            step="route",
            why="The likely departure point changes route practicality and shortlist quality.",
        ),
        "to_location": TripOpenQuestionUpdate(
            question="Which destination should I shape this trip around?",
            field="to_location",
            step="route",
            why="I need the destination before I can make the rest of the plan concrete.",
        ),
        "start_date": TripOpenQuestionUpdate(
            question="What month or travel window are you considering?",
            field="travel_window",
            step="timing",
            why="Rough timing is enough for now and keeps the trip flexible.",
        ),
        "end_date": TripOpenQuestionUpdate(
            question=(
                "How long should this trip be?"
                if configuration.start_date or configuration.travel_window
                else "Roughly how many days or nights should I plan around?"
            ),
            field="trip_length",
            step="timing",
            why="A rough trip length helps me pace the itinerary without forcing exact dates.",
        ),
        "weather_preference": TripOpenQuestionUpdate(
            question="What kind of weather are you hoping for on this trip?",
            field="weather_preference",
            step="timing",
            why="Weather preference helps Wandrix shape timing and destination fit earlier in the planning flow.",
        ),
        "adults": TripOpenQuestionUpdate(
            question="Who's travelling, and do I need to plan for any children?",
            field="adults",
            step="travellers",
            why="Group makeup affects flights, rooms, pace, and whether children need special consideration.",
        ),
        "activity_styles": TripOpenQuestionUpdate(
            question="What kind of trip do you want this to feel like?",
            field="activity_styles",
            step="vibe",
            why="The trip style shapes the right pace and activities.",
        ),
        "budget_posture": TripOpenQuestionUpdate(
            question="What overall budget feel should I optimize around, and is there anything you'd rather splurge on or keep sensible?",
            field="budget_posture",
            step="budget",
            why="Budget helps narrow the right flights and hotels, but the tradeoffs are often mixed.",
        ),
    }
    return [questions[field] for field in missing_fields if field in questions]


def _build_trip_detail_correction_description(
    *,
    field: TripFieldKey,
    previous_value: object,
    next_value: object,
) -> str:
    label = _field_history_label(field)
    previous_text = _format_history_value(previous_value)
    next_text = _format_history_value(next_value)
    return (
        f"The user corrected {label} from {previous_text} to {next_text}."
        if previous_text and next_text
        else f"The user corrected {label}."
    )


def _field_history_label(field: TripFieldKey) -> str:
    return {
        "from_location": "the departure point",
        "from_location_flexible": "departure flexibility",
        "to_location": "the destination",
        "start_date": "the start date",
        "end_date": "the end date",
        "travel_window": "the travel window",
        "trip_length": "the trip length",
        "weather_preference": "the weather preference",
        "budget_posture": "the budget posture",
        "budget_gbp": "the budget amount",
        "adults": "the adult count",
        "children": "the child count",
        "travelers_flexible": "traveller flexibility",
        "activity_styles": "the trip style",
        "custom_style": "the custom trip style",
        "selected_modules": "the selected modules",
    }[field]


def _field_resume_label(field: TripFieldKey) -> str:
    return {
        "from_location": "departure point",
        "from_location_flexible": "departure flexibility",
        "to_location": "destination",
        "start_date": "start date",
        "end_date": "end date",
        "travel_window": "travel window",
        "trip_length": "trip length",
        "weather_preference": "weather preference",
        "budget_posture": "budget",
        "budget_gbp": "budget",
        "adults": "traveller count",
        "children": "child traveller count",
        "travelers_flexible": "traveller flexibility",
        "activity_styles": "trip style",
        "custom_style": "custom trip style",
        "selected_modules": "module scope",
    }[field]


def _format_history_value(value: object) -> str | None:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, dict):
        enabled = [name for name, is_enabled in value.items() if is_enabled]
        return ", ".join(enabled) if enabled else "no modules selected"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else None
    return str(value)


def _latest_trip_brief_confirmation_state(
    decision_history: list[ConversationDecisionEvent],
) -> bool:
    for event in reversed(decision_history):
        title = event.title.lower()
        if title == "trip details corrected":
            return False
        if title == "trip details confirmed":
            return True
    return False


def _guess_question_field(question: str) -> TripFieldKey | None:
    normalized = question.lower()
    if "focus on first" in normalized or "flights" in normalized or "hotels" in normalized:
        return "selected_modules"
    if "from" in normalized or "travelling from" in normalized:
        return "from_location"
    if "flexible departure" in normalized or "departure can stay flexible" in normalized:
        return "from_location_flexible"
    if "destination" in normalized or "trip around" in normalized:
        return "to_location"
    if "month" in normalized or "window" in normalized:
        return "travel_window"
    if "weather" in normalized or "warm" in normalized or "sun" in normalized or "snow" in normalized:
        return "weather_preference"
    if "days" in normalized or "nights" in normalized or "long" in normalized:
        return "trip_length"
    if "traveller count is flexible" in normalized or "group is still flexible" in normalized:
        return "travelers_flexible"
    if "people" in normalized:
        return "adults"
    if "feel like" in normalized or "trip style" in normalized:
        return "activity_styles"
    if "custom style" in normalized or "describe your own style" in normalized:
        return "custom_style"
    if "budget" in normalized or "premium" in normalized:
        return "budget_posture"
    return None


def _field_has_value(configuration: TripConfiguration, field: TripFieldKey) -> bool:
    value = _get_configuration_value(configuration, field)
    return _field_value_has_signal(field, value)


def _get_configuration_value(
    configuration: TripConfiguration,
    field: TripFieldKey,
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


def _field_value_has_signal(field: TripFieldKey, value: object) -> bool:
    if field in {"from_location_flexible", "travelers_flexible"}:
        return value is True
    if field == "adults":
        return isinstance(value, int) and value > 0
    return value not in (None, "", [], {})


def _field_to_option_candidate(field: TripFieldKey, value: object) -> ConversationOptionCandidate | None:
    if field == "to_location" and isinstance(value, str):
        return ConversationOptionCandidate(kind="destination", value=value)
    if field == "from_location" and isinstance(value, str):
        return ConversationOptionCandidate(kind="origin", value=value)
    if field in {"start_date", "travel_window"}:
        return ConversationOptionCandidate(kind="timing_window", value=str(value))
    if field == "weather_preference":
        return None
    if field == "from_location_flexible":
        return None
    if field == "custom_style":
        return None
    if field == "travelers_flexible":
        return None
    if field in {"end_date", "trip_length"}:
        return ConversationOptionCandidate(kind="trip_length", value=str(value))
    if field == "budget_posture":
        return ConversationOptionCandidate(kind="budget_posture", value=str(value))
    return None


def _option_identity_keys(kind: str, value: str) -> set[tuple[str, str]]:
    cleaned = " ".join(value.strip().lower().split())
    if not cleaned:
        return set()

    keys = {(kind, cleaned)}
    if kind in {"destination", "origin"}:
        primary = cleaned.split(",")[0].strip()
        if primary:
            keys.add((kind, primary))
    return keys


def _merge_field_memory_entry(
    *,
    previous_entry: ConversationFieldMemory | None,
    field: TripFieldKey,
    value: object,
    source: ConversationFieldSource,
    confidence_level: ConversationFieldConfidence | None,
    turn_id: str,
    now: datetime,
) -> ConversationFieldMemory:
    previous_confidence_level = _effective_confidence_level(previous_entry)
    if previous_entry is None:
        return ConversationFieldMemory(
            field=field,
            value=value,
            confidence_level=confidence_level,
            confidence=None,
            source=source,
            source_turn_id=turn_id,
            first_seen_at=now,
            last_seen_at=now,
        )

    previous_priority = _field_source_priority(previous_entry.source)
    incoming_priority = _field_source_priority(source)
    keep_previous_source = (
        previous_entry.value == value and previous_priority > incoming_priority
    )

    if keep_previous_source:
        return ConversationFieldMemory(
            field=field,
            value=value,
            confidence_level=_stronger_confidence_level(
                previous_confidence_level,
                confidence_level,
            ),
            confidence=None,
            source=previous_entry.source,
            source_turn_id=previous_entry.source_turn_id,
            first_seen_at=previous_entry.first_seen_at,
            last_seen_at=now,
        )

    return ConversationFieldMemory(
        field=field,
        value=value,
        confidence_level=(
            _stronger_confidence_level(previous_confidence_level, confidence_level)
            if previous_entry.value == value
            else confidence_level
        ),
        confidence=None,
        source=source,
        source_turn_id=turn_id,
        first_seen_at=previous_entry.first_seen_at,
        last_seen_at=now,
    )


def _field_source_priority(source: ConversationFieldSource) -> int:
    return {
        "profile_default": 0,
        "assistant_derived": 1,
        "user_inferred": 2,
        "user_explicit": 3,
        "board_action": 4,
    }[source]


def _resolve_field_source(
    *,
    field: TripFieldKey,
    llm_update: TripTurnUpdate,
    source_by_field: dict[TripFieldKey, ConversationFieldSource],
) -> ConversationFieldSource:
    source = source_by_field.get(field)
    if source is not None:
        return source
    return "user_explicit" if field in llm_update.confirmed_fields else "user_inferred"


def _is_confirmed_field_source(source: ConversationFieldSource) -> bool:
    return source in {"user_explicit", "board_action"}


def _effective_confidence_level(
    entry: ConversationFieldMemory | None,
) -> ConversationFieldConfidence | None:
    if entry is None:
        return None
    if entry.confidence_level is not None:
        return entry.confidence_level
    if entry.confidence is None:
        return None
    if entry.confidence >= 0.85:
        return "high"
    if entry.confidence >= 0.55:
        return "medium"
    return "low"


def _stronger_confidence_level(
    previous: ConversationFieldConfidence | None,
    incoming: ConversationFieldConfidence | None,
) -> ConversationFieldConfidence | None:
    if previous is None:
        return incoming
    if incoming is None:
        return previous
    return (
        previous
        if _field_confidence_priority(previous)
        >= _field_confidence_priority(incoming)
        else incoming
    )


def _field_confidence_priority(level: ConversationFieldConfidence) -> int:
    return {
        "low": 0,
        "medium": 1,
        "high": 2,
    }[level]


def _question_is_still_relevant(
    question: ConversationQuestion,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> bool:
    if question.field is None:
        return True

    if question.field == "selected_modules":
        return "selected_modules" in missing_fields
    if question.field == "from_location":
        return "from_location" in missing_fields
    if question.field == "from_location_flexible":
        return False
    if question.field == "to_location":
        return "to_location" in missing_fields
    if question.field in {"start_date", "travel_window"}:
        return "start_date" in missing_fields
    if question.field == "weather_preference":
        return configuration.weather_preference is None
    if question.field in {"end_date", "trip_length"}:
        return "end_date" in missing_fields
    if question.field == "adults":
        return "adults" in missing_fields
    if question.field == "budget_posture":
        return configuration.budget_posture is None
    if question.field == "custom_style":
        return configuration.custom_style is None and not configuration.activity_styles
    if question.field == "travelers_flexible":
        return False

    return True


def _normalize_legacy_open_question_updates(
    questions: list[str],
) -> list[TripOpenQuestionUpdate]:
    updates: list[TripOpenQuestionUpdate] = []
    for question in questions:
        cleaned = question.strip()
        if not cleaned:
            continue
        field = _guess_question_field(cleaned)
        updates.append(
            TripOpenQuestionUpdate(
                question=cleaned,
                field=field,
                step=_default_question_step(field),
                why=_default_question_reason(field, _default_question_step(field)),
            )
        )
    return updates


def _build_conversation_question(
    *,
    candidate: TripOpenQuestionUpdate,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> ConversationQuestion | None:
    cleaned = candidate.question.strip()
    if not cleaned:
        return None

    field = _normalize_question_field_for_missing_state(
        candidate.field or _guess_question_field(cleaned),
        configuration,
        missing_fields,
    )
    step = candidate.step or _default_question_step(field)
    question = ConversationQuestion(
        id=f"question_{uuid4().hex[:10]}",
        question=cleaned,
        field=field,
        step=step,
        priority=_resolve_open_question_priority(
            field=field,
            step=step,
            requested_priority=candidate.priority,
            configuration=configuration,
            missing_fields=missing_fields,
        ),
        why=(candidate.why.strip() if candidate.why else None)
        or _default_question_reason(field, step),
        status="open",
    )
    if not _question_is_still_relevant(question, configuration, missing_fields):
        return None
    return question


def _resolve_open_question_priority(
    *,
    field: TripFieldKey | None,
    step: TripDetailsStepKey | None,
    requested_priority: int,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> int:
    if field is not None:
        default_priority = _default_question_priority_for_field(
            field=field,
            configuration=configuration,
            missing_fields=missing_fields,
        )
        return max(1, min(5, default_priority))
    if step is not None:
        return max(1, min(5, _default_question_priority_for_step(step)))
    return max(1, min(5, requested_priority))


def _default_question_priority_for_field(
    *,
    field: TripFieldKey,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> int:
    has_destination = bool(configuration.to_location)
    has_route = bool(configuration.from_location or configuration.to_location)
    has_timing = bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )

    if field == "to_location":
        return 1
    if field == "selected_modules":
        return 2 if has_destination else 3
    if field == "from_location":
        return 2 if has_destination else 4
    if field == "from_location_flexible":
        return 3
    if field in {"travel_window", "start_date"}:
        return 2
    if field == "weather_preference":
        return 3
    if field in {"trip_length", "end_date"}:
        return 3 if has_timing else 2
    if field in {"adults", "children"}:
        return 3 if has_route else 4
    if field == "travelers_flexible":
        return 3 if has_route else 4
    if field == "activity_styles":
        return 4
    if field == "custom_style":
        return 4
    if field in {"budget_posture", "budget_gbp"}:
        return 5
    return 3


def _default_question_priority_for_step(step: TripDetailsStepKey) -> int:
    return {
        "route": 1,
        "timing": 2,
        "modules": 3,
        "travellers": 3,
        "vibe": 4,
        "budget": 5,
    }[step]


def _default_question_step(field: TripFieldKey | None) -> TripDetailsStepKey | None:
    if field == "selected_modules":
        return "modules"
    if field in {"from_location", "to_location"}:
        return "route"
    if field == "from_location_flexible":
        return "route"
    if field in {"start_date", "end_date", "travel_window", "trip_length"}:
        return "timing"
    if field == "weather_preference":
        return "timing"
    if field in {"adults", "children"}:
        return "travellers"
    if field == "travelers_flexible":
        return "travellers"
    if field == "activity_styles":
        return "vibe"
    if field == "custom_style":
        return "vibe"
    if field in {"budget_posture", "budget_gbp"}:
        return "budget"
    return None


def _default_question_reason(
    field: TripFieldKey | None,
    step: TripDetailsStepKey | None,
) -> str | None:
    if field == "selected_modules":
        return "Module scope decides which details matter next."
    if field == "to_location":
        return "The destination is the highest-value planning decision right now."
    if field == "from_location":
        return "The likely departure point changes route practicality and flight options."
    if field == "from_location_flexible":
        return "Departure can stay flexible for now, so Wandrix should avoid treating it as fixed too early."
    if field in {"start_date", "travel_window"}:
        return "Rough timing is enough to keep the trip moving without locking exact dates."
    if field == "weather_preference":
        return "Weather preference helps Wandrix steer timing and destination fit earlier in the planning flow."
    if field in {"end_date", "trip_length"}:
        return "A rough length helps pace the itinerary before exact dates are chosen."
    if field in {"adults", "children"}:
        return "Group makeup changes rooms, flights, pace, and whether children need special consideration."
    if field == "travelers_flexible":
        return "The traveller count can stay flexible during intake, but later booking-grade planning will still need firmer numbers."
    if field == "activity_styles":
        return "Trip style helps Wandrix shape the right pace and experiences."
    if field == "custom_style":
        return "A custom trip-style note can carry nuance that preset style chips cannot."
    if field in {"budget_posture", "budget_gbp"}:
        return "Budget narrows realistic flight and hotel options, but the posture is often nuanced."
    if step == "route":
        return "The route needs to be clearer before the rest of the brief can firm up."
    if step == "timing":
        return "Timing is the next biggest planning gap."
    return None


def _normalize_question_field_for_missing_state(
    field: TripFieldKey | None,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> TripFieldKey | None:
    if field == "start_date" and "start_date" in missing_fields:
        return "travel_window"
    if field == "end_date" and "end_date" in missing_fields:
        return "trip_length"
    return field


def _question_identity(
    *,
    field: TripFieldKey | None,
    step: TripDetailsStepKey | None,
    question: str,
) -> tuple[TripFieldKey | None, TripDetailsStepKey | None, str]:
    if field is not None:
        return (field, step, "")
    if step is not None:
        return (None, step, question)
    return (None, None, question)


def _normalize_question_text(question: str) -> str:
    return " ".join(question.strip().lower().split())


def _open_question_sort_key(
    question: ConversationQuestion,
) -> tuple[int, int, str]:
    status_priority = {
        "open": 0,
        "answered": 1,
        "dismissed": 2,
    }[question.status]
    return (status_priority, question.priority, question.question.lower())


def _decision_card_is_useful(
    *,
    title: str,
    description: str,
    options: list[str],
) -> bool:
    if not title or not description:
        return False
    if len(options) < 2:
        return False

    normalized_title = title.lower()
    normalized_description = description.lower()
    normalized_options = [option.lower() for option in options]

    generic_titles = {
        "next trip decisions",
        "next steps",
        "what kind of trip do you want",
        "choose your options",
        "trip choices",
    }
    if normalized_title in generic_titles:
        return False

    generic_options = {"option 1", "option 2", "option 3", "yes", "no", "maybe"}
    if all(option in generic_options for option in normalized_options):
        return False

    useful_terms = (
        "timing",
        "window",
        "departure",
        "origin",
        "feel",
        "pace",
        "food",
        "highlights",
        "outdoors",
        "weekend",
        "planning mode",
        "quick plan",
        "advanced",
    )
    useful_signal = any(term in normalized_title for term in useful_terms) or any(
        term in normalized_description for term in useful_terms
    )
    if useful_signal:
        return True

    return len(set(normalized_options)) >= 2 and any(
        len(option.split()) >= 2 for option in normalized_options
    )


def _is_early_draft_ready(configuration: TripConfiguration) -> bool:
    has_destination = bool(configuration.to_location)
    has_timing_signal = bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )
    return has_destination and has_timing_signal
