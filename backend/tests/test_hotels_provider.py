from contextlib import contextmanager

from app.services.providers import hotels
from app.schemas.trip_planning import TripConfiguration


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.is_success = status_code < 400

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if not self.is_success:
            raise RuntimeError("request failed")


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def get(self, path: str, params: dict) -> _FakeResponse:
        self.calls.append((path, params))
        if path == "/api/search":
            return _FakeResponse(
                {
                    "result": {
                        "list": [
                            {
                                "location_id": "1",
                                "hotel_key": "g298564-d15194272",
                                "name": "Cross Hotel Kyoto",
                                "place_name": "Nakagyo Ward, Kyoto",
                                "short_place_name": "central Kyoto",
                                "street_address": "71-1 Daikokucho, Nakagyo-ku, Kyoto",
                                "url": "https://www.tripadvisor.com/Hotel_Review-g298564-d15194272-Reviews-Cross_Hotel_Kyoto-Kyoto_Kyoto_Prefecture_Kinki.html",
                                "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2a/example.jpg",
                            }
                        ]
                    }
                }
            )
        if path == "/api/rates":
            return _FakeResponse(
                {
                    "result": {
                        "currency": "GBP",
                        "rates": [
                            {"name": "Booking.com", "rate": 198.2, "tax": 23.5},
                            {"name": "Agoda", "rate": 205.0, "tax": 20.0},
                        ],
                    }
                }
            )
        raise AssertionError(f"Unexpected path {path}")


@contextmanager
def _fake_client_factory():
    yield _FakeClient()


def test_enrich_hotels_from_xotelo_preserves_image_address_and_rate(monkeypatch) -> None:
    monkeypatch.setattr(
        hotels,
        "create_rapidapi_client",
        lambda **_: _fake_client_factory(),
    )
    monkeypatch.setattr(
        hotels,
        "record_provider_usage",
        lambda **_: None,
    )

    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date="2026-05-20",
        end_date="2026-05-25",
    )

    results = hotels.enrich_hotels_from_xotelo(configuration)

    assert len(results) == 1
    hotel_option = results[0]
    assert hotel_option.hotel_name == "Cross Hotel Kyoto"
    assert hotel_option.address == "71-1 Daikokucho, Nakagyo-ku, Kyoto"
    assert hotel_option.image_url.endswith("/2a/example.jpg")
    assert hotel_option.source_url is not None
    assert hotel_option.source_label == "TripAdvisor"
    assert hotel_option.nightly_rate_amount == 198.2
    assert hotel_option.nightly_rate_currency == "GBP"
    assert hotel_option.nightly_tax_amount == 23.5
    assert hotel_option.rate_provider_name == "Booking.com"


def test_enrich_hotels_from_xotelo_skips_rate_lookup_without_exact_dates(
    monkeypatch,
) -> None:
    client = _FakeClient()

    @contextmanager
    def _client_factory():
        yield client

    monkeypatch.setattr(
        hotels,
        "create_rapidapi_client",
        lambda **_: _client_factory(),
    )
    monkeypatch.setattr(
        hotels,
        "record_provider_usage",
        lambda **_: None,
    )

    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="late March",
        trip_length="5 nights",
    )

    results = hotels.enrich_hotels_from_xotelo(configuration)

    assert len(results) == 1
    assert results[0].nightly_rate_amount is None
    assert [path for path, _ in client.calls] == ["/api/search"]
