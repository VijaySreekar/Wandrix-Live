import json
from pathlib import Path

from app.graph.nodes import bootstrap
from app.graph.planner import runner
from app.graph.planner.conversation_state import build_conversation_state
from app.graph.planner.turn_models import (
    ConversationOptionCandidate,
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


def test_first_prompt_triggers_planning_mode_gate_and_preserves_brief(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            travel_window="early October",
            inferred_fields=["to_location", "travel_window"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="medium"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="medium"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_inferred"),
                TripFieldSourceUpdate(field="travel_window", source="user_inferred"),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Maybe Lisbon in early October.",
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

    assert result["trip_draft"]["configuration"]["to_location"] == "Lisbon"
    assert result["trip_draft"]["configuration"]["travel_window"] == "early October"
    assert conversation["planning_mode"] is None
    assert conversation["planning_mode_status"] == "not_selected"
    assert conversation["suggestion_board"]["mode"] == "planning_mode_choice"
    assert "before i proceed" in result["assistant_response"].lower()
    assert "quick plan" in result["assistant_response"].lower()
    assert "advanced planning" in result["assistant_response"].lower()


def test_confirm_trip_details_board_action_persists_weather_preference(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_weather_1",
                "type": "confirm_trip_details",
                "to_location": "Seville",
                "travel_window": "late April",
                "trip_length": "4 nights",
                "weather_preference": "warm",
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
    field_memory = result["trip_draft"]["conversation"]["memory"]["field_memory"]

    assert configuration["weather_preference"] == "warm"
    assert field_memory["weather_preference"]["source"] == "board_action"
    assert field_memory["weather_preference"]["confidence_level"] == "high"


def test_select_advanced_plan_sets_real_advanced_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_advanced",
                "type": "select_advanced_plan",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Lisbon",
                    "travel_window": "early October",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Maybe Lisbon in early October.",
                                "changed_fields": ["to_location", "travel_window"],
                                "resulting_phase": "collecting_requirements",
                            }
                        ]
                    }
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["planning_mode_status"] == "selected"
    assert conversation["advanced_step"] == "intake"
    assert conversation["suggestion_board"]["mode"] == "details_collection"
    assert conversation["suggestion_board"]["title"] == "Build the Advanced Planning brief"
    assert "advanced planning is selected" in result["assistant_response"].lower()
    assert "defaulting to quick plan" not in result["assistant_response"].lower()


def test_advanced_intake_prefers_details_collection_over_generic_decision_cards(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_advanced_intake",
                "type": "select_advanced_plan",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "decision_cards": [
                        {
                            "title": "Choose the timing shape for Kyoto",
                            "description": "A rough travel window is the next useful choice.",
                            "options": ["Spring city break", "Autumn weekend"],
                        }
                    ],
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Maybe Kyoto.",
                                "changed_fields": ["to_location"],
                                "resulting_phase": "collecting_requirements",
                            }
                        ]
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "intake"
    assert conversation["suggestion_board"]["mode"] == "details_collection"
    assert conversation["suggestion_board"]["title"] == "Build the Advanced Planning brief"
    assert "shared brief-building step" in result["assistant_response"].lower()


