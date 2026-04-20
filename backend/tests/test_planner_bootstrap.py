from app.graph.nodes import bootstrap
from app.graph.planner import runner
from app.graph.planner.turn_models import TripFieldConfidenceUpdate, TripTurnUpdate


def test_process_trip_turn_persists_confirmation_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Marrakesh",
            activity_styles=["food"],
            inferred_fields=["to_location", "activity_styles"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="medium"),
                TripFieldConfidenceUpdate(field="activity_styles", confidence="medium"),
            ],
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
    conversation = result["trip_draft"]["conversation"]
    field_memory = conversation["memory"]["field_memory"]

    assert status["phase"] == "collecting_requirements"
    assert status["missing_fields"] == [
        "from_location",
        "start_date",
        "end_date",
        "adults",
        "budget_posture",
    ]
    assert status["confirmed_fields"] == []
    assert status["inferred_fields"] == ["activity_styles", "to_location"]
    open_questions = [item["question"] for item in conversation["open_questions"]]
    assert "What rough month are you thinking about?" in open_questions
    assert any("travell" in question.lower() and "from" in question.lower() for question in open_questions)
    assert field_memory["to_location"]["confidence_level"] == "medium"
    assert field_memory["activity_styles"]["confidence_level"] == "medium"
    assert "Marrakesh" in result["assistant_response"]
    assert "What rough month are you thinking about?" in result["assistant_response"]


def test_process_trip_turn_promotes_confirmed_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            confirmed_fields=["to_location"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
            ],
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
    field_memory = result["trip_draft"]["conversation"]["memory"]["field_memory"]

    assert status["confirmed_fields"] == ["to_location"]
    assert status["inferred_fields"] == []
    assert field_memory["to_location"]["confidence_level"] == "high"


def test_process_trip_turn_hydrates_legacy_field_memory_from_status(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            activity_styles=["food"],
            inferred_fields=["activity_styles"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="activity_styles", confidence="medium"),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Keep shaping this around food.",
            "trip_draft": {
                "title": "Legacy Lisbon draft",
                "configuration": {
                    "from_location": "London",
                    "to_location": "Lisbon",
                    "travel_window": "late September",
                    "trip_length": "four nights",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {
                    "confirmed_fields": ["to_location"],
                    "inferred_fields": [
                        "from_location",
                        "travel_window",
                        "trip_length",
                    ],
                },
                "conversation": {
                    "memory": {
                        "field_memory": {},
                    },
                },
            },
        }
    )

    field_memory = result["trip_draft"]["conversation"]["memory"]["field_memory"]

    assert field_memory["to_location"]["value"] == "Lisbon"
    assert field_memory["to_location"]["source"] == "user_explicit"
    assert field_memory["to_location"]["confidence_level"] == "high"
    assert field_memory["from_location"]["value"] == "London"
    assert field_memory["from_location"]["source"] == "user_inferred"
    assert field_memory["from_location"]["confidence_level"] == "medium"
    assert field_memory["travel_window"]["value"] == "late September"
    assert field_memory["trip_length"]["value"] == "four nights"
    assert field_memory["activity_styles"]["value"] == ["food"]


def test_inferred_update_does_not_override_confirmed_destination(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Porto",
            inferred_fields=["to_location"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="low"),
            ],
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
    field_memory = result["trip_draft"]["conversation"]["memory"]["field_memory"]

    assert configuration["to_location"] == "Lisbon"
    assert status["confirmed_fields"] == ["to_location"]
    assert status["inferred_fields"] == []
    assert field_memory["to_location"]["source"] == "user_explicit"
    assert field_memory["to_location"]["confidence_level"] == "high"


def test_confirmed_update_can_replace_previous_destination(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Porto",
            confirmed_fields=["to_location"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
            ],
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
    field_memory = result["trip_draft"]["conversation"]["memory"]["field_memory"]

    assert configuration["to_location"] == "Porto"
    assert status["confirmed_fields"] == ["to_location"]
    assert field_memory["to_location"]["confidence_level"] == "high"
