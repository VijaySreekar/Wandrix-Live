from datetime import datetime
from uuid import uuid4

from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.graph.planner.provider_enrichment import has_any_module_output
from app.graph.planner.suggestion_board import (
    build_default_decision_cards,
    build_destination_mentioned_options,
    build_suggestion_board_state,
)
from app.graph.planner.turn_models import ConversationOptionCandidate, TripTurnUpdate
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    ConversationDecisionEvent,
    ConversationFieldMemory,
    ConversationOptionMemory,
    ConversationQuestion,
    ConversationTurnSummary,
    PlannerDecisionCard,
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
) -> list[str]:
    missing_fields: list[str] = []

    if not configuration.from_location and not (
        resolved_location_context and resolved_location_context.summary
    ):
        missing_fields.append("from_location")
    if not configuration.to_location:
        missing_fields.append("to_location")
    if not configuration.start_date and not configuration.travel_window:
        missing_fields.append("start_date")
    if not configuration.end_date and not configuration.trip_length:
        missing_fields.append("end_date")
    if configuration.travelers.adults is None and configuration.travelers.children is None:
        missing_fields.append("adults")
    if not configuration.activity_styles:
        missing_fields.append("activity_styles")
    if configuration.budget_posture is None and configuration.budget_gbp is None:
        missing_fields.append("budget_posture")

    return missing_fields


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
    record_memory: bool = True,
) -> TripConversationState:
    conversation = current.model_copy(deep=True)
    missing_fields = compute_missing_fields_with_context(
        next_configuration,
        resolved_location_context,
    )
    phase = determine_phase(
        configuration=next_configuration,
        missing_fields=missing_fields,
        module_outputs=module_outputs,
        brief_confirmed=brief_confirmed,
    )

    conversation.phase = phase
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
        else build_last_turn_summary(next_configuration, missing_fields)
    )
    conversation.active_goals = merge_active_goals(current.active_goals, llm_update.active_goals)
    conversation.suggestion_board = build_suggestion_board_state(
        current=conversation,
        configuration=next_configuration,
        phase=phase,
        llm_update=llm_update,
        resolved_location_context=resolved_location_context,
        board_action=board_action or {},
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
) -> TripDraftStatus:
    status = current.model_copy(deep=True)
    status.phase = conversation.phase
    status.missing_fields = compute_missing_fields_with_context(
        configuration,
        resolved_location_context,
    )

    confirmed_fields: list[TripFieldKey] = []
    inferred_fields: list[TripFieldKey] = []
    for field, memory in conversation.memory.field_memory.items():
        if not _field_has_value(configuration, field):
            continue
        if memory.source == "user_explicit":
            confirmed_fields.append(field)
        else:
            inferred_fields.append(field)

    status.confirmed_fields = sorted(set(confirmed_fields))
    status.inferred_fields = sorted(set(field for field in inferred_fields if field not in confirmed_fields))
    status.brochure_ready = conversation.phase == "reviewing" and (
        bool(conversation.memory.turn_summaries) or has_any_module_output(module_outputs)
    )
    status.last_updated_at = now
    return status


def determine_phase(
    *,
    configuration: TripConfiguration,
    missing_fields: list[str],
    module_outputs: TripModuleOutputs,
    brief_confirmed: bool,
) -> str:
    has_route_signal = bool(configuration.from_location or configuration.to_location)
    has_timing_signal = bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )
    has_party_signal = (
        configuration.travelers.adults is not None
        or configuration.travelers.children is not None
    )
    core_shape_ready = bool(configuration.to_location and has_timing_signal)
    provider_ready = bool(configuration.to_location and has_timing_signal)

    if not has_route_signal and not has_timing_signal:
        return "opening"
    if not core_shape_ready or not has_party_signal:
        return "collecting_requirements"
    if missing_fields:
        return "collecting_requirements"
    if not brief_confirmed:
        return "awaiting_confirmation"
    if provider_ready and has_any_module_output(module_outputs):
        return "reviewing" if not missing_fields else "enriching_modules"
    if provider_ready:
        return "enriching_modules"
    return "shaping_trip"


def is_trip_brief_confirmed(
    conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    board_action: dict | None = None,
) -> bool:
    action = ConversationBoardAction.model_validate(board_action) if board_action else None
    if action and action.type == "confirm_trip_brief":
        return True
    if llm_update.confirmed_trip_brief:
        return True
    return any(
        event.title.lower() == "trip brief confirmed"
        for event in conversation.memory.decision_history
    )


