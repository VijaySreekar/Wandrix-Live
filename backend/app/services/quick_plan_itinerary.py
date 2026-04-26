from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from app.core.config import get_settings
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TimelineItem,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services.providers.activities import enrich_activities_from_geoapify
from app.services.providers.events import enrich_events_from_ticketmaster
from app.services.providers.movement import estimate_travel_duration_minutes


@dataclass(frozen=True)
class ItineraryBuildResult:
    timeline: list[TimelineItem]
    module_outputs: TripModuleOutputs


@dataclass(frozen=True)
class PlaceTemplate:
    title: str
    location: str
    summary: str
    details: tuple[str, ...]
    duration_minutes: int
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class DayTemplate:
    theme: str
    neighborhood: str
    morning_anchor: PlaceTemplate
    morning_light: PlaceTemplate
    lunch_location: str
    afternoon_anchor: PlaceTemplate
    afternoon_light: PlaceTemplate
    dinner_location: str
    evening: PlaceTemplate


CITY_CENTERS: dict[str, tuple[float, float]] = {
    "barcelona": (41.3874, 2.1686),
    "kyoto": (35.0116, 135.7681),
}


def build_provider_backed_quick_plan_itinerary(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> ItineraryBuildResult:
    activities = _safe_fetch_activities(configuration)
    events = _safe_fetch_events(configuration)
    timeline = _build_timeline(
        configuration=configuration,
        module_outputs=module_outputs,
        provider_activities=activities,
        provider_events=events,
    )
    return ItineraryBuildResult(
        timeline=timeline,
        module_outputs=TripModuleOutputs(
            flights=module_outputs.flights,
            weather=module_outputs.weather,
            hotels=module_outputs.hotels,
            activities=_dedupe_activities([*module_outputs.activities, *activities])[:8],
        ),
    )


def _safe_fetch_activities(configuration: TripConfiguration) -> list[ActivityDetail]:
    settings = get_settings()
    if not settings.geoapify_api_key:
        return []
    try:
        return enrich_activities_from_geoapify(
            configuration,
            coordinates=_city_center(configuration.to_location),
            timeout=3.0,
            category_limit=3,
        )
    except Exception:
        return []


def _safe_fetch_events(configuration: TripConfiguration) -> list[dict[str, Any]]:
    try:
        return enrich_events_from_ticketmaster(configuration)
    except Exception:
        return []


def _build_timeline(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    provider_activities: list[ActivityDetail],
    provider_events: list[dict[str, Any]],
) -> list[TimelineItem]:
    if not configuration.start_date:
        return []

    trip_days = _trip_day_count(configuration)
    if trip_days <= 0:
        return []

    template_days = _templates_for_destination(configuration.to_location)
    hotel = module_outputs.hotels[0] if module_outputs.hotels else None
    outbound = _flight_for_direction(module_outputs.flights, "outbound")
    returning = _flight_for_direction(module_outputs.flights, "return")
    hotel_location = _hotel_location(configuration, hotel)
    home_base = _city_center(configuration.to_location)
    used_provider_titles: set[str] = set()

    items: list[TimelineItem] = []
    for day_index in range(1, trip_days + 1):
        current_date = configuration.start_date + timedelta(days=day_index - 1)
        day_label = f"Day {day_index}"
        is_first = day_index == 1
        is_last = day_index == trip_days
        template = template_days[(day_index - 1) % len(template_days)]
        weather = _weather_for_day(module_outputs.weather, day_index, current_date)

        if is_first:
            items.extend(
                _build_arrival_day(
                    configuration=configuration,
                    day_label=day_label,
                    current_date=current_date,
                    outbound=outbound,
                    hotel=hotel,
                    hotel_location=hotel_location,
                    template=template,
                    weather=weather,
                    home_base=home_base,
                )
            )
            continue

        if is_last:
            items.extend(
                _build_final_day(
                    configuration=configuration,
                    day_label=day_label,
                    current_date=current_date,
                    returning=returning,
                    hotel=hotel,
                    hotel_location=hotel_location,
                    template=template,
                    home_base=home_base,
                )
            )
            continue

        provider_activity = _select_provider_activity(
            provider_activities,
            used_titles=used_provider_titles,
        )
        if provider_activity is not None:
            used_provider_titles.add(provider_activity.title.strip().lower())

        event = _select_event_for_day(provider_events, current_date)
        items.extend(
            _build_full_day(
                configuration=configuration,
                day_label=day_label,
                current_date=current_date,
                hotel=hotel,
                hotel_location=hotel_location,
                template=template,
                weather=weather,
                provider_activity=provider_activity,
                event=event,
                home_base=home_base,
            )
        )

    items.sort(
        key=lambda item: (
            _day_number(item.day_label),
            _sort_datetime(item.start_at),
            item.title.lower(),
        )
    )
    return items


def _build_arrival_day(
    *,
    configuration: TripConfiguration,
    day_label: str,
    current_date: date,
    outbound: FlightDetail | None,
    hotel: HotelStayDetail | None,
    hotel_location: str,
    template: DayTemplate,
    weather: WeatherDetail | None,
    home_base: tuple[float, float] | None,
) -> list[TimelineItem]:
    items: list[TimelineItem] = []
    flight_start, flight_end = _flight_window(
        outbound,
        fallback_date=current_date,
        fallback_start=time(8, 0),
        fallback_duration=timedelta(hours=3),
    )
    if outbound:
        items.append(
            _flight_item(
                flight=outbound,
                day_label=day_label,
                start_at=flight_start,
                end_at=flight_end,
            )
        )

    transfer_start = flight_end
    transfer_minutes = _airport_transfer_minutes(configuration, outbound, default=45)
    transfer_end = transfer_start + timedelta(minutes=transfer_minutes)
    items.append(
        _transfer_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_arrival_transfer",
            title=_arrival_transfer_title(configuration, outbound),
            day_label=day_label,
            start_at=transfer_start,
            end_at=transfer_end,
            location_label=hotel_location,
            details=[
                f"Plan roughly {transfer_minutes} minutes from the arrival gateway to the hotel base.",
                "This row keeps the first day grounded before any sightseeing starts.",
            ],
        )
    )

    reset_start = transfer_end
    reset_end = reset_start + timedelta(minutes=75)
    items.append(
        _hotel_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_hotel_reset",
            title=_hotel_reset_title(hotel),
            day_label=day_label,
            start_at=reset_start,
            end_at=reset_end,
            hotel=hotel,
            details=["Check in, unpack, and reset before keeping the first evening light."],
        )
    )

    next_start = max(reset_end, _day_time(current_date, time(17, 30), reset_end))
    evening = _weather_adjusted_evening(template, weather)
    travel_end = next_start + timedelta(
        minutes=_movement_minutes(home_base, _coords_for_place(evening), default=25)
    )
    items.append(
        _transfer_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_evening_travel",
            title=f"Travel to {evening.location}",
            day_label=day_label,
            start_at=next_start,
            end_at=travel_end,
            location_label=evening.location,
            details=["Short transfer into the first easy evening area."],
        )
    )
    activity_end = travel_end + timedelta(minutes=evening.duration_minutes)
    items.append(
        _activity_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_light_evening",
            place=evening,
            day_label=day_label,
            start_at=travel_end,
            end_at=activity_end,
            details=[
                *evening.details,
                "Arrival day is intentionally light so the flight does not make the first night feel rushed.",
            ],
        )
    )
    dinner_start = activity_end + timedelta(minutes=15)
    dinner_end = dinner_start + timedelta(minutes=90)
    items.append(
        _meal_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_dinner",
            title=f"Dinner near {evening.location}",
            day_label=day_label,
            start_at=dinner_start,
            end_at=dinner_end,
            location_label=evening.location,
            details=["Keep dinner close to the first evening area to avoid extra travel."],
        )
    )
    return items