def test_advanced_mode_branches_to_anchor_choice_without_generating_quick_plan(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
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
                "weather": True,
                "activities": True,
                "hotels": True,
            },
            confirmed_trip_brief=True,
            requested_planning_mode="advanced",
            assistant_response="",
        ),
    )

    def _fail_quick_plan(**_kwargs):
        raise AssertionError("Quick Plan draft should not run for advanced mode.")

    monkeypatch.setattr(runner, "generate_quick_plan_draft", _fail_quick_plan)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Let's do Kyoto in late March for 5 nights and use advanced planning.",
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
    observability = result["metadata"]["planner_observability"]
    anchor_cards = conversation["suggestion_board"]["advanced_anchor_cards"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "choose_anchor"
    assert conversation["advanced_anchor"] is None
    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"
    assert len(anchor_cards) == 4
    assert {card["id"] for card in anchor_cards} == {
        "flight",
        "stay",
        "trip_style",
        "activities",
    }
    assert sum(1 for card in anchor_cards if card["recommended"]) == 1
    assert next(card for card in anchor_cards if card["recommended"])["id"] == "flight"
    assert observability["provider_activation"]["quick_plan_ready"] is False
    assert result["trip_draft"]["timeline"] == []
    assert "instead of drafting the itinerary right away" in result["assistant_response"].lower()
    assert "flights, stay, trip style, or activities" in result["assistant_response"].lower()


def test_select_advanced_anchor_moves_advanced_flow_forward(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_stay",
                "type": "select_advanced_anchor",
                "advanced_anchor": "stay",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "choose_anchor",
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the current working trip details in chat.",
                                "options": [],
                                "selected_option": "confirm_trip_details",
                            }
                        ]
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    decision_history = conversation["memory"]["decision_history"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "anchor_flow"
    assert conversation["advanced_anchor"] == "stay"
    assert conversation["suggestion_board"]["mode"] == "advanced_next_step"
    assert "lead kyoto with stay first" in result["assistant_response"].lower()
    assert any(
        event["title"] == "Advanced anchor selected"
        and event["selected_option"] == "stay"
        for event in decision_history
    )


def test_chat_requested_advanced_anchor_moves_flow_forward(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_advanced_anchor="stay",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Stay first, flights later.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "selected_modules": {
                        "flights": True,
                        "weather": True,
                        "activities": True,
                        "hotels": True,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "choose_anchor",
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    decision_history = conversation["memory"]["decision_history"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "anchor_flow"
    assert conversation["advanced_anchor"] == "stay"
    assert conversation["suggestion_board"]["mode"] == "advanced_next_step"
    assert "lead kyoto with stay first" in result["assistant_response"].lower()
    assert any(
        event["title"] == "Advanced anchor selected"
        and event["selected_option"] == "stay"
        for event in decision_history
    )


def test_advanced_mode_allows_flexible_departure_to_reach_anchor_choice(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            confirmed_trip_brief=True,
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "That brief looks right.",
            "trip_draft": {
                "title": "Kyoto Food Escape",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "from_location_flexible": True,
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "intake",
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Kyoto in late March for around five nights. Departure is flexible for now.",
                                "changed_fields": [
                                    "to_location",
                                    "travel_window",
                                    "trip_length",
                                    "from_location_flexible",
                                ],
                                "resulting_phase": "collecting_requirements",
                            }
                        ]
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    board = conversation["suggestion_board"]
    recommended_card = next(
        card for card in board["advanced_anchor_cards"] if card["recommended"]
    )

    assert conversation["advanced_step"] == "choose_anchor"
    assert board["mode"] == "advanced_anchor_choice"
    assert "from_location" not in result["trip_draft"]["status"]["missing_fields"]
    assert recommended_card["id"] != "flight"


def test_advanced_details_collection_marks_flexible_departure_as_route_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_advanced_flexible_origin",
                "type": "select_advanced_plan",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "from_location_flexible": True,
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Kyoto sounds good. Departure is flexible for now.",
                                "changed_fields": [
                                    "to_location",
                                    "from_location_flexible",
                                ],
                                "resulting_phase": "collecting_requirements",
                            }
                        ]
                    }
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    route_item = next(item for item in board["have_details"] if item["id"] == "route")

    assert board["mode"] == "details_collection"
    assert board["details_form"]["from_location_flexible"] is True
    assert route_item["value"] == "Flexible departure -> Kyoto"


def test_unresolved_destination_options_get_explicit_helper_state(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            mentioned_options=[
                ConversationOptionCandidate(kind="destination", value="Kyoto"),
                ConversationOptionCandidate(kind="destination", value="Osaka"),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Kyoto or Osaka, not sure yet.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Kyoto or Osaka, not sure yet.",
                                "changed_fields": [],
                                "resulting_phase": "opening",
                            }
                        ]
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert board["mode"] == "helper"
    assert "kyoto" in board["title"].lower()
    assert "osaka" in board["title"].lower()
    assert "both options are still in play" in board["subtitle"].lower()
    assert "do not need to force the destination yet" in result["assistant_response"].lower()


def test_advanced_mode_allows_flexible_travellers_to_reach_anchor_choice(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            confirmed_trip_brief=True,
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "That brief looks right.",
            "trip_draft": {
                "title": "Kyoto Food Escape",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "travelers_flexible": True,
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "intake",
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Kyoto in late March for five nights. Traveller count is still flexible.",
                                "changed_fields": [
                                    "to_location",
                                    "travel_window",
                                    "trip_length",
                                    "travelers_flexible",
                                ],
                                "resulting_phase": "collecting_requirements",
                            }
                        ]
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]

    assert conversation["advanced_step"] == "choose_anchor"
    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"
    assert "adults" not in result["trip_draft"]["status"]["missing_fields"]


