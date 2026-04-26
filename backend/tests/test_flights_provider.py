from datetime import date

from app.schemas.trip_planning import FlightDetail, TripConfiguration
from app.services.providers import flights


def test_flights_provider_uses_travelpayouts_before_amadeus(monkeypatch) -> None:
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=date(2027, 3, 23),
        end_date=date(2027, 3, 29),
    )
    configuration.travelers.adults = 2
    called_amadeus = False

    monkeypatch.setattr(
        flights,
        "enrich_flights_from_travelpayouts",
        lambda _: [
            FlightDetail(
                id="travelpayouts_outbound",
                direction="outbound",
                carrier="Working Air",
                departure_airport="LHR",
                arrival_airport="KIX",
            )
        ],
    )

    def _raise_if_called(_):
        nonlocal called_amadeus
        called_amadeus = True
        return []

    monkeypatch.setattr(flights, "enrich_flights_from_amadeus", _raise_if_called)

    result = flights.enrich_flights(configuration)

    assert result[0].id == "travelpayouts_outbound"
    assert called_amadeus is False


def test_flights_provider_falls_back_to_amadeus_when_travelpayouts_is_empty(
    monkeypatch,
) -> None:
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=date(2027, 3, 23),
        end_date=date(2027, 3, 29),
    )
    configuration.travelers.adults = 2

    monkeypatch.setattr(flights, "enrich_flights_from_travelpayouts", lambda _: [])
    monkeypatch.setattr(
        flights,
        "enrich_flights_from_amadeus",
        lambda _: [
            FlightDetail(
                id="amadeus_outbound",
                direction="outbound",
                carrier="Fallback Air",
                departure_airport="LHR",
                arrival_airport="KIX",
            )
        ],
    )

    result = flights.enrich_flights(configuration)

    assert result[0].id == "amadeus_outbound"


def test_amadeus_mapping_preserves_segments_layovers_and_fare_detail() -> None:
    offer = {
        "price": {"total": "682.40", "currency": "GBP"},
        "itineraries": [
            {
                "duration": "PT15H20M",
                "segments": [
                    {
                        "carrierCode": "BA",
                        "number": "5",
                        "departure": {"iataCode": "LHR", "at": "2027-03-23T09:00:00"},
                        "arrival": {"iataCode": "DOH", "at": "2027-03-23T18:00:00"},
                        "duration": "PT7H",
                    },
                    {
                        "carrierCode": "JL",
                        "number": "799",
                        "departure": {"iataCode": "DOH", "at": "2027-03-23T20:15:00"},
                        "arrival": {"iataCode": "KIX", "at": "2027-03-24T07:20:00"},
                        "duration": "PT8H5M",
                    },
                ],
            }
        ],
    }

    result = flights._map_offer_to_flights(  # noqa: SLF001
        offer,
        {"BA": "British Airways", "JL": "Japan Airlines"},
        offer_index=0,
    )

    assert len(result) == 1
    outbound = result[0]
    assert outbound.stop_count == 1
    assert outbound.duration_text == "15h 20m"
    assert outbound.price_text == "GBP 682.40"
    assert outbound.fare_amount == 682.40
    assert outbound.fare_currency == "GBP"
    assert outbound.layover_summary == "Layover: 2h 15m in DOH"
    assert outbound.inventory_notice == "Schedule and fare can change before booking."
    assert outbound.inventory_source == "live"
    assert outbound.stop_details_available is True
    assert [leg.departure_airport for leg in outbound.legs] == ["LHR", "DOH"]
    assert [leg.arrival_airport for leg in outbound.legs] == ["DOH", "KIX"]
    assert outbound.legs[1].carrier == "Japan Airlines"


def test_travelpayouts_mapping_exposes_cached_inventory_detail_without_raw_provider_copy() -> None:
    offer = {
        "price": 514,
        "airline": "BA",
        "flight_number": "7",
        "origin": "LON",
        "origin_airport": "LHR",
        "destination": "OSA",
        "destination_airport": "KIX",
        "departure_at": "2027-03-23T10:30:00+00:00",
        "return_at": "2027-03-29T13:20:00+00:00",
        "duration_to": 860,
        "duration_back": 900,
        "transfers": 1,
        "return_transfers": 0,
    }

    result = flights._map_travelpayouts_offer_to_flights(offer, offer_index=1)  # noqa: SLF001

    assert [flight.direction for flight in result] == ["outbound", "return"]
    outbound, returning = result
    assert outbound.price_text == "GBP 514"
    assert outbound.fare_amount == 514
    assert outbound.fare_currency == "GBP"
    assert outbound.stop_count == 1
    assert outbound.duration_text == "14h 20m"
    assert outbound.layover_summary == "1 stop; connection airport is not supplied yet."
    assert outbound.inventory_notice == "Partial schedule detail; verify exact times before booking."
    assert outbound.inventory_source == "cached"
    assert outbound.stop_details_available is False
    assert outbound.timing_quality is None
    assert outbound.legs[0].departure_airport == "LHR"
    assert returning.stop_count == 0
    assert returning.duration_text == "15h"
