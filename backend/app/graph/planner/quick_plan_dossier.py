from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_context import build_quick_plan_conversation_context
from app.graph.planner.quick_plan_dates import QuickPlanWorkingDateDecision
from app.graph.planner.turn_models import TripTurnUpdate
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    ConversationFieldMemory,
    TripConversationState,
    TripFieldKey,
)
from app.schemas.trip_planning import PlanningModuleKey, TripConfiguration


QuickPlanModuleScopeSource = Literal[
    "default_full_trip",
    "user_explicit",
    "board_action",
]

_MODULE_ORDER: tuple[PlanningModuleKey, ...] = (
    "flights",
    "hotels",
    "activities",
    "weather",
)


class QuickPlanReadiness(BaseModel):
    ready: bool
    allowed_modules: list[PlanningModuleKey] = Field(default_factory=list)
    blocked_modules: dict[PlanningModuleKey, list[str]] = Field(default_factory=dict)
    missing_requirements: list[str] = Field(default_factory=list)
    next_question: dict[str, Any] | None = None
    module_scope_source: QuickPlanModuleScopeSource = "default_full_trip"


class QuickPlanDossier(BaseModel):
    readiness: QuickPlanReadiness
    trip_configuration: dict[str, Any]
    module_scope: dict[str, Any]
    module_scope_source: QuickPlanModuleScopeSource
    recent_raw_messages: list[dict[str, Any]] = Field(default_factory=list)
    compact_memory: dict[str, Any] = Field(default_factory=dict)
    decision_history: list[dict[str, Any]] = Field(default_factory=list)
    active_goals: list[str] = Field(default_factory=list)
    mentioned_options: list[dict[str, Any]] = Field(default_factory=list)
    rejected_options: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    field_readiness: dict[str, Any] = Field(default_factory=dict)


def evaluate_quick_plan_readiness(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    brief_confirmed: bool,
    planning_mode: str | None,
    board_action: dict,
) -> dict[str, Any]:
    module_scope_source = _resolve_module_scope_source(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
    )
    destination_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="to_location",
        brief_confirmed=brief_confirmed,
    )
    origin_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="from_location",
        brief_confirmed=brief_confirmed,
    )
    origin_flexibility_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="from_location_flexible",
        brief_confirmed=brief_confirmed,
    )
    timing_snapshots = [
        _projected_field_snapshot(
            current_conversation=current_conversation,
            llm_update=llm_update,
            configuration=configuration,
            field=field,
            brief_confirmed=brief_confirmed,
        )
        for field in ["start_date", "end_date", "travel_window", "trip_length"]
    ]
    adults_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="adults",
        brief_confirmed=brief_confirmed,
    )
    traveler_flexibility_snapshot = _projected_field_snapshot(
        current_conversation=current_conversation,
        llm_update=llm_update,
        configuration=configuration,
        field="travelers_flexible",
        brief_confirmed=brief_confirmed,
    )

    destination_ready = _is_destination_ready(destination_snapshot)
    timing_ready = _is_timing_ready(timing_snapshots)
    origin_ready = _is_origin_ready(
        origin_snapshot,
        origin_flexibility_snapshot=origin_flexibility_snapshot,
    )
    traveler_ready = _is_traveler_ready(adults_snapshot)

    reliability_blockers: list[dict[str, Any]] = []
    missing_requirements: list[str] = []
    if not brief_confirmed:
        base_reasons = ["trip brief is not confirmed yet"]
        missing_requirements.append("confirmed_trip_brief")
    elif planning_mode != "quick":
        base_reasons = ["quick planning is not active"]
        missing_requirements.append("quick_plan_selection")
    elif not destination_ready:
        base_reasons = ["destination is required"]
        missing_requirements.append("destination")
        reliability_blockers.append(
            _provider_reliability_blocker(
                category="destination",
                field="to_location",
                reason=base_reasons[0],
                snapshot=destination_snapshot,
            )
        )
    elif not timing_ready:
        base_reasons = ["exact or assistant-derived working dates are required"]
        missing_requirements.append("working_dates")
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

    allowed_modules: list[PlanningModuleKey] = []
    blocked_modules: dict[PlanningModuleKey, list[str]] = {}
    selected_modules = configuration.selected_modules.model_dump(mode="json")
    for module_name in _MODULE_ORDER:
        if not selected_modules.get(module_name):
            continue

        blockers = list(base_reasons)
        if not blockers and module_name == "flights" and not origin_ready:
            blockers.append(_origin_blocker_reason(origin_snapshot))
            missing_requirements.append("origin")
            reliability_blockers.append(
                _provider_reliability_blocker(
                    category="origin",
                    field="from_location",
                    reason=blockers[0],
                    snapshot=origin_snapshot,
                )
            )
        if not blockers and module_name in {"flights", "hotels"} and not traveler_ready:
            blockers.append(
                "adult traveler count is required when flights or hotels are included"
            )
            missing_requirements.append("adult_traveler_count")
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

    missing_requirements = list(dict.fromkeys(missing_requirements))
    readiness = QuickPlanReadiness(
        ready=bool(allowed_modules) and not blocked_modules and not base_reasons,
        allowed_modules=allowed_modules,
        blocked_modules=blocked_modules,
        missing_requirements=missing_requirements,
        next_question=_next_provider_reliability_question(reliability_blockers),
        module_scope_source=module_scope_source,
    )

    return {
        "brief_confirmed": brief_confirmed,
        "planning_mode": planning_mode,
        "scope_explicit": module_scope_source != "default_full_trip",
        "module_scope_source": module_scope_source,
        "destination_ready": destination_ready,
        "timing_ready": timing_ready,
        "origin_ready": origin_ready,
        "traveler_ready": traveler_ready,
        "quick_plan_ready": readiness.ready,
        "allowed_modules": readiness.allowed_modules,
        "blocked_modules": readiness.blocked_modules,
        "missing_requirements": readiness.missing_requirements,
        "quick_plan_readiness": readiness.model_dump(mode="json"),
        "reliability_blockers": _dedupe_provider_reliability_blockers(
            reliability_blockers
        ),
        "next_reliability_question": readiness.next_question,
        "field_readiness": {
            "destination": destination_snapshot,
            "origin": origin_snapshot,
            "origin_flexibility": origin_flexibility_snapshot,
            "travellers": adults_snapshot,
            "traveller_flexibility": traveler_flexibility_snapshot,
            "timing": timing_snapshots,
        },
    }


