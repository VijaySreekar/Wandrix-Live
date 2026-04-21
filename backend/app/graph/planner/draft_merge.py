from app.graph.planner.turn_models import TripTurnUpdate
from app.schemas.trip_conversation import TripFieldKey
from app.schemas.trip_planning import TripConfiguration


def merge_trip_configuration(
    current: TripConfiguration,
    llm_update: TripTurnUpdate,
) -> TripConfiguration:
    configuration = current.model_copy(deep=True)

    if llm_update.from_location and _should_apply_field(
        field="from_location",
        llm_update=llm_update,
        current_value=configuration.from_location,
        next_value=llm_update.from_location,
    ):
        configuration.from_location = llm_update.from_location

    if llm_update.to_location and _should_apply_field(
        field="to_location",
        llm_update=llm_update,
        current_value=configuration.to_location,
        next_value=llm_update.to_location,
    ):
        configuration.to_location = llm_update.to_location

    if llm_update.travel_window and _should_apply_field(
        field="travel_window",
        llm_update=llm_update,
        current_value=configuration.travel_window,
        next_value=llm_update.travel_window,
    ):
        configuration.travel_window = llm_update.travel_window

    if llm_update.trip_length and _should_apply_field(
        field="trip_length",
        llm_update=llm_update,
        current_value=configuration.trip_length,
        next_value=llm_update.trip_length,
    ):
        configuration.trip_length = llm_update.trip_length

    if _should_clear_exact_timing_field(
        exact_field="start_date",
        rough_field="travel_window",
        llm_update=llm_update,
    ):
        configuration.start_date = None

    if _should_clear_exact_timing_field(
        exact_field="end_date",
        rough_field="trip_length",
        llm_update=llm_update,
    ):
        configuration.end_date = None

    if llm_update.start_date and _should_apply_exact_timing_field(
        field="start_date",
        rough_field="travel_window",
        llm_update=llm_update,
        current_value=configuration.start_date,
        next_value=llm_update.start_date,
        current_rough_value=configuration.travel_window,
    ):
        configuration.start_date = llm_update.start_date
        if _should_clear_rough_timing_field(
            exact_field="start_date",
            rough_field="travel_window",
            llm_update=llm_update,
        ):
            configuration.travel_window = None

    if llm_update.end_date and _should_apply_exact_timing_field(
        field="end_date",
        rough_field="trip_length",
        llm_update=llm_update,
        current_value=configuration.end_date,
        next_value=llm_update.end_date,
        current_rough_value=configuration.trip_length,
    ):
        configuration.end_date = llm_update.end_date
        if _should_clear_rough_timing_field(
            exact_field="end_date",
            rough_field="trip_length",
            llm_update=llm_update,
        ):
            configuration.trip_length = None

    if llm_update.budget_posture and _should_apply_field(
        field="budget_posture",
        llm_update=llm_update,
        current_value=configuration.budget_posture,
        next_value=llm_update.budget_posture,
    ):
        configuration.budget_posture = llm_update.budget_posture

    if llm_update.budget_gbp is not None and _should_apply_field(
        field="budget_gbp",
        llm_update=llm_update,
        current_value=configuration.budget_gbp,
        next_value=llm_update.budget_gbp,
    ):
        configuration.budget_gbp = llm_update.budget_gbp

    if llm_update.adults is not None and _should_apply_field(
        field="adults",
        llm_update=llm_update,
        current_value=configuration.travelers.adults,
        next_value=llm_update.adults,
    ):
        configuration.travelers.adults = llm_update.adults

    if llm_update.children is not None and _should_apply_field(
        field="children",
        llm_update=llm_update,
        current_value=configuration.travelers.children,
        next_value=llm_update.children,
    ):
        configuration.travelers.children = llm_update.children

    if llm_update.activity_styles:
        if (
            "activity_styles" in llm_update.confirmed_fields
            or not configuration.activity_styles
            or configuration.activity_styles == llm_update.activity_styles
        ):
            configuration.activity_styles = list(dict.fromkeys(llm_update.activity_styles))

    if _has_selected_module_changes(llm_update):
        if (
            "selected_modules" in llm_update.confirmed_fields
            or configuration.selected_modules == TripConfiguration().selected_modules
        ):
            for field_name in ("flights", "weather", "activities", "hotels"):
                next_value = getattr(llm_update.selected_modules, field_name)
                if next_value is not None:
                    setattr(configuration.selected_modules, field_name, next_value)

    return configuration


def derive_trip_title(configuration: TripConfiguration) -> str:
    if configuration.to_location:
        return f"{configuration.to_location} trip"
    return "Trip planner"


def _has_selected_module_changes(llm_update: TripTurnUpdate) -> bool:
    return any(
        getattr(llm_update.selected_modules, field_name) is not None
        for field_name in ("flights", "weather", "activities", "hotels")
    )


def _should_apply_field(
    *,
    field: TripFieldKey,
    llm_update: TripTurnUpdate,
    current_value: object | None,
    next_value: object | None,
) -> bool:
    if next_value is None:
        return False

    if field in llm_update.confirmed_fields:
        return True

    if field not in llm_update.inferred_fields:
        return True

    return current_value in (None, "", [], {}) or current_value == next_value


def _should_apply_exact_timing_field(
    *,
    field: TripFieldKey,
    rough_field: TripFieldKey,
    llm_update: TripTurnUpdate,
    current_value: object | None,
    next_value: object | None,
    current_rough_value: object | None,
) -> bool:
    if not _should_apply_field(
        field=field,
        llm_update=llm_update,
        current_value=current_value,
        next_value=next_value,
    ):
        return False

    if field in llm_update.confirmed_fields:
        return True

    if current_rough_value not in (None, "", [], {}):
        return current_value == next_value

    return True


def _should_clear_exact_timing_field(
    *,
    exact_field: TripFieldKey,
    rough_field: TripFieldKey,
    llm_update: TripTurnUpdate,
) -> bool:
    return (
        rough_field in llm_update.confirmed_fields
        and exact_field not in llm_update.confirmed_fields
    )


def _should_clear_rough_timing_field(
    *,
    exact_field: TripFieldKey,
    rough_field: TripFieldKey,
    llm_update: TripTurnUpdate,
) -> bool:
    return (
        exact_field in llm_update.confirmed_fields
        and rough_field not in llm_update.confirmed_fields
    )
