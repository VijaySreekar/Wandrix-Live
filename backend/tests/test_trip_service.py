from app.schemas.trip_draft import TripDraftStatus


def test_trip_draft_status_defaults() -> None:
    status = TripDraftStatus()

    assert status.phase == "opening"
    assert status.brochure_ready is False
    assert status.missing_fields == []