def build_quick_plan_dossier(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    readiness: QuickPlanReadiness,
    provider_activation: dict[str, Any],
    raw_messages: list[dict[str, Any]],
    user_input: str,
    board_action: dict,
    working_date_decision: QuickPlanWorkingDateDecision | None = None,
) -> QuickPlanDossier:
    if not readiness.ready:
        raise ValueError("QuickPlanDossier can only be built after readiness passes.")

    module_scope_source = readiness.module_scope_source
    assumptions: list[dict[str, Any]] = []
    if working_date_decision is not None:
        assumptions.append(
            {
                "type": "assistant_chosen_working_dates",
                "start_date": working_date_decision.start_date.isoformat(),
                "end_date": working_date_decision.end_date.isoformat(),
                "confidence": working_date_decision.confidence,
                "rationale": working_date_decision.rationale,
            }
        )

    return QuickPlanDossier(
        readiness=readiness,
        trip_configuration={
            "confirmed_or_derived": configuration.model_dump(mode="json"),
            "field_readiness": provider_activation.get("field_readiness", {}),
        },
        module_scope={
            "modules": configuration.selected_modules.model_dump(mode="json"),
            "allowed_modules": readiness.allowed_modules,
            "blocked_modules": readiness.blocked_modules,
        },
        module_scope_source=module_scope_source,
        recent_raw_messages=_build_recent_raw_messages(
            raw_messages=raw_messages,
            user_input=user_input,
            board_action=board_action,
        ),
        compact_memory=build_quick_plan_conversation_context(current_conversation),
        decision_history=_build_decision_history(current_conversation),
        active_goals=list(
            dict.fromkeys([*current_conversation.active_goals, *llm_update.active_goals])
        )[:10],
        mentioned_options=[
            option.model_dump(mode="json")
            for option in current_conversation.memory.mentioned_options[-10:]
        ],
        rejected_options=[
            option.model_dump(mode="json")
            for option in current_conversation.memory.rejected_options[-10:]
        ],
        assumptions=assumptions,
        field_readiness=provider_activation.get("field_readiness", {}),
    )


