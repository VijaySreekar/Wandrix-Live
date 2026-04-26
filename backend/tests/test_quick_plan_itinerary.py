from datetime import date, datetime
from types import SimpleNamespace

from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services import quick_plan_itinerary
from app.services.quick_plan_itinerary import build_provider_backed_quick_plan_itinerary


def test_provider_backed_itinerary_builds_clocked_barcelona_timeline(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        quick_plan_itinerary,
        "get_settings",
        lambda: SimpleNamespace(geoapify_api_key="geoapify"),
    )
    monkeypatch.setattr(
        quick_plan_itinerary,
        "enrich_activities_from_geoapify",
        lambda *_args, **_kwargs: [
            ActivityDetail(
                id="geoapify_1",
                title="Santa Caterina Market",
                category="commercial.marketplace",
                location_label="El Born",
                source_label="Geoapify",
                estimated_duration_minutes=45,
                notes=["Provider-backed food market add-on."],
            )
        ],
    )
    monkeypatch.setattr(
        quick_plan_itinerary,
        "enrich_events_from_ticketmaster",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        quick_plan_itinerary,
        "estimate_travel_duration_minutes",
        lambda **_kwargs: SimpleNamespace(minutes=25),
    )

    result = build_provider_backed_quick_plan_itinerary(
        configuration=TripConfiguration(
            from_location="London",
            to_location="Barcelona",
            start_date=date(2027, 5, 7),
            end_date=date(2027, 5, 10),
            travelers={"adults": 2},
        ),
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="out",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="BCN",
                    departure_time=datetime(2027, 5, 7, 8, 0),
                    arrival_time=datetime(2027, 5, 7, 11, 0),
                    notes=[],
                ),
                FlightDetail(
                    id="ret",
                    direction="return",
                    carrier="BA",
                    departure_airport="BCN",
                    arrival_airport="LHR",
                    departure_time=datetime(2027, 5, 10, 18, 0),
                    arrival_time=datetime(2027, 5, 10, 20, 0),
                    notes=[],
                ),
            ],
            hotels=[
                HotelStayDetail(
                    id="hotel",
                    hotel_name="Barcelona Central Stay",
                    area="Eixample",
                    address="Carrer de Mallorca, Barcelona",
                    notes=[],
                )
            ],
            weather=[
                WeatherDetail(
                    id="weather_1",
                    day_label="Day 2",
                    summary="Clear",
                    forecast_date=date(2027, 5, 8),
                    weather_risk_level="low",
                )
            ],
        ),
    )

    titles = [item.title for item in result.timeline]
    assert "Gothic Quarter walk" in titles or "Sagrada Familia" in titles
    assert "Santa Caterina Market" in titles
    assert any(item.type == "transfer" for item in result.timeline)
    assert any(item.type == "meal" and item.day_label == "Day 2" for item in result.timeline)
    assert any(item.type == "flight" and item.day_label == "Day 1" for item in result.timeline)
    assert any(item.type == "flight" and item.day_label == "Day 4" for item in result.timeline)
    assert all(item.start_at and item.end_at for item in result.timeline)
    assert result.module_outputs.activities[0].title == "Santa Caterina Market"


def test_provider_backed_itinerary_uses_curated_fallback_when_providers_fail(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        quick_plan_itinerary,
        "get_settings",
        lambda: SimpleNamespace(geoapify_api_key="geoapify"),
    )
    monkeypatch.setattr(
        quick_plan_itinerary,
        "enrich_activities_from_geoapify",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("geoapify down")),
    )
    monkeypatch.setattr(
        quick_plan_itinerary,
        "enrich_events_from_ticketmaster",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("ticketmaster down")),
    )
    monkeypatch.setattr(
        quick_plan_itinerary,
        "estimate_travel_duration_minutes",
        lambda **_kwargs: SimpleNamespace(minutes=30),
    )

    result = build_provider_backed_quick_plan_itinerary(
        configuration=TripConfiguration(
            from_location="London",
            to_location="Kyoto",
            start_date=date(2027, 4, 10),
            end_date=date(2027, 4, 12),
            travelers={"adults": 2},
        ),
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="out",
                    direction="outbound",
                    carrier="Best-fit route estimate",
                    departure_airport="LHR",
                    arrival_airport="KIX",
                    notes=[],
                ),
                FlightDetail(
                    id="ret",
                    direction="return",
                    carrier="Best-fit route estimate",
                    departure_airport="KIX",
                    arrival_airport="LHR",
                    notes=[],
                ),
            ],
            hotels=[
                HotelStayDetail(
                    id="hotel",
                    hotel_name="Central Kyoto Stay",
                    area="Central Kyoto",
                    notes=[],
                )
            ],
        ),
    )

    titles = [item.title for item in result.timeline]
    assert any("Transfer from KIX" in title for title in titles)
    assert any("Kiyomizu" in title or "Fushimi Inari" in title for title in titles)
    assert any(item.type == "meal" for item in result.timeline)
    assert any(
        item.type == "transfer" and "95 minutes" in " ".join(item.details)
        for item in result.timeline
    )