def _build_full_day(
    *,
    configuration: TripConfiguration,
    day_label: str,
    current_date: date,
    hotel: HotelStayDetail | None,
    hotel_location: str,
    template: DayTemplate,
    weather: WeatherDetail | None,
    provider_activity: ActivityDetail | None,
    event: dict[str, Any] | None,
    home_base: tuple[float, float] | None,
) -> list[TimelineItem]:
    morning_start = _day_time(current_date, time(9, 30))
    items: list[TimelineItem] = []

    morning_anchor = _weather_adjusted_morning(template, weather)
    travel_minutes = _movement_minutes(
        home_base,
        _coords_for_place(morning_anchor),
        default=30,
    )
    morning_travel_end = morning_start + timedelta(minutes=travel_minutes)
    items.append(
        _transfer_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_morning_travel",
            title=f"Travel to {template.neighborhood}",
            day_label=day_label,
            start_at=morning_start,
            end_at=morning_travel_end,
            location_label=template.neighborhood,
            details=[f"Start from {hotel_location} and move into the day’s main area."],
        )
    )

    anchor_end = morning_travel_end + timedelta(minutes=morning_anchor.duration_minutes)
    items.append(
        _activity_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_morning_anchor",
            place=morning_anchor,
            day_label=day_label,
            start_at=morning_travel_end,
            end_at=anchor_end,
        )
    )
    light_start = anchor_end + timedelta(minutes=10)
    light_end = light_start + timedelta(minutes=template.morning_light.duration_minutes)
    items.append(
        _activity_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_morning_light",
            place=template.morning_light,
            day_label=day_label,
            start_at=light_start,
            end_at=light_end,
            details=[
                *template.morning_light.details,
                "This is a nearby lighter stop, not a second heavy anchor.",
            ],
        )
    )
    lunch_start = max(
        light_end + timedelta(minutes=15),
        _day_time(current_date, time(12, 30), light_end),
    )
    lunch_end = lunch_start + timedelta(minutes=75)
    items.append(
        _meal_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_lunch",
            title=f"Lunch around {template.lunch_location}",
            day_label=day_label,
            start_at=lunch_start,
            end_at=lunch_end,
            location_label=template.lunch_location,
            details=["Lunch is placed inside the same area rhythm so the day does not fragment."],
        )
    )

    afternoon_travel_start = lunch_end + timedelta(minutes=15)
    afternoon_travel_minutes = _movement_minutes(
        _coords_for_place(morning_anchor),
        _coords_for_place(template.afternoon_anchor),
        default=30,
    )
    afternoon_start = afternoon_travel_start + timedelta(minutes=afternoon_travel_minutes)
    items.append(
        _transfer_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_afternoon_travel",
            title=f"Travel to {template.afternoon_anchor.location}",
            day_label=day_label,
            start_at=afternoon_travel_start,
            end_at=afternoon_start,
            location_label=template.afternoon_anchor.location,
            details=["Move to the afternoon cluster with a realistic travel buffer."],
        )
    )
    afternoon_end = afternoon_start + timedelta(
        minutes=template.afternoon_anchor.duration_minutes
    )
    items.append(
        _activity_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_afternoon_anchor",
            place=template.afternoon_anchor,
            day_label=day_label,
            start_at=afternoon_start,
            end_at=afternoon_end,
        )
    )

    light_place = _provider_place_or_template(provider_activity, template.afternoon_light)
    light_start = afternoon_end + timedelta(minutes=10)
    light_end = light_start + timedelta(
        minutes=provider_activity.estimated_duration_minutes
        if provider_activity and provider_activity.estimated_duration_minutes
        else light_place.duration_minutes
    )
    items.append(
        _activity_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_afternoon_light",
            place=light_place,
            day_label=day_label,
            start_at=light_start,
            end_at=light_end,
            source_label=provider_activity.source_label if provider_activity else None,
            source_url=provider_activity.source_url if provider_activity else None,
            details=[
                *light_place.details,
                "Placed as a lighter add-on because it is close enough to fit medium pacing.",
            ],
        )
    )

    reset_travel_start = light_end + timedelta(minutes=10)
    reset_travel_minutes = _movement_minutes(
        _coords_for_place(light_place),
        home_base,
        default=30,
    )
    reset_start = reset_travel_start + timedelta(minutes=reset_travel_minutes)
    items.append(
        _transfer_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_hotel_return",
            title="Travel back to the hotel",
            day_label=day_label,
            start_at=reset_travel_start,
            end_at=reset_start,
            location_label=hotel_location,
            details=["Return to the stay base before dinner so the day has breathing room."],
        )
    )
    reset_end = reset_start + timedelta(minutes=75)
    items.append(
        _hotel_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_hotel_reset",
            title="Hotel reset",
            day_label=day_label,
            start_at=reset_start,
            end_at=reset_end,
            hotel=hotel,
            details=["Rest, change, and reset before dinner or an evening event."],
        )
    )

    dinner_start = max(
        reset_end + timedelta(minutes=20),
        _day_time(current_date, time(19, 30), reset_end),
    )
    dinner_end = dinner_start + timedelta(minutes=90)
    items.append(
        _meal_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_dinner",
            title=f"Dinner around {template.dinner_location}",
            day_label=day_label,
            start_at=dinner_start,
            end_at=dinner_end,
            location_label=template.dinner_location,
            details=["Dinner is planned after a hotel reset rather than stacked directly after sightseeing."],
        )
    )
    if event is not None:
        event_item = _event_item(event, day_label=day_label, current_date=current_date)
        if event_item and event_item.start_at and _safe_datetime_gte(event_item.start_at, dinner_end):
            items.append(event_item)
    else:
        evening_start = dinner_end + timedelta(minutes=15)
        evening_end = evening_start + timedelta(minutes=template.evening.duration_minutes)
        items.append(
            _activity_item(
                item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_evening",
                place=template.evening,
                day_label=day_label,
                start_at=evening_start,
                end_at=evening_end,
                details=[
                    *template.evening.details,
                    "Optional evening layer; skip it if the day already feels full.",
                ],
            )
        )
    return items


