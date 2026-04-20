from datetime import date

from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_planning import TripModuleSelection

from app.graph.planner.turn_models import TripTurnUpdate


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

    parsed_start_date = _parse_optional_date(action.start_date)
    if parsed_start_date:
        merged_update.start_date = parsed_start_date
        _mark_confirmed(merged_update, "start_date")

    parsed_end_date = _parse_optional_date(action.end_date)
    if parsed_end_date:
        merged_update.end_date = parsed_end_date
        _mark_confirmed(merged_update, "end_date")

    if action.adults is not None:
        merged_update.adults = action.adults
        _mark_confirmed(merged_update, "adults")

    if action.children is not None:
        merged_update.children = action.children
        _mark_confirmed(merged_update, "children")

    if action.activity_styles:
        merged_update.activity_styles = list(dict.fromkeys(action.activity_styles))
        _mark_confirmed(merged_update, "activity_styles")

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


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
