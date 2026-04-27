from contextlib import contextmanager

from app.services.providers.movement import (
    MovementEstimate,
    estimate_travel_duration_minutes,
)


def test_mapbox_movement_falls_back_to_heuristic_when_routing_fails(monkeypatch) -> None:
    @contextmanager
    def _raising_client():
        raise RuntimeError("routing unavailable")
        yield

    monkeypatch.setattr(
        "app.services.providers.movement.create_mapbox_client",
        _raising_client,
    )

    estimate = estimate_travel_duration_minutes(
        origin_latitude=35.0116,
        origin_longitude=135.7681,
        destination_latitude=35.0212,
        destination_longitude=135.7767,
    )

    assert isinstance(estimate, MovementEstimate)
    assert estimate is not None
    assert estimate.minutes >= 8
    assert estimate.source == "heuristic"