def _build_final_day(
    *,
    configuration: TripConfiguration,
    day_label: str,
    current_date: date,
    returning: FlightDetail | None,
    hotel: HotelStayDetail | None,
    hotel_location: str,
    template: DayTemplate,
    home_base: tuple[float, float] | None,
) -> list[TimelineItem]:
    items: list[TimelineItem] = []
    flight_start, flight_end = _flight_window(
        returning,
        fallback_date=current_date,
        fallback_start=time(18, 0),
        fallback_duration=timedelta(hours=3),
    )
    checkout_start = _day_time(current_date, time(9, 30), flight_start)
    checkout_end = checkout_start + timedelta(minutes=45)
    items.append(
        _hotel_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_checkout",
            title=_hotel_checkout_title(hotel),
            day_label=day_label,
            start_at=checkout_start,
            end_at=checkout_end,
            hotel=hotel,
            details=["Keep checkout explicit so the return flight does not get crowded."],
        )
    )
    latest_airport_transfer_start = flight_start - timedelta(
        minutes=_airport_transfer_minutes(configuration, returning, default=45) + 120
    )
    if latest_airport_transfer_start > checkout_end + timedelta(hours=1):
        nearby_start = checkout_end + timedelta(minutes=30)
        nearby_end = min(
            nearby_start + timedelta(minutes=template.morning_light.duration_minutes),
            latest_airport_transfer_start,
        )
        if nearby_end > nearby_start:
            items.append(
                _activity_item(
                    item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_light_stop",
                    place=template.morning_light,
                    day_label=day_label,
                    start_at=nearby_start,
                    end_at=nearby_end,
                    details=[
                        *template.morning_light.details,
                        "Final-day stop stays close and flexible before the airport run.",
                    ],
                )
            )
    transfer_minutes = _airport_transfer_minutes(configuration, returning, default=45)
    transfer_start = flight_start - timedelta(minutes=transfer_minutes + 120)
    transfer_end = transfer_start + timedelta(minutes=transfer_minutes)
    items.append(
        _transfer_item(
            item_id=f"itinerary_{day_label.lower().replace(' ', '_')}_airport_transfer",
            title=_return_transfer_title(configuration, returning),
            day_label=day_label,
            start_at=transfer_start,
            end_at=transfer_end,
            location_label=returning.departure_airport if returning else hotel_location,
            details=[
                f"Plan roughly {transfer_minutes} minutes to the departure gateway.",
                "Arrive with a two-hour airport buffer before the return flight.",
            ],
        )
    )
    if returning:
        items.append(
            _flight_item(
                flight=returning,
                day_label=day_label,
                start_at=flight_start,
                end_at=flight_end,
            )
        )
    return items


