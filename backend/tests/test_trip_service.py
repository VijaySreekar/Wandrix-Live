from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.services.trip_service import _effective_trip_updated_at
from app.schemas.trip_draft import TripDraftStatus


def test_trip_draft_status_defaults() -> None:
    status = TripDraftStatus()

    assert status.phase == "opening"
    assert status.brochure_ready is False
    assert status.missing_fields == []


def test_effective_trip_updated_at_uses_fresher_draft_activity() -> None:
    trip_updated_at = datetime(2026, 4, 24, 8, tzinfo=UTC)
    draft_updated_at = trip_updated_at + timedelta(hours=12)
    trip = SimpleNamespace(
        updated_at=trip_updated_at,
        draft=SimpleNamespace(updated_at=draft_updated_at, status={}),
    )

    assert _effective_trip_updated_at(trip) == draft_updated_at


def test_effective_trip_updated_at_uses_status_last_updated_at() -> None:
    trip_updated_at = datetime(2026, 4, 24, 8, tzinfo=UTC)
    status_updated_at = trip_updated_at + timedelta(hours=13)
    trip = SimpleNamespace(
        updated_at=trip_updated_at,
        draft=SimpleNamespace(
            updated_at=trip_updated_at + timedelta(hours=1),
            status={"last_updated_at": status_updated_at.isoformat()},
        ),
    )

    assert _effective_trip_updated_at(trip) == status_updated_at
