from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.trip_planning import (
    ActivityDetail,
    BudgetPosture,
    FlightDetail,
    HotelStayDetail,
    TripBudgetEstimate,
    TripBudgetEstimateCategory,
    TripConfiguration,
    TripModuleOutputs,
)


@dataclass(frozen=True)
class ParsedPrice:
    low_amount: float
    high_amount: float
    currency: str


def estimate_quick_plan_budget(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> TripBudgetEstimate:
    estimate_currency = _estimate_currency(configuration, module_outputs)
    categories = [
        _estimate_flights(module_outputs.flights),
        _estimate_stay(configuration, module_outputs.hotels),
        _estimate_activities(module_outputs.activities),
        _estimate_food(configuration, estimate_currency),
        _estimate_local_transport(configuration, estimate_currency),
    ]
    total_currency = _combined_total_currency(categories)
    total_low = None
    total_high = None
    caveat = "Directional estimate only; prices are not booking-confirmed and may change."

    if total_currency:
        priced_categories = [
            category
            for category in categories
            if category.low_amount is not None
            and category.high_amount is not None
            and category.currency == total_currency
        ]
        if priced_categories:
            total_low = round(sum(category.low_amount or 0 for category in priced_categories), 2)
            total_high = round(sum(category.high_amount or 0 for category in priced_categories), 2)
        if len(priced_categories) < len(categories):
            caveat = (
                "Directional estimate only; unavailable categories are excluded and prices "
                "are not booking-confirmed."
            )
    else:
        caveat = (
            "Directional category estimates only; mixed or missing currencies prevent a "
            "reliable combined total."
        )

    return TripBudgetEstimate(
        total_low_amount=total_low,
        total_high_amount=total_high,
        currency=total_currency,
        categories=categories,
        caveat=caveat,
    )


def _estimate_flights(flights: list[FlightDetail]) -> TripBudgetEstimateCategory:
    priced_flights = [
        flight
        for flight in flights
        if flight.fare_amount is not None and flight.fare_currency
    ]
    currencies = {flight.fare_currency for flight in priced_flights if flight.fare_currency}
    if not priced_flights:
        return _unavailable_category(
            "flights",
            "Flights",
            "No accepted flight fare amount was available.",
        )
    if len(currencies) != 1:
        return _unavailable_category(
            "flights",
            "Flights",
            "Accepted flight fares use mixed currencies, so no category total is shown.",
        )

    total = round(sum(flight.fare_amount or 0 for flight in priced_flights), 2)
    currency = next(iter(currencies))
    return TripBudgetEstimateCategory(
        category="flights",
        label="Flights",
        low_amount=total,
        high_amount=total,
        currency=currency,
        source="provider_price",
        notes=["Uses accepted outbound/return fare amounts when provider data supplies them."],
    )


def _estimate_stay(
    configuration: TripConfiguration,
    hotels: list[HotelStayDetail],
) -> TripBudgetEstimateCategory:
    hotel = hotels[0] if hotels else None
    nights = _trip_nights(configuration)
    if hotel is None or hotel.nightly_rate_amount is None or not hotel.nightly_rate_currency:
        return _unavailable_category(
            "stay",
            "Stay",
            "No accepted nightly stay rate was available.",
        )

    total = round(hotel.nightly_rate_amount * nights, 2)
    return TripBudgetEstimateCategory(
        category="stay",
        label="Stay",
        low_amount=total,
        high_amount=total,
        currency=hotel.nightly_rate_currency,
        source="provider_price",
        notes=[f"Uses {nights} night{'s' if nights != 1 else ''} at the accepted nightly rate."],
    )


def _estimate_activities(
    activities: list[ActivityDetail],
) -> TripBudgetEstimateCategory:
    parsed_prices = [
        parsed
        for parsed in (_parse_activity_price(activity.price_text) for activity in activities)
        if parsed is not None
    ]
    currencies = {parsed.currency for parsed in parsed_prices}
    if not parsed_prices:
        return _unavailable_category(
            "activities",
            "Activities",
            "Structured activity prices were not available or safely parseable.",
        )
    if len(currencies) != 1:
        return _unavailable_category(
            "activities",
            "Activities",
            "Activity prices use mixed currencies, so no category total is shown.",
        )

    currency = next(iter(currencies))
    return TripBudgetEstimateCategory(
        category="activities",
        label="Activities",
        low_amount=round(sum(parsed.low_amount for parsed in parsed_prices), 2),
        high_amount=round(sum(parsed.high_amount for parsed in parsed_prices), 2),
        currency=currency,
        source="provider_price",
        notes=["Uses only structured activity price text that could be safely parsed."],
    )


def _estimate_food(
    configuration: TripConfiguration,
    currency: str,
) -> TripBudgetEstimateCategory:
    low_per_person_day, high_per_person_day = _food_daily_band(
        configuration.budget_posture
    )
    return _planner_band_category(
        "food",
        "Food",
        currency,
        low_per_person_day,
        high_per_person_day,
        configuration,
        "Planner estimate based on trip length, party size, and budget posture.",
    )


def _estimate_local_transport(
    configuration: TripConfiguration,
    currency: str,
) -> TripBudgetEstimateCategory:
    low_per_person_day, high_per_person_day = _local_transport_daily_band(
        configuration.budget_posture
    )
    return _planner_band_category(
        "local_transport",
        "Local transport",
        currency,
        low_per_person_day,
        high_per_person_day,
        configuration,
        "Planner estimate for local movement, transfers, and short hops.",
    )


def _planner_band_category(
    category: str,
    label: str,
    currency: str,
    low_per_person_day: float,
    high_per_person_day: float,
    configuration: TripConfiguration,
    note: str,
) -> TripBudgetEstimateCategory:
    travelers = max(configuration.travelers.adults or 1, 1)
    days = _trip_days(configuration)
    return TripBudgetEstimateCategory(
        category=category,
        label=label,
        low_amount=round(low_per_person_day * travelers * days, 2),
        high_amount=round(high_per_person_day * travelers * days, 2),
        currency=currency,
        source="planner_estimate",
        notes=[note],
    )


def _unavailable_category(
    category: str,
    label: str,
    note: str,
) -> TripBudgetEstimateCategory:
    return TripBudgetEstimateCategory(
        category=category,
        label=label,
        source="unavailable",
        notes=[note],
    )


def _parse_activity_price(value: str | None) -> ParsedPrice | None:
    if not value:
        return None

    normalized = value.strip()
    currency_match = re.search(r"\b([A-Z]{3})\b", normalized)
    if not currency_match:
        return None

    amounts = [
        float(match)
        for match in re.findall(r"\d+(?:\.\d+)?", normalized.replace(",", ""))
    ]
    if not amounts:
        return None

    low_amount = min(amounts)
    high_amount = max(amounts)
    return ParsedPrice(
        low_amount=low_amount,
        high_amount=high_amount,
        currency=currency_match.group(1).upper(),
    )


def _estimate_currency(
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> str:
    known_currencies = {
        currency
        for currency in [
            *(flight.fare_currency for flight in module_outputs.flights),
            *(hotel.nightly_rate_currency for hotel in module_outputs.hotels),
            *(
                parsed.currency
                for parsed in (
                    _parse_activity_price(activity.price_text)
                    for activity in module_outputs.activities
                )
                if parsed is not None
            ),
        ]
        if currency
    }
    if len(known_currencies) == 1:
        return next(iter(known_currencies))
    return configuration.budget_currency or "GBP"


def _combined_total_currency(
    categories: list[TripBudgetEstimateCategory],
) -> str | None:
    currencies = {
        category.currency
        for category in categories
        if category.low_amount is not None and category.high_amount is not None
    }
    if len(currencies) == 1:
        return next(iter(currencies))
    return None


def _trip_nights(configuration: TripConfiguration) -> int:
    if configuration.start_date and configuration.end_date:
        return max((configuration.end_date - configuration.start_date).days, 1)
    return 1


def _trip_days(configuration: TripConfiguration) -> int:
    if configuration.start_date and configuration.end_date:
        return max((configuration.end_date - configuration.start_date).days + 1, 1)
    return 3


def _food_daily_band(posture: BudgetPosture | None) -> tuple[float, float]:
    if posture == "budget":
        return (35, 55)
    if posture == "premium":
        return (95, 155)
    return (60, 95)


def _local_transport_daily_band(posture: BudgetPosture | None) -> tuple[float, float]:
    if posture == "budget":
        return (8, 18)
    if posture == "premium":
        return (25, 55)
    return (14, 32)