def _templates_for_destination(destination: str | None) -> list[DayTemplate]:
    normalized = (destination or "").lower()
    if "kyoto" in normalized:
        return _kyoto_templates()
    if "barcelona" in normalized:
        return _barcelona_templates()
    return _generic_templates(destination or "the destination")


def _barcelona_templates() -> list[DayTemplate]:
    return [
        DayTemplate(
            theme="Old city, market streets, and El Born",
            neighborhood="Gothic Quarter",
            morning_anchor=PlaceTemplate(
                "Gothic Quarter walk",
                "Gothic Quarter",
                "A compact old-city walk through Roman lanes, plazas, and historic streets.",
                ("Start early before the busiest lanes fill.", "Keep this as a wandering anchor rather than a museum-heavy block."),
                75,
                41.3839,
                2.1763,
            ),
            morning_light=PlaceTemplate(
                "Barcelona Cathedral",
                "Gothic Quarter",
                "A short architectural stop that fits naturally after the old-city walk.",
                ("Best as a lighter nearby stop before lunch.",),
                35,
                41.3839,
                2.1762,
            ),
            lunch_location="El Born",
            afternoon_anchor=PlaceTemplate(
                "Picasso Museum and El Born lanes",
                "El Born",
                "A culture anchor with enough neighborhood texture around it to carry the afternoon.",
                ("Treat museum timing as planner-estimated until ticket slots are checked.",),
                95,
                41.3852,
                2.1809,
            ),
            afternoon_light=PlaceTemplate(
                "Ciutadella Park walk",
                "Ciutadella Park",
                "An easy outdoor decompression stop after the museum.",
                ("Works well as the light add-on before returning to the hotel.",),
                45,
                41.3881,
                2.1875,
            ),
            dinner_location="El Born",
            evening=PlaceTemplate(
                "Passeig del Born evening walk",
                "El Born",
                "A low-friction evening stroll close to dinner.",
                ("Optional if the day already feels full.",),
                45,
                41.3845,
                2.1824,
            ),
        ),
        DayTemplate(
            theme="Gaudi icons and Gracia",
            neighborhood="Eixample and Gracia",
            morning_anchor=PlaceTemplate(
                "Sagrada Familia",
                "Eixample",
                "Barcelona's defining architectural anchor and the day’s main ticketed stop.",
                ("Use a timed entry when booking; this plan only estimates the window.",),
                100,
                41.4036,
                2.1744,
            ),
            morning_light=PlaceTemplate(
                "Hospital de Sant Pau",
                "Sant Pau",
                "A nearby modernist complex that pairs well with Sagrada Familia.",
                ("Close enough to fit as a light second stop without crossing the city.",),
                55,
                41.4124,
                2.1743,
            ),
            lunch_location="Gracia",
            afternoon_anchor=PlaceTemplate(
                "Park Guell",
                "Gracia",
                "A Gaudi-heavy afternoon with open-air views and a different city texture.",
                ("Outdoor-heavy; move earlier if the weather is hot.",),
                100,
                41.4145,
                2.1527,
            ),
            afternoon_light=PlaceTemplate(
                "Gracia squares",
                "Gracia",
                "A lighter wander through local plazas after Park Guell.",
                ("Good medium-pacing add-on if energy is still there.",),
                45,
                41.4034,
                2.1576,
            ),
            dinner_location="Gracia",
            evening=PlaceTemplate(
                "Casa Mila exterior and Passeig de Gracia",
                "Passeig de Gracia",
                "An easy evening architecture walk without adding another heavy ticket.",
                ("Keep it as exterior viewing unless the user wants more Gaudi tickets.",),
                45,
                41.3954,
                2.1619,
            ),
        ),
        DayTemplate(
            theme="Montjuic viewpoints and Poble-sec",
            neighborhood="Montjuic",
            morning_anchor=PlaceTemplate(
                "Montjuic Castle viewpoints",
                "Montjuic",
                "A scenic morning anchor with city and sea views.",
                ("Start before the heat if the weather is warm.",),
                90,
                41.3634,
                2.1651,
            ),
            morning_light=PlaceTemplate(
                "Joan Miro Foundation area",
                "Montjuic",
                "A culture-forward nearby stop that keeps the route compact.",
                ("Use as a lighter culture stop unless tickets are confirmed.",),
                60,
                41.3686,
                2.1590,
            ),
            lunch_location="Poble-sec",
            afternoon_anchor=PlaceTemplate(
                "MNAC terraces and museum area",
                "Montjuic",
                "A polished afternoon anchor around art, architecture, and views.",
                ("The terraces also work if the museum itself is skipped.",),
                90,
                41.3688,
                2.1530,
            ),
            afternoon_light=PlaceTemplate(
                "Magic Fountain and Placa d'Espanya approach",
                "Montjuic",
                "A short orientation stop near the base of Montjuic.",
                ("Treat fountain show timing separately; this is the daytime area walk.",),
                40,
                41.3712,
                2.1517,
            ),
            dinner_location="Poble-sec",
            evening=PlaceTemplate(
                "Poble-sec tapas crawl",
                "Poble-sec",
                "A food-led evening that keeps the night close to the day’s route.",
                ("Keep this flexible rather than booking a rigid multi-stop route.",),
                60,
                41.3745,
                2.1645,
            ),
        ),
        DayTemplate(
            theme="Market, waterfront, and beach air",
            neighborhood="La Rambla and Barceloneta",
            morning_anchor=PlaceTemplate(
                "La Boqueria and La Rambla market start",
                "La Rambla",
                "A food-and-market morning before the tourist flow peaks.",
                ("Best as an early browse rather than a rushed snack stop.",),
                70,
                41.3817,
                2.1717,
            ),
            morning_light=PlaceTemplate(
                "Palau Guell exterior",
                "Raval",
                "A nearby Gaudi-era stop that adds texture without a full ticketed block.",
                ("Use as a short nearby add-on before moving toward the water.",),
                35,
                41.3789,
                2.1741,
            ),
            lunch_location="Barceloneta",
            afternoon_anchor=PlaceTemplate(
                "Barceloneta waterfront walk",
                "Barceloneta",
                "A lighter sea-facing afternoon to balance the denser culture days.",
                ("Good day to slow the pace if previous days were museum-heavy.",),
                90,
                41.3767,
                2.1890,
            ),
            afternoon_light=PlaceTemplate(
                "Port Vell marina",
                "Port Vell",
                "A simple waterside add-on before returning to the hotel.",
                ("Keep it optional in poor weather.",),
                40,
                41.3762,
                2.1840,
            ),
            dinner_location="Barceloneta",
            evening=PlaceTemplate(
                "Beach promenade",
                "Barceloneta",
                "A low-pressure evening walk after dinner.",
                ("Optional and weather-dependent.",),
                45,
                41.3784,
                2.1925,
            ),
        ),
    ]


