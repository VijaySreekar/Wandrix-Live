from app.schemas.trip_draft import TripDraft


def test_trip_draft_defaults_match_board_shape() -> None:
    draft = TripDraft(
        trip_id="trip_test",
        thread_id="thread_test",
        title="Japan Spring Escape",
    )

    assert draft.configuration.selected_modules.flights is True
    assert draft.configuration.selected_modules.weather is True
    assert draft.timeline == []
    assert draft.module_outputs.activities == []
    assert draft.status.phase == "collecting_requirements"
    assert draft.status.brochure_ready is False