def merge_open_questions(
    current_questions: list[ConversationQuestion],
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> list[ConversationQuestion]:
    normalized_existing = {
        question.question.strip().lower(): question
        for question in current_questions
        if question.status == "open"
        and _question_is_still_relevant(question, configuration, missing_fields)
    }
    merged: list[ConversationQuestion] = list(normalized_existing.values())

    for text in [*llm_update.open_questions, *_build_default_open_questions(configuration, missing_fields)]:
        cleaned = text.strip()
        if not cleaned:
            continue
        normalized = cleaned.lower()
        if normalized in normalized_existing:
            continue
        merged.append(
            ConversationQuestion(
                id=f"question_{uuid4().hex[:10]}",
                question=cleaned,
                field=_guess_question_field(cleaned),
                priority=1,
            )
        )
        normalized_existing[normalized] = merged[-1]

    return merged[:3]


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
        if not title or not description:
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
) -> TripConversationMemory:
    memory = current.model_copy(deep=True)

    for field in sorted(set([*llm_update.confirmed_fields, *llm_update.inferred_fields])):
        value = _get_configuration_value(next_configuration, field)
        if value in (None, "", [], {}):
            continue
        source = "user_explicit" if field in llm_update.confirmed_fields else "user_inferred"
        previous_entry = memory.field_memory.get(field)
        memory.field_memory[field] = ConversationFieldMemory(
            field=field,
            value=value,
            confidence=1.0 if source == "user_explicit" else 0.65,
            source=source,
            source_turn_id=turn_id,
            first_seen_at=previous_entry.first_seen_at if previous_entry else now,
            last_seen_at=now,
        )

        previous_value = _get_configuration_value(previous_configuration, field)
        if (
            previous_value not in (None, "", [], {})
            and previous_value != value
            and source == "user_explicit"
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
    memory.decision_history = _merge_decision_history(
        current=memory.decision_history,
        decision_cards=decision_cards,
        llm_update=llm_update,
        turn_id=turn_id,
        now=now,
        board_action=board_action,
    )
    memory.turn_summaries = _merge_turn_summaries(
        current=memory.turn_summaries,
        turn_id=turn_id,
        user_message=user_message,
        assistant_message=assistant_response,
        changed_fields=sorted(set([*llm_update.confirmed_fields, *llm_update.inferred_fields])),
        phase=phase,
        now=now,
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


def build_last_turn_summary(
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> str:
    destination = configuration.to_location or "the destination"
    if missing_fields:
        return f"The trip is leaning toward {destination}, but key planning details are still open."
    return f"The trip shape is stable enough to start building around {destination}."


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


def _merge_decision_history(
    *,
    current: list[ConversationDecisionEvent],
    decision_cards: list[PlannerDecisionCard],
    llm_update: TripTurnUpdate,
    turn_id: str,
    now: datetime,
    board_action: dict,
) -> list[ConversationDecisionEvent]:
    merged = list(current)
    seen = {
        (item.title.lower(), tuple(option.lower() for option in item.options))
        for item in merged
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
    if action and action.type == "confirm_trip_brief":
        confirmation_key = ("trip brief confirmed", tuple())
        if confirmation_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=action.action_id,
                    title="Trip brief confirmed",
                    description="The user confirmed the full working trip brief.",
                    options=[],
                    selected_option="confirm_trip_brief",
                    source_turn_id=turn_id,
                    resolved_at=now,
                )
            )
    elif llm_update.confirmed_trip_brief:
        confirmation_key = ("trip brief confirmed", tuple())
        if confirmation_key not in seen:
            merged.append(
                ConversationDecisionEvent(
                    id=f"decision_{uuid4().hex[:10]}",
                    title="Trip brief confirmed",
                    description="The user confirmed the full working trip brief in chat.",
                    options=[],
                    selected_option="confirm_trip_brief",
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
    phase: str,
    now: datetime,
) -> list[ConversationTurnSummary]:
    merged = list(current)
    merged.append(
        ConversationTurnSummary(
            turn_id=turn_id,
            user_message=user_message.strip(),
            assistant_message=assistant_message.strip(),
            changed_fields=changed_fields,
            resulting_phase=phase,
            created_at=now,
        )
    )
    return merged[-10:]


def _build_default_open_questions(
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> list[str]:
    questions: dict[str, str] = {
        "from_location": "Where would you be travelling from for this trip?",
        "to_location": "Which destination should I shape this trip around?",
        "start_date": "What month or travel window are you considering?",
        "end_date": (
            "How long should this trip be?"
            if configuration.start_date or configuration.travel_window
            else "Roughly how many days or nights should I plan around?"
        ),
        "adults": "How many people should I plan for?",
        "activity_styles": "What kind of trip do you want this to feel like?",
        "budget_posture": "Should I keep this budget, mid-range, or premium?",
    }
    return [questions[field] for field in missing_fields if field in questions]


def _guess_question_field(question: str) -> TripFieldKey | None:
    normalized = question.lower()
    if "from" in normalized or "travelling from" in normalized:
        return "from_location"
    if "destination" in normalized or "trip around" in normalized:
        return "to_location"
    if "month" in normalized or "window" in normalized:
        return "travel_window"
    if "days" in normalized or "nights" in normalized or "long" in normalized:
        return "trip_length"
    if "people" in normalized:
        return "adults"
    if "budget" in normalized or "premium" in normalized:
        return "budget_posture"
    return None


def _field_has_value(configuration: TripConfiguration, field: TripFieldKey) -> bool:
    value = _get_configuration_value(configuration, field)
    return value not in (None, "", [], {})


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


def _field_to_option_candidate(field: TripFieldKey, value: object) -> ConversationOptionCandidate | None:
    if field == "to_location" and isinstance(value, str):
        return ConversationOptionCandidate(kind="destination", value=value)
    if field == "from_location" and isinstance(value, str):
        return ConversationOptionCandidate(kind="origin", value=value)
    if field in {"start_date", "travel_window"}:
        return ConversationOptionCandidate(kind="timing_window", value=str(value))
    if field in {"end_date", "trip_length"}:
        return ConversationOptionCandidate(kind="trip_length", value=str(value))
    if field == "budget_posture":
        return ConversationOptionCandidate(kind="budget_posture", value=str(value))
    return None


def _question_is_still_relevant(
    question: ConversationQuestion,
    configuration: TripConfiguration,
    missing_fields: list[str],
) -> bool:
    if question.field is None:
        return True

    if question.field == "from_location":
        return "from_location" in missing_fields
    if question.field == "to_location":
        return "to_location" in missing_fields
    if question.field in {"start_date", "travel_window"}:
        return "start_date" in missing_fields
    if question.field in {"end_date", "trip_length"}:
        return "end_date" in missing_fields
    if question.field == "adults":
        return "adults" in missing_fields
    if question.field == "budget_posture":
        return configuration.budget_posture is None

    return True