def _kyoto_templates() -> list[DayTemplate]:
    return [
        DayTemplate(
            theme="Higashiyama temples and Gion",
            neighborhood="Higashiyama",
            morning_anchor=PlaceTemplate(
                "Kiyomizu-dera and Sannenzaka",
                "Higashiyama",
                "Kyoto's classic temple-and-lanes anchor with strong first-impression value.",
                ("Start early because the lanes get crowded.",),
                100,
                34.9949,
                135.7850,
            ),
            morning_light=PlaceTemplate(
                "Ninenzaka lanes",
                "Higashiyama",
                "A nearby atmospheric wander that fits naturally after Kiyomizu-dera.",
                ("Keep this as a slow walk rather than another major ticket.",),
                45,
                34.9985,
                135.7808,
            ),
            lunch_location="Higashiyama",
            afternoon_anchor=PlaceTemplate(
                "Yasaka Shrine and Maruyama Park",
                "Gion",
                "A compact shrine-and-park cluster before the evening Gion rhythm.",
                ("Good flexible afternoon if temple timing slips.",),
                80,
                35.0037,
                135.7786,
            ),
            afternoon_light=PlaceTemplate(
                "Gion lanes",
                "Gion",
                "A light atmospheric walk before returning to the hotel.",
                ("Keep etiquette-sensitive and avoid presenting geisha sightings as guaranteed.",),
                45,
                35.0041,
                135.7750,
            ),
            dinner_location="Gion",
            evening=PlaceTemplate(
                "Pontocho evening walk",
                "Pontocho",
                "A narrow-lane evening stroll that pairs well with dinner.",
                ("Optional if arrival or temple walking made the day full.",),
                45,
                35.0052,
                135.7709,
            ),
        ),
        DayTemplate(
            theme="Fushimi Inari and Nishiki Market",
            neighborhood="Fushimi and central Kyoto",
            morning_anchor=PlaceTemplate(
                "Fushimi Inari lower mountain walk",
                "Fushimi Inari",
                "A signature shrine walk that works best before crowds and heat.",
                ("Do the lower loop unless the user wants a more strenuous climb.",),
                110,
                34.9671,
                135.7727,
            ),
            morning_light=PlaceTemplate(
                "Fushimi sake streets",
                "Fushimi",
                "A lighter neighborhood add-on after the shrine route.",
                ("Keep it short so lunch does not slide too late.",),
                45,
                34.9323,
                135.7616,
            ),
            lunch_location="Nishiki Market",
            afternoon_anchor=PlaceTemplate(
                "Nishiki Market tasting walk",
                "Nishiki Market",
                "A food-forward afternoon anchor with lots of small bites.",
                ("Better as grazing plus browsing than a single formal meal.",),
                85,
                35.0050,
                135.7647,
            ),
            afternoon_light=PlaceTemplate(
                "Teramachi covered arcade",
                "Teramachi",
                "An easy covered add-on if weather is wet or energy dips.",
                ("Works well as a practical weather fallback.",),
                45,
                35.0056,
                135.7671,
            ),
            dinner_location="Kawaramachi",
            evening=PlaceTemplate(
                "Kamo River stroll",
                "Kamo River",
                "A gentle evening reset along the river.",
                ("Skip in heavy rain.",),
                45,
                35.0064,
                135.7715,
            ),
        ),
        DayTemplate(
            theme="Arashiyama bamboo and riverside",
            neighborhood="Arashiyama",
            morning_anchor=PlaceTemplate(
                "Arashiyama bamboo grove and Tenryu-ji area",
                "Arashiyama",
                "A west-side Kyoto anchor combining bamboo, temple grounds, and scenery.",
                ("Go early; this area loses charm when it is too crowded.",),
                110,
                35.0170,
                135.6719,
            ),
            morning_light=PlaceTemplate(
                "Togetsukyo Bridge",
                "Arashiyama",
                "A nearby scenic bridge stop before lunch.",
                ("A simple add-on that does not overload the morning.",),
                35,
                35.0129,
                135.6778,
            ),
            lunch_location="Arashiyama",
            afternoon_anchor=PlaceTemplate(
                "Okochi Sanso or riverside garden time",
                "Arashiyama",
                "A calmer garden-style afternoon after the main bamboo route.",
                ("Use this as the slower anchor if the morning was busy.",),
                80,
                35.0173,
                135.6698,
            ),
            afternoon_light=PlaceTemplate(
                "Riverside tea pause",
                "Arashiyama",
                "A light pause before heading back across the city.",
                ("Keeps the day medium-paced despite the cross-city transfer.",),
                40,
                35.0122,
                135.6769,
            ),
            dinner_location="Central Kyoto",
            evening=PlaceTemplate(
                "Kyoto Station skyway or central evening walk",
                "Central Kyoto",
                "A low-effort evening after the west-side excursion.",
                ("Keep close to the hotel if the Arashiyama day runs long.",),
                45,
                34.9858,
                135.7588,
            ),
        ),
        DayTemplate(
            theme="Nijo and Imperial Kyoto",
            neighborhood="Central Kyoto",
            morning_anchor=PlaceTemplate(
                "Nijo Castle",
                "Nijo",
                "A strong history anchor with palace interiors and gardens.",
                ("Treat opening hours as unconfirmed until ticketing is checked.",),
                100,
                35.0142,
                135.7482,
            ),
            morning_light=PlaceTemplate(
                "Kyoto Imperial Palace Park",
                "Imperial Palace Park",
                "A lighter open-air counterpoint to Nijo.",
                ("Good for breathing room between structured sights.",),
                55,
                35.0254,
                135.7621,
            ),
            lunch_location="Karasuma Oike",
            afternoon_anchor=PlaceTemplate(
                "Kyoto International Manga Museum or craft streets",
                "Karasuma Oike",
                "A central culture stop that keeps travel time low.",
                ("Choose this when the trip wants culture without another temple.",),
                80,
                35.0116,
                135.7594,
            ),
            afternoon_light=PlaceTemplate(
                "Small shops around Sanjo",
                "Sanjo",
                "A simple local-shopping add-on before the hotel reset.",
                ("Keep it flexible and easy to skip.",),
                45,
                35.0086,
                135.7629,
            ),
            dinner_location="Sanjo or Pontocho",
            evening=PlaceTemplate(
                "Pontocho after dinner",
                "Pontocho",
                "A polished but easy evening lane walk.",
                ("Optional if the group wants a quieter night.",),
                45,
                35.0052,
                135.7709,
            ),
        ),
    ]


