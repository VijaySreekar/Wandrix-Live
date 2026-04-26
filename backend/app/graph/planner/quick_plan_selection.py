from __future__ import annotations

import re

from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


def prioritize_quick_plan_module_outputs(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    return TripModuleOutputs(
        flights=_rank_flights(module_outputs.flights),
        hotels=_rank_hotels(configuration=configuration, hotels=module_outputs.hotels),
        weather=module_outputs.weather,
        activities=_rank_activities(module_outputs.activities),
    )


def build_quick_plan_timeline_module_outputs(
    module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    selected_flights = _select_primary_flights(module_outputs.flights)
    selected_hotels = module_outputs.hotels[:1]
    return TripModuleOutputs(
        flights=selected_flights,
        hotels=selected_hotels,
        weather=module_outputs.weather[:7],
        activities=module_outputs.activities[:8],
    )


def _select_primary_flights(flights: list[FlightDetail]) -> list[FlightDetail]:
    outbound = next((flight for flight in flights if flight.direction == "outbound"), None)
    returning = next((flight for flight in flights if flight.direction == "return"), None)
    return [flight for flight in [outbound, returning] if flight is not None]


def _rank_flights(flights: list[FlightDetail]) -> list[FlightDetail]:
    return sorted(
        flights,
        key=lambda flight: (
            0 if flight.direction == "outbound" else 1,
            _flight_score(flight),
        ),
    )


def _flight_score(flight: FlightDetail) -> tuple[float, float, str]:
    stop_penalty = float(flight.stop_count if flight.stop_count is not None else 2) * 18
    price_penalty = _extract_price_amount(flight.price_text) or 9999
    timing_penalty = 0.0

    timing_quality = (flight.timing_quality or "").lower()
    if "useful" in timing_quality:
        timing_penalty -= 12
    if "late" in timing_quality:
        timing_penalty += 18
    if "early return" in timing_quality:
        timing_penalty += 10

    if flight.direction == "outbound" and flight.arrival_time:
        arrival_hour = flight.arrival_time.hour
        if 10 <= arrival_hour <= 16:
            timing_penalty -= 8
        elif arrival_hour >= 21:
            timing_penalty += 16
    if flight.direction == "return" and flight.departure_time:
        departure_hour = flight.departure_time.hour
        if 12 <= departure_hour <= 19:
            timing_penalty -= 8
        elif departure_hour <= 8:
            timing_penalty += 14

    return (stop_penalty + timing_penalty, price_penalty, flight.id)


def _rank_hotels(
    *,
    configuration: TripConfiguration,
    hotels: list[HotelStayDetail],
) -> list[HotelStayDetail]:
    return sorted(hotels, key=lambda hotel: _hotel_score(configuration, hotel))


def _hotel_score(
    configuration: TripConfiguration,
    hotel: HotelStayDetail,
) -> tuple[float, float, str]:
    rate = hotel.nightly_rate_amount
    missing_rate_penalty = 45 if rate is None else 0
    budget_penalty = _hotel_budget_penalty(configuration, rate)
    evidence_bonus = 0
    if hotel.image_url:
        evidence_bonus -= 6
    if hotel.source_url:
        evidence_bonus -= 4
    if hotel.area:
        evidence_bonus -= 5
    if hotel.address:
        evidence_bonus -= 3

    return (
        missing_rate_penalty + budget_penalty + evidence_bonus,
        rate if rate is not None else 9999,
        hotel.hotel_name.lower(),
    )


def _hotel_budget_penalty(
    configuration: TripConfiguration,
    nightly_rate: float | None,
) -> float:
    if nightly_rate is None:
        return 0

    if configuration.budget_amount and configuration.start_date and configuration.end_date:
        nights = max((configuration.end_date - configuration.start_date).days, 1)
        travelers = max(configuration.travelers.adults or 1, 1)
        rough_nightly_budget = configuration.budget_amount / nights / max(travelers, 1)
        if nightly_rate > rough_nightly_budget:
            return min((nightly_rate - rough_nightly_budget) / 8, 35)
        return -8

    if configuration.budget_posture == "budget":
        return nightly_rate / 18
    if configuration.budget_posture == "premium":
        return 0 if nightly_rate >= 140 else 8
    return nightly_rate / 32


def _rank_activities(activities: list[ActivityDetail]) -> list[ActivityDetail]:
    return sorted(activities, key=_activity_score)


def _activity_score(activity: ActivityDetail) -> tuple[int, str]:
    score = 0
    if activity.start_at:
        score -= 8
    if activity.image_url:
        score -= 5
    if activity.source_url:
        score -= 4
    if activity.venue_name or activity.location_label:
        score -= 3
    if activity.estimated_duration_minutes:
        score -= 2
    return (score, activity.title.lower())


def _extract_price_amount(price_text: str | None) -> float | None:
    if not price_text:
        return None
    matches = re.findall(r"\d+(?:\.\d+)?", price_text.replace(",", ""))
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None
