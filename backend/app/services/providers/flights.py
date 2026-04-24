from datetime import datetime

from app.integrations.amadeus.client import create_amadeus_client
from app.integrations.travelpayouts.client import create_travelpayouts_client
from app.schemas.trip_planning import FlightDetail, FlightLegDetail, TripConfiguration
from app.services.providers.iata_lookup import resolve_location_iata


def enrich_flights(configuration: TripConfiguration) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    try:
        cached_flights = enrich_flights_from_travelpayouts(configuration)
    except Exception:
        cached_flights = []

    if cached_flights:
        return cached_flights

    try:
        return enrich_flights_from_amadeus(configuration)
    except Exception:
        return []


def enrich_flights_from_amadeus(configuration: TripConfiguration) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    origin_code = resolve_location_iata(configuration.from_location or "")
    destination_code = resolve_location_iata(configuration.to_location or "")

    if not origin_code or not destination_code:
        return []

    adults = max(configuration.travelers.adults or 1, 1)
    children = max(configuration.travelers.children or 0, 0)

    with create_amadeus_client() as client:
        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": destination_code,
            "departureDate": configuration.start_date.isoformat(),
            "adults": adults,
            "max": 2,
            "currencyCode": "GBP",
        }

        if configuration.end_date and configuration.end_date >= configuration.start_date:
            params["returnDate"] = configuration.end_date.isoformat()

        if children > 0:
            params["children"] = children

        response = client.get("/v2/shopping/flight-offers", params=params)
        response.raise_for_status()
        payload = response.json()

    offers = payload.get("data") or []
    if not offers:
        return []

    dictionaries = payload.get("dictionaries") or {}
    carriers = dictionaries.get("carriers") or {}
    mapped_flights: list[FlightDetail] = []
    for offer_index, offer in enumerate(offers[:3]):
        mapped_flights.extend(
            _map_offer_to_flights(
                offer,
                carriers,
                offer_index=offer_index,
            )
        )
    return mapped_flights


def enrich_flights_from_travelpayouts(
    configuration: TripConfiguration,
) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    origin_code = resolve_location_iata(configuration.from_location or "")
    destination_code = resolve_location_iata(configuration.to_location or "")

    if not origin_code or not destination_code:
        return []

    offers = _search_travelpayouts_offers(
        origin_code=origin_code,
        destination_code=destination_code,
        configuration=configuration,
    )
    if not offers:
        return []

    mapped_flights: list[FlightDetail] = []
    for offer_index, offer in enumerate(offers[:3]):
        mapped_flights.extend(_map_travelpayouts_offer_to_flights(offer, offer_index=offer_index))
    return mapped_flights


def _map_offer_to_flights(
    offer: dict,
    carriers: dict[str, str],
    *,
    offer_index: int = 0,
) -> list[FlightDetail]:
    itineraries = offer.get("itineraries") or []
    price = (offer.get("price") or {}).get("total")
    currency = (offer.get("price") or {}).get("currency")
    flights: list[FlightDetail] = []

    for itinerary_index, itinerary in enumerate(itineraries):
        segments = itinerary.get("segments") or []
        if not segments:
            continue

        first_segment = segments[0]
        last_segment = segments[-1]
        carrier_code = first_segment.get("carrierCode") or ""
        carrier_name = carriers.get(carrier_code, carrier_code or "Carrier unavailable")
        stop_count = max(len(segments) - 1, 0)
        price_text = _format_price_text(price=price, currency=currency, inventory_label="Live fare snapshot")
        legs = _build_amadeus_legs(segments=segments, carriers=carriers)
        layover_summary = _build_layover_summary(legs)
        notes = []

        if price_text:
            notes.append(price_text)
        if stop_count == 0:
            notes.append("Direct routing in current live inventory.")
        else:
            notes.append(f"{stop_count} stop(s) in current live inventory.")
        if layover_summary:
            notes.append(layover_summary)

        flights.append(
            FlightDetail(
                id=f"amadeus_offer_{offer_index + 1}_flight_{itinerary_index + 1}",
                direction="outbound" if itinerary_index == 0 else "return",
                carrier=carrier_name,
                flight_number=first_segment.get("number"),
                departure_airport=(first_segment.get("departure") or {}).get("iataCode") or "TBD",
                arrival_airport=(last_segment.get("arrival") or {}).get("iataCode") or "TBD",
                departure_time=_parse_amadeus_datetime(
                    (first_segment.get("departure") or {}).get("at")
                ),
                arrival_time=_parse_amadeus_datetime(
                    (last_segment.get("arrival") or {}).get("at")
                ),
                duration_text=_format_duration(itinerary.get("duration")),
                price_text=price_text,
                stop_count=stop_count,
                layover_summary=layover_summary,
                legs=legs,
                timing_quality=_build_timing_quality(
                    direction="outbound" if itinerary_index == 0 else "return",
                    departure_time=_parse_amadeus_datetime(
                        (first_segment.get("departure") or {}).get("at")
                    ),
                    arrival_time=_parse_amadeus_datetime(
                        (last_segment.get("arrival") or {}).get("at")
                    ),
                ),
                inventory_notice="Live inventory snapshot; availability and fares can change.",
                notes=notes,
            )
        )

    return flights