def _generic_templates(destination: str) -> list[DayTemplate]:
    place = destination or "the destination"
    center = PlaceTemplate(
        f"{place} old town and central orientation",
        place,
        "A central orientation block shaped around the strongest known area.",
        ("Replace with stronger provider-backed places as they become available.",),
        90,
    )
    light = PlaceTemplate(
        f"{place} cafe and local streets",
        place,
        "A lighter nearby stop to keep medium pacing.",
        ("Flexible add-on.",),
        45,
    )
    return [
        DayTemplate(
            theme=f"{place} food and culture",
            neighborhood=place,
            morning_anchor=center,
            morning_light=light,
            lunch_location=place,
            afternoon_anchor=center,
            afternoon_light=light,
            dinner_location=place,
            evening=light,
        )
    ]


def _flight_for_direction(
    flights: list[FlightDetail],
    direction: str,
) -> FlightDetail | None:
    return next((flight for flight in flights if flight.direction == direction), None)


def _flight_window(
    flight: FlightDetail | None,
    *,
    fallback_date: date,
    fallback_start: time,
    fallback_duration: timedelta,
) -> tuple[datetime, datetime]:
    if flight and flight.departure_time and flight.arrival_time:
        return flight.departure_time, flight.arrival_time
    if flight and flight.arrival_time:
        return flight.arrival_time - fallback_duration, flight.arrival_time
    if flight and flight.departure_time:
        return flight.departure_time, flight.departure_time + fallback_duration
    start = datetime.combine(fallback_date, fallback_start)
    return start, start + fallback_duration


def _day_time(
    current_date: date,
    clock: time,
    reference: datetime | None = None,
) -> datetime:
    return datetime.combine(current_date, clock, tzinfo=reference.tzinfo if reference else None)


def _safe_datetime_gte(first: datetime, second: datetime) -> bool:
    if first.tzinfo is None and second.tzinfo is not None:
        second = second.replace(tzinfo=None)
    elif first.tzinfo is not None and second.tzinfo is None:
        first = first.replace(tzinfo=None)
    return first >= second


