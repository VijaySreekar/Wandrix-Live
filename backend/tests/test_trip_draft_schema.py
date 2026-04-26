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
    assert draft.budget_estimate is None
    assert draft.status.phase == "opening"
    assert draft.status.confirmed_fields == []
    assert draft.status.inferred_fields == []
    assert draft.status.brochure_ready is False
    assert draft.conversation.open_questions == []
    assert draft.conversation.memory.field_memory == {}
