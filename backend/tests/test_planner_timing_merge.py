from datetime import date

from app.graph.planner.draft_merge import merge_trip_configuration
from app.graph.planner.turn_models import TripTurnUpdate
from app.schemas.trip_planning import TripConfiguration


def test_inferred_exact_dates_do_not_override_rough_timing() -> None:
    configuration = merge_trip_configuration(
        TripConfiguration(),
        TripTurnUpdate(
            start_date=date(2026, 10, 3),
            end_date=date(2026, 10, 8),
            travel_window="early October",
            trip_length="five-ish days",
            inferred_fields=["start_date", "end_date", "travel_window", "trip_length"],
        ),
    )

    assert configuration.travel_window == "early October"
    assert configuration.trip_length == "five-ish days"
    assert configuration.start_date is None
    assert configuration.end_date is None


def test_confirmed_rough_timing_clears_previous_exact_dates() -> None:
    current = TripConfiguration(
        start_date=date(2026, 10, 3),
        end_date=date(2026, 10, 8),
    )

    configuration = merge_trip_configuration(
        current,
        TripTurnUpdate(
            travel_window="sometime in spring",
            trip_length="about a week",
            confirmed_fields=["travel_window", "trip_length"],
        ),
    )

    assert configuration.travel_window == "sometime in spring"
    assert configuration.trip_length == "about a week"
    assert configuration.start_date is None
    assert configuration.end_date is None


def test_confirmed_exact_dates_clear_previous_rough_timing() -> None:
    current = TripConfiguration(
        travel_window="late September",
        trip_length="four nights",
    )

    configuration = merge_trip_configuration(
        current,
        TripTurnUpdate(
            start_date=date(2026, 9, 26),
            end_date=date(2026, 9, 30),
            confirmed_fields=["start_date", "end_date"],
        ),
    )

    assert configuration.start_date == date(2026, 9, 26)
    assert configuration.end_date == date(2026, 9, 30)
    assert configuration.travel_window is None
    assert configuration.trip_length is None
