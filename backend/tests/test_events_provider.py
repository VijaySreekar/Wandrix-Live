from contextlib import contextmanager

from app.services.providers import events
from app.schemas.trip_planning import TripConfiguration


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def get(self, path: str, params: dict) -> _FakeResponse:
        assert path == "/events.json"
        assert params["city"] == "Kyoto"
        return _FakeResponse(self._payload)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_ticketmaster_events_are_normalized(monkeypatch) -> None:
    monkeypatch.setattr(
        events,
        "create_ticketmaster_client",
        lambda: _FakeClient(
            {
                "_embedded": {
                    "events": [
                        {
                            "id": "evt_1",
                            "name": "Kyoto Jazz Night",
                            "url": "https://example.com/jazz",
                            "images": [
                                {
                                    "url": "https://example.com/jazz-wide.jpg",
                                    "ratio": "16_9",
                                    "width": 1136,
                                }
                            ],
                            "dates": {
                                "start": {"dateTime": "2027-03-24T19:30:00Z"},
                                "end": {"dateTime": "2027-03-24T22:00:00Z"},
                                "status": {"code": "onsale", "name": "On Sale"},
                            },
                            "sales": {
                                "public": {
                                    "startDateTime": "2027-01-10T10:00:00Z",
                                    "endDateTime": "2027-03-24T18:00:00Z",
                                }
                            },
                            "priceRanges": [
                                {
                                    "min": 35.0,
                                    "max": 85.0,
                                    "currency": "GBP",
                                }
                            ],
                            "_embedded": {
                                "venues": [
                                    {
                                        "name": "Blue Note Kyoto",
                                        "city": {"name": "Kyoto"},
                                    }
                                ]
                            },
                            "classifications": [
                                {
                                    "segment": {"name": "Music"},
                                    "genre": {"name": "Jazz"},
                                }
                            ],
                        }
                    ]
                }
            }
        ),
    )

    normalized = events.enrich_events_from_ticketmaster(
        TripConfiguration(
            to_location="Kyoto",
            start_date="2027-03-22",
            end_date="2027-03-27",
        )
    )

    assert normalized[0]["id"] == "ticketmaster_evt_1"
    assert normalized[0]["kind"] == "event"
    assert normalized[0]["venue_name"] == "Blue Note Kyoto"
    assert normalized[0]["location_label"] == "Blue Note Kyoto, Kyoto"
    assert normalized[0]["source_label"] == "Ticketmaster"
    assert normalized[0]["start_at"] is not None
    assert normalized[0]["image_url"] == "https://example.com/jazz-wide.jpg"
    assert normalized[0]["price_text"] == "GBP 35-85"
    assert normalized[0]["status_text"] == "On Sale"
    assert normalized[0]["availability_text"] == "Public sale window: 10 Jan to 24 Mar."


def test_ticketmaster_event_errors_fall_back_to_empty_results(monkeypatch) -> None:
    @contextmanager
    def _raising_client():
        raise RuntimeError("boom")
        yield

    monkeypatch.setattr(events, "create_ticketmaster_client", _raising_client)

    normalized = events.enrich_events_from_ticketmaster(
        TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
        )
    )

    assert normalized == []


def test_ticketmaster_events_geocode_when_venue_coordinates_are_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        events,
        "create_ticketmaster_client",
        lambda: _FakeClient(
            {
                "_embedded": {
                    "events": [
                        {
                            "id": "evt_2",
                            "name": "Kyoto Night Market",
                            "dates": {
                                "start": {"dateTime": "2027-03-25T18:00:00Z"},
                            },
                            "_embedded": {
                                "venues": [
                                    {
                                        "name": "Riverside Plaza",
                                        "city": {"name": "Kyoto"},
                                    }
                                ]
                            },
                        }
                    ]
                }
            }
        ),
    )
    monkeypatch.setattr(
        events,
        "resolve_destination_coordinates",
        lambda location_name: (35.0116, 135.7681),
    )

    normalized = events.enrich_events_from_ticketmaster(
        TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
        )
    )

    assert normalized[0]["latitude"] == 35.0116
    assert normalized[0]["longitude"] == 135.7681
    assert normalized[0]["estimated_duration_minutes"] == 120