def _map_travelpayouts_offer_to_flights(offer: dict, *, offer_index: int = 0) -> list[FlightDetail]:
    notes = []
    price = offer.get("price")
    price_text = _format_price_text(
        price=price,
        currency="GBP",
        inventory_label="Cached fare snapshot",
    )
    if price_text is not None:
        notes.append(price_text)

    transfers = offer.get("transfers")
    return_transfers = offer.get("return_transfers")
    if isinstance(transfers, int):
        notes.append(
            "Direct outbound option from cached inventory."
            if transfers == 0
            else f"{transfers} stop(s) outbound in cached inventory."
        )
    if isinstance(return_transfers, int) and offer.get("return_at"):
        notes.append(
            "Direct return option from cached inventory."
            if return_transfers == 0
            else f"{return_transfers} stop(s) returning in cached inventory."
        )

    inventory_notice = "Cached inventory snapshot with partial leg detail; verify schedules before relying on exact timings."

    outbound_departure = _parse_amadeus_datetime(offer.get("departure_at"))
    outbound_duration = _format_duration_minutes(offer.get("duration_to") or offer.get("duration"))
    outbound_stop_count = transfers if isinstance(transfers, int) else None
    outbound_legs = _build_travelpayouts_legs(
        offer=offer,
        direction="outbound",
        departure_time=outbound_departure,
        duration_text=outbound_duration,
    )
    flights = [
        FlightDetail(
            id=f"travelpayouts_offer_{offer_index + 1}_flight_outbound",
            direction="outbound",
            carrier=(offer.get("airline") or "Carrier unavailable"),
            flight_number=offer.get("flight_number"),
            departure_airport=(offer.get("origin_airport") or offer.get("origin") or "TBD"),
            arrival_airport=(
                offer.get("destination_airport") or offer.get("destination") or "TBD"
            ),
            departure_time=outbound_departure,
            arrival_time=None,
            duration_text=outbound_duration,
            price_text=price_text,
            stop_count=outbound_stop_count,
            layover_summary=_build_cached_transfer_summary(outbound_stop_count),
            legs=outbound_legs,
            timing_quality=_build_timing_quality(
                direction="outbound",
                departure_time=outbound_departure,
                arrival_time=None,
            ),
            inventory_notice=inventory_notice,
            notes=notes,
        )
    ]

    return_at = _parse_amadeus_datetime(offer.get("return_at"))
    if return_at:
        return_duration = _format_duration_minutes(offer.get("duration_back") or offer.get("duration"))
        return_stop_count = return_transfers if isinstance(return_transfers, int) else None
        flights.append(
            FlightDetail(
                id=f"travelpayouts_offer_{offer_index + 1}_flight_return",
                direction="return",
                carrier=(offer.get("airline") or "Carrier unavailable"),
                flight_number=None,
                departure_airport=(offer.get("destination_airport") or offer.get("destination") or "TBD"),
                arrival_airport=(offer.get("origin_airport") or offer.get("origin") or "TBD"),
                departure_time=return_at,
                arrival_time=None,
                duration_text=return_duration,
                price_text=price_text,
                stop_count=return_stop_count,
                layover_summary=_build_cached_transfer_summary(return_stop_count),
                legs=_build_travelpayouts_legs(
                    offer=offer,
                    direction="return",
                    departure_time=return_at,
                    duration_text=return_duration,
                ),
                timing_quality=_build_timing_quality(
                    direction="return",
                    departure_time=return_at,
                    arrival_time=None,
                ),
                inventory_notice=inventory_notice,
                notes=notes,
            )
        )

    return flights


