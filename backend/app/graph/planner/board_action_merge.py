from datetime import date

from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import ConversationFieldConfidence
from app.schemas.trip_planning import TripModuleSelection

from app.graph.planner.turn_models import (
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)


def apply_board_action_updates(
    llm_update: TripTurnUpdate,
    *,
    board_action: dict,
) -> TripTurnUpdate:
    if not board_action:
        return llm_update

    action = ConversationBoardAction.model_validate(board_action)
    if action.type == "select_quick_plan":
        merged_update = llm_update.model_copy(deep=True)
        merged_update.requested_planning_mode = "quick"
        return merged_update

    if action.type == "select_advanced_plan":
        merged_update = llm_update.model_copy(deep=True)
        merged_update.requested_planning_mode = "advanced"
        return merged_update

    if action.type == "finalize_quick_plan":
        merged_update = llm_update.model_copy(deep=True)
        merged_update.planner_intent = "confirm_plan"
        return merged_update

    if action.type == "reopen_plan":
        merged_update = llm_update.model_copy(deep=True)
        merged_update.planner_intent = "reopen_plan"
        return merged_update

    if action.type != "confirm_trip_details":
        return llm_update

    merged_update = llm_update.model_copy(deep=True)

    if action.from_location:
        merged_update.from_location = action.from_location.strip()
        _mark_confirmed(merged_update, "from_location")

    if action.to_location:
        merged_update.to_location = action.to_location.strip()
        _mark_confirmed(merged_update, "to_location")

    if action.selected_modules:
        merged_update.selected_modules = action.selected_modules
        _mark_confirmed(merged_update, "selected_modules")

    if action.travel_window:
        merged_update.travel_window = action.travel_window.strip()
        _mark_confirmed(merged_update, "travel_window")

    if action.trip_length:
        merged_update.trip_length = action.trip_length.strip()
        _mark_confirmed(merged_update, "trip_length")

    if action.weather_preference:
        merged_update.weather_preference = action.weather_preference.strip()
        _mark_confirmed(merged_update, "weather_preference")

    parsed_start_date = _parse_optional_date(action.start_date)
    if parsed_start_date:
        merged_update.start_date = parsed_start_date
        _mark_confirmed(merged_update, "start_date")

    parsed_end_date = _parse_optional_date(action.end_date)
    if parsed_end_date:
        merged_update.end_date = parsed_end_date
        _mark_confirmed(merged_update, "end_date")

    if action.adults is not None and action.adults > 0:
        merged_update.adults = action.adults
        _mark_confirmed(merged_update, "adults")

    if action.children is not None and action.children > 0:
        merged_update.children = action.children
        _mark_confirmed(merged_update, "children")

    if action.travelers_flexible is not None:
        merged_update.travelers_flexible = action.travelers_flexible
        _mark_confirmed(merged_update, "travelers_flexible")

    if action.activity_styles:
        merged_update.activity_styles = list(dict.fromkeys(action.activity_styles))
        _mark_confirmed(merged_update, "activity_styles")

    if action.custom_style:
        merged_update.custom_style = action.custom_style.strip()
        _mark_confirmed(merged_update, "custom_style")

    if action.budget_posture:
        merged_update.budget_posture = action.budget_posture
        _mark_confirmed(merged_update, "budget_posture")

    if action.budget_gbp is not None:
        merged_update.budget_gbp = action.budget_gbp
        _mark_confirmed(merged_update, "budget_gbp")

    merged_update.confirmed_trip_brief = True

    return merged_update


def _mark_confirmed(update: TripTurnUpdate, field: str) -> None:
    if field not in update.confirmed_fields:
        update.confirmed_fields.append(field)
    if field in update.inferred_fields:
        update.inferred_fields.remove(field)
    _set_field_confidence(update, field, "high")
    _set_field_source(update, field)


def _set_field_confidence(
    update: TripTurnUpdate,
    field: str,
    confidence: ConversationFieldConfidence,
) -> None:
    for existing in update.field_confidences:
        if existing.field == field:
            existing.confidence = confidence
            return
    update.field_confidences.append(
        TripFieldConfidenceUpdate(field=field, confidence=confidence)
    )


def _set_field_source(update: TripTurnUpdate, field: str) -> None:
    for existing in update.field_sources:
        if existing.field == field:
            existing.source = "board_action"
            return
    update.field_sources.append(
        TripFieldSourceUpdate(field=field, source="board_action")
    )


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
