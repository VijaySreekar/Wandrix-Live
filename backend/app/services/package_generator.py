from datetime import timedelta

from app.schemas.package import DailyPlan, TravelPackageRequest, TravelPackageResponse


def generate_travel_package(
    payload: TravelPackageRequest,
) -> TravelPackageResponse:
    duration_nights = (payload.end_date - payload.start_date).days
    recommendations = build_recommendations(payload)
    itinerary = build_itinerary(payload, duration_nights)

    estimated_total = payload.budget_gbp
    if estimated_total is None:
        estimated_total = round(duration_nights * 180 * payload.travelers.adults, 2)

    inclusions: list[str] = []
    if payload.include_flights:
        inclusions.append("Return flight suggestions")
    if payload.include_hotel:
        inclusions.append("Hotel shortlist")
    inclusions.append("Day-by-day itinerary")

    summary = (
        f"A {duration_nights}-night {payload.pace} trip from {payload.origin} to "
        f"{payload.destination} built around {format_interests(payload.interests)}."
    )

    return TravelPackageResponse(
        title=f"{payload.destination} Travel Package",
        summary=summary,
        origin=payload.origin,
        destination=payload.destination,
        duration_nights=duration_nights,
        travelers=payload.travelers,
        estimated_total_gbp=estimated_total,
        inclusions=inclusions,
        recommendations=recommendations,
        itinerary=itinerary,
    )


def build_recommendations(payload: TravelPackageRequest) -> list[str]:
    recommendations = [
        f"Book the main activities in {payload.destination} before arrival.",
        f"Keep one flexible block each day to adapt the trip pace to {payload.pace}.",
    ]
    if payload.budget_gbp is not None:
        recommendations.append(
            f"Target an average daily spend of about GBP {payload.budget_gbp / max((payload.end_date - payload.start_date).days, 1):.0f}."
        )
    if payload.interests:
        recommendations.append(
            f"Prioritize experiences tied to {format_interests(payload.interests)}."
        )
    return recommendations


def build_itinerary(
    payload: TravelPackageRequest,
    duration_nights: int,
) -> list[DailyPlan]:
    itinerary: list[DailyPlan] = []
    interests_text = format_interests(payload.interests)

    for offset in range(duration_nights):
        current_date = payload.start_date + timedelta(days=offset)
        day_number = offset + 1

        itinerary.append(
            DailyPlan(
                day=day_number,
                date=current_date,
                morning=(
                    f"Start day {day_number} with a local {payload.pace} experience in "
                    f"{payload.destination} focused on {interests_text}."
                ),
                afternoon=(
                    f"Explore signature neighborhoods and plan one anchor activity for "
                    f"{payload.travelers.adults + payload.travelers.children} travelers."
                ),
                evening=(
                    f"Wrap up with food, views, or nightlife that matches a {payload.pace} trip style."
                ),
            )
        )

    return itinerary


def format_interests(interests: list[str]) -> str:
    if not interests:
        return "classic travel highlights"
    return ", ".join(interests)
