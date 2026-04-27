from datetime import date

from app.graph.planner.quick_plan_budget import estimate_quick_plan_budget
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


def test_quick_plan_budget_includes_flight_fares() -> None:
    estimate = estimate_quick_plan_budget(
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="outbound",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="LIS",
                    fare_amount=220,
                    fare_currency="GBP",
                ),
                FlightDetail(
                    id="return",
                    direction="return",
                    carrier="BA",
                    departure_airport="LIS",
                    arrival_airport="LHR",
                    fare_amount=180,
                    fare_currency="GBP",
                ),
            ]
        ),
    )

    flights = _category(estimate, "flights")

    assert flights.low_amount == 400
    assert flights.high_amount == 400
    assert flights.currency == "GBP"
    assert flights.source == "provider_price"


def test_quick_plan_budget_includes_stay_total_from_trip_nights() -> None:
    estimate = estimate_quick_plan_budget(
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(
            hotels=[
                HotelStayDetail(
                    id="hotel_1",
                    hotel_name="Lisbon Base",
                    area="Baixa",
                    nightly_rate_amount=150,
                    nightly_rate_currency="GBP",
                )
            ]
        ),
    )

    stay = _category(estimate, "stay")

    assert stay.low_amount == 450
    assert stay.high_amount == 450
    assert stay.currency == "GBP"
    assert stay.source == "provider_price"


def test_quick_plan_budget_handles_missing_provider_prices_without_inventing() -> None:
    estimate = estimate_quick_plan_budget(
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="outbound",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="LIS",
                )
            ],
            hotels=[
                HotelStayDetail(
                    id="hotel_1",
                    hotel_name="Lisbon Base",
                    area="Baixa",
                )
            ],
        ),
    )

    assert _category(estimate, "flights").source == "unavailable"
    assert _category(estimate, "flights").low_amount is None
    assert _category(estimate, "stay").source == "unavailable"
    assert _category(estimate, "stay").low_amount is None
    assert _category(estimate, "food").source == "planner_estimate"
    assert _category(estimate, "local_transport").source == "planner_estimate"


def test_quick_plan_budget_parses_structured_activity_price_ranges() -> None:
    estimate = estimate_quick_plan_budget(
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(
            activities=[
                ActivityDetail(
                    id="fado",
                    title="Fado night",
                    price_text="GBP 35-85",
                ),
                ActivityDetail(
                    id="museum",
                    title="Museum visit",
                    price_text="GBP 20",
                ),
                ActivityDetail(
                    id="market",
                    title="Market wander",
                    price_text="Free entry",
                ),
            ]
        ),
    )

    activities = _category(estimate, "activities")

    assert activities.low_amount == 55
    assert activities.high_amount == 105
    assert activities.currency == "GBP"
    assert activities.source == "provider_price"


def test_quick_plan_budget_mixed_currencies_skip_combined_total() -> None:
    estimate = estimate_quick_plan_budget(
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="outbound",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="LIS",
                    fare_amount=220,
                    fare_currency="GBP",
                )
            ],
            hotels=[
                HotelStayDetail(
                    id="hotel_1",
                    hotel_name="Lisbon Base",
                    area="Baixa",
                    nightly_rate_amount=150,
                    nightly_rate_currency="EUR",
                )
            ],
        ),
    )

    assert _category(estimate, "flights").currency == "GBP"
    assert _category(estimate, "stay").currency == "EUR"
    assert estimate.total_low_amount is None
    assert estimate.total_high_amount is None
    assert estimate.currency is None


def test_quick_plan_budget_does_not_change_user_budget_amount() -> None:
    configuration = _configuration()
    configuration.budget_amount = 1200
    configuration.budget_currency = "GBP"

    estimate_quick_plan_budget(
        configuration=configuration,
        module_outputs=TripModuleOutputs(
            hotels=[
                HotelStayDetail(
                    id="hotel_1",
                    hotel_name="Lisbon Base",
                    area="Baixa",
                    nightly_rate_amount=150,
                    nightly_rate_currency="GBP",
                )
            ]
        ),
    )

    assert configuration.budget_amount == 1200
    assert configuration.budget_currency == "GBP"


def _configuration() -> TripConfiguration:
    return TripConfiguration(
        to_location="Lisbon",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 21),
        budget_posture="mid_range",
        travelers={"adults": 2},
    )


def _category(estimate, category):
    return next(item for item in estimate.categories if item.category == category)
