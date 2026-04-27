from types import SimpleNamespace

from app.schemas.trip_planning import TripConfiguration
from app.services.providers import activities


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeGeoapifyClient:
    def __init__(self, responses_by_category: dict[str, dict], calls: list[str]) -> None:
        self._responses_by_category = responses_by_category
        self._calls = calls

    def __enter__(self) -> "_FakeGeoapifyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, path: str, params: dict) -> _FakeResponse:
        assert path == "/places"
        category = params["categories"]
        self._calls.append(category)
        return _FakeResponse(self._responses_by_category.get(category, {"features": []}))


def _feature(
    *,
    name: str,
    category: str,
    address_line2: str,
    coordinates: tuple[float, float],
    distance: int = 450,
) -> dict:
    longitude, latitude = coordinates
    return {
        "type": "Feature",
        "properties": {
            "name": name,
            "categories": [category],
            "address_line2": address_line2,
            "formatted": f"{name}, {address_line2}",
            "distance": distance,
            "suburb": address_line2.split(",")[0].strip(),
            "city": "Kyoto",
        },
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
    }


def test_geoapify_activity_enrichment_filters_generic_restaurants_and_keeps_real_anchors(
    monkeypatch,
) -> None:
    calls: list[str] = []
    responses = {
        "commercial.marketplace": {
            "features": [
                _feature(
                    name="Nishiki Market",
                    category="commercial.marketplace",
                    address_line2="Nakagyo Ward, Kyoto",
                    coordinates=(135.7681, 35.0051),
                )
            ]
        },
        "catering.restaurant": {
            "features": [
                _feature(
                    name="サイゼリヤ",
                    category="catering.restaurant",
                    address_line2="Nakagyo Ward, Kyoto",
                    coordinates=(135.7691, 35.0052),
                ),
                _feature(
                    name="Pontocho Food Alley",
                    category="catering.restaurant",
                    address_line2="Nakagyo Ward, Kyoto",
                    coordinates=(135.7710, 35.0046),
                ),
            ]
        },
        "catering.cafe": {
            "features": [
                _feature(
                    name="ドトール",
                    category="catering.cafe",
                    address_line2="Nakagyo Ward, Kyoto",
                    coordinates=(135.7701, 35.0056),
                )
            ]
        },
        "entertainment.culture": {
            "features": [
                _feature(
                    name="Kyoto National Museum",
                    category="entertainment.culture",
                    address_line2="Higashiyama Ward, Kyoto",
                    coordinates=(135.7727, 34.9899),
                )
            ]
        },
        "tourism.sights": {
            "features": [
                _feature(
                    name="Kiyomizu-dera",
                    category="tourism.sights",
                    address_line2="Higashiyama Ward, Kyoto",
                    coordinates=(135.7850, 34.9949),
                )
            ]
        },
    }

    monkeypatch.setattr(
        activities,
        "create_geoapify_client",
        lambda: _FakeGeoapifyClient(responses, calls),
    )
    monkeypatch.setattr(activities, "get_settings", lambda: SimpleNamespace(geoapify_api_key="test"))
    monkeypatch.setattr(activities, "resolve_destination_coordinates", lambda _: (35.0, 135.0))

    results = activities.enrich_activities_from_geoapify(
        TripConfiguration(
            to_location="Kyoto",
            activity_styles=["food", "culture"],
        )
    )

    assert calls == [
        "commercial.marketplace",
        "catering.restaurant",
        "catering.cafe",
        "entertainment.culture",
        "tourism.sights",
    ]
    assert [item.title for item in results] == [
        "Nishiki Market",
        "Pontocho Food Alley",
        "Kyoto National Museum",
        "Kiyomizu-dera",
    ]
    assert all(item.title not in {"サイゼリヤ", "ドトール"} for item in results)


def test_geoapify_activity_enrichment_uses_english_first_titles_and_preserves_local_name(
    monkeypatch,
) -> None:
    calls: list[str] = []
    responses = {
        "commercial.marketplace": {
            "features": [
                _feature(
                    name="錦市場",
                    category="commercial.marketplace",
                    address_line2="Nishiki Market, Nakagyo Ward, Kyoto",
                    coordinates=(135.7649, 35.0048),
                )
            ]
        },
        "catering.restaurant": {"features": []},
        "catering.cafe": {"features": []},
    }

    monkeypatch.setattr(
        activities,
        "create_geoapify_client",
        lambda: _FakeGeoapifyClient(responses, calls),
    )
    monkeypatch.setattr(activities, "get_settings", lambda: SimpleNamespace(geoapify_api_key="test"))
    monkeypatch.setattr(activities, "resolve_destination_coordinates", lambda _: (35.0, 135.0))

    results = activities.enrich_activities_from_geoapify(
        TripConfiguration(
            to_location="Kyoto",
            activity_styles=["food"],
        )
    )

    assert calls == ["commercial.marketplace", "catering.restaurant", "catering.cafe"]
    assert len(results) == 1
    assert results[0].title == "Nishiki Market"
    assert results[0].venue_name == "錦市場"
    assert results[0].location_label == "Nakagyo Ward, Kyoto"
    assert "Local name: 錦市場" in results[0].notes


def test_geoapify_activity_enrichment_avoids_street_name_titles_for_local_script_places(
    monkeypatch,
) -> None:
    calls: list[str] = []
    responses = {
        "commercial.marketplace": {
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "name": "錦市場",
                        "categories": ["building", "commercial.marketplace"],
                        "address_line2": "Nishikikōji Street, Nakagyo Ward, Kyoto",
                        "formatted": "錦市場, Nishikikōji Street, Nakagyo Ward, Kyoto",
                        "distance": 420,
                        "suburb": "Nakagyo Ward",
                        "city": "Kyoto",
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [135.7649, 35.0048],
                    },
                }
            ]
        },
        "catering.restaurant": {"features": []},
        "catering.cafe": {"features": []},
    }

    monkeypatch.setattr(
        activities,
        "create_geoapify_client",
        lambda: _FakeGeoapifyClient(responses, calls),
    )
    monkeypatch.setattr(activities, "get_settings", lambda: SimpleNamespace(geoapify_api_key="test"))
    monkeypatch.setattr(activities, "resolve_destination_coordinates", lambda _: (35.0, 135.0))

    results = activities.enrich_activities_from_geoapify(
        TripConfiguration(
            to_location="Kyoto",
            activity_styles=["food"],
        )
    )

    assert len(results) == 1
    assert results[0].title == "Market tasting walk in Nakagyo Ward"
    assert results[0].category == "commercial.marketplace"
    assert results[0].location_label == "Nakagyo Ward, Kyoto"
