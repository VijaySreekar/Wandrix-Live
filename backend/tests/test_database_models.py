from app.models import BrowserSessionModel, TripDraftModel, TripModel


def test_database_models_have_expected_table_names() -> None:
    assert BrowserSessionModel.__tablename__ == "browser_sessions"
    assert TripModel.__tablename__ == "trips"
    assert TripDraftModel.__tablename__ == "trip_drafts"
