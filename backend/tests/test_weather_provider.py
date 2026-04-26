from datetime import date

from app.schemas.trip_planning import TripConfiguration
from app.services.providers import weather


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "daily": {
                "time": ["2026-05-01", "2026-05-02", "2026-05-03"],
                "weather_code": [0, 63, 95],
                "temperature_2m_max": [22.2, 18.4, 31.1],
                "temperature_2m_min": [13.8, 11.2, 24.0],
            }
        }


class _FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def get(self, _path: str, params: dict):
        assert params["start_date"] == "2026-05-01"
        assert params["end_date"] == "2026-05-03"
        return _FakeResponse()


def test_open_meteo_weather_maps_forecast_signals(monkeypatch) -> None:
    configuration = TripConfiguration(
        to_location="Lisbon",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 3),
    )

    monkeypatch.setattr(weather, "_today", lambda: date(2026, 4, 26))
    monkeypatch.setattr(weather, "create_open_meteo_client", lambda: _FakeClient())

    result = weather.enrich_weather_from_open_meteo(
        configuration,
        coordinates=(38.72, -9.14),
    )

    assert result[0].forecast_date == date(2026, 5, 1)
    assert result[0].condition_tags == ["clear"]
    assert result[0].temperature_band == "mild"
    assert result[0].weather_risk_level == "low"
    assert "rain" in result[1].condition_tags
    assert result[1].weather_risk_level == "medium"
    assert "storm" in result[2].condition_tags
    assert result[2].temperature_band == "hot"
    assert result[2].weather_risk_level == "high"


def test_open_meteo_weather_clamps_forecast_window_to_provider_horizon(
    monkeypatch,
) -> None:
    captured: dict = {}

    class _ClampedResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "daily": {
                    "time": [
                        "2026-05-07",
                        "2026-05-08",
                        "2026-05-09",
                        "2026-05-10",
                        "2026-05-11",
                    ],
                    "weather_code": [1, 1, 2, 3, 61],
                    "temperature_2m_max": [22, 22, 23, 20, 18],
                    "temperature_2m_min": [14, 14, 15, 13, 12],
                }
            }

    class _ClampedClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def get(self, _path: str, params: dict):
            captured["params"] = params
            return _ClampedResponse()

    configuration = TripConfiguration(
        to_location="Barcelona",
        start_date=date(2026, 5, 7),
        end_date=date(2026, 5, 16),
    )

    monkeypatch.setattr(weather, "_today", lambda: date(2026, 4, 26))
    monkeypatch.setattr(
        weather,
        "create_open_meteo_client",
        lambda: _ClampedClient(),
    )

    result = weather.enrich_weather_from_open_meteo(
        configuration,
        coordinates=(41.39, 2.17),
    )

    assert captured["params"]["start_date"] == "2026-05-07"
    assert captured["params"]["end_date"] == "2026-05-11"
    assert [item.forecast_date for item in result] == [
        date(2026, 5, 7),
        date(2026, 5, 8),
        date(2026, 5, 9),
        date(2026, 5, 10),
        date(2026, 5, 11),
    ]


def test_open_meteo_weather_returns_empty_when_dates_are_beyond_forecast_horizon(
    monkeypatch,
) -> None:
    class _UnexpectedClient:
        def __enter__(self):
            raise AssertionError("Weather API should not be called beyond horizon.")

        def __exit__(self, *_args) -> None:
            return None

    configuration = TripConfiguration(
        to_location="Barcelona",
        start_date=date(2026, 6, 7),
        end_date=date(2026, 6, 16),
    )

    monkeypatch.setattr(weather, "_today", lambda: date(2026, 4, 26))
    monkeypatch.setattr(
        weather,
        "create_open_meteo_client",
        lambda: _UnexpectedClient(),
    )

    assert (
        weather.enrich_weather_from_open_meteo(
            configuration,
            coordinates=(41.39, 2.17),
        )
        == []
    )
