from app.graph.nodes import bootstrap
from app.graph.nodes.bootstrap import TripTurnUpdate


def test_process_trip_turn_persists_confirmation_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Marrakesh",
            activity_styles=["food"],
            inferred_fields=["to_location", "activity_styles"],
            open_questions=["What rough month are you thinking about?"],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Somewhere warm with amazing food, maybe Marrakesh.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    status = result["trip_draft"]["status"]

    assert status["phase"] == "collecting_requirements"
    assert status["missing_fields"] == ["from_location", "start_date", "end_date"]
    assert status["confirmed_fields"] == []
    assert status["inferred_fields"] == ["activity_styles", "to_location"]
    assert status["open_questions"] == [
        "What rough month are you thinking about?",
        "Where would you be flying or traveling from?",
    ]
    assert "Marrakesh" in result["assistant_response"]
    assert "What rough month are you thinking about?" in result["assistant_response"]


def test_process_trip_turn_promotes_confirmed_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            confirmed_fields=["to_location"],
            assistant_response="Locked Lisbon as the destination.",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Definitely Lisbon.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {"to_location": "Lisbon"},
                "timeline": [],
                "module_outputs": {},
                "status": {
                    "inferred_fields": ["to_location"],
                    "open_questions": ["Which city are you leaning toward?"],
                },
            },
        }
    )

    status = result["trip_draft"]["status"]

    assert status["confirmed_fields"] == ["to_location"]
    assert status["inferred_fields"] == []


def test_inferred_update_does_not_override_confirmed_destination(monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Porto",
            inferred_fields=["to_location"],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Maybe Porto could work too.",
            "trip_draft": {
                "title": "Lisbon trip",
                "configuration": {"to_location": "Lisbon"},
                "timeline": [],
                "module_outputs": {},
                "status": {
                    "confirmed_fields": ["to_location"],
                },
            },
        }
    )

    configuration = result["trip_draft"]["configuration"]
    status = result["trip_draft"]["status"]

    assert configuration["to_location"] == "Lisbon"
    assert status["confirmed_fields"] == ["to_location"]
    assert status["inferred_fields"] == []


def test_confirmed_update_can_replace_previous_destination(monkeypatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Porto",
            confirmed_fields=["to_location"],
            assistant_response="Switching the destination to Porto.",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Actually make it Porto.",
            "trip_draft": {
                "title": "Lisbon trip",
                "configuration": {"to_location": "Lisbon"},
                "timeline": [],
                "module_outputs": {},
                "status": {
                    "confirmed_fields": ["to_location"],
                },
            },
        }
    )

    configuration = result["trip_draft"]["configuration"]
    status = result["trip_draft"]["status"]

    assert configuration["to_location"] == "Porto"
    assert status["confirmed_fields"] == ["to_location"]