def test_quick_plan_blocks_flights_until_traveller_count_is_reliable(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            from_location="London",
            travel_window="late September",
            trip_length="4 nights",
            confirmed_fields=["to_location", "from_location", "travel_window", "trip_length"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="from_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="high"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="from_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_explicit"),
                TripFieldSourceUpdate(field="trip_length", source="user_explicit"),
            ],
            selected_modules={
                "flights": True,
                "weather": False,
                "activities": False,
                "hotels": True,
            },
            travelers_flexible=True,
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Yes, use Quick Plan. It will probably be two of us, but that is still flexible.",
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

    assert observability["provider_activation"]["quick_plan_ready"] is False
    assert observability["provider_activation"]["blocked_modules"]["flights"] == [
        "traveller count is not reliable enough yet"
    ]
    assert observability["provider_activation"]["blocked_modules"]["hotels"] == [
        "traveller count is not reliable enough yet"
    ]


def test_zero_adults_does_not_count_as_reliable_traveller_signal(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Kyoto",
            from_location="London",
            travel_window="late March",
            trip_length="5 nights",
            confirmed_fields=["to_location", "from_location", "travel_window", "trip_length"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="from_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="high"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="from_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_explicit"),
                TripFieldSourceUpdate(field="trip_length", source="user_explicit"),
            ],
            selected_modules={
                "flights": True,
                "weather": False,
                "activities": False,
                "hotels": True,
            },
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Go ahead with a quick plan.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "travelers": {
                        "adults": 0,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert observability["provider_activation"]["traveler_ready"] is False
    assert observability["provider_activation"]["field_readiness"]["travellers"]["has_value"] is False
    assert observability["provider_activation"]["blocked_modules"]["flights"] == [
        "traveller count is not reliable enough yet"
    ]
    assert observability["provider_activation"]["blocked_modules"]["hotels"] == [
        "traveller count is not reliable enough yet"
    ]


def test_budget_posture_alone_is_enough_for_required_budget_readiness(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_budget_posture_only",
                "type": "select_advanced_plan",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "budget_posture": "mid_range",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "memory": {
                        "turn_summaries": [
                            {
                                "turn_id": "turn_seed",
                                "user_message": "Kyoto in late March for five nights, probably mid-range overall.",
                                "changed_fields": [
                                    "to_location",
                                    "travel_window",
                                    "trip_length",
                                    "budget_posture",
                                ],
                                "resulting_phase": "collecting_requirements",
                            }
                        ]
                    }
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    budget_item = next(item for item in board["have_details"] if item["id"] == "budget")

    assert board["mode"] == "details_collection"
    assert budget_item["value"] == "mid-range"
    assert "budget_posture" not in result["trip_draft"]["status"]["missing_fields"]


def test_advanced_activities_only_scope_keeps_details_board_narrow(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Let us just focus on activities for now.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "travelers": {
                        "adults": 2,
                    },
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "intake",
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    need_detail_ids = {item["id"] for item in board["need_details"]}

    assert board["mode"] == "details_collection"
    assert "activities for now" in board["subtitle"].lower()
    assert "flights or hotels for later" in board["subtitle"].lower()
    assert "budget" not in need_detail_ids


def test_confirm_trip_details_persists_custom_trip_style(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_custom_style",
                "type": "confirm_trip_details",
                "to_location": "Kyoto",
                "travel_window": "late March",
                "trip_length": "5 nights",
                "custom_style": "slow temple mornings and market-heavy afternoons",
                "selected_modules": {
                    "flights": False,
                    "weather": True,
                    "activities": True,
                    "hotels": True,
                },
                "adults": 2,
                "budget_posture": "mid_range",
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
    field_memory = result["trip_draft"]["conversation"]["memory"]["field_memory"]

    assert (
        configuration["custom_style"]
        == "slow temple mornings and market-heavy afternoons"
    )
    assert field_memory["custom_style"]["source"] == "board_action"
    assert field_memory["custom_style"]["confidence_level"] == "high"


def test_reselecting_same_advanced_anchor_does_not_duplicate_decision_history(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_stay_repeat",
                "type": "select_advanced_anchor",
                "advanced_anchor": "stay",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "anchor_flow",
                    "advanced_anchor": "stay",
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the current working trip details in chat.",
                                "options": [],
                                "selected_option": "confirm_trip_details",
                            },
                            {
                                "id": "decision_anchor_stay",
                                "title": "Advanced anchor selected",
                                "description": "The user chose stay to lead the next Advanced Planning step.",
                                "options": ["flight", "stay", "trip_style", "activities"],
                                "selected_option": "stay",
                            },
                        ]
                    },
                },
            },
        }
    )

    decision_history = result["trip_draft"]["conversation"]["memory"]["decision_history"]
    matching_events = [
        event
        for event in decision_history
        if event["title"] == "Advanced anchor selected"
        and event["selected_option"] == "stay"
    ]

    assert len(matching_events) == 1
