from app.graph.nodes import bootstrap
from app.graph.planner import runner
from app.graph.planner.turn_models import (
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)


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
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="assistant_derived"),
                TripFieldSourceUpdate(field="activity_styles", source="user_inferred"),
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
        "selected_modules",
    ]
    assert status["confirmed_fields"] == []
    assert status["inferred_fields"] == ["activity_styles", "to_location"]
    open_questions = [item["question"] for item in conversation["open_questions"]]
    assert "What rough month are you thinking about?" in open_questions
    assert any("travell" in question.lower() and "from" in question.lower() for question in open_questions)
    assert field_memory["to_location"]["confidence_level"] == "medium"
    assert field_memory["to_location"]["source"] == "assistant_derived"
    assert field_memory["activity_styles"]["confidence_level"] == "medium"
    assert field_memory["activity_styles"]["source"] == "user_inferred"
    assert "Marrakesh" in result["assistant_response"]
    assert "main thing i'd confirm next" in result["assistant_response"].lower()


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
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
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


def test_process_trip_turn_moves_into_shaping_when_brief_is_usable(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            travel_window="early October",
            trip_length="long weekend",
            inferred_fields=["to_location", "travel_window", "trip_length"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="medium"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="medium"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_inferred"),
                TripFieldSourceUpdate(field="trip_length", source="user_inferred"),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Let's do Barcelona in early October for a long weekend.",
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

    assert status["phase"] == "shaping_trip"
    assert status["missing_fields"] == [
        "from_location",
        "adults",
        "activity_styles",
        "budget_posture",
        "selected_modules",
    ]
    assert "strong first direction" in result["assistant_response"].lower()


def test_process_trip_turn_keeps_profile_home_base_soft_on_brief_confirmation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            travel_window="late September",
            trip_length="4 nights",
            confirmed_fields=["to_location", "travel_window", "trip_length"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="high"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_explicit"),
                TripFieldSourceUpdate(field="trip_length", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Yes, Lisbon in late September for 4 nights sounds right.",
            "profile_context": {
                "home_city": "London",
                "preferred_styles": ["food"],
                "trip_pace": "relaxed",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    configuration = result["trip_draft"]["configuration"]
    conversation = result["trip_draft"]["conversation"]

    assert configuration["from_location"] is None
    assert "saved home base around london" in result["assistant_response"].lower()
    assert conversation["planning_mode"] is None
    assert "from_location" not in conversation["memory"]["field_memory"]


def test_process_trip_turn_ignores_weak_quick_plan_request_before_brief_confirmation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Go ahead.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    history_titles = [event["title"] for event in conversation["memory"]["decision_history"]]

    assert conversation["planning_mode"] is None
    assert conversation["planning_mode_status"] == "not_selected"
    assert "quick plan" not in result["assistant_response"].lower()
    assert "Planning mode selected" not in history_titles


def test_process_trip_turn_accepts_explicit_quick_plan_request_after_confirmation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            travel_window="late September",
            trip_length="4 nights",
            confirmed_fields=["to_location", "travel_window", "trip_length"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="high"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_explicit"),
                TripFieldSourceUpdate(field="trip_length", source="user_explicit"),
            ],
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Yes, that works. Build the quick draft.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    history_titles = [event["title"] for event in conversation["memory"]["decision_history"]]

    assert conversation["planning_mode"] == "quick"
    assert conversation["planning_mode_status"] == "selected"
    assert "started a quick plan" in result["assistant_response"].lower()
    assert "Planning mode selected" in history_titles