def _resolve_module_scope_source(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
) -> QuickPlanModuleScopeSource:
    source_by_field = {item.field: item.source for item in llm_update.field_sources}
    if source_by_field.get("selected_modules") == "board_action":
        return "board_action"
    if _has_selected_module_changes(llm_update) or "selected_modules" in {
        *llm_update.confirmed_fields,
        *llm_update.inferred_fields,
    }:
        return "user_explicit"

    memory = current_conversation.memory.field_memory.get("selected_modules")
    module_value = configuration.selected_modules.model_dump(mode="json")
    if memory is not None and memory.value == module_value:
        if memory.source == "board_action":
            return "board_action"
        return "user_explicit"

    if configuration.selected_modules != TripConfiguration().selected_modules:
        return "user_explicit"
    return "default_full_trip"


def _has_selected_module_changes(llm_update: TripTurnUpdate) -> bool:
    return any(
        getattr(llm_update.selected_modules, field_name) is not None
        for field_name in ("flights", "weather", "activities", "hotels")
    )


def _projected_field_snapshot(
    *,
    current_conversation: TripConversationState,
    llm_update: TripTurnUpdate,
    configuration: TripConfiguration,
    field: TripFieldKey,
    brief_confirmed: bool = False,
) -> dict[str, Any]:
    source_by_field = {item.field: item.source for item in llm_update.field_sources}
    confidence_by_field = {
        item.field: item.confidence for item in llm_update.field_confidences
    }
    value = _get_configuration_value(configuration, field)
    memory = current_conversation.memory.field_memory.get(field)

    source = source_by_field.get(field)
    if source is None and _memory_matches(memory, value):
        source = memory.source

    confidence_level = confidence_by_field.get(field)
    if confidence_level is None and _memory_matches(memory, value):
        confidence_level = memory.confidence_level

    has_value = _snapshot_value_has_signal(field, value)
    if brief_confirmed and has_value and source is None:
        source = "confirmed_brief"
        confidence_level = confidence_level or "high"

    return {
        "field": field,
        "has_value": has_value,
        "value": value,
        "source": source,
        "confidence_level": confidence_level,
    }


def _memory_matches(memory: ConversationFieldMemory | None, value: Any) -> bool:
    return memory is not None and memory.value == value


def _get_configuration_value(configuration: TripConfiguration, field: TripFieldKey):
    if field == "adults":
        return configuration.travelers.adults
    if field == "children":
        return configuration.travelers.children
    if field == "activity_styles":
        return configuration.activity_styles
    if field == "selected_modules":
        return configuration.selected_modules.model_dump(mode="json")
    return getattr(configuration, field)


def _snapshot_value_has_signal(field: TripFieldKey, value: object | None) -> bool:
    if field == "adults":
        return isinstance(value, int) and value > 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return value is not None


def _is_destination_ready(snapshot: dict[str, Any]) -> bool:
    if not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "confirmed_brief":
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {
        "medium",
        "high",
    }:
        return True
    return False


def _is_origin_ready(
    snapshot: dict[str, Any],
    *,
    origin_flexibility_snapshot: dict[str, Any] | None = None,
) -> bool:
    if (
        origin_flexibility_snapshot
        and origin_flexibility_snapshot.get("value") is True
    ):
        return False
    if not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "confirmed_brief":
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {
        "medium",
        "high",
    }:
        return True
    return False


def _is_timing_ready(snapshots: list[dict[str, Any]]) -> bool:
    by_field = {snapshot["field"]: snapshot for snapshot in snapshots}
    return _exact_date_snapshot_ready(
        by_field.get("start_date")
    ) and _exact_date_snapshot_ready(by_field.get("end_date"))


def _exact_date_snapshot_ready(snapshot: dict[str, Any] | None) -> bool:
    if not snapshot or not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "confirmed_brief":
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {
        "medium",
        "high",
    }:
        return True
    if snapshot["source"] == "assistant_derived" and snapshot["confidence_level"] in {
        "medium",
        "high",
    }:
        return True
    return False


