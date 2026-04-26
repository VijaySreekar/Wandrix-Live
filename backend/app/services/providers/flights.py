from datetime import datetime

from app.integrations.amadeus.client import create_amadeus_client
from app.integrations.travelpayouts.client import create_travelpayouts_client
from app.schemas.trip_planning import FlightDetail, FlightLegDetail, TripConfiguration
from app.services.providers.iata_lookup import FlightGateway, resolve_flight_gateway


def enrich_flights(
    configuration: TripConfiguration,
    *,
    timeout: float | None = None,
    allow_live_fallback: bool = True,
    parameter_sets_limit: int | None = None,
) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    try:
        if timeout is None and parameter_sets_limit is None:
            cached_flights = enrich_flights_from_travelpayouts(configuration)
        else:
            cached_flights = enrich_flights_from_travelpayouts(
                configuration,
                timeout=timeout,
                parameter_sets_limit=parameter_sets_limit,
            )
    except Exception:
        cached_flights = []

    if cached_flights:
        return cached_flights

    if not allow_live_fallback:
        return []

    try:
        if timeout is None:
            return enrich_flights_from_amadeus(configuration)
        return enrich_flights_from_amadeus(configuration, timeout=timeout)
    except Exception:
        return []


def enrich_flights_from_amadeus(
    configuration: TripConfiguration,
    *,
    timeout: float | None = None,
) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    origin_gateway = resolve_flight_gateway(configuration.from_location or "")
    destination_gateway = resolve_flight_gateway(configuration.to_location or "")

    if not origin_gateway or not destination_gateway:
        return []

    adults = max(configuration.travelers.adults or 1, 1)
    children = max(configuration.travelers.children or 0, 0)

    with create_amadeus_client(timeout=timeout) as client:
        params = {
            "originLocationCode": origin_gateway.search_iata,
            "destinationLocationCode": destination_gateway.search_iata,
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
                gateway_notes_by_direction=_build_gateway_notes_by_direction(
                    origin_gateway=origin_gateway,
                    destination_gateway=destination_gateway,
                ),
            )
        )
    return mapped_flights


def enrich_flights_from_travelpayouts(
    configuration: TripConfiguration,
    *,
    timeout: float | None = None,
    parameter_sets_limit: int | None = None,
) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    origin_gateway = resolve_flight_gateway(configuration.from_location or "")
    destination_gateway = resolve_flight_gateway(configuration.to_location or "")

    if not origin_gateway or not destination_gateway:
        return []

    offers = _search_travelpayouts_offers(
        origin_code=origin_gateway.search_iata,
        destination_code=destination_gateway.search_iata,
        configuration=configuration,
        timeout=timeout,
        parameter_sets_limit=parameter_sets_limit,
    )
    if not offers:
        return []

    mapped_flights: list[FlightDetail] = []
    for offer_index, offer in enumerate(offers[:3]):
        mapped_flights.extend(
            _map_travelpayouts_offer_to_flights(
                offer,
                offer_index=offer_index,
                gateway_notes_by_direction=_build_gateway_notes_by_direction(
                    origin_gateway=origin_gateway,
                    destination_gateway=destination_gateway,
                ),
            )
        )
    return mapped_flights


