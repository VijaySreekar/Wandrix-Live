from datetime import datetime

from app.integrations.amadeus.client import create_amadeus_client
from app.integrations.travelpayouts.client import create_travelpayouts_client
from app.schemas.trip_planning import FlightDetail, TripConfiguration
from app.services.providers.iata_lookup import resolve_location_iata


def enrich_flights(configuration: TripConfiguration) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    try:
        live_flights = enrich_flights_from_amadeus(configuration)
    except Exception:
        live_flights = []

    if live_flights:
        return live_flights

    try:
        return enrich_flights_from_travelpayouts(configuration)
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
    first_offer = offers[0]

    return _map_offer_to_flights(first_offer, carriers)


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

    first_offer = offers[0]
    return _map_travelpayouts_offer_to_flights(first_offer)


def _map_offer_to_flights(
    offer: dict,
    carriers: dict[str, str],
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
        notes = []

        if price and currency:
            notes.append(f"Live fare snapshot: {currency} {price}")
        if stop_count == 0:
            notes.append("Direct routing in the current live offer.")
        else:
            notes.append(f"{stop_count} stop(s) in the current live offer.")

        flights.append(
            FlightDetail(
                id=f"amadeus_flight_{itinerary_index + 1}",
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
                notes=notes,
            )
        )

    return flights


def _map_travelpayouts_offer_to_flights(offer: dict) -> list[FlightDetail]:
    notes = []
    price = offer.get("price")
    if price is not None:
        notes.append(f"Cached Aviasales fare snapshot: GBP {price}")

    transfers = offer.get("transfers")
    return_transfers = offer.get("return_transfers")
    if isinstance(transfers, int):
        notes.append(
            "Direct outbound option from cached Aviasales data."
            if transfers == 0
            else f"{transfers} stop(s) outbound in cached Aviasales data."
        )
    if isinstance(return_transfers, int) and offer.get("return_at"):
        notes.append(
            "Direct return option from cached Aviasales data."
            if return_transfers == 0
            else f"{return_transfers} stop(s) returning in cached Aviasales data."
        )

    deep_link = offer.get("link")
    if isinstance(deep_link, str) and deep_link.strip():
        notes.append(f"Aviasales link: https://www.aviasales.com{deep_link}")

    flights = [
        FlightDetail(
            id="travelpayouts_flight_outbound",
            direction="outbound",
            carrier=(offer.get("airline") or "Carrier unavailable"),
            flight_number=offer.get("flight_number"),
            departure_airport=(offer.get("origin_airport") or offer.get("origin") or "TBD"),
            arrival_airport=(
                offer.get("destination_airport") or offer.get("destination") or "TBD"
            ),
            departure_time=_parse_amadeus_datetime(offer.get("departure_at")),
            arrival_time=None,
            duration_text=_format_duration_minutes(offer.get("duration_to") or offer.get("duration")),
            notes=notes,
        )
    ]

    return_at = _parse_amadeus_datetime(offer.get("return_at"))
    if return_at:
        flights.append(
            FlightDetail(
                id="travelpayouts_flight_return",
                direction="return",
                carrier=(offer.get("airline") or "Carrier unavailable"),
                flight_number=None,
                departure_airport=(offer.get("destination_airport") or offer.get("destination") or "TBD"),
                arrival_airport=(offer.get("origin_airport") or offer.get("origin") or "TBD"),
                departure_time=return_at,
                arrival_time=None,
                duration_text=_format_duration_minutes(offer.get("duration_back") or offer.get("duration")),
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


def _can_search_flights(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.selected_modules.flights
        and configuration.from_location
        and configuration.to_location
        and configuration.start_date
    )