def _is_traveler_ready(snapshot: dict[str, Any]) -> bool:
    if not snapshot["has_value"]:
        return False
    if snapshot["source"] in {"user_explicit", "board_action"}:
        return True
    if snapshot["source"] == "confirmed_brief":
        return True
    if snapshot["source"] == "user_inferred" and snapshot["confidence_level"] in {
        "medium",
        "high",
    }:
        return True
    return False


def _best_timing_snapshot(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    for field in ["start_date", "travel_window", "trip_length", "end_date"]:
        for snapshot in snapshots:
            if snapshot["field"] == field and snapshot["has_value"]:
                return snapshot
    return snapshots[0] if snapshots else {"field": "travel_window"}


def _provider_reliability_blocker(
    *,
    category: str,
    field: TripFieldKey,
    reason: str,
    snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "category": category,
        "field": field,
        "reason": reason,
        "source": snapshot.get("source") if snapshot else None,
        "confidence_level": snapshot.get("confidence_level") if snapshot else None,
        "has_value": bool(snapshot.get("has_value")) if snapshot else False,
        "value": snapshot.get("value") if snapshot else None,
    }


def _dedupe_provider_reliability_blockers(
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for blocker in blockers:
        key = (blocker["category"], blocker["reason"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(blocker)
    return deduped


def _next_provider_reliability_question(
    blockers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for blocker in _dedupe_provider_reliability_blockers(blockers):
        question = _provider_reliability_question(blocker)
        if question:
            return question
    return None


def _provider_reliability_question(blocker: dict[str, Any]) -> dict[str, Any] | None:
    category = blocker.get("category")
    if category == "destination":
        return {
            "question": "Which destination should I use for the Quick Plan?",
            "field": "to_location",
            "step": "route",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    if category == "timing":
        return {
            "question": "Should I use these working dates for the Quick Plan?",
            "field": blocker.get("field") or "travel_window",
            "step": "timing",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    if category == "origin":
        value = blocker.get("value")
        question = (
            f"Should I use {value} as the flight origin?"
            if value
            else "Where should I search flights from?"
        )
        return {
            "question": question,
            "field": "from_location",
            "step": "route",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    if category == "travellers":
        return {
            "question": "How many adult travelers should I use for flights and stays?",
            "field": "adults",
            "step": "travellers",
            "priority": 1,
            "why": _provider_reliability_question_reason(blocker),
        }
    return None


def _origin_blocker_reason(snapshot: dict[str, Any]) -> str:
    if snapshot.get("has_value"):
        return "flight origin needs confirmation before flights are included"
    return "origin is required when flights are included"


def _provider_reliability_question_reason(blocker: dict[str, Any]) -> str:
    if not blocker.get("has_value"):
        return "Quick Plan needs this before Wandrix can generate a complete logistics-aware draft."
    source = blocker.get("source")
    confidence = blocker.get("confidence_level")
    if source == "profile_default":
        return "This currently comes from profile memory, so Wandrix needs trip-specific confirmation before live checks."
    if confidence == "low":
        return "This is only a low-confidence working assumption, so Wandrix should confirm it before live checks."
    return "This detail is still provisional, so Wandrix should confirm it before live checks."


def _build_recent_raw_messages(
    *,
    raw_messages: list[dict[str, Any]],
    user_input: str,
    board_action: dict,
) -> list[dict[str, Any]]:
    messages = list(raw_messages[-8:])
    if user_input.strip():
        messages.append({"role": "user", "content": user_input.strip()})
    elif board_action:
        try:
            action = ConversationBoardAction.model_validate(board_action)
            messages.append(
                {
                    "role": "system",
                    "content": f"Board action: {action.type}",
                }
            )
        except Exception:
            messages.append({"role": "system", "content": "Board action received."})
    return messages[-9:]


def _build_decision_history(
    conversation: TripConversationState,
) -> list[dict[str, Any]]:
    return [
        decision.model_dump(mode="json")
        for decision in conversation.memory.decision_history[-8:]
    ]
