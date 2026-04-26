from __future__ import annotations

from typing import Any

from app.graph.planner.turn_models import QuickPlanDraft
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


_QUICK_PLAN_FIELDS = {
    "from_location",
    "to_location",
    "start_date",
    "end_date",
    "travel_window",
    "trip_length",
    "adults",
    "children",
    "budget_posture",
    "budget_amount",
    "budget_currency",
    "activity_styles",
    "custom_style",
    "selected_modules",
    "weather_preference",
}


def build_quick_plan_conversation_context(
    conversation: TripConversationState,
) -> dict:
    """Return the compact planning context needed by Quick Plan LLM calls."""

    field_memory = {}
    for field, memory in conversation.memory.field_memory.items():
        if field not in _QUICK_PLAN_FIELDS:
            continue
        field_memory[field] = {
            "value": memory.value,
            "source": memory.source,
            "confidence_level": memory.confidence_level,
        }

    turn_summaries = [
        {
            "summary_text": summary.summary_text,
            "active_goal": summary.active_goal,
            "changed_fields": summary.changed_fields,
            "open_fields": summary.open_fields,
        }
        for summary in conversation.memory.turn_summaries[-4:]
    ]

    decision_memory = [
        {
            "key": decision.key,
            "status": decision.status,
            "value_summary": decision.value_summary,
            "confidence": decision.confidence,
        }
        for decision in conversation.memory.decision_memory[-8:]
    ]

    return {
        "phase": conversation.phase,
        "planning_mode": conversation.planning_mode,
        "planning_mode_status": conversation.planning_mode_status,
        "active_goals": conversation.active_goals[:8],
        "last_turn_summary": conversation.last_turn_summary,
        "field_memory": field_memory,
        "turn_summaries": turn_summaries,
        "decision_memory": decision_memory,
    }


def build_quick_plan_generation_context(
    *,
    conversation: TripConversationState,
    dossier: Any | None,
) -> dict:
    if dossier is None:
        return {"compact_memory": build_quick_plan_conversation_context(conversation)}
    return {
        "readiness": {
            "allowed_modules": dossier.readiness.allowed_modules,
            "module_scope_source": dossier.readiness.module_scope_source,
            "missing_requirements": dossier.readiness.missing_requirements,
        },
        "assumptions": dossier.assumptions,
        "compact_memory": dossier.compact_memory,
        "active_goals": dossier.active_goals[:8],
        "decision_history": dossier.decision_history[-8:],
        "mentioned_options": dossier.mentioned_options[-8:],
        "rejected_options": dossier.rejected_options[-8:],
        "recent_raw_messages": dossier.recent_raw_messages[-6:],
    }


def build_quick_plan_configuration_payload(configuration: TripConfiguration) -> dict:
    return {
        "from_location": configuration.from_location,
        "to_location": configuration.to_location,
        "start_date": configuration.start_date.isoformat()
        if configuration.start_date
        else None,
        "end_date": configuration.end_date.isoformat()
        if configuration.end_date
        else None,
        "travel_window": configuration.travel_window,
        "trip_length": configuration.trip_length,
        "travelers": configuration.travelers.model_dump(mode="json"),
        "budget_posture": configuration.budget_posture,
        "budget_amount": configuration.budget_amount,
        "budget_currency": configuration.budget_currency,
        "selected_modules": configuration.selected_modules.model_dump(mode="json"),
        "activity_styles": configuration.activity_styles,
        "custom_style": configuration.custom_style,
        "weather_preference": configuration.weather_preference,
    }


def build_quick_plan_module_payload(module_outputs: TripModuleOutputs) -> dict:
    return {
        "flights": [
            flight.model_dump(
                mode="json",
                include={
                    "id",
                    "direction",
                    "carrier",
                    "flight_number",
                    "departure_airport",
                    "arrival_airport",
                    "departure_time",
                    "arrival_time",
                    "duration_text",
                    "price_text",
                    "fare_amount",
                    "fare_currency",
                    "stop_count",
                    "layover_summary",
                    "timing_quality",
                    "inventory_notice",
                    "notes",
                },
            )
            for flight in module_outputs.flights[:4]
        ],
        "hotels": [
            hotel.model_dump(
                mode="json",
                include={
                    "id",
                    "hotel_name",
                    "area",
                    "address",
                    "nightly_rate_amount",
                    "nightly_rate_currency",
                    "check_in",
                    "check_out",
                    "notes",
                    "source_label",
                },
            )
            for hotel in module_outputs.hotels[:4]
        ],
        "activities": [
            activity.model_dump(
                mode="json",
                include={
                    "id",
                    "title",
                    "category",
                    "day_label",
                    "time_label",
                    "start_at",
                    "end_at",
                    "location_label",
                    "venue_name",
                    "price_text",
                    "notes",
                    "source_label",
                },
            )
            for activity in module_outputs.activities[:12]
        ],
        "weather": [
            weather.model_dump(mode="json")
            for weather in module_outputs.weather[:7]
        ],
    }


def build_quick_plan_draft_payload(draft: QuickPlanDraft) -> dict:
    return {
        "board_summary": draft.board_summary,
        "timeline_preview": [
            item.model_dump(mode="json") for item in draft.timeline_preview[:16]
        ],
    }
