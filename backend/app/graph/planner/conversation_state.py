from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

from app.graph.planner.date_resolution import build_advanced_date_options
from app.graph.planner.details_collection import compute_scope_missing_fields
from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.graph.planner.provider_enrichment import has_any_module_output
from app.graph.planner.suggestion_board import (
    build_advanced_stay_hotel_workspace,
    build_advanced_stay_hotel_options,
    build_advanced_stay_options,
    build_default_decision_cards,
    build_destination_mentioned_options,
    build_suggestion_board_state,
)
from app.services.providers.events import enrich_events_from_ticketmaster
from app.services.providers.movement import estimate_travel_duration_minutes
from app.graph.planner.turn_models import (
    ConversationOptionCandidate,
    RequestedActivityScheduleEdit,
    RequestedTripStyleDirectionUpdate,
    RequestedTripStylePaceUpdate,
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
    AdvancedActivityCandidateCard,
    AdvancedActivityDayPlan,
    AdvancedActivityPlacementPreference,
    AdvancedActivityPlanningState,
    AdvancedActivityTimelineBlock,
    AdvancedDateResolutionState,
    AdvancedStayPlanningSegment,
    AdvancedStayPlanningState,
    PlannerTripDirectionAccent,
    PlannerTripDirectionPrimary,
    PlannerTripPace,
    PlannerTripStyleSelectionStatus,
    TripStylePlanningState,
    PlannerConfirmationStatus,
    PlannerAdvancedStep,
    PlannerAdvancedAnchor,
    PlannerFinalizedVia,
    PlannerActivityDaypart,
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
from app.schemas.trip_planning import ActivityDetail, TripConfiguration, TripModuleOutputs


@dataclass(frozen=True)
class _ActivityReviewSignals:
    nightlife_titles: tuple[str, ...] = ()
    neighbourhood_titles: tuple[str, ...] = ()
    outdoors_titles: tuple[str, ...] = ()
    far_anchor_titles: tuple[str, ...] = ()
    weighted_nightlife: float = 0.0
    weighted_neighbourhood: float = 0.0
    weighted_outdoors: float = 0.0
    transfer_count: int = 0
    unique_location_count: int = 0
    lead_event_title: str | None = None
    lead_event_location_label: str | None = None
    strong_candidate_ids: tuple[str, ...] = ()


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
    conversation.trip_style_planning = merge_trip_style_planning_state(
        current=current.trip_style_planning,
        configuration=next_configuration,
        llm_update=llm_update,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        board_action=board_action or {},
    )
    conversation.stay_planning = merge_stay_planning_state(
        current=current.stay_planning,
        configuration=next_configuration,
        module_outputs=module_outputs,
        llm_update=llm_update,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        board_action=board_action or {},
    )
    conversation.activity_planning = merge_activity_planning_state(
        current=current.activity_planning,
        configuration=next_configuration,
        module_outputs=module_outputs,
        llm_update=llm_update,
        planning_mode=planning_mode,
        advanced_step=advanced_step,
        advanced_anchor=advanced_anchor,
        board_action=board_action or {},
        stay_planning=conversation.stay_planning,
        trip_style_planning=conversation.trip_style_planning,
    )
    conversation.stay_planning = _apply_activity_review_to_stay_planning(
        current=conversation.stay_planning,
        activity_planning=conversation.activity_planning,
        configuration=next_configuration,
        module_outputs=module_outputs,
        llm_update=llm_update,
        board_action=board_action or {},
        planning_mode=planning_mode,
        advanced_anchor=advanced_anchor,
    )
    conversation.activity_planning = _finalize_activity_completion_state(
        current=conversation.activity_planning,
        stay_planning=conversation.stay_planning,
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


def _apply_activity_review_to_stay_planning(
    *,
    current: AdvancedStayPlanningState,
    activity_planning: AdvancedActivityPlanningState,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    llm_update: TripTurnUpdate,
    board_action: dict,
    planning_mode: PlannerPlanningMode | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
) -> AdvancedStayPlanningState:
    stay_planning = current.model_copy(deep=True)
    if planning_mode != "advanced" or advanced_anchor != "activities":
        return stay_planning
    if not stay_planning.selected_stay_option_id:
        return stay_planning

    selected_option = _find_requested_stay_option_for_review(
        stay_planning=stay_planning,
        llm_update=llm_update,
        board_action=board_action,
    )
    if selected_option is not None:
        _apply_stay_option_selection(
            stay_planning=stay_planning,
            configuration=configuration,
            module_outputs=module_outputs,
            selected_option=selected_option,
        )
        stay_planning.accepted_stay_review_signature = None
        stay_planning.accepted_stay_review_summary = None
        stay_planning.accepted_hotel_review_signature = None
        stay_planning.accepted_hotel_review_summary = None

    selected_hotel = _find_requested_hotel_for_review(
        stay_planning=stay_planning,
        configuration=configuration,
        module_outputs=module_outputs,
        llm_update=llm_update,
        board_action=board_action,
    )
    if selected_hotel is not None:
        _apply_hotel_selection(
            stay_planning=stay_planning,
            selected_hotel=selected_hotel,
        )
        stay_planning.accepted_hotel_review_signature = None
        stay_planning.accepted_hotel_review_summary = None

    signals = _derive_activity_review_signals(
        stay_planning=stay_planning,
        activity_planning=activity_planning,
    )
    stay_status, stay_notes = _evaluate_activity_driven_stay_compatibility(
        selected_option_id=stay_planning.selected_stay_option_id,
        selected_stay_direction=stay_planning.selected_stay_direction,
        signals=signals,
    )
    stay_review_signature = _build_activity_review_signature(
        scope="stay",
        stay_planning=stay_planning,
        signals=signals,
    )
    if _has_requested_review_resolution(
        llm_update=llm_update,
        board_action=board_action,
        scope="stay",
    ) and stay_status in {"strained", "conflicted"}:
        stay_planning.accepted_stay_review_signature = stay_review_signature
        stay_planning.accepted_stay_review_summary = stay_notes[0] if stay_notes else None
        stay_status = "fit"
        stay_notes = []
    elif (
        stay_status in {"strained", "conflicted"}
        and stay_planning.accepted_stay_review_signature == stay_review_signature
    ):
        stay_status = "fit"
        stay_notes = []

    stay_planning.compatibility_status = stay_status
    stay_planning.compatibility_notes = stay_notes
    stay_planning.selection_status = (
        "needs_review" if stay_status in {"strained", "conflicted"} else "selected"
    )
    review_segment_id = (
        stay_planning.active_segment_id
        or next(
            (
                option.segment_id
                for option in stay_planning.recommended_stay_options
                if option.segment_id
            ),
            None,
        )
        or "segment_primary"
    )
    if stay_status in {"strained", "conflicted"}:
        stay_planning.recommended_stay_options = _retune_stay_options_for_activity_review(
            configuration=configuration,
            current_options=stay_planning.recommended_stay_options,
            segment_id=review_segment_id,
            selected_stay_option_id=stay_planning.selected_stay_option_id,
            signals=signals,
        )

    if stay_planning.selected_hotel_card is None:
        if stay_status == "fit":
            stay_planning.hotel_compatibility_status = "fit"
            stay_planning.hotel_compatibility_notes = []
            if stay_planning.hotel_selection_status == "needs_review":
                stay_planning.hotel_selection_status = "selected"
        return stay_planning

    hotel_status, hotel_notes = _evaluate_activity_driven_hotel_compatibility(
        selected_option_id=stay_planning.selected_stay_option_id,
        selected_option_title=stay_planning.selected_stay_direction
        or "the current stay direction",
        selected_hotel=stay_planning.selected_hotel_card,
        stay_compatibility_status=stay_status,
        stay_compatibility_notes=stay_notes,
        signals=signals,
    )
    hotel_review_signature = _build_activity_review_signature(
        scope="hotel",
        stay_planning=stay_planning,
        signals=signals,
    )
    if _has_requested_review_resolution(
        llm_update=llm_update,
        board_action=board_action,
        scope="hotel",
    ) and hotel_status in {"strained", "conflicted"}:
        stay_planning.accepted_hotel_review_signature = hotel_review_signature
        stay_planning.accepted_hotel_review_summary = hotel_notes[0] if hotel_notes else None
        hotel_status = "fit"
        hotel_notes = []
    elif (
        hotel_status in {"strained", "conflicted"}
        and stay_planning.accepted_hotel_review_signature == hotel_review_signature
    ):
        hotel_status = "fit"
        hotel_notes = []

    stay_planning.hotel_compatibility_status = hotel_status
    stay_planning.hotel_compatibility_notes = hotel_notes
    stay_planning.hotel_selection_status = (
        "needs_review" if hotel_status in {"strained", "conflicted"} else "selected"
    )
    stay_planning.hotel_substep = (
        "hotel_review" if hotel_status in {"strained", "conflicted"} else "hotel_selected"
    )
    if hotel_status in {"strained", "conflicted"}:
        selected_option = next(
            (
                option
                for option in stay_planning.recommended_stay_options
                if option.id == stay_planning.selected_stay_option_id
            ),
            None,
        )
        if selected_option is not None:
            hotel_cards = (
                build_advanced_stay_hotel_options(
                    configuration=configuration,
                    selected_stay_option=selected_option,
                    hotels=module_outputs.hotels,
                )
                if module_outputs.hotels
                else stay_planning.recommended_hotels
            )
            (
                stay_planning.recommended_hotels,
                stay_planning.hotel_results_summary,
            ) = _retune_hotel_cards_for_activity_review(
                hotel_cards=hotel_cards,
                selected_hotel_id=stay_planning.selected_hotel_id,
                selected_option_id=selected_option.id,
                signals=signals,
            )
    return stay_planning


def _retune_stay_options_for_activity_review(
    *,
    configuration: TripConfiguration,
    current_options: list,
    segment_id: str,
    selected_stay_option_id: str | None,
    signals: _ActivityReviewSignals,
):
    options = build_advanced_stay_options(
        configuration=configuration,
        segment_id=segment_id,
    )
    if not options:
        return current_options

    recommended_option_id = _recommend_stay_option_from_activity_review(
        signals=signals,
        fallback_id=selected_stay_option_id,
    )
    evidence = _format_conflict_titles(
        signals.nightlife_titles
        or signals.far_anchor_titles
        or signals.neighbourhood_titles
        or signals.outdoors_titles
    )

    updated_options = []
    for option in options:
        update: dict = {
            "recommended": option.id == recommended_option_id,
            "badge": None,
        }
        if option.id == recommended_option_id and option.id != selected_stay_option_id:
            update["badge"] = "Better fit now"
        if option.id == recommended_option_id:
            if option.id == "stay_food_forward":
                update["summary"] = (
                    f"{option.summary.rstrip('.')} That now lines up better with {evidence} and the evening pull they create."
                )
                update["best_for"] = [
                    f"{evidence} pulling the trip toward stronger evenings",
                    *option.best_for[:2],
                ][:3]
            elif option.id in {"stay_connected_hub", "stay_split_strategy"}:
                update["summary"] = (
                    f"{option.summary.rstrip('.')} That now fits the spread of {evidence} more cleanly."
                )
                update["best_for"] = [
                    "Trips whose anchors now spread across multiple areas",
                    *option.best_for[:2],
                ][:3]
            elif option.id == "stay_central_base":
                update["best_for"] = [
                    f"Keeping {evidence} within a simpler day-to-day radius",
                    *option.best_for[:2],
                ][:3]
        updated_options.append(option.model_copy(update=update))

    return sorted(
        updated_options,
        key=lambda option: (
            option.id != recommended_option_id,
            option.id == selected_stay_option_id,
            option.title.lower(),
        ),
    )


def _recommend_stay_option_from_activity_review(
    *,
    signals: _ActivityReviewSignals,
    fallback_id: str | None,
) -> str:
    if signals.transfer_count >= 4 or (
        signals.unique_location_count >= 4 and signals.weighted_outdoors >= 2.0
    ):
        return "stay_split_strategy"
    if signals.weighted_nightlife >= 3.0 or signals.weighted_neighbourhood >= 3.0:
        return "stay_food_forward"
    if (
        signals.transfer_count >= 3
        or signals.weighted_outdoors >= 3.0
        or len(signals.far_anchor_titles) >= 1
    ):
        return "stay_connected_hub"
    if signals.weighted_neighbourhood >= 2.0:
        return "stay_central_base"
    return fallback_id or "stay_central_base"


def _retune_hotel_cards_for_activity_review(
    *,
    hotel_cards: list,
    selected_hotel_id: str | None,
    selected_option_id: str,
    signals: _ActivityReviewSignals,
) -> tuple[list, str | None]:
    if not hotel_cards:
        return [], None

    evidence = _format_conflict_titles(
        signals.nightlife_titles
        or signals.neighbourhood_titles
        or signals.far_anchor_titles
        or signals.outdoors_titles
    )
    rescored_cards = []
    for card in hotel_cards:
        hotel_text = " ".join(
            [
                card.hotel_name,
                card.area or "",
                card.summary,
                card.why_it_fits,
                *card.tradeoffs,
                *card.style_tags,
            ]
        ).lower()
        score = card.fit_score

        if signals.weighted_nightlife >= 3.0 or signals.weighted_neighbourhood >= 3.0:
            if any(token in hotel_text for token in ["food", "dining", "market", "gion", "evening", "culture", "walk"]):
                score += 18
            if any(token in hotel_text for token in ["station", "hub", "airport", "practical"]):
                score -= 18
        if (
            selected_option_id in {"stay_connected_hub", "stay_split_strategy"}
            or signals.transfer_count >= 3
            or signals.weighted_outdoors >= 3.0
            or signals.far_anchor_titles
        ):
            if any(token in hotel_text for token in ["station", "hub", "connected", "central", "transport", "practical"]):
                score += 16
            if any(token in hotel_text for token in ["quiet", "residential", "local"]):
                score -= 10

        score = max(0, min(score, 100))
        update: dict = {
            "fit_score": score,
            "recommended": False,
            "cta_label": "Use this hotel",
        }
        if card.id != selected_hotel_id and score > card.fit_score:
            update["why_it_fits"] = (
                f"{card.why_it_fits.rstrip('.')} It now matches {evidence} more naturally."
            )
            update["cta_label"] = "Switch to this hotel"
        rescored_cards.append(card.model_copy(update=update))

    sorted_cards = sorted(
        rescored_cards,
        key=lambda card: (
            -card.fit_score,
            card.nightly_rate_amount is None,
            card.nightly_rate_amount if card.nightly_rate_amount is not None else float("inf"),
            card.hotel_name.lower(),
        ),
    )
    recommended_card_id = next(
        (card.id for card in sorted_cards if card.id != selected_hotel_id),
        sorted_cards[0].id if sorted_cards else None,
    )
    visible_cards = [
        card.model_copy(update={"recommended": card.id == recommended_card_id})
        for card in sorted_cards
    ]
    summary = (
        f"These hotel options have been re-ranked around {evidence}, with {next((card.hotel_name for card in visible_cards if card.recommended), 'the strongest alternative')} now leading."
    )
    return visible_cards, summary


def _find_requested_stay_option_for_review(
    *,
    stay_planning: AdvancedStayPlanningState,
    llm_update: TripTurnUpdate,
    board_action: dict,
):
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "select_stay_option" and action.stay_option_id:
        return next(
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
    if not llm_update.requested_stay_option_title:
        return None
    requested_title = " ".join(
        llm_update.requested_stay_option_title.strip().lower().split()
    )
    matching_options = [
        option
        for option in stay_planning.recommended_stay_options
        if " ".join(option.title.strip().lower().split()) == requested_title
    ]
    if len(matching_options) != 1:
        return None
    return matching_options[0]


def _apply_stay_option_selection(
    *,
    stay_planning: AdvancedStayPlanningState,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    selected_option,
) -> None:
    strategy_changed = stay_planning.selected_stay_option_id != selected_option.id
    stay_planning.active_segment_id = selected_option.segment_id
    stay_planning.selected_stay_option_id = selected_option.id
    stay_planning.selected_stay_direction = selected_option.title
    stay_planning.selection_status = "selected"
    stay_planning.selection_rationale = selected_option.summary
    stay_planning.selection_assumptions = list(selected_option.best_for[:4])
    stay_planning.compatibility_status = "fit"
    stay_planning.compatibility_notes = []
    stay_planning.hotel_substep = "hotel_shortlist"
    stay_planning.hotel_filters.max_nightly_rate = None
    stay_planning.hotel_filters.area_filter = None
    stay_planning.hotel_filters.style_filter = None
    stay_planning.hotel_sort_order = "best_fit"
    stay_planning.hotel_page = 1

    if strategy_changed:
        stay_planning.selected_hotel_id = None
        stay_planning.selected_hotel_name = None
        stay_planning.hotel_selection_status = "none"
        stay_planning.hotel_selection_rationale = None
        stay_planning.hotel_selection_assumptions = []
        stay_planning.hotel_compatibility_status = "fit"
        stay_planning.hotel_compatibility_notes = []
        stay_planning.selected_hotel_card = None

    all_hotel_cards = build_advanced_stay_hotel_options(
        configuration=configuration,
        selected_stay_option=selected_option,
        hotels=module_outputs.hotels,
    )
    hotel_workspace = build_advanced_stay_hotel_workspace(
        configuration=configuration,
        selected_stay_option=selected_option,
        hotel_cards=all_hotel_cards,
        filters=stay_planning.hotel_filters,
        sort_order=stay_planning.hotel_sort_order,
        page=stay_planning.hotel_page,
        selected_hotel_id=stay_planning.selected_hotel_id,
    )
    stay_planning.recommended_hotels = hotel_workspace["hotel_cards"]
    stay_planning.hotel_results_status = hotel_workspace["hotel_results_status"]
    stay_planning.hotel_results_summary = hotel_workspace["hotel_results_summary"]
    stay_planning.hotel_page = hotel_workspace["hotel_page"]
    stay_planning.hotel_page_size = hotel_workspace["hotel_page_size"]
    stay_planning.hotel_total_results = hotel_workspace["hotel_total_results"]
    stay_planning.hotel_total_pages = hotel_workspace["hotel_total_pages"]
    stay_planning.available_hotel_areas = []
    stay_planning.available_hotel_styles = []
    stay_planning.selected_hotel_card = hotel_workspace["selected_hotel_card"]
    if (
        stay_planning.recommended_hotels
        or stay_planning.hotel_results_status in {"blocked", "empty"}
    ):
        stay_planning.hotel_substep = "hotel_shortlist"


def _find_requested_hotel_for_review(
    *,
    stay_planning: AdvancedStayPlanningState,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    llm_update: TripTurnUpdate,
    board_action: dict,
):
    selected_option = next(
        (
            option
            for option in stay_planning.recommended_stay_options
            if option.id == stay_planning.selected_stay_option_id
        ),
        None,
    )
    if selected_option is None:
        return None

    all_hotel_cards = (
        build_advanced_stay_hotel_options(
            configuration=configuration,
            selected_stay_option=selected_option,
            hotels=module_outputs.hotels,
        )
        if module_outputs.hotels
        else stay_planning.recommended_hotels
    )
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "select_stay_hotel" and action.stay_hotel_id:
        return next(
            (hotel for hotel in all_hotel_cards if hotel.id == action.stay_hotel_id),
            None,
        )
    if not llm_update.requested_stay_hotel_name:
        return None
    requested_hotel_name = _normalize_hotel_name(llm_update.requested_stay_hotel_name)
    matching_hotels = [
        hotel
        for hotel in all_hotel_cards
        if _normalize_hotel_name(hotel.hotel_name) == requested_hotel_name
    ]
    if len(matching_hotels) != 1:
        return None
    return matching_hotels[0]


def _apply_hotel_selection(
    *,
    stay_planning: AdvancedStayPlanningState,
    selected_hotel,
) -> None:
    selected_option = next(
        (
            option
            for option in stay_planning.recommended_stay_options
            if option.id == stay_planning.selected_stay_option_id
        ),
        None,
    )
    stay_planning.selected_hotel_id = selected_hotel.id
    stay_planning.selected_hotel_name = selected_hotel.hotel_name
    stay_planning.selected_hotel_card = selected_hotel
    stay_planning.hotel_selection_status = "selected"
    stay_planning.hotel_selection_rationale = selected_hotel.why_it_fits
    stay_planning.hotel_selection_assumptions = (
        list(selected_option.best_for[:3]) if selected_option else []
    )
    stay_planning.hotel_compatibility_status = "fit"
    stay_planning.hotel_compatibility_notes = []
    stay_planning.hotel_substep = "hotel_selected"


def _has_requested_review_resolution(
    *,
    llm_update: TripTurnUpdate,
    board_action: dict,
    scope: str,
) -> bool:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "keep_current_stay_choice" and scope == "stay":
        return True
    if action and action.type == "keep_current_hotel_choice" and scope == "hotel":
        return True
    return any(resolution.scope == scope for resolution in llm_update.requested_review_resolutions)


def _build_activity_review_signature(
    *,
    scope: str,
    stay_planning: AdvancedStayPlanningState,
    signals: _ActivityReviewSignals,
) -> str:
    strong_ids = ",".join(signals.strong_candidate_ids[:6]) or "none"
    nightlife = int(signals.weighted_nightlife * 10)
    neighbourhood = int(signals.weighted_neighbourhood * 10)
    outdoors = int(signals.weighted_outdoors * 10)
    return "|".join(
        [
            scope,
            stay_planning.selected_stay_option_id or "none",
            stay_planning.selected_hotel_id or "none" if scope == "hotel" else "no-hotel",
            strong_ids,
            f"night:{nightlife}",
            f"neighbourhood:{neighbourhood}",
            f"outdoors:{outdoors}",
            f"transfer:{signals.transfer_count}",
            f"locations:{signals.unique_location_count}",
            signals.lead_event_title or "no-lead-event",
        ]
    )


def _derive_activity_review_signals(
    *,
    stay_planning: AdvancedStayPlanningState,
    activity_planning: AdvancedActivityPlanningState,
) -> _ActivityReviewSignals:
    scheduled_candidate_ids = {
        block.candidate_id
        for block in activity_planning.timeline_blocks
        if block.candidate_id and block.type in {"activity", "event"}
    }
    reserve_ids = set(activity_planning.unscheduled_candidate_ids)
    strong_candidates: list[tuple[AdvancedActivityCandidateCard, float]] = []
    nightlife_titles: list[str] = []
    neighbourhood_titles: list[str] = []
    outdoors_titles: list[str] = []
    weighted_nightlife = 0.0
    weighted_neighbourhood = 0.0
    weighted_outdoors = 0.0
    location_keys: list[str] = []

    stay_tokens = _extract_location_tokens(
        " ".join(
            part
            for part in [
                stay_planning.selected_stay_direction or "",
                stay_planning.selected_hotel_name or "",
                stay_planning.selected_hotel_card.area if stay_planning.selected_hotel_card else "",
            ]
            if part
        )
    )

    for candidate in activity_planning.visible_candidates:
        weight = 0.0
        if candidate.id in scheduled_candidate_ids:
            weight += 2.0
        if candidate.disposition == "essential":
            weight += 1.5
        if candidate.kind == "event" and candidate.id in reserve_ids:
            weight += 1.0
        if candidate.kind == "event" and candidate.start_at:
            weight += 1.0
        if weight < 1.0:
            continue

        strong_candidates.append((candidate, weight))
        text = _candidate_review_text(candidate)
        if _candidate_has_nightlife_signal(candidate=candidate, text=text):
            weighted_nightlife += weight
            nightlife_titles.append(candidate.title)
        if _candidate_has_neighbourhood_signal(candidate=candidate, text=text):
            weighted_neighbourhood += weight
            neighbourhood_titles.append(candidate.title)
        if _candidate_has_outdoors_signal(text=text):
            weighted_outdoors += weight
            outdoors_titles.append(candidate.title)
        location_key = _primary_location_key(candidate.location_label)
        if location_key:
            location_keys.append(location_key)

    lead_event = next(
        (
            candidate
            for candidate, _ in strong_candidates
            if candidate.kind == "event" and candidate.start_at is not None
        ),
        None,
    )
    far_anchor_titles: list[str] = []
    if lead_event and stay_tokens:
        lead_location_tokens = _extract_location_tokens(
            " ".join(
                part
                for part in [
                    lead_event.location_label or "",
                    lead_event.venue_name or "",
                ]
                if part
            )
        )
        if lead_location_tokens and stay_tokens.isdisjoint(lead_location_tokens):
            far_anchor_titles.append(lead_event.title)

    transfer_count = sum(
        1 for block in activity_planning.timeline_blocks if block.type == "transfer"
    )
    return _ActivityReviewSignals(
        nightlife_titles=tuple(dict.fromkeys(nightlife_titles)),
        neighbourhood_titles=tuple(dict.fromkeys(neighbourhood_titles)),
        outdoors_titles=tuple(dict.fromkeys(outdoors_titles)),
        far_anchor_titles=tuple(dict.fromkeys(far_anchor_titles)),
        weighted_nightlife=weighted_nightlife,
        weighted_neighbourhood=weighted_neighbourhood,
        weighted_outdoors=weighted_outdoors,
        transfer_count=transfer_count,
        unique_location_count=len(set(location_keys)),
        lead_event_title=lead_event.title if lead_event else None,
        lead_event_location_label=lead_event.location_label if lead_event else None,
        strong_candidate_ids=tuple(candidate.id for candidate, _ in strong_candidates),
    )


def _evaluate_activity_driven_stay_compatibility(
    *,
    selected_option_id: str,
    selected_stay_direction: str | None,
    signals: _ActivityReviewSignals,
) -> tuple[str, list[str]]:
    severe_notes: list[str] = []
    moderate_notes: list[str] = []
    evidence = _format_conflict_titles(
        signals.nightlife_titles
        or signals.far_anchor_titles
        or signals.neighbourhood_titles
        or signals.outdoors_titles
    )
    stay_label = (selected_stay_direction or "this base").lower()

    if selected_option_id == "stay_quiet_local":
        if signals.weighted_nightlife >= 3.0:
            severe_notes.append(
                f"{evidence} now pull too heavily toward later nights for {stay_label} to stay effortless."
            )
        if signals.transfer_count >= 2 or signals.unique_location_count >= 3:
            moderate_notes.append(
                f"{_format_conflict_titles(signals.far_anchor_titles or signals.neighbourhood_titles or signals.outdoors_titles)} now spread the trip too widely for {stay_label} to feel easy day to day."
            )
    elif selected_option_id == "stay_food_forward":
        if signals.weighted_outdoors >= 3.0 or signals.transfer_count >= 3:
            moderate_notes.append(
                f"{_format_conflict_titles(signals.outdoors_titles or signals.far_anchor_titles)} now pull the trip farther from a dining-led neighbourhood rhythm than {stay_label} was chosen for."
            )
    elif selected_option_id == "stay_central_base":
        if signals.far_anchor_titles and signals.transfer_count >= 2:
            moderate_notes.append(
                f"{_format_conflict_titles(signals.far_anchor_titles)} are now acting like the real centre of gravity, which weakens {stay_label} as the cleanest base."
            )
    elif selected_option_id == "stay_connected_hub":
        if signals.weighted_neighbourhood >= 3.0 and signals.weighted_nightlife >= 2.0:
            moderate_notes.append(
                f"{_format_conflict_titles(signals.neighbourhood_titles or signals.nightlife_titles)} now make the trip feel more neighbourhood-led than {stay_label} naturally supports."
            )
    elif selected_option_id == "stay_split_strategy":
        if signals.transfer_count <= 1 and signals.unique_location_count <= 2:
            moderate_notes.append(
                "the current activities plan no longer looks varied enough to justify splitting the stay."
            )

    if severe_notes:
        return "conflicted", severe_notes[:4]
    if moderate_notes:
        return "strained", moderate_notes[:4]
    return "fit", []


def _evaluate_activity_driven_hotel_compatibility(
    *,
    selected_option_id: str,
    selected_option_title: str,
    selected_hotel,
    stay_compatibility_status: str,
    stay_compatibility_notes: list[str],
    signals: _ActivityReviewSignals,
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
                stay_compatibility_notes[0]
                if stay_compatibility_notes
                else "this hotel sits inside a stay direction that no longer fits the broader trip as cleanly"
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

    if any(token in hotel_text for token in ["station", "airport", "hub"]) and (
        signals.weighted_neighbourhood >= 3.0 or signals.weighted_nightlife >= 3.0
    ):
        return (
            "strained",
            [
                f"{selected_hotel.hotel_name} now feels too practical for {_format_conflict_titles(signals.neighbourhood_titles or signals.nightlife_titles)} and the more neighbourhood-led evening structure they create."
            ],
        )
    if any(token in hotel_text for token in ["quiet", "residential", "local"]) and signals.weighted_nightlife >= 3.0:
        return (
            "conflicted",
            [
                f"{selected_hotel.hotel_name} is now too calm for {_format_conflict_titles(signals.nightlife_titles)}, which are pulling the trip toward later nights."
            ],
        )
    if signals.far_anchor_titles and any(
        token in hotel_text for token in ["station", "central", "hub", "practical"]
    ):
        return (
            "strained",
            [
                f"{_format_conflict_titles(signals.far_anchor_titles)} are now acting like the trip's real anchor, which weakens {selected_hotel.hotel_name} as the most natural hotel base inside {selected_option_title.lower()}."
            ],
        )
    if signals.transfer_count >= 3 and selected_option_id in {"stay_quiet_local", "stay_food_forward"}:
        return (
            "strained",
            [
                f"{selected_hotel.hotel_name} now adds too much movement friction for how widely the activities plan is spreading across the trip."
            ],
        )

    return "fit", []


def _candidate_review_text(candidate: AdvancedActivityCandidateCard) -> str:
    return " ".join(
        part.lower()
        for part in [
            candidate.title,
            candidate.summary or "",
            candidate.location_label or "",
            candidate.venue_name or "",
        ]
        if part
    )


def _candidate_has_nightlife_signal(
    *,
    candidate: AdvancedActivityCandidateCard,
    text: str,
) -> bool:
    nightlife_tokens = [
        "nightlife",
        "late night",
        "late-night",
        "bars",
        "bar",
        "cocktail",
        "cocktails",
        "club",
        "party",
        "jazz",
        "concert",
        "music",
        "dj",
        "after dark",
        "after-dark",
        "izakaya",
    ]
    if any(token in text for token in nightlife_tokens):
        return True
    return bool(candidate.start_at and candidate.start_at.hour >= 19)


def _candidate_has_neighbourhood_signal(
    *,
    candidate: AdvancedActivityCandidateCard,
    text: str,
) -> bool:
    neighbourhood_tokens = [
        "food",
        "market",
        "dining",
        "restaurant",
        "cafe",
        "cafes",
        "tasting",
        "izakaya",
        "alley",
        "walk",
        "cocktail",
    ]
    if any(token in text for token in neighbourhood_tokens):
        return True
    return bool(candidate.time_label and candidate.time_label.lower() == "evening")


def _candidate_has_outdoors_signal(text: str) -> bool:
    return any(
        token in text
        for token in [
            "day trip",
            "day-trip",
            "hike",
            "hiking",
            "beach",
            "coast",
            "nature",
            "mountain",
            "trail",
            "excursion",
            "outdoors",
        ]
    )


def _primary_location_key(location_label: str | None) -> str | None:
    if not location_label or not isinstance(location_label, str):
        return None
    primary = location_label.split(",")[0].strip().lower()
    return primary or None


def _extract_location_tokens(text: str) -> set[str]:
    return {
        token
        for token in text.lower().replace(",", " ").replace("-", " ").split()
        if len(token) > 3
    }


def _format_conflict_titles(titles: tuple[str, ...]) -> str:
    if not titles:
        return "the latest activity anchors"
    if len(titles) == 1:
        return titles[0]
    return f"{titles[0]} and {titles[1]}"


def _append_schedule_note(notes: list[str], note: str | None) -> None:
    if not note:
        return
    cleaned = note.strip()
    if not cleaned or cleaned in notes:
        return
    notes.append(cleaned)


def _is_fixed_time_candidate(candidate: AdvancedActivityCandidateCard) -> bool:
    return candidate.kind == "event" and candidate.start_at is not None


def _default_candidate_daypart(candidate: AdvancedActivityCandidateCard) -> PlannerActivityDaypart:
    return _resolve_activity_slot_key(
        candidate.time_label,
        candidate.start_at.hour if candidate.start_at else None,
    )


def _is_activity_schedule_board_action(action: ConversationBoardAction | None) -> bool:
    if action is None:
        return False
    return action.type in {
        "move_activity_candidate_to_day",
        "move_activity_candidate_earlier",
        "move_activity_candidate_later",
        "pin_activity_candidate_daypart",
        "send_activity_candidate_to_reserve",
        "restore_activity_candidate_from_reserve",
    }


def _prune_activity_placement_preferences(
    *,
    preferences: list[AdvancedActivityPlacementPreference],
    candidates: list[AdvancedActivityCandidateCard],
) -> list[AdvancedActivityPlacementPreference]:
    valid_candidate_ids = {
        candidate.id
        for candidate in candidates
        if candidate.disposition != "pass"
    }
    return [
        preference
        for preference in preferences
        if preference.candidate_id in valid_candidate_ids
    ]


def _find_schedule_edit_candidate(
    *,
    candidates: list[AdvancedActivityCandidateCard],
    edit: RequestedActivityScheduleEdit,
) -> AdvancedActivityCandidateCard | None:
    if edit.candidate_id:
        return next(
            (candidate for candidate in candidates if candidate.id == edit.candidate_id),
            None,
        )

    matching_candidates = [
        candidate
        for candidate in candidates
        if candidate.title.strip().lower() == edit.candidate_title.strip().lower()
        and (edit.candidate_kind is None or candidate.kind == edit.candidate_kind)
    ]
    if len(matching_candidates) != 1:
        return None
    return matching_candidates[0]


def _apply_schedule_edit_to_preferences(
    *,
    preferences_by_id: dict[str, AdvancedActivityPlacementPreference],
    candidate: AdvancedActivityCandidateCard,
    action: str,
    target_day_index: int | None,
    target_daypart: PlannerActivityDaypart | None,
    current_blocks_by_candidate_id: dict[str, AdvancedActivityTimelineBlock],
    schedule_notes: list[str],
) -> None:
    preference = preferences_by_id.get(candidate.id)
    if preference is None:
        preference = AdvancedActivityPlacementPreference(candidate_id=candidate.id)
    current_block = current_blocks_by_candidate_id.get(candidate.id)

    if action in {"move_to_day", "pin_daypart", "move_earlier", "move_later"} and _is_fixed_time_candidate(candidate):
        _append_schedule_note(
            schedule_notes,
            f"{candidate.title} keeps its fixed event time, so I left that slot locked and adjusted the rest around it instead.",
        )
        if action not in {"reserve", "restore"}:
            preferences_by_id[candidate.id] = preference
            return

    if action == "move_to_day":
        if target_day_index is None:
            return
        preference.day_index = target_day_index
        preference.daypart = (
            preference.daypart
            or current_block.daypart
            or _default_candidate_daypart(candidate)
        )
        preference.reserved = False
    elif action == "pin_daypart":
        if target_daypart is None:
            return
        preference.daypart = target_daypart
        preference.day_index = preference.day_index or (
            current_block.day_index if current_block else None
        )
        preference.reserved = False
    elif action in {"move_earlier", "move_later"}:
        sequence: tuple[PlannerActivityDaypart, ...] = (
            "morning",
            "afternoon",
            "evening",
        )
        baseline_daypart = (
            preference.daypart
            or current_block.daypart
            or _default_candidate_daypart(candidate)
        )
        baseline_index = sequence.index(baseline_daypart)
        offset = -1 if action == "move_earlier" else 1
        next_index = baseline_index + offset
        if next_index < 0 or next_index >= len(sequence):
            _append_schedule_note(
                schedule_notes,
                f"{candidate.title} is already as {'early' if action == 'move_earlier' else 'late'} in the day as this draft can place it.",
            )
            preferences_by_id[candidate.id] = preference
            return
        preference.daypart = sequence[next_index]
        preference.day_index = preference.day_index or (
            current_block.day_index if current_block else None
        )
        preference.reserved = False
    elif action == "reserve":
        preference.reserved = True
    elif action == "restore":
        preference.reserved = False
    else:
        return

    preferences_by_id[candidate.id] = preference


def _merge_activity_placement_preferences(
    *,
    current_preferences: list[AdvancedActivityPlacementPreference],
    candidates: list[AdvancedActivityCandidateCard],
    current_timeline_blocks: list[AdvancedActivityTimelineBlock],
    board_action: dict,
    requested_schedule_edits: list[RequestedActivityScheduleEdit],
) -> tuple[list[AdvancedActivityPlacementPreference], list[str]]:
    preferences_by_id = {
        preference.candidate_id: preference.model_copy(deep=True)
        for preference in _prune_activity_placement_preferences(
            preferences=current_preferences,
            candidates=candidates,
        )
    }
    current_blocks_by_candidate_id = {
        block.candidate_id: block
        for block in current_timeline_blocks
        if block.candidate_id and block.type in {"activity", "event"}
    }
    schedule_notes: list[str] = []
    action = ConversationBoardAction.model_validate(board_action) if board_action else None

    if _is_activity_schedule_board_action(action):
        candidate = next(
            (
                item
                for item in candidates
                if item.id == action.activity_candidate_id
            ),
            None,
        )
        if candidate is not None:
            board_action_map = {
                "move_activity_candidate_to_day": "move_to_day",
                "move_activity_candidate_earlier": "move_earlier",
                "move_activity_candidate_later": "move_later",
                "pin_activity_candidate_daypart": "pin_daypart",
                "send_activity_candidate_to_reserve": "reserve",
                "restore_activity_candidate_from_reserve": "restore",
            }
            mapped_action = board_action_map.get(action.type)
            if mapped_action is not None:
                _apply_schedule_edit_to_preferences(
                    preferences_by_id=preferences_by_id,
                    candidate=candidate,
                    action=mapped_action,
                    target_day_index=action.activity_target_day_index,
                    target_daypart=action.activity_target_daypart,
                    current_blocks_by_candidate_id=current_blocks_by_candidate_id,
                    schedule_notes=schedule_notes,
                )

    for edit in requested_schedule_edits:
        candidate = _find_schedule_edit_candidate(candidates=candidates, edit=edit)
        if candidate is None:
            continue
        _apply_schedule_edit_to_preferences(
            preferences_by_id=preferences_by_id,
            candidate=candidate,
            action=edit.action,
            target_day_index=edit.target_day_index,
            target_daypart=edit.target_daypart,
            current_blocks_by_candidate_id=current_blocks_by_candidate_id,
            schedule_notes=schedule_notes,
        )

    return list(preferences_by_id.values()), schedule_notes


def merge_activity_planning_state(
    *,
    current: AdvancedActivityPlanningState,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    llm_update: TripTurnUpdate,
    planning_mode: PlannerPlanningMode | None,
    advanced_step: PlannerAdvancedStep | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
    board_action: dict,
    stay_planning: AdvancedStayPlanningState,
    trip_style_planning: TripStylePlanningState,
) -> AdvancedActivityPlanningState:
    activity_planning = current.model_copy(deep=True)
    action = ConversationBoardAction.model_validate(board_action) if board_action else None

    if planning_mode != "advanced":
        return activity_planning

    is_active_workspace = (
        advanced_step == "anchor_flow" and advanced_anchor == "activities"
    )
    is_seeded = bool(
        activity_planning.recommended_candidates
        or activity_planning.timeline_blocks
        or activity_planning.visible_candidates
    )
    if not is_active_workspace and not is_seeded:
        return activity_planning

    previous_candidates = {
        candidate.id: candidate for candidate in activity_planning.recommended_candidates
    }
    candidates = _build_ranked_activity_candidates(
        configuration=configuration,
        module_outputs=module_outputs,
        previous_candidates=previous_candidates,
        stay_planning=stay_planning,
        trip_style_planning=trip_style_planning,
    )
    if is_active_workspace:
        candidates = _apply_activity_board_action(
            candidates=candidates,
            board_action=board_action,
        )
        candidates = _apply_requested_activity_decisions(
            candidates=candidates,
            decisions=llm_update.requested_activity_decisions,
        )
        (
            placement_preferences,
            preference_notes,
        ) = _merge_activity_placement_preferences(
            current_preferences=activity_planning.placement_preferences,
            candidates=candidates,
            current_timeline_blocks=activity_planning.timeline_blocks,
            board_action=board_action,
            requested_schedule_edits=llm_update.requested_activity_schedule_edits,
        )
        activity_planning.placement_preferences = placement_preferences
    else:
        activity_planning.placement_preferences = _prune_activity_placement_preferences(
            preferences=activity_planning.placement_preferences,
            candidates=candidates,
        )
        preference_notes = []

    essential_ids = [candidate.id for candidate in candidates if candidate.disposition == "essential"]
    maybe_ids = [candidate.id for candidate in candidates if candidate.disposition == "maybe"]
    passed_ids = [candidate.id for candidate in candidates if candidate.disposition == "pass"]
    visible_candidates = [
        candidate for candidate in candidates if candidate.disposition != "pass"
    ]
    selected_event_ids = [
        candidate.id
        for candidate in candidates
        if candidate.kind == "event" and candidate.disposition == "essential"
    ]
    (
        day_plans,
        timeline_blocks,
        reserved_candidate_ids,
        unscheduled_candidate_ids,
        schedule_summary,
        schedule_notes,
        schedule_status,
    ) = _build_activity_schedule(
        candidates=visible_candidates,
        configuration=configuration,
        stay_planning=stay_planning,
        trip_style_planning=trip_style_planning,
        placement_preferences=activity_planning.placement_preferences,
    )
    schedule_notes = [*preference_notes, *schedule_notes][:4]
    if trip_style_planning.selection_status == "completed" and (
        (action and action.type in {
            "select_trip_style_direction_primary",
            "select_trip_style_direction_accent",
            "clear_trip_style_direction_accent",
            "confirm_trip_style_direction",
            "keep_current_trip_style_direction",
            "select_trip_style_pace",
            "confirm_trip_style_pace",
            "keep_current_trip_style_pace",
        })
        or llm_update.requested_trip_style_direction_updates
        or llm_update.requested_trip_style_pace_updates
    ):
        direction_note = _build_trip_style_activity_note(
            trip_style_planning=trip_style_planning
        )
        if direction_note:
            schedule_notes = [direction_note, *schedule_notes][:4]
    pace_note = _build_trip_style_pace_activity_note(
        trip_style_planning=trip_style_planning,
        unscheduled_candidate_ids=unscheduled_candidate_ids,
    )
    if pace_note:
        schedule_notes = [pace_note, *schedule_notes][:4]

    activity_planning.recommended_candidates = candidates
    activity_planning.visible_candidates = visible_candidates
    activity_planning.essential_ids = essential_ids
    activity_planning.maybe_ids = maybe_ids
    activity_planning.passed_ids = passed_ids
    activity_planning.selected_event_ids = selected_event_ids
    activity_planning.reserved_candidate_ids = reserved_candidate_ids
    activity_planning.workspace_summary = _build_activity_workspace_summary(
        visible_candidates=visible_candidates,
        essential_ids=essential_ids,
        passed_ids=passed_ids,
        reserved_candidate_ids=reserved_candidate_ids,
        overflow_candidate_ids=[
            candidate_id
            for candidate_id in unscheduled_candidate_ids
            if candidate_id not in reserved_candidate_ids
        ],
    )
    activity_planning.day_plans = day_plans
    activity_planning.timeline_blocks = timeline_blocks
    activity_planning.unscheduled_candidate_ids = unscheduled_candidate_ids
    activity_planning.schedule_summary = schedule_summary
    activity_planning.schedule_notes = schedule_notes
    activity_planning.schedule_status = schedule_status
    activity_planning.workspace_touched = bool(
        activity_planning.workspace_touched
        or activity_planning.essential_ids
        or activity_planning.passed_ids
        or activity_planning.selected_event_ids
        or activity_planning.completion_anchor_ids
        or (action is not None and action.type != "select_advanced_anchor")
        or llm_update.requested_activity_decisions
        or llm_update.requested_activity_schedule_edits
        or llm_update.requested_trip_style_direction_updates
        or llm_update.requested_trip_style_pace_updates
        or llm_update.requested_stay_option_title
        or llm_update.requested_review_resolutions
    )
    return activity_planning


def _finalize_activity_completion_state(
    *,
    current: AdvancedActivityPlanningState,
    stay_planning: AdvancedStayPlanningState,
) -> AdvancedActivityPlanningState:
    activity_planning = current.model_copy(deep=True)

    unresolved_review = (
        stay_planning.selection_status == "needs_review"
        or stay_planning.compatibility_status in {"strained", "conflicted"}
        or stay_planning.hotel_selection_status == "needs_review"
        or stay_planning.hotel_compatibility_status in {"strained", "conflicted"}
    )
    scheduled_blocks = [
        block
        for block in activity_planning.timeline_blocks
        if block.type in {"activity", "event"} and block.candidate_id
    ]
    fixed_time_events = [
        block
        for block in scheduled_blocks
        if block.type == "event" and block.fixed_time
    ]
    essential_candidates = [
        candidate
        for candidate in activity_planning.visible_candidates
        if candidate.disposition == "essential"
    ]
    scheduled_candidate_ids = list(
        dict.fromkeys(
            block.candidate_id
            for block in scheduled_blocks
            if block.candidate_id
        )
    )
    has_real_anchor = bool(
        fixed_time_events
        or len(essential_candidates) >= 2
        or (
            len(essential_candidates) >= 1
            and len(scheduled_candidate_ids) >= 5
            and len(activity_planning.day_plans) <= 2
        )
    )
    is_completed = (
        activity_planning.schedule_status == "ready"
        and has_real_anchor
        and activity_planning.workspace_touched
        and not unresolved_review
    )

    if not is_completed:
        activity_planning.completion_status = "in_progress"
        activity_planning.completion_summary = None
        activity_planning.completion_anchor_ids = []
        return activity_planning

    completion_anchor_ids = list(
        dict.fromkeys(
            [
                *[
                    block.candidate_id
                    for block in fixed_time_events
                    if block.candidate_id
                ],
                *[candidate.id for candidate in essential_candidates],
                *scheduled_candidate_ids,
            ]
        )
    )[:4]

    if fixed_time_events:
        lead_event = fixed_time_events[0]
        completion_summary = (
            f"{lead_event.title} is now giving the trip a clear timed centerpiece, so we have enough shape to move on."
        )
    elif essential_candidates:
        anchor_titles = ", ".join(candidate.title for candidate in essential_candidates[:2])
        completion_summary = (
            f"{anchor_titles} {'are now giving' if len(essential_candidates) > 1 else 'is now giving'} the trip a clear center, and the draft days are strong enough to move on."
        )
    else:
        completion_summary = (
            f"The draft days now have enough shape across {len(scheduled_candidate_ids)} planned stops to move on."
        )

    activity_planning.completion_status = "completed"
    activity_planning.completion_summary = completion_summary
    activity_planning.completion_anchor_ids = completion_anchor_ids
    return activity_planning


def _build_ranked_activity_candidates(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    previous_candidates: dict[str, AdvancedActivityCandidateCard],
    stay_planning: AdvancedStayPlanningState,
    trip_style_planning: TripStylePlanningState,
) -> list[AdvancedActivityCandidateCard]:
    scored_candidates: list[tuple[float, AdvancedActivityCandidateCard]] = []

    for activity in module_outputs.activities:
        candidate = _build_activity_candidate_card(
            activity=activity,
            configuration=configuration,
            trip_style_planning=trip_style_planning,
            previous_candidate=previous_candidates.get(activity.id),
        )
        score = _score_activity_candidate(
            candidate=candidate,
            configuration=configuration,
            stay_planning=stay_planning,
            trip_style_planning=trip_style_planning,
        )
        scored_candidates.append((score, candidate))

    for event_payload in enrich_events_from_ticketmaster(configuration):
        event_id = event_payload.get("id")
        if not isinstance(event_id, str):
            continue
        candidate = _build_event_candidate_card(
            payload=event_payload,
            configuration=configuration,
            trip_style_planning=trip_style_planning,
            previous_candidate=previous_candidates.get(event_id),
        )
        score = _score_activity_candidate(
            candidate=candidate,
            configuration=configuration,
            stay_planning=stay_planning,
            trip_style_planning=trip_style_planning,
        )
        scored_candidates.append((score, candidate))

    ranked = [
        candidate
        for _, candidate in sorted(
            scored_candidates,
            key=lambda item: (
                item[0],
                item[1].kind == "event",
                item[1].title.lower(),
            ),
            reverse=True,
        )
    ]
    top_ids = {candidate.id for candidate in ranked[:4]}
    for candidate in ranked:
        candidate.recommended = candidate.id in top_ids and candidate.disposition != "pass"
    return ranked[:12]


def _build_activity_candidate_card(
    *,
    activity: ActivityDetail,
    configuration: TripConfiguration,
    trip_style_planning: TripStylePlanningState,
    previous_candidate: AdvancedActivityCandidateCard | None,
) -> AdvancedActivityCandidateCard:
    location_label = None
    notes = [note.strip() for note in activity.notes if isinstance(note, str) and note.strip()]
    if notes:
        location_label = notes[0]
    ranking_reasons = _build_activity_ranking_reasons(
        kind="activity",
        configuration=configuration,
        trip_style_planning=trip_style_planning,
        title=activity.title,
        category=activity.category,
        start_at=activity.start_at,
        location_label=activity.location_label,
    )
    return AdvancedActivityCandidateCard(
        id=activity.id,
        kind="activity",
        title=activity.title,
        latitude=activity.latitude,
        longitude=activity.longitude,
        venue_name=activity.venue_name,
        location_label=activity.location_label or location_label,
        summary=_build_activity_candidate_summary(
            title=activity.title,
            category=activity.category,
            time_label=activity.time_label,
            venue_name=activity.venue_name,
        ),
        source_label=activity.source_label or "Geoapify",
        source_url=activity.source_url,
        image_url=activity.image_url,
        availability_text=activity.availability_text,
        price_text=activity.price_text,
        status_text=activity.status_text,
        estimated_duration_minutes=activity.estimated_duration_minutes,
        time_label=activity.time_label,
        start_at=activity.start_at,
        end_at=activity.end_at,
        recommended=False,
        disposition=previous_candidate.disposition if previous_candidate else "maybe",
        ranking_reasons=ranking_reasons,
    )


def _build_event_candidate_card(
    *,
    payload: dict[str, object],
    configuration: TripConfiguration,
    trip_style_planning: TripStylePlanningState,
    previous_candidate: AdvancedActivityCandidateCard | None,
) -> AdvancedActivityCandidateCard:
    title = payload.get("title")
    if not isinstance(title, str):
        title = "Live event"
    ranking_reasons = _build_activity_ranking_reasons(
        kind="event",
        configuration=configuration,
        trip_style_planning=trip_style_planning,
        title=title,
        category=None,
        start_at=payload.get("start_at"),
        location_label=payload.get("location_label")
        if isinstance(payload.get("location_label"), str)
        else None,
    )
    return AdvancedActivityCandidateCard(
        id=str(payload.get("id") or f"event_{uuid4().hex[:8]}"),
        kind="event",
        title=title,
        latitude=payload.get("latitude") if isinstance(payload.get("latitude"), (int, float)) else None,
        longitude=payload.get("longitude") if isinstance(payload.get("longitude"), (int, float)) else None,
        venue_name=payload.get("venue_name")
        if isinstance(payload.get("venue_name"), str)
        else None,
        location_label=payload.get("location_label")
        if isinstance(payload.get("location_label"), str)
        else None,
        summary=payload.get("summary") if isinstance(payload.get("summary"), str) else None,
        source_label=payload.get("source_label")
        if isinstance(payload.get("source_label"), str)
        else "Ticketmaster",
        source_url=payload.get("source_url")
        if isinstance(payload.get("source_url"), str)
        else None,
        image_url=payload.get("image_url")
        if isinstance(payload.get("image_url"), str)
        else None,
        availability_text=payload.get("availability_text")
        if isinstance(payload.get("availability_text"), str)
        else None,
        price_text=payload.get("price_text")
        if isinstance(payload.get("price_text"), str)
        else None,
        status_text=payload.get("status_text")
        if isinstance(payload.get("status_text"), str)
        else None,
        estimated_duration_minutes=payload.get("estimated_duration_minutes")
        if isinstance(payload.get("estimated_duration_minutes"), int)
        else None,
        time_label=None,
        start_at=payload.get("start_at") if isinstance(payload.get("start_at"), datetime) else None,
        end_at=payload.get("end_at") if isinstance(payload.get("end_at"), datetime) else None,
        recommended=False,
        disposition=previous_candidate.disposition if previous_candidate else "maybe",
        ranking_reasons=ranking_reasons,
    )


def _score_activity_candidate(
    *,
    candidate: AdvancedActivityCandidateCard,
    configuration: TripConfiguration,
    stay_planning: AdvancedStayPlanningState,
    trip_style_planning: TripStylePlanningState,
) -> float:
    score = 0.0
    text = " ".join(
        part.lower()
        for part in [
            candidate.title,
            candidate.summary or "",
            candidate.location_label or "",
        ]
        if part
    )

    for style in configuration.activity_styles:
        if style in text:
            score += 2.0

    if (
        trip_style_planning.selection_status in {"selected", "completed"}
        and trip_style_planning.selected_primary_direction
    ):
        score += _score_candidate_against_trip_direction(
            candidate=candidate,
            text=text,
            primary=trip_style_planning.selected_primary_direction,
            accent=trip_style_planning.selected_accent,
        )

    custom_style = (configuration.custom_style or "").strip().lower()
    if custom_style:
        custom_tokens = [token for token in custom_style.split() if len(token) > 3]
        if any(token in text for token in custom_tokens):
            score += 2.5

    if configuration.weather_preference:
        weather_text = configuration.weather_preference.lower()
        if any(token in weather_text for token in ["sun", "warm", "dry", "mild"]):
            if any(token in text for token in ["outdoor", "park", "garden", "market", "festival"]):
                score += 1.0
        if any(token in weather_text for token in ["cool", "rain", "indoor"]):
            if any(token in text for token in ["museum", "gallery", "theatre", "indoor"]):
                score += 1.0

    if candidate.kind == "event":
        score += 3.0
        score += _score_event_candidate_signals(candidate=candidate, configuration=configuration)
    if candidate.recommended:
        score += 0.5

    if configuration.to_location and candidate.location_label:
        if configuration.to_location.lower() in candidate.location_label.lower():
            score += 0.75

    score += _score_candidate_against_stay_context(
        candidate=candidate,
        stay_planning=stay_planning,
    )

    return score


def _score_event_candidate_signals(
    *,
    candidate: AdvancedActivityCandidateCard,
    configuration: TripConfiguration,
) -> float:
    if candidate.kind != "event":
        return 0.0

    score = 0.0
    if candidate.start_at:
        score += 1.5
    if configuration.start_date and configuration.end_date and candidate.start_at:
        if configuration.start_date <= candidate.start_at.date() <= configuration.end_date:
            score += 3.0
        else:
            score -= 3.5
    elif configuration.travel_window and candidate.start_at:
        score += 1.0

    event_text = " ".join(
        part.lower()
        for part in [
            candidate.title,
            candidate.summary or "",
            candidate.venue_name or "",
            candidate.location_label or "",
            candidate.status_text or "",
        ]
        if part
    )
    if any(token in event_text for token in ["festival", "concert", "jazz", "match", "show", "market", "theatre"]):
        score += 1.25
    if candidate.price_text:
        score += 0.5
    if candidate.availability_text:
        score += 0.5
    if candidate.status_text and any(
        token in candidate.status_text.lower() for token in ["cancel", "postpon", "resched"]
    ):
        score -= 2.5
    if not candidate.summary and not candidate.venue_name:
        score -= 1.5

    return score


def _build_activity_ranking_reasons(
    *,
    kind: str,
    configuration: TripConfiguration,
    trip_style_planning: TripStylePlanningState,
    title: str,
    category: str | None,
    start_at: object,
    location_label: str | None,
) -> list[str]:
    reasons: list[str] = []
    if kind == "event":
        reasons.append("Gives the trip a real timed moment to build around.")
    elif category:
        reasons.append(_category_reason(category))

    if (
        trip_style_planning.selection_status in {"selected", "completed"}
        and trip_style_planning.selected_primary_direction
    ):
        reasons.append(
            f"Supports the chosen {_trip_direction_primary_label(trip_style_planning.selected_primary_direction)} direction."
        )
    elif configuration.activity_styles:
        style_label = configuration.activity_styles[0].replace("_", " ")
        reasons.append(f"Supports the current {style_label} direction.")

    if (
        trip_style_planning.selection_status in {"selected", "completed"}
        and trip_style_planning.selected_accent
    ):
        reasons.append(
            f"Keeps a {_trip_direction_accent_label(trip_style_planning.selected_accent)} accent in view."
        )

    if configuration.custom_style and any(
        token in title.lower()
        for token in configuration.custom_style.lower().split()
        if len(token) > 3
    ):
        reasons.append("Lines up with the custom vibe you described.")

    if configuration.to_location:
        reasons.append(f"Feels rooted in {configuration.to_location}.")

    if isinstance(start_at, datetime):
        reasons.append("Worth keeping visible early because the timing is fixed.")
    elif location_label:
        reasons.append("Looks easy to weave into the trip without overcomplicating the day.")

    return reasons[:4]


def _score_candidate_against_trip_direction(
    *,
    candidate: AdvancedActivityCandidateCard,
    text: str,
    primary: PlannerTripDirectionPrimary,
    accent: PlannerTripDirectionAccent | None,
) -> float:
    score = 0.0
    primary_tokens: dict[PlannerTripDirectionPrimary, tuple[str, ...]] = {
        "food_led": ("food", "market", "tasting", "restaurant", "dining", "cafe"),
        "culture_led": ("museum", "temple", "gallery", "heritage", "history", "theatre", "shrine"),
        "nightlife_led": ("night", "bar", "late", "club", "jazz", "cocktail", "live music"),
        "outdoors_led": ("park", "garden", "trail", "outdoor", "viewpoint", "nature", "hike"),
        "balanced": ("market", "museum", "walk", "garden", "district"),
    }
    accent_tokens: dict[PlannerTripDirectionAccent, tuple[str, ...]] = {
        "local": ("local", "neighborhood", "neighbourhood", "alley", "hidden"),
        "classic": ("iconic", "classic", "must-see", "heritage", "historic", "signature"),
        "polished": ("design", "chef", "premium", "refined", "reservation", "boutique"),
        "romantic": ("scenic", "sunset", "river", "romantic", "intimate", "lantern"),
        "relaxed": ("slow", "garden", "tea", "walk", "easy", "calm"),
    }

    if any(token in text for token in primary_tokens[primary]):
        score += 3.0
    if accent and any(token in text for token in accent_tokens[accent]):
        score += 1.75
    if primary == "nightlife_led" and candidate.kind == "event":
        score += 0.75
    if primary == "culture_led" and candidate.kind == "event":
        score += 0.5
    if primary == "balanced":
        score += 0.5
    return score


def _build_trip_style_activity_note(
    *,
    trip_style_planning: TripStylePlanningState,
) -> str | None:
    primary = trip_style_planning.selected_primary_direction
    if primary is None:
        return None
    accent_line = (
        f" with a {_trip_direction_accent_label(trip_style_planning.selected_accent)} accent"
        if trip_style_planning.selected_accent
        else ""
    )
    return (
        f"I reranked the shortlist around your {_trip_direction_primary_label(primary)} direction{accent_line} while keeping your existing activity edits in place."
    )


def _build_trip_style_pace_activity_note(
    *,
    trip_style_planning: TripStylePlanningState,
    unscheduled_candidate_ids: list[str],
) -> str | None:
    if trip_style_planning.pace_status != "completed" or not trip_style_planning.selected_pace:
        return None
    if trip_style_planning.selected_pace == "slow":
        if unscheduled_candidate_ids:
            return "Slow pace is keeping extra ideas in reserve instead of filling every daypart."
        return "Slow pace is keeping the automatic day plan lighter while preserving fixed events and manual edits."
    if trip_style_planning.selected_pace == "full":
        return "Full pace is using more dayparts while still keeping fixed events locked."
    return "Balanced pace is aiming for two main flexible moments most days before saving overflow ideas for later."


def _build_activity_candidate_summary(
    *,
    title: str,
    category: str | None,
    time_label: str | None,
    venue_name: str | None,
) -> str | None:
    summary_parts = [
        _editorial_activity_summary(category=category, title=title),
        _time_summary_label(time_label),
    ]

    if (
        venue_name
        and venue_name.strip()
        and venue_name.strip() != title
        and not venue_name.isascii()
    ):
        summary_parts.append(f"Known locally as {venue_name.strip()}.")

    summary = " ".join(part for part in summary_parts if part).strip()
    return summary or None


def _editorial_activity_summary(*, category: str | None, title: str) -> str:
    lowered_title = title.lower()
    if "market" in lowered_title:
        return "Food market with plenty to browse and taste."
    if any(token in lowered_title for token in ["alley", "izakaya", "bar", "jazz", "night"]):
        return "Atmospheric pick for the later part of the day."
    if any(token in lowered_title for token in ["museum", "gallery"]):
        return "Culture-led stop with enough substance to shape part of the day."
    if any(token in lowered_title for token in ["shrine", "temple", "garden", "palace", "castle"]):
        return "Classic sight worth building part of the day around."

    lowered_category = (category or "").lower()
    if "commercial.marketplace" in lowered_category:
        return "Food market with plenty to browse and taste."
    if "catering.restaurant" in lowered_category:
        return "Food-led stop that can carry part of the day well."
    if "catering.cafe" in lowered_category:
        return "Cafe stop that works well as a lighter pause."
    if "catering.bar" in lowered_category:
        return "Evening-facing stop with more atmosphere than a generic meal."
    if "entertainment.culture" in lowered_category:
        return "Culture-led stop with enough substance to shape part of the day."
    if "tourism.sights" in lowered_category:
        return "Classic sight worth building part of the day around."
    if "leisure.park" in lowered_category or "natural" in lowered_category:
        return "Slower outdoor stop when the trip needs breathing room."
    return "Solid trip pick that can help give the day a clearer center."


def _time_summary_label(time_label: str | None) -> str:
    return {
        "Morning": "Best earlier in the day.",
        "Afternoon": "Easy to place in the middle of the day.",
        "Evening": "Best once the day turns toward dinner and wandering.",
        "Flexible": "Flexible enough to place where the day needs it most.",
    }.get(time_label or "", "Flexible enough to place where the day needs it most.")


def _category_reason(category: str) -> str:
    lowered_category = category.lower()
    if "commercial.marketplace" in lowered_category:
        return "Adds a strong food-market moment to the trip."
    if "catering.restaurant" in lowered_category or "catering.cafe" in lowered_category:
        return "Supports the food side of the trip well."
    if "catering.bar" in lowered_category:
        return "Adds a stronger evening note to the trip."
    if "museum" in lowered_category or "gallery" in lowered_category or "entertainment.culture" in lowered_category:
        return "Adds real cultural weight to the trip."
    if "tourism.sights" in lowered_category:
        return "Brings in a classic sightseeing moment."
    if "leisure.park" in lowered_category or "natural" in lowered_category:
        return "Helps the trip breathe a bit more."
    return f"Matches the trip's {category.split('.')[-1].replace('_', ' ')} direction."


def _apply_activity_board_action(
    *,
    candidates: list[AdvancedActivityCandidateCard],
    board_action: dict,
) -> list[AdvancedActivityCandidateCard]:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action is None or action.type != "set_activity_candidate_disposition":
        return candidates
    if not action.activity_candidate_id or not action.activity_candidate_disposition:
        return candidates

    updated: list[AdvancedActivityCandidateCard] = []
    for candidate in candidates:
        if candidate.id != action.activity_candidate_id:
            updated.append(candidate)
            continue
        updated.append(
            candidate.model_copy(
                update={"disposition": action.activity_candidate_disposition}
            )
        )
    return updated


def _apply_requested_activity_decisions(
    *,
    candidates: list[AdvancedActivityCandidateCard],
    decisions,
) -> list[AdvancedActivityCandidateCard]:
    updated_candidates = candidates
    for decision in decisions:
        matching_candidates = [
            candidate
            for candidate in updated_candidates
            if candidate.disposition != "pass"
            and candidate.title.strip().lower() == decision.candidate_title.strip().lower()
            and (
                decision.candidate_kind is None or candidate.kind == decision.candidate_kind
            )
        ]
        if len(matching_candidates) != 1:
            continue
        target_id = matching_candidates[0].id
        updated_candidates = [
            candidate.model_copy(update={"disposition": decision.disposition})
            if candidate.id == target_id
            else candidate
            for candidate in updated_candidates
        ]
    return updated_candidates


def _build_activity_workspace_summary(
    *,
    visible_candidates: list[AdvancedActivityCandidateCard],
    essential_ids: list[str],
    passed_ids: list[str],
    reserved_candidate_ids: list[str],
    overflow_candidate_ids: list[str],
) -> str:
    lead_event = next(
        (
            candidate
            for candidate in visible_candidates
            if candidate.kind == "event" and candidate.start_at is not None
        ),
        None,
    )
    event_count = sum(1 for candidate in visible_candidates if candidate.kind == "event")
    activity_count = sum(
        1 for candidate in visible_candidates if candidate.kind == "activity"
    )
    if lead_event and visible_candidates and visible_candidates[0].id == lead_event.id:
        reserve_events = sum(
            1
            for candidate in visible_candidates
            if candidate.kind == "event" and candidate.id != lead_event.id
        )
        return (
            f"Event-led around {lead_event.title}, "
            f"{activity_count} supporting activity option{'s' if activity_count != 1 else ''}"
            + (
                f", {reserve_events} reserve event{'s' if reserve_events != 1 else ''}"
                if reserve_events
                else ""
            )
            + (
                f", {len(passed_ids)} passed"
                if passed_ids
                else ""
            )
            + "."
        )
    summary_parts = [
        f"{len(essential_ids)} essential" if essential_ids else None,
        f"{activity_count} activity options" if activity_count else None,
        f"{event_count} live events" if event_count else None,
        f"{len(reserved_candidate_ids)} saved for later" if reserved_candidate_ids else None,
        f"{len(overflow_candidate_ids)} still not fitting cleanly" if overflow_candidate_ids else None,
        f"{len(passed_ids)} passed" if passed_ids else None,
    ]
    summary = ", ".join(part for part in summary_parts if part)
    return summary or "Ranked activity ideas are ready to sort."


def _score_candidate_against_stay_context(
    *,
    candidate: AdvancedActivityCandidateCard,
    stay_planning: AdvancedStayPlanningState,
) -> float:
    stay_context = _selected_stay_context_label(stay_planning)
    if not stay_context:
        return 0.0

    candidate_text = " ".join(
        part.lower()
        for part in [
            candidate.title,
            candidate.location_label or "",
            candidate.summary or "",
        ]
        if part
    )
    stay_tokens = [
        token
        for token in stay_context.lower().replace(",", " ").split()
        if len(token) > 3
    ]
    if any(token in candidate_text for token in stay_tokens):
        return 1.5
    return 0.0


def _selected_stay_context_label(
    stay_planning: AdvancedStayPlanningState,
) -> str | None:
    return stay_planning.selected_hotel_name or stay_planning.selected_stay_direction


def _build_activity_schedule(
    *,
    candidates: list[AdvancedActivityCandidateCard],
    configuration: TripConfiguration,
    stay_planning: AdvancedStayPlanningState,
    trip_style_planning: TripStylePlanningState,
    placement_preferences: list[AdvancedActivityPlacementPreference],
) -> tuple[
    list[AdvancedActivityDayPlan],
    list[AdvancedActivityTimelineBlock],
    list[str],
    list[str],
    str | None,
    list[str],
    str,
]:
    if not candidates:
        return [], [], [], [], "No activity anchors are active yet.", [], "none"

    day_specs = _build_activity_day_specs(configuration)
    if not day_specs:
        return [], [], [], [candidate.id for candidate in candidates], None, [], "none"

    slot_order = ("morning", "afternoon", "evening")
    pace = (
        trip_style_planning.selected_pace
        if trip_style_planning.pace_status == "completed"
        else "balanced"
    )
    scheduled_slots: dict[int, dict[str, AdvancedActivityTimelineBlock]] = {
        day_index: {} for day_index, _, _ in day_specs
    }
    unscheduled_candidate_ids: list[str] = []
    schedule_notes: list[str] = []
    preference_map = {
        preference.candidate_id: preference for preference in placement_preferences
    }
    reserved_candidate_ids = [
        candidate.id
        for candidate in candidates
        if (
            candidate.disposition != "pass"
            and preference_map.get(candidate.id) is not None
            and preference_map[candidate.id].reserved
        )
    ]

    fixed_events = [
        candidate
        for candidate in candidates
        if candidate.kind == "event" and candidate.start_at is not None
    ]
    for candidate in fixed_events:
        if candidate.id in reserved_candidate_ids:
            continue
        preference = preference_map.get(candidate.id)
        day_index = _resolve_candidate_day_index(candidate=candidate, day_specs=day_specs)
        slot_key = _resolve_activity_slot_key(
            candidate.time_label,
            candidate.start_at.hour if candidate.start_at else None,
        )
        if preference and (
            (preference.day_index is not None and preference.day_index != day_index)
            or (preference.daypart is not None and preference.daypart != slot_key)
        ):
            _append_schedule_note(
                schedule_notes,
                f"{candidate.title} keeps its fixed event time, so I kept that slot locked and adjusted the rest around it.",
            )
        if day_index is None or slot_key in scheduled_slots[day_index]:
            unscheduled_candidate_ids.append(candidate.id)
            continue
        scheduled_slots[day_index][slot_key] = _build_scheduled_candidate_block(
            candidate=candidate,
            day_index=day_index,
            day_specs=day_specs,
            slot_key=slot_key,
            fixed_time=True,
            manual_override=bool(
                preference and (preference.day_index is not None or preference.daypart is not None)
            ),
        )

    scheduled_candidate_ids = {
        scheduled_id for scheduled_id in scheduled_slots_to_candidate_ids(scheduled_slots)
    }
    preferred_candidates = [
        candidate
        for candidate in candidates
        if candidate.id not in scheduled_candidate_ids
        and candidate.id not in reserved_candidate_ids
        and candidate.disposition in {"essential", "maybe"}
        and preference_map.get(candidate.id) is not None
        and (
            preference_map[candidate.id].day_index is not None
            or preference_map[candidate.id].daypart is not None
        )
    ]
    preferred_candidates.sort(
        key=lambda candidate: (
            candidate.disposition != "essential",
            candidate.kind != "event",
            preference_map[candidate.id].day_index is None,
            preference_map[candidate.id].daypart is None,
            candidate.title.lower(),
        )
    )
    for candidate in preferred_candidates:
        preference = preference_map.get(candidate.id)
        if preference is None:
            continue
        placement, placement_note = _select_preferred_activity_slot_for_candidate(
            candidate=candidate,
            preference=preference,
            day_specs=day_specs,
            scheduled_slots=scheduled_slots,
            stay_planning=stay_planning,
        )
        _append_schedule_note(schedule_notes, placement_note)
        if placement is None:
            unscheduled_candidate_ids.append(candidate.id)
            continue
        day_index, slot_key = placement
        scheduled_slots[day_index][slot_key] = _build_scheduled_candidate_block(
            candidate=candidate,
            day_index=day_index,
            day_specs=day_specs,
            slot_key=slot_key,
            fixed_time=False,
            manual_override=True,
        )

    flexible_candidates = [
        candidate
        for candidate in candidates
        if candidate.id not in {scheduled_id for scheduled_id in scheduled_slots_to_candidate_ids(scheduled_slots)}
        and candidate.id not in reserved_candidate_ids
        and candidate.disposition in {"essential", "maybe"}
    ]
    flexible_candidates.sort(
        key=lambda candidate: (
            candidate.disposition != "essential",
            candidate.kind != "event",
            not candidate.recommended,
            candidate.title.lower(),
        )
    )

    for candidate in flexible_candidates:
        placement = _select_activity_slot_for_candidate(
            candidate=candidate,
            day_specs=day_specs,
            scheduled_slots=scheduled_slots,
            stay_planning=stay_planning,
            pace=pace,
        )
        if placement is None:
            unscheduled_candidate_ids.append(candidate.id)
            continue
        day_index, slot_key = placement
        scheduled_slots[day_index][slot_key] = _build_scheduled_candidate_block(
            candidate=candidate,
            day_index=day_index,
            day_specs=day_specs,
            slot_key=slot_key,
            fixed_time=False,
            manual_override=False,
        )

    day_plans: list[AdvancedActivityDayPlan] = []
    timeline_blocks: list[AdvancedActivityTimelineBlock] = []
    scheduled_candidate_ids: set[str] = set()
    for day_index, day_label, day_date in day_specs:
        base_blocks = [
            scheduled_slots[day_index][slot_key]
            for slot_key in slot_order
            if slot_key in scheduled_slots[day_index]
        ]
        scheduled_candidate_ids.update(
            block.candidate_id for block in base_blocks if block.candidate_id
        )
        day_blocks = _insert_transfer_blocks(base_blocks)
        day_plans.append(
            AdvancedActivityDayPlan(
                id=f"activity_day_{day_index}",
                day_index=day_index,
                day_label=day_label,
                date=day_date,
                blocks=day_blocks,
            )
        )
        timeline_blocks.extend(day_blocks)

    remaining_unscheduled = [
        candidate.id
        for candidate in candidates
        if candidate.id not in scheduled_candidate_ids
        and candidate.id not in unscheduled_candidate_ids
        and candidate.id not in reserved_candidate_ids
        and candidate.disposition != "pass"
    ]
    unscheduled_candidate_ids = [*reserved_candidate_ids, *unscheduled_candidate_ids, *remaining_unscheduled]

    scheduled_stops = [
        block for block in timeline_blocks if block.type in {"activity", "event"}
    ]
    if not scheduled_stops:
        return (
            day_plans,
            timeline_blocks,
            reserved_candidate_ids,
            unscheduled_candidate_ids,
            None,
            schedule_notes,
            "none",
        )

    lead_event = next(
        (
            candidate
            for candidate in candidates
            if candidate.kind == "event"
            and candidate.start_at is not None
            and candidate.id in scheduled_candidate_ids
        ),
        None,
    )
    supporting_activity_count = sum(
        1 for block in timeline_blocks if block.type == "activity"
    )

    if lead_event:
        summary_parts = [
            f"Built around {lead_event.title}",
            f"{supporting_activity_count} supporting stop{'s' if supporting_activity_count != 1 else ''}",
        ]
    else:
        summary_parts = [
            f"{len(day_plans)} day{'s' if len(day_plans) != 1 else ''} taking shape",
            f"{len(scheduled_stops)} planned stop{'s' if len(scheduled_stops) != 1 else ''}",
        ]
    if unscheduled_candidate_ids:
        summary_parts.append(
            f"{len(unscheduled_candidate_ids)} still saved for later"
        )
    return (
        day_plans,
        timeline_blocks,
        reserved_candidate_ids,
        unscheduled_candidate_ids,
        ", ".join(summary_parts),
        schedule_notes,
        "ready",
    )


def _select_preferred_activity_slot_for_candidate(
    *,
    candidate: AdvancedActivityCandidateCard,
    preference: AdvancedActivityPlacementPreference,
    day_specs: list[tuple[int, str, date | None]],
    scheduled_slots: dict[int, dict[str, AdvancedActivityTimelineBlock]],
    stay_planning: AdvancedStayPlanningState,
) -> tuple[tuple[int, str] | None, str | None]:
    slot_order: tuple[PlannerActivityDaypart, ...] = ("morning", "afternoon", "evening")
    best_choice: tuple[float, int, str] | None = None

    for day_index, _, _ in day_specs:
        occupied_slots = scheduled_slots[day_index]
        for slot_key in slot_order:
            if slot_key in occupied_slots:
                continue
            score = 0.0
            if preference.day_index is not None:
                if day_index == preference.day_index:
                    score += 8.0
                else:
                    score -= abs(day_index - preference.day_index) * 3.0
            if preference.daypart is not None:
                if slot_key == preference.daypart:
                    score += 6.0
                else:
                    score -= 4.0
            else:
                preferred_slot = _default_candidate_daypart(candidate)
                if slot_key == preferred_slot:
                    score += 2.0
            score -= len(occupied_slots) * 0.75
            score += _score_candidate_against_stay_context(
                candidate=candidate,
                stay_planning=stay_planning,
            )
            anchor_blocks = list(occupied_slots.values())
            if anchor_blocks:
                closest_minutes = _estimate_candidate_anchor_minutes(
                    candidate=candidate,
                    anchor_blocks=anchor_blocks,
                )
                if closest_minutes is not None:
                    score -= min(closest_minutes / 45.0, 2.5)
            if best_choice is None or score > best_choice[0]:
                best_choice = (score, day_index, slot_key)

    if best_choice is None:
        return None, None

    chosen_day_index = best_choice[1]
    chosen_daypart = best_choice[2]
    if (
        preference.day_index is not None
        and preference.daypart is not None
        and (
            chosen_day_index != preference.day_index
            or chosen_daypart != preference.daypart
        )
    ):
        return (
            (chosen_day_index, chosen_daypart),
            f"{candidate.title} stayed in the plan, but I shifted it off the exact requested slot to keep the day workable.",
        )
    if preference.day_index is not None and chosen_day_index != preference.day_index:
        return (
            (chosen_day_index, chosen_daypart),
            f"{candidate.title} moved to the nearest workable day instead of being forced into a crowded one.",
        )
    if preference.daypart is not None and chosen_daypart != preference.daypart:
        return (
            (chosen_day_index, chosen_daypart),
            f"{candidate.title} stayed in the same day flow, but I softened the requested timing a little to keep the draft balanced.",
        )
    return (chosen_day_index, chosen_daypart), None


def scheduled_slots_to_candidate_ids(
    scheduled_slots: dict[int, dict[str, AdvancedActivityTimelineBlock]]
) -> list[str]:
    candidate_ids: list[str] = []
    for day_slots in scheduled_slots.values():
        candidate_ids.extend(
            block.candidate_id for block in day_slots.values() if block.candidate_id
        )
    return candidate_ids


def _build_activity_day_specs(
    configuration: TripConfiguration,
) -> list[tuple[int, str, date | None]]:
    if configuration.start_date and configuration.end_date:
        trip_days = max((configuration.end_date - configuration.start_date).days + 1, 1)
        return [
            (
                index + 1,
                f"Day {index + 1}",
                configuration.start_date + timedelta(days=index),
            )
            for index in range(min(trip_days, 10))
        ]

    if configuration.start_date:
        return [(1, "Day 1", configuration.start_date)]

    fallback_days = 3
    if configuration.trip_length:
        normalized_tokens = configuration.trip_length.replace("-", " ").split()
        fallback_days = next(
            (int(token) for token in normalized_tokens if token.isdigit()),
            fallback_days,
        )
    return [
        (index + 1, f"Day {index + 1}", None)
        for index in range(max(1, min(fallback_days, 5)))
    ]


def _resolve_candidate_day_index(
    *,
    candidate: AdvancedActivityCandidateCard,
    day_specs: list[tuple[int, str, date | None]],
) -> int | None:
    if not candidate.start_at:
        return day_specs[0][0] if day_specs else None

    candidate_date = candidate.start_at.date()
    for day_index, _, day_date in day_specs:
        if day_date == candidate_date:
            return day_index

    return day_specs[0][0] if len(day_specs) == 1 else None


def _select_activity_slot_for_candidate(
    *,
    candidate: AdvancedActivityCandidateCard,
    day_specs: list[tuple[int, str, date | None]],
    scheduled_slots: dict[int, dict[str, AdvancedActivityTimelineBlock]],
    stay_planning: AdvancedStayPlanningState,
    pace: PlannerTripPace,
) -> tuple[int, str] | None:
    slot_order = ("morning", "afternoon", "evening")
    preferred_slot = _resolve_activity_slot_key(candidate.time_label)
    best_choice: tuple[float, int, str] | None = None

    for day_index, _, _ in day_specs:
        occupied_slots = scheduled_slots[day_index]
        if not _pace_allows_flexible_candidate(
            candidate=candidate,
            occupied_slots=occupied_slots,
            pace=pace,
        ):
            continue
        for slot_key in slot_order:
            if slot_key in occupied_slots:
                continue
            score = 0.0
            if preferred_slot == slot_key:
                score += 3.0
            elif candidate.time_label in {None, "", "Flexible"}:
                score += 1.0
            score -= len(occupied_slots) * 0.75
            score += _score_candidate_against_stay_context(
                candidate=candidate,
                stay_planning=stay_planning,
            )
            anchor_blocks = list(occupied_slots.values())
            if anchor_blocks:
                closest_minutes = _estimate_candidate_anchor_minutes(
                    candidate=candidate,
                    anchor_blocks=anchor_blocks,
                )
                if closest_minutes is not None:
                    score -= min(closest_minutes / 45.0, 2.5)
            if best_choice is None or score > best_choice[0]:
                best_choice = (score, day_index, slot_key)

    if best_choice is None:
        return None
    return best_choice[1], best_choice[2]


def _pace_allows_flexible_candidate(
    *,
    candidate: AdvancedActivityCandidateCard,
    occupied_slots: dict[str, AdvancedActivityTimelineBlock],
    pace: PlannerTripPace,
) -> bool:
    occupied_count = len(occupied_slots)
    if pace == "full":
        return occupied_count < 3
    if pace == "balanced":
        return occupied_count < 2
    if candidate.disposition == "essential":
        return occupied_count < 2
    return occupied_count < 1


def _estimate_candidate_anchor_minutes(
    *,
    candidate: AdvancedActivityCandidateCard,
    anchor_blocks: list[AdvancedActivityTimelineBlock],
) -> float | None:
    estimates = []
    for block in anchor_blocks:
        if not block.details:
            continue
        block_latitude, block_longitude = _extract_coordinates_from_block_details(block)
        if block_latitude is None or block_longitude is None:
            continue
        estimate = estimate_travel_duration_minutes(
            origin_latitude=block_latitude,
            origin_longitude=block_longitude,
            destination_latitude=candidate.latitude,
            destination_longitude=candidate.longitude,
        )
        if estimate is not None:
            estimates.append(estimate.minutes)
    if not estimates:
        return None
    return min(estimates)


def _build_scheduled_candidate_block(
    *,
    candidate: AdvancedActivityCandidateCard,
    day_index: int,
    day_specs: list[tuple[int, str, date | None]],
    slot_key: str,
    fixed_time: bool,
    manual_override: bool,
) -> AdvancedActivityTimelineBlock:
    _, day_label, day_date = next(
        spec for spec in day_specs if spec[0] == day_index
    )
    scheduled_start_at, scheduled_end_at = _resolve_block_times(
        candidate=candidate,
        day_date=day_date,
        slot_key=slot_key,
        fixed_time=fixed_time,
    )
    block_type = "event" if candidate.kind == "event" else "activity"
    details = []
    if candidate.latitude is not None and candidate.longitude is not None:
        details.append(f"coords:{candidate.latitude:.6f},{candidate.longitude:.6f}")
    if candidate.estimated_duration_minutes:
        details.append(f"Give this about {candidate.estimated_duration_minutes} minutes.")
    if candidate.source_label:
        details.append(f"Source: {candidate.source_label}.")
    return AdvancedActivityTimelineBlock(
        id=f"activity_schedule_{candidate.id}_{day_index}_{slot_key}",
        type=block_type,
        candidate_id=candidate.id,
        title=candidate.title,
        day_index=day_index,
        day_label=day_label,
        daypart=slot_key,
        venue_name=candidate.venue_name,
        location_label=candidate.location_label,
        start_at=scheduled_start_at,
        end_at=scheduled_end_at,
        summary=candidate.summary,
        details=details[:6],
        source_label=candidate.source_label,
        source_url=candidate.source_url,
        image_url=candidate.image_url,
        availability_text=candidate.availability_text,
        price_text=candidate.price_text,
        status_text=candidate.status_text,
        fixed_time=fixed_time,
        manual_override=manual_override,
    )


def _resolve_block_times(
    *,
    candidate: AdvancedActivityCandidateCard,
    day_date: date | None,
    slot_key: str,
    fixed_time: bool,
) -> tuple[datetime | None, datetime | None]:
    if fixed_time and candidate.start_at:
        if candidate.end_at:
            return candidate.start_at, candidate.end_at
        fallback_duration = candidate.estimated_duration_minutes or 120
        return candidate.start_at, candidate.start_at + timedelta(minutes=fallback_duration)

    if day_date is None:
        return None, None

    slot_starts = {
        "morning": time(9, 30),
        "afternoon": time(13, 30),
        "evening": time(18, 0),
    }
    slot_durations = {
        "morning": 120,
        "afternoon": 150,
        "evening": 150,
    }
    start_time = slot_starts.get(slot_key, time(11, 0))
    start_at = datetime.combine(day_date, start_time, tzinfo=timezone.utc)
    duration_minutes = min(
        candidate.estimated_duration_minutes or slot_durations.get(slot_key, 120),
        slot_durations.get(slot_key, 150),
    )
    return start_at, start_at + timedelta(minutes=duration_minutes)


def _resolve_activity_slot_key(
    time_label: str | None,
    hour: int | None = None,
) -> str:
    lowered = (time_label or "").lower()
    if hour is not None:
        if hour < 12:
            return "morning"
        if hour < 17:
            return "afternoon"
        return "evening"
    if "morning" in lowered:
        return "morning"
    if "afternoon" in lowered:
        return "afternoon"
    if "evening" in lowered or "night" in lowered:
        return "evening"
    return "afternoon"


def _insert_transfer_blocks(
    blocks: list[AdvancedActivityTimelineBlock],
) -> list[AdvancedActivityTimelineBlock]:
    if len(blocks) < 2:
        return blocks

    enriched_blocks: list[AdvancedActivityTimelineBlock] = []
    for index, block in enumerate(blocks):
        enriched_blocks.append(block)
        if index == len(blocks) - 1:
            continue
        next_block = blocks[index + 1]
        estimate = _estimate_transfer_block(block, next_block)
        if estimate is None or estimate.minutes < 15:
            continue

        transfer_start_at = block.end_at
        transfer_end_at = (
            min(next_block.start_at, block.end_at + timedelta(minutes=estimate.minutes))
            if block.end_at and next_block.start_at
            else None
        )
        enriched_blocks.append(
            AdvancedActivityTimelineBlock(
                id=f"transfer_{block.id}_{next_block.id}",
                type="transfer",
                candidate_id=None,
                title="Travel between plans",
                day_index=block.day_index,
                day_label=block.day_label,
                daypart=None,
                location_label=next_block.location_label,
                start_at=transfer_start_at,
                end_at=transfer_end_at,
                summary=f"Set aside about {estimate.minutes} minutes to get to the next stop.",
                details=[f"Travel-time estimate based on {estimate.source}."],
                source_label=None,
                source_url=None,
                fixed_time=False,
                manual_override=False,
            )
        )
    return enriched_blocks


def _estimate_transfer_block(
    origin_block: AdvancedActivityTimelineBlock,
    destination_block: AdvancedActivityTimelineBlock,
):
    origin_coordinates = _extract_coordinates_from_block_details(origin_block)
    destination_coordinates = _extract_coordinates_from_block_details(destination_block)
    if origin_coordinates[0] is None or destination_coordinates[0] is None:
        return None
    return estimate_travel_duration_minutes(
        origin_latitude=origin_coordinates[0],
        origin_longitude=origin_coordinates[1],
        destination_latitude=destination_coordinates[0],
        destination_longitude=destination_coordinates[1],
    )


def _extract_coordinates_from_block_details(
    block: AdvancedActivityTimelineBlock,
) -> tuple[float | None, float | None]:
    for detail in block.details:
        if not detail.startswith("coords:"):
            continue
        payload = detail.removeprefix("coords:")
        latitude_text, _, longitude_text = payload.partition(",")
        try:
            return float(latitude_text), float(longitude_text)
        except ValueError:
            return None, None
    return None, None


def merge_stay_planning_state(
    *,
    current: AdvancedStayPlanningState,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    llm_update: TripTurnUpdate,
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
                stay_planning.hotel_filters.max_nightly_rate = None
                stay_planning.hotel_filters.area_filter = None
                stay_planning.hotel_filters.style_filter = None
                stay_planning.hotel_sort_order = "best_fit"

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
        stay_planning.hotel_filters.max_nightly_rate = None
        stay_planning.hotel_filters.area_filter = None
        stay_planning.hotel_filters.style_filter = None
        stay_planning.hotel_sort_order = "best_fit"
        stay_planning.hotel_results_status = "blocked"
        stay_planning.hotel_results_summary = None
        stay_planning.hotel_page = 1
        stay_planning.hotel_page_size = 6
        stay_planning.hotel_total_results = 0
        stay_planning.hotel_total_pages = 1
        stay_planning.available_hotel_areas = []
        stay_planning.available_hotel_styles = []
        stay_planning.selected_hotel_card = None
    elif selected_option is not None:
        exact_hotel_workspace_ready = bool(
            configuration.start_date and configuration.end_date
        )
        stay_planning.selected_stay_option_id = selected_option.id
        stay_planning.selected_stay_direction = selected_option.title
        if stay_planning.selection_status == "none":
            stay_planning.selection_status = "selected"
        if not stay_planning.selection_rationale:
            stay_planning.selection_rationale = selected_option.summary
        if not stay_planning.selection_assumptions:
            stay_planning.selection_assumptions = list(selected_option.best_for[:4])
        stay_planning.hotel_filters.max_nightly_rate = None
        stay_planning.hotel_filters.area_filter = None
        stay_planning.hotel_filters.style_filter = None
        stay_planning.hotel_sort_order = "best_fit"
        stay_planning.hotel_page = 1

        all_hotel_cards = build_advanced_stay_hotel_options(
            configuration=configuration,
            selected_stay_option=selected_option,
            hotels=module_outputs.hotels,
        )
        hotel_workspace = build_advanced_stay_hotel_workspace(
            configuration=configuration,
            selected_stay_option=selected_option,
            hotel_cards=all_hotel_cards,
            filters=stay_planning.hotel_filters,
            sort_order=stay_planning.hotel_sort_order,
            page=stay_planning.hotel_page,
            selected_hotel_id=stay_planning.selected_hotel_id,
        )
        stay_planning.recommended_hotels = hotel_workspace["hotel_cards"]
        stay_planning.hotel_results_status = hotel_workspace["hotel_results_status"]
        stay_planning.hotel_results_summary = hotel_workspace["hotel_results_summary"]
        stay_planning.hotel_page = hotel_workspace["hotel_page"]
        stay_planning.hotel_page_size = hotel_workspace["hotel_page_size"]
        stay_planning.hotel_total_results = hotel_workspace["hotel_total_results"]
        stay_planning.hotel_total_pages = hotel_workspace["hotel_total_pages"]
        stay_planning.available_hotel_areas = []
        stay_planning.available_hotel_styles = []
        stay_planning.selected_hotel_card = hotel_workspace["selected_hotel_card"]
        if (
            stay_planning.recommended_hotels
            or stay_planning.hotel_results_status in {"blocked", "empty"}
        ) and stay_planning.hotel_substep == "strategy_choice":
            stay_planning.hotel_substep = "hotel_shortlist"

        selected_hotel = stay_planning.selected_hotel_card
        if (
            exact_hotel_workspace_ready
            and action
            and action.type == "select_stay_hotel"
            and action.stay_hotel_id
        ):
            selected_hotel = next(
                (
                    hotel
                    for hotel in all_hotel_cards
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
        elif (
            exact_hotel_workspace_ready
            and llm_update.requested_stay_hotel_name
        ):
            requested_hotel_name = _normalize_hotel_name(
                llm_update.requested_stay_hotel_name
            )
            selected_hotel = next(
                (
                    hotel
                    for hotel in all_hotel_cards
                    if _normalize_hotel_name(hotel.hotel_name) == requested_hotel_name
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
            stay_planning.selected_hotel_card = None
            if stay_planning.hotel_compatibility_status not in {"strained", "conflicted"}:
                stay_planning.hotel_compatibility_status = "fit"
                stay_planning.hotel_compatibility_notes = []
            stay_planning.hotel_substep = (
                "hotel_shortlist"
                if (
                    stay_planning.recommended_hotels
                    or stay_planning.hotel_results_status in {"blocked", "empty"}
                )
                else "strategy_choice"
            )
        elif selected_hotel is not None:
            stay_planning.selected_hotel_id = selected_hotel.id
            stay_planning.selected_hotel_name = selected_hotel.hotel_name
            stay_planning.selected_hotel_card = selected_hotel
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
                for hotel in all_hotel_cards
                if hotel.id == stay_planning.selected_hotel_id
            ),
            stay_planning.selected_hotel_card,
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


def _normalize_hotel_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def merge_trip_style_planning_state(
    *,
    current: TripStylePlanningState,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    planning_mode: PlannerPlanningMode | None,
    advanced_step: PlannerAdvancedStep | None,
    advanced_anchor: PlannerAdvancedAnchor | None,
    board_action: dict,
) -> TripStylePlanningState:
    trip_style_planning = current.model_copy(deep=True)

    if planning_mode != "advanced":
        return trip_style_planning

    is_active_workspace = (
        advanced_step == "anchor_flow" and advanced_anchor == "trip_style"
    )
    is_seeded = bool(
        trip_style_planning.workspace_touched
        or trip_style_planning.selected_primary_direction
        or trip_style_planning.selection_status != "none"
    )
    if not is_active_workspace and not is_seeded:
        return trip_style_planning

    (
        trip_style_planning.recommended_primary_directions,
        trip_style_planning.recommended_accents,
    ) = _recommend_trip_style_direction(configuration=configuration)
    trip_style_planning.recommended_paces = _recommend_trip_style_paces(
        configuration=configuration,
        trip_style_planning=trip_style_planning,
    )

    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    updates: list[RequestedTripStyleDirectionUpdate] = []
    if action is not None:
        mapped_update = _map_trip_style_board_action(action)
        if mapped_update is not None:
            updates.append(mapped_update)
    updates.extend(llm_update.requested_trip_style_direction_updates)

    for update in updates:
        if update.action == "select_primary" and update.primary is not None:
            trip_style_planning.selected_primary_direction = update.primary
            trip_style_planning.selection_status = "selected"
            if trip_style_planning.substep == "completed":
                trip_style_planning.substep = "pace"
        elif update.action == "select_accent" and update.accent is not None:
            trip_style_planning.selected_accent = update.accent
            trip_style_planning.selection_status = "selected"
            if trip_style_planning.substep == "completed":
                trip_style_planning.substep = "pace"
        elif update.action == "clear_accent":
            trip_style_planning.selected_accent = None
            if trip_style_planning.selected_primary_direction:
                trip_style_planning.selection_status = "selected"
            if trip_style_planning.substep == "completed":
                trip_style_planning.substep = "pace"
        elif update.action in {"confirm", "keep_current"}:
            if update.primary is not None:
                trip_style_planning.selected_primary_direction = update.primary
            if update.accent is not None:
                trip_style_planning.selected_accent = update.accent
            if trip_style_planning.selected_primary_direction is None:
                trip_style_planning.selected_primary_direction = (
                    trip_style_planning.recommended_primary_directions[0]
                    if trip_style_planning.recommended_primary_directions
                    else "balanced"
                )
            if trip_style_planning.pace_status == "completed":
                trip_style_planning.selection_status = "completed"
                trip_style_planning.substep = "completed"
            else:
                trip_style_planning.selection_status = "selected"
                trip_style_planning.substep = "pace"

    trip_style_planning.recommended_paces = _recommend_trip_style_paces(
        configuration=configuration,
        trip_style_planning=trip_style_planning,
    )

    pace_updates: list[RequestedTripStylePaceUpdate] = []
    if action is not None:
        mapped_pace_update = _map_trip_style_pace_board_action(action)
        if mapped_pace_update is not None:
            pace_updates.append(mapped_pace_update)
    pace_updates.extend(llm_update.requested_trip_style_pace_updates)

    for update in pace_updates:
        if update.action == "select_pace" and update.pace is not None:
            trip_style_planning.selected_pace = update.pace
            trip_style_planning.pace_status = "selected"
            if trip_style_planning.selected_primary_direction:
                trip_style_planning.substep = "pace"
        elif update.action in {"confirm", "keep_current"}:
            if update.pace is not None:
                trip_style_planning.selected_pace = update.pace
            if trip_style_planning.selected_pace is None:
                trip_style_planning.selected_pace = (
                    trip_style_planning.recommended_paces[0]
                    if trip_style_planning.recommended_paces
                    else "balanced"
                )
            if trip_style_planning.selected_primary_direction is None:
                trip_style_planning.selected_primary_direction = (
                    trip_style_planning.recommended_primary_directions[0]
                    if trip_style_planning.recommended_primary_directions
                    else "balanced"
                )
            trip_style_planning.selection_status = "completed"
            trip_style_planning.pace_status = "completed"
            trip_style_planning.substep = "completed"

    trip_style_planning.workspace_touched = bool(
        trip_style_planning.workspace_touched or updates or pace_updates
    )
    trip_style_planning.workspace_summary = _build_trip_style_workspace_summary(
        trip_style_planning=trip_style_planning,
        configuration=configuration,
    )
    trip_style_planning.selection_rationale = _build_trip_style_selection_rationale(
        trip_style_planning=trip_style_planning,
        configuration=configuration,
    )
    trip_style_planning.downstream_influence_summary = (
        _build_trip_style_downstream_influence_summary(
            trip_style_planning=trip_style_planning
        )
    )
    trip_style_planning.pace_rationale = _build_trip_style_pace_rationale(
        trip_style_planning=trip_style_planning,
        configuration=configuration,
    )
    trip_style_planning.pace_downstream_influence_summary = (
        _build_trip_style_pace_downstream_influence_summary(
            trip_style_planning=trip_style_planning
        )
    )
    trip_style_planning.completion_summary = (
        _build_trip_style_completion_summary(trip_style_planning=trip_style_planning)
        if trip_style_planning.substep == "completed"
        else None
    )

    return trip_style_planning


def _map_trip_style_board_action(
    action: ConversationBoardAction,
) -> RequestedTripStyleDirectionUpdate | None:
    action_map = {
        "select_trip_style_direction_primary": "select_primary",
        "select_trip_style_direction_accent": "select_accent",
        "clear_trip_style_direction_accent": "clear_accent",
        "confirm_trip_style_direction": "confirm",
        "keep_current_trip_style_direction": "keep_current",
    }
    mapped_action = action_map.get(action.type)
    if mapped_action is None:
        return None
    return RequestedTripStyleDirectionUpdate(
        action=mapped_action,
        primary=action.trip_style_direction_primary,
        accent=action.trip_style_direction_accent,
    )


def _map_trip_style_pace_board_action(
    action: ConversationBoardAction,
) -> RequestedTripStylePaceUpdate | None:
    action_map = {
        "select_trip_style_pace": "select_pace",
        "confirm_trip_style_pace": "confirm",
        "keep_current_trip_style_pace": "keep_current",
    }
    mapped_action = action_map.get(action.type)
    if mapped_action is None:
        return None
    return RequestedTripStylePaceUpdate(
        action=mapped_action,
        pace=action.trip_style_pace,
    )


def _recommend_trip_style_direction(
    *,
    configuration: TripConfiguration,
) -> tuple[list[PlannerTripDirectionPrimary], list[PlannerTripDirectionAccent]]:
    primary_scores: dict[PlannerTripDirectionPrimary, float] = {
        "food_led": 0.0,
        "culture_led": 0.0,
        "nightlife_led": 0.0,
        "outdoors_led": 0.0,
        "balanced": 0.5,
    }
    accent_scores: dict[PlannerTripDirectionAccent, float] = {
        "local": 0.0,
        "classic": 0.0,
        "polished": 0.0,
        "romantic": 0.0,
        "relaxed": 0.0,
    }

    custom_style = (configuration.custom_style or "").strip().lower()
    style_tokens = set(configuration.activity_styles)

    if "food" in style_tokens:
        primary_scores["food_led"] += 3.0
    if "culture" in style_tokens:
        primary_scores["culture_led"] += 3.0
    if "nightlife" in style_tokens:
        primary_scores["nightlife_led"] += 3.0
    if "outdoors" in style_tokens or "adventure" in style_tokens:
        primary_scores["outdoors_led"] += 3.0

    if "luxury" in style_tokens:
        accent_scores["polished"] += 2.5
    if "romantic" in style_tokens:
        accent_scores["romantic"] += 2.5
    if "relaxed" in style_tokens:
        accent_scores["relaxed"] += 2.5

    if any(token in custom_style for token in ["food", "market", "dining", "tasting", "restaurant", "cafe"]):
        primary_scores["food_led"] += 2.5
    if any(token in custom_style for token in ["culture", "museum", "temple", "heritage", "gallery", "history"]):
        primary_scores["culture_led"] += 2.5
    if any(token in custom_style for token in ["nightlife", "bar", "late", "jazz", "cocktail", "live music"]):
        primary_scores["nightlife_led"] += 2.5
    if any(token in custom_style for token in ["outdoors", "hike", "viewpoint", "park", "nature", "day trip"]):
        primary_scores["outdoors_led"] += 2.5

    if any(token in custom_style for token in ["local", "hidden", "neighborhood", "neighbourhood", "authentic"]):
        accent_scores["local"] += 2.0
    if any(token in custom_style for token in ["classic", "must-see", "first time", "iconic"]):
        accent_scores["classic"] += 2.0
    if any(token in custom_style for token in ["polished", "design", "refined", "premium"]):
        accent_scores["polished"] += 2.0
    if any(token in custom_style for token in ["romantic", "intimate", "scenic", "couple"]):
        accent_scores["romantic"] += 2.0
    if any(token in custom_style for token in ["relaxed", "slow", "easy", "calm", "gentle"]):
        accent_scores["relaxed"] += 2.0

    destination = (configuration.to_location or "").lower()
    if destination:
        if any(token in destination for token in ["kyoto", "rome", "florence", "paris"]):
            primary_scores["culture_led"] += 0.75
            accent_scores["classic"] += 0.5
        if any(token in destination for token in ["barcelona", "lisbon", "tokyo", "osaka"]):
            primary_scores["food_led"] += 0.5
        if any(token in destination for token in ["ibiza", "berlin", "seoul"]):
            primary_scores["nightlife_led"] += 0.75
        if any(token in destination for token in ["banff", "interlaken", "queenstown"]):
            primary_scores["outdoors_led"] += 0.75

    sorted_primaries = sorted(
        primary_scores,
        key=lambda direction: (primary_scores[direction], direction == "balanced"),
        reverse=True,
    )
    top_primary_score = primary_scores[sorted_primaries[0]]
    if top_primary_score <= 1.0:
        sorted_primaries = ["balanced", *[item for item in sorted_primaries if item != "balanced"]]

    sorted_accents = sorted(
        accent_scores,
        key=lambda accent: accent_scores[accent],
        reverse=True,
    )
    recommended_accents = [
        accent
        for accent in sorted_accents
        if accent_scores[accent] > 0
    ]
    if not recommended_accents:
        recommended_accents = ["local", "classic", "relaxed"]

    return sorted_primaries[:5], recommended_accents[:5]


def _recommend_trip_style_paces(
    *,
    configuration: TripConfiguration,
    trip_style_planning: TripStylePlanningState,
) -> list[PlannerTripPace]:
    scores: dict[PlannerTripPace, float] = {
        "slow": 0.0,
        "balanced": 1.0,
        "full": 0.0,
    }
    custom_style = (configuration.custom_style or "").strip().lower()
    trip_length = (configuration.trip_length or "").strip().lower()

    if trip_style_planning.selected_accent == "relaxed":
        scores["slow"] += 3.0
    if "relaxed" in configuration.activity_styles:
        scores["slow"] += 2.0
    if any(token in custom_style for token in ["slow", "relaxed", "easy", "calm", "gentle", "open time"]):
        scores["slow"] += 2.5
    if any(token in custom_style for token in ["packed", "maximize", "maximise", "as much as possible", "full days", "coverage"]):
        scores["full"] += 3.0
    if any(token in trip_length for token in ["weekend", "3 day", "3-day", "3 night", "3-night"]):
        scores["balanced"] += 1.5
    if configuration.start_date and configuration.end_date:
        trip_days = (configuration.end_date - configuration.start_date).days + 1
        if trip_days <= 3:
            scores["balanced"] += 1.0
        elif trip_days >= 6:
            scores["slow"] += 0.75

    sorted_paces = sorted(scores, key=lambda pace: scores[pace], reverse=True)
    return sorted_paces[:3]


def _build_trip_style_workspace_summary(
    *,
    trip_style_planning: TripStylePlanningState,
    configuration: TripConfiguration,
) -> str:
    destination = configuration.to_location or "this trip"
    if trip_style_planning.selected_primary_direction:
        primary_label = _trip_direction_primary_label(
            trip_style_planning.selected_primary_direction
        )
        accent_line = (
            f" with a {_trip_direction_accent_label(trip_style_planning.selected_accent)} accent"
            if trip_style_planning.selected_accent
            else ""
        )
        return (
            f"{destination} is currently being shaped as a {primary_label}{accent_line} trip."
        )
    recommended_primary = (
        trip_style_planning.recommended_primary_directions[0]
        if trip_style_planning.recommended_primary_directions
        else "balanced"
    )
    return (
        f"Choose the main trip character for {destination}. Right now, {_trip_direction_primary_label(recommended_primary)} is the strongest starting direction."
    )


def _build_trip_style_selection_rationale(
    *,
    trip_style_planning: TripStylePlanningState,
    configuration: TripConfiguration,
) -> str | None:
    primary = trip_style_planning.selected_primary_direction
    if primary is None:
        return None

    reasons: list[str] = []
    custom_style = (configuration.custom_style or "").strip()
    if configuration.activity_styles:
        reasons.append(
            f"It builds on the intake style signals around {', '.join(configuration.activity_styles[:2]).replace('_', ' ')}."
        )
    if custom_style:
        reasons.append(f'It also keeps the nuance of "{custom_style}".')
    if trip_style_planning.selected_accent:
        reasons.append(
            f"The {_trip_direction_accent_label(trip_style_planning.selected_accent)} accent softens how Wandrix ranks and spaces the later picks."
        )
    if not reasons:
        reasons.append(
            "It gives Wandrix one clear trip character to rank around before the activities branch opens."
        )
    return " ".join(reasons[:3])


def _build_trip_style_downstream_influence_summary(
    *,
    trip_style_planning: TripStylePlanningState,
) -> str | None:
    primary = trip_style_planning.selected_primary_direction
    if primary is None:
        return None
    primary_effects = {
        "food_led": "Activities will now prioritize markets, tastings, dining neighborhoods, and culinary events first.",
        "culture_led": "Activities will now prioritize museums, temples, galleries, heritage walks, and performances first.",
        "nightlife_led": "Activities will now prioritize evening districts, late events, bars, and live music first.",
        "outdoors_led": "Activities will now prioritize parks, viewpoints, open-air routes, hikes, and day trips first.",
        "balanced": "Activities will now stay broadly mixed and avoid overcommitting too early to one kind of day.",
    }
    accent_effects = {
        "local": "The accent will pull the shortlist toward neighborhood-scale, less tourist-first picks.",
        "classic": "The accent will keep first-time and iconic anchors visible early.",
        "polished": "The accent will boost refined, design-forward, and reservation-worthy options.",
        "romantic": "The accent will boost scenic, intimate, and couple-friendly choices.",
        "relaxed": "The accent will keep the shortlist a little lighter and lower-friction.",
    }
    parts = [primary_effects[primary]]
    if trip_style_planning.selected_accent:
        parts.append(accent_effects[trip_style_planning.selected_accent])
    return " ".join(parts)


def _build_trip_style_pace_rationale(
    *,
    trip_style_planning: TripStylePlanningState,
    configuration: TripConfiguration,
) -> str | None:
    pace = trip_style_planning.selected_pace
    if pace is None:
        recommended = (
            trip_style_planning.recommended_paces[0]
            if trip_style_planning.recommended_paces
            else "balanced"
        )
        return (
            f"{_trip_pace_label(recommended)} is the strongest starting pace for the current trip context."
        )
    if pace == "slow":
        return "Slow pace keeps the days lower-friction, with more open time and fewer automatic fills."
    if pace == "full":
        return "Full pace fits a trip that wants more coverage and is comfortable using more dayparts."
    if configuration.trip_length:
        return (
            f"Balanced pace gives {configuration.trip_length} enough structure without filling every gap."
        )
    return "Balanced pace keeps two main moments in view most days while leaving room to adjust."


def _build_trip_style_pace_downstream_influence_summary(
    *,
    trip_style_planning: TripStylePlanningState,
) -> str | None:
    pace = trip_style_planning.selected_pace
    if pace is None:
        return None
    return {
        "slow": "Activities will auto-place fewer flexible ideas per day and keep lower-priority maybes in reserve first.",
        "balanced": "Activities will usually place up to two flexible moments per day before saving extra ideas for later.",
        "full": "Activities can use more dayparts, up to three flexible moments per day, while fixed events stay locked.",
    }[pace]


def _build_trip_style_completion_summary(
    *,
    trip_style_planning: TripStylePlanningState,
) -> str | None:
    primary = trip_style_planning.selected_primary_direction
    if primary is None:
        return None
    pace_line = (
        f" at a {_trip_pace_label(trip_style_planning.selected_pace).lower()} pace"
        if trip_style_planning.selected_pace
        else ""
    )
    accent_line = (
        f" with a {_trip_direction_accent_label(trip_style_planning.selected_accent)} accent"
        if trip_style_planning.selected_accent
        else ""
    )
    return (
        f"The trip character is now set as {_trip_direction_primary_label(primary)}{accent_line}{pace_line}, so activities can rank and space the days around it next."
    )


def _trip_pace_label(pace: PlannerTripPace | None) -> str:
    if pace is None:
        return "Balanced"
    return {
        "slow": "Slow",
        "balanced": "Balanced",
        "full": "Full",
    }[pace]


def _trip_direction_primary_label(primary: PlannerTripDirectionPrimary) -> str:
    return {
        "food_led": "food-led",
        "culture_led": "culture-led",
        "nightlife_led": "nightlife-led",
        "outdoors_led": "outdoors-led",
        "balanced": "balanced",
    }[primary]


def _trip_direction_accent_label(accent: PlannerTripDirectionAccent) -> str:
    return {
        "local": "local",
        "classic": "classic",
        "polished": "polished",
        "romantic": "romantic",
        "relaxed": "relaxed",
    }[accent]


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
    if action and action.type == "confirm_trip_style_direction":
        selected_primary = action.trip_style_direction_primary or "balanced"
        selection_key = (
            "trip style direction confirmed",
            (
                selected_primary,
                action.trip_style_direction_accent or "none",
            ),
        )
        if selection_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Trip style direction confirmed",
                    description="The user confirmed the working trip character for Advanced Planning.",
                    options=["trip_style_direction"],
                    selected_option=selected_primary or "balanced",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
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
    if llm_update.requested_stay_option_title and not action:
        stay_selection_key = " ".join(
            llm_update.requested_stay_option_title.strip().lower().split()
        )
        selection_key = ("stay strategy selected", (stay_selection_key,))
        if stay_selection_key not in existing_stay_selections:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Stay strategy selected",
                    description="The user switched the working stay direction in chat.",
                    options=["working_stay_direction"],
                    selected_option=stay_selection_key,
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
            existing_stay_selections.add(stay_selection_key)
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
        llm_update.requested_stay_hotel_name
        and not action
    ):
        hotel_selection_key = _normalize_hotel_name(llm_update.requested_stay_hotel_name)
        selection_key = ("stay hotel selected", (hotel_selection_key,))
        if hotel_selection_key not in existing_hotel_selections:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Stay hotel selected",
                    description=(
                        "The user chose a working hotel inside the selected stay direction in chat."
                    ),
                    options=["working_hotel_choice"],
                    selected_option=hotel_selection_key,
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
            seen.add(selection_key)
            existing_hotel_selections.add(hotel_selection_key)
    if action and action.type == "keep_current_stay_choice":
        merged.append(
            ConversationDecisionEvent(
                id=action.action_id,
                title="Stay review resolved",
                description="The user kept the current stay direction despite the review warning.",
                options=["keep_current_stay_choice"],
                selected_option="keep_current_stay_choice",
                source_turn_id=turn_id,
                resolved_at=now,
            )
        )
    if action and action.type == "keep_current_hotel_choice":
        merged.append(
            ConversationDecisionEvent(
                id=action.action_id,
                title="Hotel review resolved",
                description="The user kept the current hotel despite the review warning.",
                options=["keep_current_hotel_choice"],
                selected_option="keep_current_hotel_choice",
                source_turn_id=turn_id,
                resolved_at=now,
            )
        )
    if llm_update.requested_review_resolutions and not action:
        for resolution in llm_update.requested_review_resolutions:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title=f"{resolution.scope.title()} review resolved",
                    description=(
                        f"The user kept the current {resolution.scope} choice in chat despite the review warning."
                    ),
                    options=[f"keep_current_{resolution.scope}_choice"],
                    selected_option=f"keep_current_{resolution.scope}_choice",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
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
    if (
        llm_update.requested_trip_style_direction_updates
        and not action
        and planning_mode == "advanced"
    ):
        if any(update.action in {"confirm", "keep_current"} for update in llm_update.requested_trip_style_direction_updates):
            selected_primary = next(
                (
                    update.primary
                    for update in llm_update.requested_trip_style_direction_updates
                    if update.primary is not None
                ),
                "balanced",
            )
            selection_key = ("trip style direction confirmed", (selected_primary,))
            if selection_key not in seen:
                merged.append(
                    ConversationDecisionEvent(
                        id=f"decision_{uuid4().hex[:10]}",
                        title="Trip style direction confirmed",
                        description="The user confirmed the working trip character in chat.",
                        options=["trip_style_direction"],
                        selected_option=selected_primary,
                        source_turn_id=turn_id,
                        resolved_at=now,
                    )
                )
                seen.add(selection_key)
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
