from datetime import datetime

from app.integrations.amadeus.client import create_amadeus_client
from app.schemas.trip_planning import FlightDetail, TripConfiguration


def enrich_flights_from_amadeus(configuration: TripConfiguration) -> list[FlightDetail]:
    if not _can_search_flights(configuration):
        return []

    origin_code = _resolve_location_iata(configuration.from_location or "")
    destination_code = _resolve_location_iata(configuration.to_location or "")

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


def _resolve_location_iata(keyword: str) -> str | None:
    if not keyword.strip():
        return None

    cleaned_keyword = keyword.strip()
    if len(cleaned_keyword) == 3 and cleaned_keyword.isalpha():
        return cleaned_keyword.upper()

    with create_amadeus_client() as client:
        response = client.get(
            "/v1/reference-data/locations",
            params={
                "subType": "CITY,AIRPORT",
                "keyword": cleaned_keyword[:20],
                "page[limit]": 5,
            },
        )
        response.raise_for_status()
        payload = response.json()

    candidates = payload.get("data") or []
    if not candidates:
        return None

    city_candidate = next(
        (
            item
            for item in candidates
            if item.get("subType") == "CITY" and item.get("iataCode")
        ),
        None,
    )
    if city_candidate:
        return city_candidate["iataCode"]

    first_candidate = candidates[0]
    iata_code = first_candidate.get("iataCode")
    return iata_code if isinstance(iata_code, str) else None


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


def _can_search_flights(configuration: TripConfiguration) -> bool:
    return bool(
        configuration.selected_modules.flights
        and configuration.from_location
        and configuration.to_location
        and configuration.start_date
    )