def _map_offer_to_flights(
    offer: dict,
    carriers: dict[str, str],
    *,
    offer_index: int = 0,
    gateway_notes_by_direction: dict[str, list[str]] | None = None,
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
        fare_amount = _coerce_price_amount(price)
        fare_currency = str(currency).upper() if currency else None
        price_text = _format_price_text(price=price, currency=currency)
        legs = _build_amadeus_legs(segments=segments, carriers=carriers)
        layover_summary = _build_layover_summary(legs)
        direction = "outbound" if itinerary_index == 0 else "return"
        notes = list((gateway_notes_by_direction or {}).get(direction, []))

        if price_text:
            notes.append(f"Estimated fare: {price_text}.")
        if stop_count == 0:
            notes.append("Direct route.")
        else:
            notes.append(f"{stop_count} stop(s) with connection detail available.")
        if layover_summary:
            notes.append(layover_summary)

        flights.append(
            FlightDetail(
                id=f"amadeus_offer_{offer_index + 1}_flight_{itinerary_index + 1}",
                direction=direction,
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
                fare_amount=fare_amount,
                fare_currency=fare_currency,
                stop_count=stop_count,
                stop_details_available=True,
                layover_summary=layover_summary,
                legs=legs,
                timing_quality=_build_timing_quality(
                    direction=direction,
                    departure_time=_parse_amadeus_datetime(
                        (first_segment.get("departure") or {}).get("at")
                    ),
                    arrival_time=_parse_amadeus_datetime(
                        (last_segment.get("arrival") or {}).get("at")
                    ),
                ),
                inventory_notice="Schedule and fare can change before booking.",
                inventory_source="live",
                notes=notes,
            )
        )

    return flights


def _map_travelpayouts_offer_to_flights(
    offer: dict,
    *,
    offer_index: int = 0,
    gateway_notes_by_direction: dict[str, list[str]] | None = None,
) -> list[FlightDetail]:
    price = offer.get("price")
    price_text = _format_price_text(price=price, currency="GBP")
    fare_amount = _coerce_price_amount(price)
    outbound_notes = list((gateway_notes_by_direction or {}).get("outbound", []))
    return_notes = list((gateway_notes_by_direction or {}).get("return", []))
    if price_text is not None:
        outbound_notes.append(f"Estimated fare: {price_text}.")
        return_notes.append(f"Estimated fare: {price_text}.")

    transfers = offer.get("transfers")
    return_transfers = offer.get("return_transfers")
    if isinstance(transfers, int):
        outbound_notes.append(
            "Direct outbound route."
            if transfers == 0
            else f"{transfers} stop(s) outbound; stop airports are not supplied yet."
        )
    if isinstance(return_transfers, int) and offer.get("return_at"):
        return_notes.append(
            "Direct return route."
            if return_transfers == 0
            else f"{return_transfers} stop(s) returning; stop airports are not supplied yet."
        )

    inventory_notice = "Partial schedule detail; verify exact times before booking."

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
            fare_amount=fare_amount,
            fare_currency="GBP",
            stop_count=outbound_stop_count,
            stop_details_available=False,
            layover_summary=_build_cached_transfer_summary(outbound_stop_count),
            legs=outbound_legs,
            timing_quality=None,
            inventory_notice=inventory_notice,
            inventory_source="cached",
            notes=outbound_notes,
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
                fare_amount=fare_amount,
                fare_currency="GBP",
                stop_count=return_stop_count,
                stop_details_available=False,
                layover_summary=_build_cached_transfer_summary(return_stop_count),
                legs=_build_travelpayouts_legs(
                    offer=offer,
                    direction="return",
                    departure_time=return_at,
                    duration_text=return_duration,
                ),
                timing_quality=None,
                inventory_notice=inventory_notice,
                inventory_source="cached",
                notes=return_notes,
            )
        )

    return flights


def _search_travelpayouts_offers(
    *,
    origin_code: str,
    destination_code: str,
    configuration: TripConfiguration,
    timeout: float | None = None,
    parameter_sets_limit: int | None = None,
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

    if parameter_sets_limit is not None:
        parameter_sets = parameter_sets[: max(parameter_sets_limit, 0)]

    with create_travelpayouts_client(timeout=timeout) as client:
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


def _build_gateway_notes_by_direction(
    *,
    origin_gateway: FlightGateway,
    destination_gateway: FlightGateway,
) -> dict[str, list[str]]:
    return {
        "outbound": _build_gateway_notes(
            origin_gateway=origin_gateway,
            destination_gateway=destination_gateway,
        ),
        "return": _build_gateway_notes(
            origin_gateway=destination_gateway,
            destination_gateway=origin_gateway,
        ),
    }


def _build_gateway_notes(
    *,
    origin_gateway: FlightGateway,
    destination_gateway: FlightGateway,
) -> list[str]:
    notes = [
        origin_gateway.planning_note("origin"),
        destination_gateway.planning_note("destination"),
    ]
    return [note for note in notes if note]


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
        return "Direct route."
    if stop_count == 1:
        return "1 stop; connection airport is not supplied yet."
    return f"{stop_count} stops; connection airports are not supplied yet."


def _format_price_text(
    *,
    price: object | None,
    currency: object | None,
) -> str | None:
    if price in (None, "") or currency in (None, ""):
        return None
    return f"{str(currency).upper()} {price}"


def _coerce_price_amount(price: object | None) -> float | None:
    if price in (None, ""):
        return None
    try:
        return float(str(price).replace(",", ""))
    except ValueError:
        return None


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
