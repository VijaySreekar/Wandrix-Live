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
from app.schemas.trip_conversation import AdvancedDateOptionCard, TripConversationState
from app.schemas.trip_planning import (
    ActivityDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


def _sample_hotel_outputs() -> TripModuleOutputs:
    return TripModuleOutputs(
        hotels=[
            HotelStayDetail(
                id="hotel_gion_house",
                hotel_name="Gion House Hotel",
                area="Gion",
                address="221 Gionmachi Kitagawa, Higashiyama-ku, Kyoto",
                image_url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/28/example.jpg",
                source_url="https://www.tripadvisor.com/Hotel_Review-g298564-d1-Reviews-Gion_House_Hotel-Kyoto_Kyoto_Prefecture_Kinki.html",
                source_label="TripAdvisor",
                nightly_rate_amount=182,
                nightly_rate_currency="GBP",
                nightly_tax_amount=19,
                rate_provider_name="Booking.com",
                notes=[
                    "Cached hotel search result from Xotelo via RapidAPI.",
                    "Area fit: food and evening walking",
                ],
            ),
            HotelStayDetail(
                id="hotel_station_stay",
                hotel_name="Kyoto Station Stay",
                area="Central Kyoto Station",
                address="84 Higashishiokoji-cho, Shimogyo-ku, Kyoto",
                image_url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/29/example.jpg",
                source_url="https://www.tripadvisor.com/Hotel_Review-g298564-d2-Reviews-Kyoto_Station_Stay-Kyoto_Kyoto_Prefecture_Kinki.html",
                source_label="TripAdvisor",
                nightly_rate_amount=164,
                nightly_rate_currency="GBP",
                nightly_tax_amount=17,
                rate_provider_name="Vio.com",
                notes=[
                    "Cached hotel search result from Xotelo via RapidAPI.",
                    "Area fit: connected hub",
                ],
            ),
            HotelStayDetail(
                id="hotel_higashiyama",
                hotel_name="Higashiyama Quiet Hotel",
                area="Higashiyama",
                address="512 Kiyomizu, Higashiyama-ku, Kyoto",
                image_url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/30/example.jpg",
                source_url="https://www.tripadvisor.com/Hotel_Review-g298564-d3-Reviews-Higashiyama_Quiet_Hotel-Kyoto_Kyoto_Prefecture_Kinki.html",
                source_label="TripAdvisor",
                notes=[
                    "Cached hotel search result from Xotelo via RapidAPI.",
                    "Area fit: quiet local base",
                ],
            ),
        ]
    )


def _sample_dense_activity_outputs() -> TripModuleOutputs:
    return TripModuleOutputs(
        activities=[
            ActivityDetail(id="activity_1", title="Late izakaya crawl"),
            ActivityDetail(id="activity_2", title="Cocktail bar hop"),
            ActivityDetail(id="activity_3", title="Night market tasting route"),
            ActivityDetail(id="activity_4", title="Evening jazz set"),
            ActivityDetail(id="activity_5", title="After-dark food alley walk"),
        ]
    )


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
        lambda **_: TripTurnUpdate(
            assistant_response="",
            start_date=runner.datetime(2027, 3, 22, tzinfo=runner.timezone.utc).date(),
            end_date=runner.datetime(2027, 3, 27, tzinfo=runner.timezone.utc).date(),
            confirmed_fields=["start_date", "end_date"],
        ),
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


def test_confirm_trip_details_board_action_persists_flexible_departure(
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
                "action_id": "action_route_flexible_1",
                "type": "confirm_trip_details",
                "to_location": "Kyoto",
                "from_location_flexible": True,
                "travel_window": "late March",
                "trip_length": "5 nights",
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

    assert configuration["from_location_flexible"] is True
    assert field_memory["from_location_flexible"]["source"] == "board_action"
    assert field_memory["from_location_flexible"]["confidence_level"] == "high"


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


def test_advanced_mode_enters_date_resolution_before_anchor_choice(
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
    date_cards = conversation["suggestion_board"]["date_option_cards"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "resolve_dates"
    assert conversation["advanced_anchor"] is None
    assert conversation["suggestion_board"]["mode"] == "advanced_date_resolution"
    assert len(date_cards) == 3
    assert sum(1 for card in date_cards if card["recommended"]) == 1
    assert observability["provider_activation"]["quick_plan_ready"] is False
    assert result["trip_draft"]["timeline"] == []
    assert "three workable date windows" in result["assistant_response"].lower()
    assert "pick the date window" in result["assistant_response"].lower()


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
    stay_cards = conversation["suggestion_board"]["stay_cards"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "anchor_flow"
    assert conversation["advanced_anchor"] == "stay"
    assert conversation["suggestion_board"]["mode"] == "advanced_stay_choice"
    assert len(stay_cards) == 4
    assert sum(1 for card in stay_cards if card["recommended"]) == 1
    assert all(card["strategy_type"] == "single_base" for card in stay_cards)
    assert "four stay strategies" in result["assistant_response"].lower()


def test_advanced_mode_with_exact_dates_skips_date_resolution(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Kyoto",
            start_date=runner.datetime(2027, 3, 22, tzinfo=runner.timezone.utc).date(),
            end_date=runner.datetime(2027, 3, 27, tzinfo=runner.timezone.utc).date(),
            confirmed_fields=["to_location", "start_date", "end_date"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="advanced",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Kyoto from 22 March to 27 March. Use Advanced Planning.",
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

    assert conversation["advanced_step"] == "choose_anchor"
    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"


def test_selecting_date_option_keeps_advanced_flow_in_resolution_until_confirmed(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.graph.planner.conversation_state.build_advanced_date_options",
        lambda configuration: [
            AdvancedDateOptionCard(
                id="date_option_fixed",
                title="22 Mar - 27 Mar",
                start_date=runner.datetime(2027, 3, 22, tzinfo=runner.timezone.utc).date(),
                end_date=runner.datetime(2027, 3, 27, tzinfo=runner.timezone.utc).date(),
                nights=5,
                reason="Cleanest late-March fit",
                recommended=True,
                cta_label="Use this trip window",
            )
        ],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_select_date_option",
                "type": "select_date_option",
                "date_option_id": "date_option_fixed",
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
                    "advanced_step": "resolve_dates",
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
    board = conversation["suggestion_board"]

    assert conversation["advanced_step"] == "resolve_dates"
    assert board["mode"] == "advanced_date_resolution"
    assert board["selected_date_option_id"] == "date_option_fixed"
    assert board["selected_start_date"] == "2027-03-22"
    assert board["selected_end_date"] == "2027-03-27"
    assert board["date_requires_confirmation"] is True
    assert result["trip_draft"]["configuration"]["start_date"] is None
    assert result["trip_draft"]["configuration"]["end_date"] is None


def test_pick_dates_for_me_selects_recommended_option_but_waits_for_confirmation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.graph.planner.conversation_state.build_advanced_date_options",
        lambda configuration: [
            AdvancedDateOptionCard(
                id="date_option_first",
                title="20 Mar - 25 Mar",
                start_date=runner.datetime(2027, 3, 20, tzinfo=runner.timezone.utc).date(),
                end_date=runner.datetime(2027, 3, 25, tzinfo=runner.timezone.utc).date(),
                nights=5,
                reason="Earlier late-March fit",
                recommended=False,
                cta_label="Use this trip window",
            ),
            AdvancedDateOptionCard(
                id="date_option_recommended",
                title="22 Mar - 27 Mar",
                start_date=runner.datetime(2027, 3, 22, tzinfo=runner.timezone.utc).date(),
                end_date=runner.datetime(2027, 3, 27, tzinfo=runner.timezone.utc).date(),
                nights=5,
                reason="Cleanest late-March fit",
                recommended=True,
                cta_label="Use this trip window",
            ),
        ],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_pick_dates",
                "type": "pick_dates_for_me",
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
                    "advanced_step": "resolve_dates",
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

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    recommended_card = next(card for card in board["date_option_cards"] if card["recommended"])

    assert board["selected_date_option_id"] == recommended_card["id"]
    assert result["trip_draft"]["conversation"]["advanced_step"] == "resolve_dates"
    assert "working trip window for now" in result["assistant_response"].lower()


def test_confirm_working_dates_persists_exact_dates_and_advances_to_anchor_choice(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.graph.planner.conversation_state.build_advanced_date_options",
        lambda configuration: [
            AdvancedDateOptionCard(
                id="date_option_fixed",
                title="22 Mar - 27 Mar",
                start_date=runner.datetime(2027, 3, 22, tzinfo=runner.timezone.utc).date(),
                end_date=runner.datetime(2027, 3, 27, tzinfo=runner.timezone.utc).date(),
                nights=5,
                reason="Cleanest late-March fit",
                recommended=True,
                cta_label="Use this trip window",
            )
        ],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_confirm_dates",
                "type": "confirm_working_dates",
                "date_option_id": "date_option_fixed",
                "start_date": "2027-03-22",
                "end_date": "2027-03-27",
                "trip_length": "5 nights",
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
                    "advanced_step": "resolve_dates",
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
                    "advanced_date_resolution": {
                        "source_timing_text": "late March",
                        "source_trip_length_text": "5 nights",
                        "recommended_date_options": [
                            {
                                "id": "date_option_fixed",
                                "title": "22 Mar - 27 Mar",
                                "start_date": "2027-03-22",
                                "end_date": "2027-03-27",
                                "nights": 5,
                                "reason": "Cleanest late-March fit",
                                "recommended": True,
                                "cta_label": "Use this trip window",
                            }
                        ],
                        "selected_date_option_id": "date_option_fixed",
                        "selected_start_date": "2027-03-22",
                        "selected_end_date": "2027-03-27",
                        "selection_status": "selected",
                        "selection_rationale": "Cleanest late-March fit",
                        "requires_confirmation": True,
                    },
                },
            },
        }
    )

    configuration = result["trip_draft"]["configuration"]
    conversation = result["trip_draft"]["conversation"]

    assert configuration["start_date"] == "2027-03-22"
    assert configuration["end_date"] == "2027-03-27"
    assert configuration["travel_window"] is None
    assert configuration["trip_length"] == "5 nights"
    assert conversation["advanced_step"] == "choose_anchor"
    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"


def test_weekend_prompts_produce_weekend_date_windows(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            travel_window="May",
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
            confirmed_trip_brief=True,
            requested_planning_mode="advanced",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Let's do Lisbon for a long weekend in May with Advanced Planning.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert board["mode"] == "advanced_date_resolution"
    assert len(board["date_option_cards"]) == 3
    assert all("Fri" in card["title"] for card in board["date_option_cards"])


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
    stay_cards = conversation["suggestion_board"]["stay_cards"]

    assert conversation["planning_mode"] == "advanced"
    assert conversation["advanced_step"] == "anchor_flow"
    assert conversation["advanced_anchor"] == "stay"
    assert conversation["suggestion_board"]["mode"] == "advanced_stay_choice"
    assert len(stay_cards) == 4
    assert sum(1 for card in stay_cards if card["recommended"]) == 1
    assert all(card["strategy_type"] == "single_base" for card in stay_cards)
    assert "four stay strategies" in result["assistant_response"].lower()
    assert any(
        event["title"] == "Advanced anchor selected"
        and event["selected_option"] == "stay"
        for event in decision_history
    )


def test_advanced_anchor_reply_wins_over_mode_selection_echo(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_planning_mode="advanced",
            requested_advanced_anchor="stay",
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "In Advanced Planning, start with stay first.",
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
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]

    assert conversation["advanced_step"] == "anchor_flow"
    assert conversation["advanced_anchor"] == "stay"
    assert conversation["suggestion_board"]["mode"] == "advanced_stay_choice"
    assert "four stay strategies" in result["assistant_response"].lower()
    assert "advanced planning is selected for kyoto" not in result["assistant_response"].lower()


def test_select_stay_option_persists_working_stay_direction(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    captured: dict = {}

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules=None,
    ):
        captured["allowed_modules"] = sorted(allowed_modules or [])
        return _sample_hotel_outputs()

    monkeypatch.setattr(runner, "build_module_outputs", _fake_build_module_outputs)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_select_stay_central",
                "type": "select_stay_option",
                "stay_option_id": "stay_central_base",
                "stay_segment_id": "segment_primary",
            },
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
                    "advanced_step": "anchor_flow",
                    "advanced_anchor": "stay",
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    stay_planning = conversation["stay_planning"]
    decision_history = conversation["memory"]["decision_history"]

    assert captured["allowed_modules"] == ["hotels"]
    assert conversation["suggestion_board"]["mode"] == "advanced_stay_hotel_choice"
    assert stay_planning["selected_stay_option_id"] == "stay_central_base"
    assert stay_planning["selected_stay_direction"] == "Central base for Kyoto"
    assert stay_planning["selection_status"] == "selected"
    assert stay_planning["hotel_substep"] == "hotel_shortlist"
    assert len(stay_planning["recommended_hotels"]) == 3
    assert stay_planning["recommended_hotels"][0]["hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["recommended_hotels"][0]["image_url"]
    assert stay_planning["recommended_hotels"][0]["address"]
    assert stay_planning["recommended_hotels"][0]["nightly_rate_amount"] == 164
    assert stay_planning["recommended_hotels"][0]["rate_provider_name"] == "Vio.com"
    assert stay_planning["compatibility_status"] == "fit"
    assert "hotel" not in (stay_planning["selection_rationale"] or "").lower()
    assert any(
        event["title"] == "Stay strategy selected"
        and event["selected_option"] == "stay_central_base"
        for event in decision_history
    )
    assert "hotel options inside that base" in result["assistant_response"].lower()


def test_select_stay_hotel_persists_working_hotel_choice(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: _sample_hotel_outputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_select_stay_hotel",
                "type": "select_stay_hotel",
                "stay_hotel_id": "hotel_station_stay",
                "stay_hotel_name": "Kyoto Station Stay",
            },
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
                "module_outputs": _sample_hotel_outputs().model_dump(mode="json"),
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "anchor_flow",
                    "advanced_anchor": "stay",
                    "stay_planning": {
                        "active_segment_id": "segment_primary",
                        "segments": [
                            {
                                "id": "segment_primary",
                                "title": "Kyoto stay",
                                "destination_name": "Kyoto",
                                "summary": "Primary stay direction for Kyoto around late March, 5 nights.",
                            }
                        ],
                        "hotel_substep": "hotel_shortlist",
                        "recommended_stay_options": [
                            {
                                "id": "stay_central_base",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Central base for Kyoto",
                                "summary": "Stay in the most walkable part of Kyoto so first-time highlights and easier evenings stay simple.",
                                "area_label": "Most central neighbourhoods",
                                "areas": [],
                                "best_for": [
                                    "Short trips that need easy orientation",
                                    "Keeping arrival and departure days lighter",
                                ],
                                "tradeoffs": ["Usually busier and a little pricier"],
                                "recommended": True,
                                "badge": "Recommended",
                                "cta_label": "Build around this base",
                            }
                        ],
                        "selected_stay_option_id": "stay_central_base",
                        "selected_stay_direction": "Central base for Kyoto",
                        "selection_status": "selected",
                        "selection_rationale": "Stay in the most walkable part of Kyoto so first-time highlights and easier evenings stay simple.",
                        "selection_assumptions": [
                            "Short trips that need easy orientation",
                            "Keeping arrival and departure days lighter",
                        ],
                        "compatibility_status": "fit",
                        "compatibility_notes": [],
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    stay_planning = conversation["stay_planning"]
    decision_history = conversation["memory"]["decision_history"]

    assert conversation["suggestion_board"]["mode"] == "advanced_stay_hotel_selected"
    assert stay_planning["selected_hotel_id"] == "hotel_station_stay"
    assert stay_planning["selected_hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["hotel_selection_status"] == "selected"
    assert stay_planning["hotel_substep"] == "hotel_selected"
    assert conversation["suggestion_board"]["hotel_cards"][0]["nightly_rate_amount"] == 164
    assert conversation["suggestion_board"]["hotel_cards"][0]["source_url"]
    assert any(
        event["title"] == "Stay hotel selected"
        and event["selected_option"] == "hotel_station_stay"
        for event in decision_history
    )
    assert "not a booking" in result["assistant_response"].lower()


def test_stay_review_state_surfaces_on_the_board(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Keep going.",
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
                    "stay_planning": {
                        "active_segment_id": "segment_primary",
                        "segments": [
                            {
                                "id": "segment_primary",
                                "title": "Kyoto stay",
                                "destination_name": "Kyoto",
                                "summary": "Primary stay direction for Kyoto around late March, 5 nights.",
                            }
                        ],
                        "recommended_stay_options": [
                            {
                                "id": "stay_quiet_local",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Quieter local base",
                                "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                                "area_label": "Calmer residential pockets",
                                "areas": [],
                                "best_for": ["Relaxed pacing and easier mornings"],
                                "tradeoffs": ["Daily travel can need more planning"],
                                "recommended": True,
                                "badge": "Recommended",
                                "cta_label": "Build around this base",
                            }
                        ],
                        "selected_stay_option_id": "stay_quiet_local",
                        "selected_stay_direction": "Quieter local base",
                        "selection_status": "needs_review",
                        "selection_rationale": "Choose a calmer local area so the trip starts and ends more gently.",
                        "selection_assumptions": ["Relaxed pacing and easier mornings"],
                        "compatibility_status": "strained",
                        "compatibility_notes": [
                            "The activity anchors now pull too far across the city for this base to stay effortless."
                        ],
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert board["mode"] == "advanced_stay_review"
    assert board["stay_selection_status"] == "needs_review"
    assert board["stay_compatibility_status"] == "strained"
    assert board["stay_compatibility_notes"] == [
        "The activity anchors now pull too far across the city for this base to stay effortless."
    ]
    assert "needs a second look" in result["assistant_response"].lower()


def test_selected_quiet_stay_moves_into_review_when_trip_turns_nightlife_heavy(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: _sample_dense_activity_outputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Keep going with the nightlife-heavy version.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "activity_styles": ["nightlife"],
                    "custom_style": "late-night bars and food alleys",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "anchor_flow",
                    "advanced_anchor": "stay",
                    "stay_planning": {
                        "active_segment_id": "segment_primary",
                        "segments": [
                            {
                                "id": "segment_primary",
                                "title": "Kyoto stay",
                                "destination_name": "Kyoto",
                                "summary": "Primary stay direction for Kyoto around late March, 5 nights.",
                            }
                        ],
                        "recommended_stay_options": [
                            {
                                "id": "stay_quiet_local",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Quieter local base",
                                "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                                "area_label": "Calmer residential pockets",
                                "areas": [],
                                "best_for": ["Relaxed pacing and easier mornings"],
                                "tradeoffs": ["Daily travel can need more planning"],
                                "recommended": True,
                                "badge": "Recommended",
                                "cta_label": "Build around this base",
                            }
                        ],
                        "selected_stay_option_id": "stay_quiet_local",
                        "selected_stay_direction": "Quieter local base",
                        "selection_status": "selected",
                        "selection_rationale": "Choose a calmer local area so the trip starts and ends more gently.",
                        "selection_assumptions": ["Relaxed pacing and easier mornings"],
                        "compatibility_status": "fit",
                        "compatibility_notes": [],
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_stay_review"
    assert stay_planning["selection_status"] == "needs_review"
    assert stay_planning["compatibility_status"] == "conflicted"
    assert "later nights" in stay_planning["compatibility_notes"][0]
    assert "needs a second look" in result["assistant_response"].lower()


def test_selected_stay_hotel_moves_into_review_when_the_stay_itself_conflicts(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(
            hotels=_sample_hotel_outputs().hotels,
            activities=_sample_dense_activity_outputs().activities,
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Let's keep the nightlife-heavy version.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "activity_styles": ["nightlife"],
                    "custom_style": "late-night bars and food alleys",
                },
                "timeline": [],
                "module_outputs": TripModuleOutputs(
                    hotels=_sample_hotel_outputs().hotels,
                    activities=_sample_dense_activity_outputs().activities,
                ).model_dump(mode="json"),
                "status": {},
                "conversation": {
                    "planning_mode": "advanced",
                    "planning_mode_status": "selected",
                    "advanced_step": "anchor_flow",
                    "advanced_anchor": "stay",
                    "stay_planning": {
                        "active_segment_id": "segment_primary",
                        "segments": [
                            {
                                "id": "segment_primary",
                                "title": "Kyoto stay",
                                "destination_name": "Kyoto",
                                "summary": "Primary stay direction for Kyoto around late March, 5 nights.",
                            }
                        ],
                        "hotel_substep": "hotel_selected",
                        "recommended_stay_options": [
                            {
                                "id": "stay_quiet_local",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Quieter local base",
                                "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                                "area_label": "Calmer residential pockets",
                                "areas": [],
                                "best_for": ["Relaxed pacing and easier mornings"],
                                "tradeoffs": ["Daily travel can need more planning"],
                                "recommended": True,
                                "badge": "Recommended",
                                "cta_label": "Build around this base",
                            }
                        ],
                        "selected_stay_option_id": "stay_quiet_local",
                        "selected_stay_direction": "Quieter local base",
                        "selection_status": "selected",
                        "selection_rationale": "Choose a calmer local area so the trip starts and ends more gently.",
                        "selection_assumptions": ["Relaxed pacing and easier mornings"],
                        "compatibility_status": "fit",
                        "compatibility_notes": [],
                        "recommended_hotels": [],
                        "selected_hotel_id": "hotel_station_stay",
                        "selected_hotel_name": "Kyoto Station Stay",
                        "hotel_selection_status": "selected",
                        "hotel_selection_rationale": "This hotel keeps the trip practical inside the chosen base.",
                        "hotel_selection_assumptions": [
                            "Relaxed pacing and easier mornings"
                        ],
                        "hotel_compatibility_status": "fit",
                        "hotel_compatibility_notes": [],
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_stay_review"
    assert stay_planning["selection_status"] == "needs_review"
    assert stay_planning["hotel_selection_status"] == "needs_review"
    assert stay_planning["hotel_compatibility_status"] == "conflicted"
    assert "stay direction" in stay_planning["hotel_compatibility_notes"][0]


def test_non_stay_advanced_anchor_keeps_generic_next_step(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_style",
                "type": "select_advanced_anchor",
                "advanced_anchor": "trip_style",
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
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]

    assert conversation["advanced_anchor"] == "trip_style"
    assert conversation["suggestion_board"]["mode"] == "advanced_next_step"
    assert "trip style first" in result["assistant_response"].lower()


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

    assert conversation["advanced_step"] == "resolve_dates"
    assert board["mode"] == "advanced_date_resolution"
    assert "from_location" not in result["trip_draft"]["status"]["missing_fields"]
    assert len(board["date_option_cards"]) == 3


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

    assert conversation["advanced_step"] == "resolve_dates"
    assert conversation["suggestion_board"]["mode"] == "advanced_date_resolution"
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