def _search_travelpayouts_offers(
    *,
    origin_code: str,
    destination_code: str,
    configuration: TripConfiguration,
) -> list[dict]:
    parameter_sets = [
        {
            "origin": origin_code,
            "destination": destination_code,
            "departure_at": configuration.start_date.isoformat(),
            "return_at": configuration.end_date.isoformat()
            if configuration.end_date
            else None,
            "one_way": "false" if configuration.end_date else "true",
            "sorting": "price",
            "direct": "false",
            "currency": "gbp",
            "limit": 10,
        },
        {
            "origin": origin_code,
            "destination": destination_code,
            "departure_at": configuration.start_date.strftime("%Y-%m"),
            "return_at": configuration.end_date.strftime("%Y-%m")
            if configuration.end_date
            else None,
            "one_way": "false" if configuration.end_date else "true",
            "sorting": "price",
            "direct": "false",
            "currency": "gbp",
            "limit": 10,
        },
    ]

    with create_travelpayouts_client() as client:
        for params in parameter_sets:
            response = client.get(
                "/aviasales/v3/prices_for_dates",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()
            offers = payload.get("data") or []
            if offers:
                return offers

    return []


def _build_amadeus_legs(
    *,
    segments: list[dict],
    carriers: dict[str, str],
) -> list[FlightLegDetail]:
    legs: list[FlightLegDetail] = []
    for segment in segments:
        carrier_code = segment.get("carrierCode") or ""
        departure = segment.get("departure") or {}
        arrival = segment.get("arrival") or {}
        legs.append(
            FlightLegDetail(
                carrier=carriers.get(carrier_code, carrier_code or None),
                flight_number=segment.get("number"),
                departure_airport=departure.get("iataCode") or "TBD",
                arrival_airport=arrival.get("iataCode") or "TBD",
                departure_time=_parse_amadeus_datetime(departure.get("at")),
                arrival_time=_parse_amadeus_datetime(arrival.get("at")),
                duration_text=_format_duration(segment.get("duration")),
            )
        )
    return legs


def _build_travelpayouts_legs(
    *,
    offer: dict,
    direction: str,
    departure_time: datetime | None,
    duration_text: str | None,
) -> list[FlightLegDetail]:
    if direction == "outbound":
        departure_airport = offer.get("origin_airport") or offer.get("origin") or "TBD"
        arrival_airport = offer.get("destination_airport") or offer.get("destination") or "TBD"
    else:
        departure_airport = offer.get("destination_airport") or offer.get("destination") or "TBD"
        arrival_airport = offer.get("origin_airport") or offer.get("origin") or "TBD"
    return [
        FlightLegDetail(
            carrier=offer.get("airline") or "Carrier unavailable",
            flight_number=offer.get("flight_number") if direction == "outbound" else None,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_time=departure_time,
            arrival_time=None,
            duration_text=duration_text,
        )
    ]


def _build_layover_summary(legs: list[FlightLegDetail]) -> str | None:
    if len(legs) <= 1:
        return None
    layovers: list[str] = []
    for previous_leg, next_leg in zip(legs, legs[1:]):
        if previous_leg.arrival_time is None or next_leg.departure_time is None:
            layovers.append(f"Connection via {previous_leg.arrival_airport}")
            continue
        minutes = int((next_leg.departure_time - previous_leg.arrival_time).total_seconds() // 60)
        if minutes <= 0:
            layovers.append(f"Connection via {previous_leg.arrival_airport}")
            continue
        layovers.append(f"{_format_minutes(minutes)} in {previous_leg.arrival_airport}")
    if not layovers:
        return None
    return "Layover: " + "; ".join(layovers)


def _build_cached_transfer_summary(stop_count: int | None) -> str | None:
    if stop_count is None:
        return None
    if stop_count == 0:
        return "No stops shown in cached inventory."
    if stop_count == 1:
        return "1 stop shown in cached inventory; layover timing is not provided."
    return f"{stop_count} stops shown in cached inventory; layover timing is not provided."


def _format_price_text(
    *,
    price: object | None,
    currency: object | None,
    inventory_label: str,
) -> str | None:
    if price in (None, "") or currency in (None, ""):
        return None
    return f"{inventory_label}: {str(currency).upper()} {price}"


def _build_timing_quality(
    *,
    direction: str,
    departure_time: datetime | None,
    arrival_time: datetime | None,
) -> str | None:
    if direction == "outbound" and arrival_time is not None:
        if arrival_time.hour >= 22:
            return "Very late arrival"
        if arrival_time.hour >= 18:
            return "Late arrival"
        if 8 <= arrival_time.hour <= 16:
            return "Useful arrival window"
    if direction == "return" and departure_time is not None:
        if departure_time.hour <= 10:
            return "Early return"
        if departure_time.hour <= 15:
            return "Midday return"
        return "Useful final-day window"
    if departure_time is not None:
        if 6 <= departure_time.hour <= 22:
            return "Usable departure time"
        return "Awkward departure time"
    return None


def _parse_amadeus_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_duration(value: str | None) -> str | None:
    if not value:
        return None

    if not value.startswith("PT"):
        return value

    hours = 0
    minutes = 0
    number_buffer = ""

    for char in value[2:]:
        if char.isdigit():
            number_buffer += char
            continue

        if char == "H" and number_buffer:
            hours = int(number_buffer)
            number_buffer = ""
            continue

        if char == "M" and number_buffer:
            minutes = int(number_buffer)
            number_buffer = ""
            continue

        return value

    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else value


def _format_duration_minutes(value: object | None) -> str | None:
    if not isinstance(value, int) or value <= 0:
        return None
    hours = value // 60
    minutes = value % 60
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else None


def _format_minutes(value: int) -> str:
    hours = value // 60
    minutes = value % 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _can_search_flights(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.selected_modules.flights
        and configuration.from_location
        and configuration.to_location
        and configuration.start_date
    )
