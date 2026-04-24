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
