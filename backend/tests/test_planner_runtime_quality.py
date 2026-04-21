import json
from pathlib import Path

from app.graph.nodes import bootstrap
from app.graph.planner import runner
from app.graph.planner.conversation_state import build_conversation_state
from app.graph.planner.turn_models import (
    ProposedTimelineItem,
    QuickPlanDraft,
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


def test_turn_summary_stores_resume_friendly_state() -> None:
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Lisbon",
            travel_window="early October",
        ),
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            travel_window="early October",
            inferred_fields=["to_location", "travel_window"],
            active_goals=["Resolve the destination and timing before narrowing flights."],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Lisbon in early October is the current direction.",
        turn_id="turn_1",
        user_message="Maybe Lisbon in early October.",
        now=runner.datetime.now(runner.timezone.utc),
    )

    summary = conversation.memory.turn_summaries[-1]

    assert summary.summary_text is not None
    assert "changed destination" in summary.summary_text.lower()
    assert "still resolving" in summary.summary_text.lower()
    assert "planner focus" in summary.summary_text.lower()
    assert "to_location" in summary.changed_fields
    assert "travel_window" in summary.changed_fields
    assert summary.open_fields
    assert summary.next_open_question is not None
    assert summary.active_goal == "Resolve the destination and timing before narrowing flights."


def test_process_trip_turn_blocks_flights_until_origin_is_reliable(monkeypatch) -> None:
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
                "flights": True,
                "weather": False,
                "activities": False,
                "hotels": False,
            },
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Yes, use flights only and build the quick draft.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert result["trip_draft"]["conversation"]["planning_mode"] == "quick"
    assert observability["provider_activation"]["quick_plan_ready"] is False
    assert observability["provider_activation"]["blocked_modules"]["flights"] == [
        "departure point is not reliable enough yet"
    ]
    assert "not triggering live planning yet" in result["assistant_response"].lower()


def test_process_trip_turn_allows_ready_nonflight_modules_to_start_quick_plan(
    monkeypatch,
) -> None:
    captured: dict = {}

    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            travel_window="early October",
            trip_length="long weekend",
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

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules=None,
    ):
        captured["allowed_modules"] = sorted(allowed_modules or [])
        return TripModuleOutputs()

    monkeypatch.setattr(runner, "build_module_outputs", _fake_build_module_outputs)
    monkeypatch.setattr(
        runner,
        "generate_quick_plan_draft",
        lambda **_: QuickPlanDraft(
            board_summary="Barcelona now has a food-first quick draft built around a compact autumn weekend.",
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Tapas crawl around El Born",
                    day_label="Day 1",
                    summary="A compact first-evening route after arrival.",
                )
            ],
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Yes, just activities. Build the quick draft.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert captured["allowed_modules"] == ["activities"]
    assert observability["provider_activation"]["quick_plan_ready"] is True
    assert observability["provider_activation"]["allowed_modules"] == ["activities"]
    assert "started a quick plan" in result["assistant_response"].lower()
    assert len(result["trip_draft"]["timeline"]) == 1


def test_planner_evaluation_case_set_is_well_formed() -> None:
    fixture_path = (
        Path(__file__).resolve().parent / "fixtures" / "planner_evaluation_cases.json"
    )
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert len(cases) >= 8
    categories = {case["category"] for case in cases}
    assert {
        "broad_ask",
        "rough_dates",
        "correction",
        "rejection",
        "soft_approval",
        "explicit_confirmation",
        "profile_context",
        "module_scope",
    }.issubset(categories)
    for case in cases:
        assert case["id"]
        assert case["description"]
        assert case["turns"]
        assert isinstance(case["expected"], dict)