def _sort_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.max
    if value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def _flight_item(
    *,
    flight: FlightDetail,
    day_label: str,
    start_at: datetime,
    end_at: datetime,
) -> TimelineItem:
    title = (
        f"{flight.carrier} flight to {flight.arrival_airport}"
        if flight.direction == "outbound"
        else f"{flight.carrier} return flight to {flight.arrival_airport}"
    )
    return TimelineItem(
        id=f"itinerary_flight_{flight.id}",
        type="flight",
        title=title,
        day_label=day_label,
        start_at=start_at,
        end_at=end_at,
        timing_source="provider_exact" if flight.departure_time or flight.arrival_time else "planner_estimate",
        timing_note=(
            "Flight timing comes from the selected flight option."
            if flight.departure_time or flight.arrival_time
            else "Planner-estimated flight window because the selected route has no exact time yet."
        ),
        location_label=f"{flight.departure_airport} to {flight.arrival_airport}",
        summary=flight.duration_text,
        details=[detail for detail in [flight.price_text, flight.layover_summary] if detail],
        source_module="flights",
        status="draft",
    )


def _transfer_item(
    *,
    item_id: str,
    title: str,
    day_label: str,
    start_at: datetime,
    end_at: datetime,
    location_label: str | None,
    details: list[str],
) -> TimelineItem:
    minutes = max(int((end_at - start_at).total_seconds() // 60), 1)
    return TimelineItem(
        id=item_id,
        type="transfer",
        title=title,
        day_label=day_label,
        start_at=start_at,
        end_at=end_at,
        timing_source="planner_estimate",
        timing_note=f"Planner-estimated travel time: about {minutes} minutes.",
        location_label=location_label,
        summary=f"About {minutes} minutes in transit.",
        details=details,
        status="draft",
    )


def _hotel_item(
    *,
    item_id: str,
    title: str,
    day_label: str,
    start_at: datetime,
    end_at: datetime,
    hotel: HotelStayDetail | None,
    details: list[str],
) -> TimelineItem:
    return TimelineItem(
        id=item_id,
        type="hotel",
        title=title,
        day_label=day_label,
        start_at=start_at,
        end_at=end_at,
        timing_source="planner_estimate",
        timing_note="Planner-estimated hotel buffer.",
        venue_name=hotel.hotel_name if hotel else None,
        location_label=_hotel_location(None, hotel),
        summary=hotel.hotel_name if hotel else None,
        details=details,
        source_module="hotels" if hotel else None,
        status="draft",
    )


def _activity_item(
    *,
    item_id: str,
    place: PlaceTemplate,
    day_label: str,
    start_at: datetime,
    end_at: datetime,
    source_label: str | None = None,
    source_url: str | None = None,
    details: list[str] | None = None,
) -> TimelineItem:
    return TimelineItem(
        id=item_id,
        type="activity",
        title=place.title,
        day_label=day_label,
        start_at=start_at,
        end_at=end_at,
        timing_source="planner_estimate",
        timing_note="Planner-estimated activity window.",
        location_label=place.location,
        summary=place.summary,
        details=details or list(place.details),
        source_label=source_label,
        source_url=source_url,
        source_module="activities",
        status="draft",
    )


def _meal_item(
    *,
    item_id: str,
    title: str,
    day_label: str,
    start_at: datetime,
    end_at: datetime,
    location_label: str,
    details: list[str],
) -> TimelineItem:
    return TimelineItem(
        id=item_id,
        type="meal",
        title=title,
        day_label=day_label,
        start_at=start_at,
        end_at=end_at,
        timing_source="planner_estimate",
        timing_note="Planner-estimated meal window.",
        location_label=location_label,
        summary="Meal stop placed to keep the day balanced.",
        details=details,
        source_module="activities",
        status="draft",
    )


def _event_item(
    event: dict[str, Any],
    *,
    day_label: str,
    current_date: date,
) -> TimelineItem | None:
    start_at = event.get("start_at")
    end_at = event.get("end_at")
    if not isinstance(start_at, datetime):
        return None
    if start_at.date() != current_date:
        return None
    if not isinstance(end_at, datetime) or end_at <= start_at:
        end_at = start_at + timedelta(minutes=int(event.get("estimated_duration_minutes") or 120))
    return TimelineItem(
        id=str(event.get("id") or f"itinerary_event_{day_label.lower()}"),
        type="event",
        title=str(event.get("title") or "Timed local event"),
        day_label=day_label,
        start_at=start_at,
        end_at=end_at,
        timing_source="provider_exact",
        timing_note="Timed event window from Ticketmaster.",
        venue_name=event.get("venue_name") if isinstance(event.get("venue_name"), str) else None,
        location_label=event.get("location_label") if isinstance(event.get("location_label"), str) else None,
        summary=event.get("summary") if isinstance(event.get("summary"), str) else None,
        details=["Optional timed event; keep it only if it matches the group’s energy."],
        source_label="Ticketmaster",
        source_url=event.get("source_url") if isinstance(event.get("source_url"), str) else None,
        image_url=event.get("image_url") if isinstance(event.get("image_url"), str) else None,
        availability_text=event.get("availability_text") if isinstance(event.get("availability_text"), str) else None,
        price_text=event.get("price_text") if isinstance(event.get("price_text"), str) else None,
        status_text=event.get("status_text") if isinstance(event.get("status_text"), str) else None,
        source_module="activities",
        status="draft",
    )


def _provider_place_or_template(
    activity: ActivityDetail | None,
    fallback: PlaceTemplate,
) -> PlaceTemplate:
    if activity is None:
        return fallback
    return PlaceTemplate(
        title=activity.title,
        location=activity.location_label or activity.venue_name or fallback.location,
        summary=activity.category or fallback.summary,
        details=tuple(activity.notes[:2]) or fallback.details,
        duration_minutes=activity.estimated_duration_minutes or fallback.duration_minutes,
        latitude=activity.latitude,
        longitude=activity.longitude,
    )


def _select_provider_activity(
    activities: list[ActivityDetail],
    *,
    used_titles: set[str],
) -> ActivityDetail | None:
    for activity in activities:
        key = activity.title.strip().lower()
        if not key or key in used_titles:
            continue
        if activity.estimated_duration_minutes and activity.estimated_duration_minutes > 120:
            continue
        return activity
    return None


def _select_event_for_day(
    events: list[dict[str, Any]],
    current_date: date,
) -> dict[str, Any] | None:
    for event in events:
        start_at = event.get("start_at")
        if isinstance(start_at, datetime) and start_at.date() == current_date and start_at.hour >= 20:
            return event
    return None


def _weather_for_day(
    weather: list[WeatherDetail],
    day_index: int,
    current_date: date,
) -> WeatherDetail | None:
    return next(
        (
            item
            for item in weather
            if item.forecast_date == current_date or item.day_label == f"Day {day_index}"
        ),
        None,
    )


def _weather_adjusted_morning(
    template: DayTemplate,
    weather: WeatherDetail | None,
) -> PlaceTemplate:
    if weather and weather.weather_risk_level == "high":
        return template.afternoon_anchor
    return template.morning_anchor


def _weather_adjusted_evening(
    template: DayTemplate,
    weather: WeatherDetail | None,
) -> PlaceTemplate:
    if weather and weather.weather_risk_level == "high":
        return template.morning_light
    return template.evening


def _trip_day_count(configuration: TripConfiguration) -> int:
    if configuration.start_date and configuration.end_date:
        return max((configuration.end_date - configuration.start_date).days + 1, 1)
    return 4


def _hotel_location(
    configuration: TripConfiguration | None,
    hotel: HotelStayDetail | None,
) -> str:
    if hotel:
        return hotel.address or hotel.area or hotel.hotel_name
    return (configuration.to_location if configuration else None) or "Hotel base"


def _hotel_reset_title(hotel: HotelStayDetail | None) -> str:
    if hotel:
        return f"Check in and reset at {hotel.hotel_name}"
    return "Check in and hotel reset"


def _hotel_checkout_title(hotel: HotelStayDetail | None) -> str:
    if hotel:
        return f"Checkout at {hotel.hotel_name}"
    return "Checkout and luggage buffer"


def _arrival_transfer_title(
    configuration: TripConfiguration,
    flight: FlightDetail | None,
) -> str:
    destination = configuration.to_location or "the hotel"
    if flight and flight.arrival_airport:
        return f"Transfer from {flight.arrival_airport} to {destination} hotel"
    return f"Transfer to {destination} hotel"


def _return_transfer_title(
    configuration: TripConfiguration,
    flight: FlightDetail | None,
) -> str:
    origin = configuration.to_location or "hotel"
    if flight and flight.departure_airport:
        return f"Transfer from {origin} hotel to {flight.departure_airport}"
    return "Transfer from hotel to departure gateway"


def _airport_transfer_minutes(
    configuration: TripConfiguration,
    flight: FlightDetail | None,
    *,
    default: int,
) -> int:
    destination = (configuration.to_location or "").lower()
    airport = ""
    if flight:
        airport = (
            flight.arrival_airport if flight.direction == "outbound" else flight.departure_airport
        ).upper()
    if "kyoto" in destination and airport in {"KIX", "ITM", "OSA"}:
        return 95
    if "barcelona" in destination and airport == "BCN":
        return 35
    return default


def _movement_minutes(
    origin: tuple[float, float] | None,
    destination: tuple[float, float] | None,
    *,
    default: int,
) -> int:
    if origin is None or destination is None:
        return default
    estimate = estimate_travel_duration_minutes(
        origin_latitude=origin[0],
        origin_longitude=origin[1],
        destination_latitude=destination[0],
        destination_longitude=destination[1],
    )
    if estimate is None:
        return default
    return max(10, min(estimate.minutes, 75))


def _coords_for_place(place: PlaceTemplate) -> tuple[float, float] | None:
    if place.latitude is None or place.longitude is None:
        return None
    return place.latitude, place.longitude


def _city_center(destination: str | None) -> tuple[float, float] | None:
    normalized = (destination or "").lower()
    for key, coords in CITY_CENTERS.items():
        if key in normalized:
            return coords
    return None


def _day_number(day_label: str | None) -> int:
    if not day_label:
        return 999
    digits = "".join(ch for ch in day_label if ch.isdigit())
    return int(digits) if digits else 999


def _dedupe_activities(activities: list[ActivityDetail]) -> list[ActivityDetail]:
    seen: set[str] = set()
    deduped: list[ActivityDetail] = []
    for activity in activities:
        key = activity.title.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(activity)
    return deduped
