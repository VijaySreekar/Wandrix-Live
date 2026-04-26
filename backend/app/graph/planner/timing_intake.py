from app.schemas.trip_conversation import (
    PlannerChecklistItem,
    TripDetailsCollectionFormState,
    TripSuggestionBoardState,
)
from app.schemas.trip_planning import TripConfiguration
from app.graph.planner.turn_models import TripTurnUpdate


_EMPTY_TRAVEL_WINDOW_MARKERS = (
    "dates open",
    "dates are open",
    "dates still open",
    "dates can come later",
    "timing open",
    "timing is open",
    "timing still open",
    "no month picked",
    "no month chosen",
    "month not picked",
    "month not chosen",
    "when next",
)
_EMPTY_TRIP_LENGTH_MARKERS = (
    "length tbd",
    "duration tbd",
    "length undecided",
    "duration undecided",
    "length still open",
    "duration still open",
    "not sure how many days",
    "not sure how many nights",
)
_TRIP_LENGTH_SIGNALS = (
    "day",
    "night",
    "week",
    "weekend",
    "break",
    "city break",
    "short trip",
    "long trip",
)


def should_show_timing_choice(
    *,
    configuration: TripConfiguration,
    brief_confirmed: bool,
    planning_mode: str | None,
) -> bool:
    if brief_confirmed or planning_mode is not None:
        return False
    if not configuration.to_location:
        return False
    if configuration.start_date and configuration.end_date:
        return False
    return not (configuration.travel_window and configuration.trip_length)


def sanitize_timing_update(llm_update: TripTurnUpdate) -> TripTurnUpdate:
    cleaned_update = llm_update.model_copy(deep=True)

    if _is_empty_travel_window(cleaned_update.travel_window):
        cleaned_update.travel_window = None
        _remove_timing_field_metadata(cleaned_update, "travel_window")

    if _is_empty_trip_length(cleaned_update.trip_length):
        cleaned_update.trip_length = None
        _remove_timing_field_metadata(cleaned_update, "trip_length")

    return cleaned_update


def build_timing_choice_board_state(
    *,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    have_details = [
        PlannerChecklistItem(
            id="destination",
            label="Destination",
            status="known",
            value=destination,
        )
    ]
    need_details: list[PlannerChecklistItem] = []

    if configuration.travel_window:
        have_details.append(
            PlannerChecklistItem(
                id="timing",
                label="Rough timing",
                status="known",
                value=configuration.travel_window,
            )
        )
    else:
        need_details.append(
            PlannerChecklistItem(
                id="timing",
                label="Rough timing",
                status="needed",
            )
        )

    if configuration.trip_length:
        have_details.append(
            PlannerChecklistItem(
                id="trip_length",
                label="Trip length",
                status="known",
                value=configuration.trip_length,
            )
        )
    else:
        need_details.append(
            PlannerChecklistItem(
                id="trip_length",
                label="Trip length",
                status="needed",
            )
        )

    return TripSuggestionBoardState(
        mode="timing_choice",
        title=f"When should {destination} happen?",
        subtitle=_build_timing_choice_subtitle(configuration),
        have_details=have_details,
        need_details=need_details,
        visible_steps=["timing"],
        required_steps=["timing"],
        details_form=TripDetailsCollectionFormState(
            from_location=configuration.from_location,
            from_location_flexible=configuration.from_location_flexible,
            to_location=configuration.to_location,
            selected_modules=configuration.selected_modules,
            travel_window=configuration.travel_window,
            trip_length=configuration.trip_length,
            weather_preference=configuration.weather_preference,
            start_date=configuration.start_date,
            end_date=configuration.end_date,
            adults=configuration.travelers.adults,
            children=configuration.travelers.children,
            travelers_flexible=configuration.travelers_flexible,
            activity_styles=configuration.activity_styles,
            custom_style=configuration.custom_style,
            budget_posture=configuration.budget_posture,
            budget_amount=configuration.budget_amount,
            budget_currency=configuration.budget_currency,
            budget_gbp=configuration.budget_gbp,
        ),
        own_choice_prompt=None,
    )


def _build_timing_choice_subtitle(configuration: TripConfiguration) -> str:
    if configuration.travel_window and not configuration.trip_length:
        return (
            f"I have {configuration.travel_window} as the working window. "
            "Add a rough length, or type exact dates if you already know them."
        )
    if configuration.trip_length and not configuration.travel_window:
        return (
            f"I have {configuration.trip_length} as the working length. "
            "Add a month or season, or type exact dates if you already know them."
        )
    return (
        "Pick a rough window and trip length, or type exact dates in chat if you "
        "already know them."
    )


def _is_empty_travel_window(value: str | None) -> bool:
    normalized = _normalize_timing_text(value)
    return bool(normalized) and any(
        marker in normalized for marker in _EMPTY_TRAVEL_WINDOW_MARKERS
    )


def _is_empty_trip_length(value: str | None) -> bool:
    normalized = _normalize_timing_text(value)
    if not normalized:
        return False
    if any(marker in normalized for marker in _EMPTY_TRIP_LENGTH_MARKERS):
        return True
    return not any(signal in normalized for signal in _TRIP_LENGTH_SIGNALS)


def _normalize_timing_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().replace("-", " ").split())


def _remove_timing_field_metadata(update: TripTurnUpdate, field: str) -> None:
    update.confirmed_fields = [
        confirmed_field
        for confirmed_field in update.confirmed_fields
        if confirmed_field != field
    ]
    update.inferred_fields = [
        inferred_field
        for inferred_field in update.inferred_fields
        if inferred_field != field
    ]
    update.field_confidences = [
        confidence
        for confidence in update.field_confidences
        if confidence.field != field
    ]
    update.field_sources = [
        source
        for source in update.field_sources
        if source.field != field
    ]
