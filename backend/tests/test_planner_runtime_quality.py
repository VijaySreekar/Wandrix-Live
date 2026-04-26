import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.graph.nodes import bootstrap
from app.graph.planner import conversation_state
from app.graph.planner import runner
from app.graph.planner.conversation_state import build_conversation_state
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_day_architecture import (
    QuickPlanDayArchitecture,
    QuickPlanDayPlan,
)
from app.graph.planner.quick_plan_provider_brief import QuickPlanProviderBrief
from app.graph.planner.quick_plan_dates import QuickPlanWorkingDateDecision
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityIssue,
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
    QuickPlanSpecialistReviewSummary,
)
from app.graph.planner.quick_plan_repair_orchestrator import QuickPlanRepairLoopResult
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.quick_plan_strategy import QuickPlanStrategyBrief
from app.graph.planner.turn_models import (
    ConversationOptionCandidate,
    DestinationSuggestionCandidate,
    ProposedTimelineItem,
    QuickPlanDraft,
    RequestedReviewResolution,
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)
from app.schemas.trip_conversation import AdvancedDateOptionCard, TripConversationState
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


@pytest.fixture(autouse=True)
def _default_quick_plan_quality_pass(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "review_quick_plan_quality",
        lambda **_: _passing_quick_plan_quality_review(),
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
            HotelStayDetail(
                id="hotel_karasuma_house",
                hotel_name="Karasuma House Kyoto",
                area="Karasuma",
                address="310 Takoyakushi-dori, Nakagyo-ku, Kyoto",
                image_url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/31/example.jpg",
                source_url="https://www.tripadvisor.com/Hotel_Review-g298564-d4-Reviews-Karasuma_House_Kyoto-Kyoto_Kyoto_Prefecture_Kinki.html",
                source_label="TripAdvisor",
                nightly_rate_amount=209,
                nightly_rate_currency="GBP",
                nightly_tax_amount=21,
                rate_provider_name="Hotels.com",
                notes=[
                    "Cached hotel search result from Xotelo via RapidAPI.",
                    "Area fit: central access and dining",
                ],
            ),
        ]
    )


def _sample_paginated_hotel_outputs() -> TripModuleOutputs:
    base_hotels = _sample_hotel_outputs().hotels
    extra_hotels = [
        HotelStayDetail(
            id=f"hotel_extra_{index}",
            hotel_name=f"Kyoto Stay Option {index}",
            area=area,
            address=f"{100 + index} Example Street, {area}, Kyoto",
            image_url=f"https://dynamic-media-cdn.tripadvisor.com/media/photo-o/3{index}/example.jpg",
            nightly_rate_amount=110 + index * 18,
            nightly_rate_currency="GBP",
            nightly_tax_amount=14 + index,
            rate_provider_name="Trip.com",
            notes=[
                "Cached hotel search result from Xotelo via RapidAPI.",
                note,
            ],
        )
        for index, area, note in [
            (1, "Nakagyo-ku", "Area fit: central access and dining"),
            (2, "Shimogyo-ku", "Area fit: practical station access"),
            (3, "Gion", "Area fit: evening food and culture"),
            (4, "Higashiyama", "Area fit: quiet local base"),
            (5, "Karasuma", "Area fit: design-led central base"),
        ]
    ]
    return TripModuleOutputs(hotels=[*base_hotels, *extra_hotels])


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
        "origin is required when flights are included"
    ]
    assert "not triggering live planning yet" in result["assistant_response"].lower()


def test_process_trip_turn_uses_confirmed_brief_origin_without_duplicate_prompt(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_planning_mode="quick",
            confirmed_trip_brief=True,
            assistant_response="",
        ),
    )
    captured: dict = {}

    def _fake_generation(**kwargs):
        captured["allowed_modules"] = kwargs["dossier"].readiness.allowed_modules
        return QuickPlanGenerationAttempt(status="empty")

    monkeypatch.setattr(runner, "run_quick_plan_generation", _fake_generation)
    monkeypatch.setattr(
        runner,
        "run_quick_plan_repair",
        lambda **_: QuickPlanGenerationAttempt(status="empty"),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Use Quick Plan and generate the first draft itinerary now.",
            "trip_draft": {
                "title": "Kyoto plan",
                "configuration": {
                    "from_location": "London",
                    "to_location": "Kyoto",
                    "start_date": "2026-05-08",
                    "end_date": "2026-05-12",
                    "travelers": {"adults": 2},
                    "activity_styles": ["food", "culture", "relaxed"],
                    "custom_style": "calm",
                    "budget_posture": "mid_range",
                    "budget_currency": "GBP",
                    "selected_modules": {
                        "flights": True,
                        "hotels": True,
                        "activities": True,
                        "weather": True,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert captured["allowed_modules"] == ["flights", "hotels", "activities", "weather"]
    assert observability["provider_activation"]["quick_plan_ready"] is True
    assert observability["provider_activation"]["origin_ready"] is True
    assert (
        observability["provider_activation"]["field_readiness"]["origin"]["source"]
        == "confirmed_brief"
    )
    assert observability["provider_activation"]["blocked_modules"] == {}
    assert "where should i search flights from" not in result["assistant_response"].lower()


def test_quick_plan_selection_confirms_complete_visible_brief_without_origin_prompt(
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
    captured: dict = {}

    def _fake_repair_loop(**kwargs):
        captured["allowed_modules"] = kwargs["dossier"].readiness.allowed_modules
        return QuickPlanRepairLoopResult(
            attempt=QuickPlanGenerationAttempt(status="empty"),
            final_completeness_review=QuickPlanReviewResult(
                status="failed",
                show_to_user=False,
                missing_outputs=["day_coverage"],
                assistant_summary="No itinerary rows were generated.",
            ),
            repair_metadata={"repair_attempted": False, "final_visible": False},
        )

    monkeypatch.setattr(runner, "run_quick_plan_repair_loop", _fake_repair_loop)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Use Quick Plan and generate the first draft itinerary now.",
            "trip_draft": {
                "title": "Kyoto plan",
                "configuration": {
                    "from_location": "London",
                    "to_location": "Kyoto",
                    "travel_window": "this month",
                    "trip_length": "5-day",
                    "travelers": {"adults": 2},
                    "activity_styles": ["food", "culture", "relaxed"],
                    "custom_style": "calm",
                    "budget_posture": "mid_range",
                    "budget_currency": "GBP",
                    "selected_modules": {
                        "flights": True,
                        "hotels": True,
                        "activities": True,
                        "weather": True,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "suggestion_board": {
                        "mode": "planning_mode_choice",
                    },
                },
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert captured["allowed_modules"] == ["flights", "hotels", "activities", "weather"]
    assert result["trip_draft"]["conversation"]["planning_mode"] == "quick"
    assert observability["provider_activation"]["brief_confirmed"] is True
    assert observability["provider_activation"]["quick_plan_ready"] is True
    assert observability["provider_activation"]["origin_ready"] is True
    assert observability["provider_activation"]["blocked_modules"] == {}
    assert "where should i search flights from" not in result["assistant_response"].lower()


def test_quick_plan_board_action_confirms_complete_visible_brief_without_origin_prompt(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    captured: dict = {}

    def _fake_repair_loop(**kwargs):
        captured["allowed_modules"] = kwargs["dossier"].readiness.allowed_modules
        return QuickPlanRepairLoopResult(
            attempt=QuickPlanGenerationAttempt(status="empty"),
            final_completeness_review=QuickPlanReviewResult(
                status="failed",
                show_to_user=False,
                missing_outputs=["day_coverage"],
                assistant_summary="No itinerary rows were generated.",
            ),
            repair_metadata={"repair_attempted": False, "final_visible": False},
        )

    monkeypatch.setattr(runner, "run_quick_plan_repair_loop", _fake_repair_loop)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_quick",
                "type": "select_quick_plan",
            },
            "trip_draft": {
                "title": "Kyoto plan",
                "configuration": {
                    "from_location": "London",
                    "to_location": "Kyoto",
                    "travel_window": "this month",
                    "trip_length": "5-day",
                    "travelers": {"adults": 2},
                    "activity_styles": ["food", "culture", "relaxed"],
                    "custom_style": "calm",
                    "budget_posture": "mid_range",
                    "budget_currency": "GBP",
                    "selected_modules": {
                        "flights": True,
                        "hotels": True,
                        "activities": True,
                        "weather": True,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "suggestion_board": {
                        "mode": "planning_mode_choice",
                    },
                },
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert captured["allowed_modules"] == ["flights", "hotels", "activities", "weather"]
    assert result["trip_draft"]["conversation"]["planning_mode"] == "quick"
    assert observability["provider_activation"]["brief_confirmed"] is True
    assert observability["provider_activation"]["quick_plan_ready"] is True
    assert observability["provider_activation"]["origin_ready"] is True
    assert observability["provider_activation"]["blocked_modules"] == {}
    assert "where should i search flights from" not in result["assistant_response"].lower()


def test_quick_plan_retry_confirms_complete_brief_after_previous_quick_block(
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
    captured: dict = {}

    def _fake_repair_loop(**kwargs):
        captured["allowed_modules"] = kwargs["dossier"].readiness.allowed_modules
        return QuickPlanRepairLoopResult(
            attempt=QuickPlanGenerationAttempt(status="empty"),
            final_completeness_review=QuickPlanReviewResult(
                status="failed",
                show_to_user=False,
                missing_outputs=["day_coverage"],
                assistant_summary="No itinerary rows were generated.",
            ),
            repair_metadata={"repair_attempted": False, "final_visible": False},
        )

    monkeypatch.setattr(runner, "run_quick_plan_repair_loop", _fake_repair_loop)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Use Quick Plan again with the current London to Kyoto brief.",
            "trip_draft": {
                "title": "Kyoto plan",
                "configuration": {
                    "from_location": "London",
                    "to_location": "Kyoto",
                    "start_date": "2026-05-07",
                    "end_date": "2026-05-11",
                    "travel_window": "this month",
                    "trip_length": "5-day",
                    "travelers": {"adults": 2},
                    "activity_styles": ["food", "culture", "relaxed"],
                    "custom_style": "calm",
                    "budget_posture": "mid_range",
                    "budget_currency": "GBP",
                    "selected_modules": {
                        "flights": True,
                        "hotels": True,
                        "activities": True,
                        "weather": True,
                    },
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "quick",
                    "planning_mode_status": "selected",
                },
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert captured["allowed_modules"] == ["flights", "hotels", "activities", "weather"]
    assert observability["provider_activation"]["brief_confirmed"] is True
    assert observability["provider_activation"]["quick_plan_ready"] is True
    assert observability["provider_activation"]["blocked_modules"] == {}
    assert "where should i search flights from" not in result["assistant_response"].lower()


def test_select_quick_plan_before_confirmed_brief_keeps_route_gate(
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
                "action_id": "action_quick",
                "type": "select_quick_plan",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Lisbon",
                    "travel_window": "late September",
                    "trip_length": "4 nights",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": None,
                    "planning_mode_status": "not_selected",
                    "suggestion_board": {
                        "mode": "planning_mode_choice",
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    board = conversation["suggestion_board"]

    assert conversation["planning_mode"] is None
    assert conversation["planning_mode_status"] == "not_selected"
    assert board["mode"] == "details_collection"
    assert board["title"] == "Build the trip brief"
    assert any(item["id"] == "route" for item in board["need_details"])
    assert "next useful detail" in result["assistant_response"].lower()
    assert "brief on the right" in result["assistant_response"].lower()


def test_provider_blocker_adds_confidence_clarification_for_profile_origin(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Lisbon",
            travel_window="late September",
            trip_length="4 nights",
            adults=2,
            confirmed_fields=["to_location", "travel_window", "trip_length", "adults"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="high"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_explicit"),
                TripFieldSourceUpdate(field="trip_length", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
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
                "configuration": {
                    "from_location": "London",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "memory": {
                        "field_memory": {
                            "from_location": {
                                "field": "from_location",
                                "value": "London",
                                "source": "profile_default",
                                "confidence_level": "high",
                            }
                        }
                    }
                },
            },
        }
    )

    observability = result["metadata"]["planner_observability"]
    open_questions = result["trip_draft"]["conversation"]["open_questions"]
    conflicts = result["trip_draft"]["conversation"]["planner_conflicts"]

    assert observability["provider_activation"]["quick_plan_ready"] is False
    assert observability["provider_activation"]["blocked_modules"]["flights"] == [
        "flight origin needs confirmation before flights are included"
    ]
    assert observability["provider_activation"]["reliability_blockers"][0]["category"] == "origin"
    assert observability["provider_activation"]["reliability_blockers"][0]["source"] == "profile_default"
    assert open_questions[0]["field"] == "from_location"
    assert open_questions[0]["question"] == "Should I use London as the flight origin?"
    assert conflicts[0]["category"] == "provider_confidence"
    assert conflicts[0]["revision_target"] == "review"
    assert "Should I use London as the flight origin?" in result["assistant_response"]


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

    def _fake_run_quick_plan_generation(**kwargs):
        captured["allowed_modules"] = sorted(
            kwargs["dossier"].readiness.allowed_modules
        )
        draft = QuickPlanDraft(
            board_summary="Barcelona now has a food-first quick draft built around a compact autumn weekend.",
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Tapas crawl around El Born",
                    day_label="Day 1",
                    summary="A compact first-evening route after arrival.",
                )
            ],
        )
        return QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(),
            timeline_module_outputs=TripModuleOutputs(),
            draft=draft,
            strategy_brief=QuickPlanStrategyBrief(
                trip_thesis="Food-first compact weekend.",
                user_intent=["food", "culture"],
            ),
            provider_brief=QuickPlanProviderBrief(
                activity_clusters=["El Born tapas"],
            ),
            day_architecture=QuickPlanDayArchitecture(
                route_logic="Keep the weekend compact.",
                days=[
                    QuickPlanDayPlan(
                        day_index=1,
                        day_label="Day 1",
                        theme="Food arrival",
                        geography_focus="El Born",
                        pacing_target="light",
                        food_culture_intent="Tapas and orientation.",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        )

    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        _fake_run_quick_plan_generation,
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
            assistant_summary="Quick Plan passed review.",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_repair",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("Repair should not run when first candidate is complete.")
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
    assert observability["provider_activation"]["quick_plan_review"]["status"] == "complete"
    assert (
        observability["provider_activation"]["quick_plan_strategy"]["trip_thesis"]
        == "Food-first compact weekend."
    )
    assert observability["provider_activation"]["quick_plan_provider_brief"][
        "activity_clusters"
    ] == ["El Born tapas"]
    assert observability["provider_activation"]["quick_plan_day_architecture"][
        "route_logic"
    ] == "Keep the weekend compact."
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempted"] is False
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempt_count"] == 0
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is True
    assert observability["provider_activation"]["quick_plan_acceptance"]["completeness_status"] == "complete"
    assert observability["provider_activation"]["quick_plan_acceptance"]["quality_status"] == "pass"
    assert (
        observability["provider_activation"]["quick_plan_acceptance"][
            "intelligence_metadata_present"
        ]
        is True
    )
    assert observability["provider_activation"]["allowed_modules"] == ["activities"]
    assert "started a quick plan" in result["assistant_response"].lower()
    assert len(result["trip_draft"]["timeline"]) == 1
    intelligence_summary = result["trip_draft"]["conversation"][
        "quick_plan_finalization"
    ]["intelligence_summary"]
    assert intelligence_summary["plan_rationale"] == "Food-first compact weekend."
    assert intelligence_summary["accepted_module_scope"] == ["activities"]
    assert intelligence_summary["excluded_modules"][0]["reason"] == "Excluded by request"
    assert intelligence_summary["review_outcome"]["quality_status"] == "pass"


def test_process_trip_turn_does_not_claim_quick_plan_when_draft_is_empty(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Kyoto",
            from_location="Coventry",
            travel_window="summer",
            trip_length="5 days",
            adults=2,
            budget_posture="mid_range",
            budget_currency="GBP",
            activity_styles=["food", "culture"],
            custom_style="calm",
            confirmed_fields=[
                "to_location",
                "from_location",
                "travel_window",
                "trip_length",
                "adults",
                "budget_posture",
                "budget_currency",
                "activity_styles",
                "custom_style",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="from_location", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="high"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="from_location", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_explicit"),
                TripFieldSourceUpdate(field="trip_length", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            selected_modules={
                "flights": True,
                "weather": True,
                "activities": True,
                "hotels": True,
            },
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )

    def _fake_apply_quick_plan_working_dates(**kwargs):
        configuration = kwargs["configuration"].model_copy(deep=True)
        llm_update = kwargs["llm_update"].model_copy(deep=True)
        configuration.start_date = datetime(2026, 7, 10, tzinfo=timezone.utc).date()
        configuration.end_date = datetime(2026, 7, 14, tzinfo=timezone.utc).date()
        llm_update.start_date = configuration.start_date
        llm_update.end_date = configuration.end_date
        llm_update.field_sources.append(
            TripFieldSourceUpdate(field="start_date", source="assistant_derived")
        )
        llm_update.field_sources.append(
            TripFieldSourceUpdate(field="end_date", source="assistant_derived")
        )
        llm_update.field_confidences.append(
            TripFieldConfidenceUpdate(field="start_date", confidence="medium")
        )
        llm_update.field_confidences.append(
            TripFieldConfidenceUpdate(field="end_date", confidence="medium")
        )
        llm_update.inferred_fields.extend(["start_date", "end_date"])
        return (
            configuration,
            llm_update,
            QuickPlanWorkingDateDecision(
                start_date=configuration.start_date,
                end_date=configuration.end_date,
                confidence="medium",
                rationale="A summer working window keeps the rough timing usable for provider checks and daily pacing.",
            ),
        )

    monkeypatch.setattr(
        runner,
        "apply_quick_plan_working_dates",
        _fake_apply_quick_plan_working_dates,
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="empty",
            module_outputs=_sample_hotel_outputs(),
            timeline_module_outputs=_sample_hotel_outputs(),
            draft=QuickPlanDraft(),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_repair",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="empty",
            module_outputs=_sample_hotel_outputs(),
            timeline_module_outputs=_sample_hotel_outputs(),
            draft=QuickPlanDraft(),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Use Quick Plan and generate the first draft itinerary now.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    response = result["assistant_response"].lower()
    observability = result["metadata"]["planner_observability"]

    assert "built a first draft itinerary" not in response
    assert "did not return a usable day-by-day itinerary" in response
    assert "10 jul to 14 jul 2026" in response
    assert "summer working window" in response
    assert "confirm this plan" not in response
    assert observability["provider_activation"]["quick_plan_working_dates"]["rationale"].startswith(
        "A summer working window"
    )
    assert observability["provider_activation"]["quick_plan_review"]["status"] == "failed"
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempted"] is True
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempt_count"] == 1
    assert observability["provider_activation"]["quick_plan_repair"]["final_visible"] is False
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is False


def test_incomplete_quick_plan_review_keeps_previous_board_state(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(
                activities=[
                    ActivityDetail(
                        id="generated_activity",
                        title="Generated private candidate",
                    )
                ]
            ),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Generated candidate summary should stay private.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Generated private candidate",
                        day_label="Day 1",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(
            status="incomplete",
            show_to_user=False,
            missing_outputs=["day_coverage"],
            review_notes=["Candidate does not cover all days."],
            assistant_summary=(
                "I generated a Quick Plan candidate, but the private review found missing day coverage, so I kept the current board unchanged."
            ),
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_repair",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(
                activities=[
                    ActivityDetail(
                        id="repair_generated_activity",
                        title="Repair candidate still private",
                    )
                ]
            ),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Repair candidate summary should stay private.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Repair candidate still private",
                        day_label="Day 1",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [
                    {
                        "id": "existing_activity",
                        "type": "activity",
                        "title": "Existing board activity",
                        "day_label": "Day 1",
                    }
                ],
                "module_outputs": {
                    "activities": [
                        {
                            "id": "existing_activity",
                            "title": "Existing board activity",
                        }
                    ]
                },
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]
    response = result["assistant_response"].lower()

    assert result["trip_draft"]["timeline"][0]["title"] == "Existing board activity"
    assert result["trip_draft"]["module_outputs"]["activities"][0]["id"] == "existing_activity"
    assert result["trip_draft"]["budget_estimate"] is None
    assert "generated_activity" not in str(result["trip_draft"])
    assert "started a quick plan" not in response
    assert "private review found missing day coverage" in response
    assert observability["provider_activation"]["quick_plan_review"]["status"] == "incomplete"
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempted"] is True
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempt_count"] == 1
    assert observability["provider_activation"]["quick_plan_repair"]["repair_status"] == "incomplete"
    assert observability["provider_activation"]["quick_plan_repair"]["final_visible"] is False
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is False


def test_blocking_quality_failure_keeps_previous_board_state_and_blocks_success_copy(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(
                activities=[
                    ActivityDetail(
                        id="generic_generated_activity",
                        title="Generic private candidate",
                    )
                ]
            ),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Generic private candidate should stay private.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Generic private candidate",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T12:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
            assistant_summary="Completeness passed.",
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_quality",
        lambda **_: QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=8,
                pacing=8,
                local_specificity=4,
                user_fit=6,
                logistics_realism=2,
                fact_safety=8,
            ),
            issues=[
                QuickPlanQualityIssue(
                    dimension="logistics_realism",
                    severity="high",
                    issue="The timeline is not logistically possible.",
                )
            ],
            assistant_summary=(
                "I generated a complete Quick Plan, but I did not show it because "
                "the private quality review flagged generic activities."
            ),
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_repair",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("Completeness repair should not run for quality failure.")
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [
                    {
                        "id": "existing_activity",
                        "type": "activity",
                        "title": "Existing board activity",
                        "day_label": "Day 1",
                    }
                ],
                "module_outputs": {
                    "activities": [
                        {
                            "id": "existing_activity",
                            "title": "Existing board activity",
                        }
                    ]
                },
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]
    response = result["assistant_response"].lower()

    assert result["trip_draft"]["timeline"][0]["title"] == "Existing board activity"
    assert result["trip_draft"]["module_outputs"]["activities"][0]["id"] == "existing_activity"
    assert "generic_generated_activity" not in str(result["trip_draft"])
    assert "started a quick plan" not in response
    assert "private quality review flagged generic activities" in response
    assert observability["provider_activation"]["quick_plan_review"]["status"] == "complete"
    assert observability["provider_activation"]["quick_plan_completeness_review"]["status"] == "complete"
    assert observability["provider_activation"]["quick_plan_quality_review"]["status"] == "fail"
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempted"] is False
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempt_count"] == 0
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is False
    assert observability["provider_activation"]["quick_plan_acceptance"]["quality_status"] == "fail"
    assert (
        result["trip_draft"]["conversation"]["quick_plan_finalization"][
            "intelligence_summary"
        ]
        == {}
    )


def test_non_blocking_quality_failure_updates_board_as_editable_draft(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(
                activities=[
                    ActivityDetail(
                        id="generated_activity",
                        title="El Born food walk",
                    )
                ]
            ),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Editable first draft.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="El Born food walk",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T12:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
            assistant_summary="Completeness passed.",
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_quality",
        lambda **_: QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=5,
                pacing=7,
                local_specificity=4,
                user_fit=6,
                logistics_realism=8,
                fact_safety=8,
            ),
            issues=[
                QuickPlanQualityIssue(
                    dimension="local_specificity",
                    severity="medium",
                    issue="The plan should use more named local anchors.",
                )
            ],
            assistant_summary="The draft is usable but needs stronger local detail.",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert result["trip_draft"]["timeline"][0]["title"] == "El Born food walk"
    assert result["trip_draft"]["module_outputs"]["activities"][0]["id"] == "generated_activity"
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is True
    assert observability["provider_activation"]["quick_plan_acceptance"]["quality_status"] == "fail"
    assert (
        observability["provider_activation"]["quick_plan_acceptance"][
            "repair_metadata"
        ]["quality_blocking"]
        is False
    )
    assert (
        result["trip_draft"]["conversation"]["quick_plan_finalization"]["accepted"]
        is True
    )
    assert (
        result["trip_draft"]["conversation"]["quick_plan_finalization"][
            "brochure_eligible"
        ]
        is False
    )


def test_quality_failure_clamps_last_turn_summary_for_persistence(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Private candidate",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T12:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(status="complete", show_to_user=True),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_quality",
        lambda **_: QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            assistant_summary=" ".join(["Long private quality issue summary."] * 11),
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    summary = result["trip_draft"]["conversation"]["last_turn_summary"]

    assert summary is not None
    assert len(summary) <= 400


def test_failed_quick_plan_retry_overrides_stale_accepted_finalization_metadata() -> None:
    current_conversation = TripConversationState(
        planning_mode="quick",
        planning_mode_status="selected",
        quick_plan_finalization={
            "accepted": True,
            "review_status": "complete",
            "quality_status": "pass",
            "brochure_eligible": True,
            "accepted_modules": ["flights", "hotels", "activities", "weather"],
            "review_result": {"status": "complete"},
            "quality_result": {"status": "pass"},
            "intelligence_summary": {"plan_rationale": "Old accepted plan."},
        },
    )

    finalization = runner._evaluate_quick_plan_finalization(
        current_conversation=current_conversation,
        planning_mode="quick",
        timeline=[],
        module_outputs=TripModuleOutputs(),
        provider_activation={
            "quick_plan_acceptance": {
                "accepted": False,
                "review_status": "complete",
                "completeness_status": "complete",
                "quality_status": "fail",
                "accepted_modules": [],
            },
            "quick_plan_completeness_review": {"status": "complete"},
            "quick_plan_quality_review": {"status": "fail"},
        },
    )

    assert finalization["accepted"] is False
    assert finalization["quality_status"] == "fail"
    assert finalization["brochure_eligible"] is False
    assert finalization["intelligence_summary"] == {}


def test_quality_specialist_observability_is_json_safe(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Private candidate",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T12:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(status="complete", show_to_user=True),
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_quality",
        lambda **_: QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            specialist_results=[
                QuickPlanSpecialistReviewSummary(
                    specialist="local_quality",
                    status="fail",
                    show_to_user=False,
                    review_notes=["Too generic."],
                    issue_count=1,
                )
            ],
            assistant_summary="Quality review failed.",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    specialists = result["metadata"]["planner_observability"][
        "provider_activation"
    ]["quick_plan_quality_specialists"]

    assert specialists == [
        {
            "specialist": "local_quality",
            "status": "fail",
            "show_to_user": False,
            "review_notes": ["Too generic."],
            "issue_count": 1,
        }
    ]
    json.dumps(specialists)


def test_quality_repairable_review_repairs_once_and_merges_repaired_candidate(
    monkeypatch,
) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Generic first candidate should stay private.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Generic first candidate",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T12:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )

    def _fake_repair(**kwargs):
        repair_context = kwargs["repair_context"]
        captured["repair_goal"] = repair_context.repair_goal
        captured["repair_payload"] = repair_context.prompt_payload()
        return QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(
                activities=[
                    ActivityDetail(
                        id="quality_repair_activity",
                        title="El Born tapas route with Picasso Museum timing",
                    )
                ]
            ),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Barcelona now has a sharper food and culture route.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="El Born tapas route with Picasso Museum timing",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T14:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        )

    monkeypatch.setattr(runner, "run_quick_plan_repair", _fake_repair)
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(status="complete", show_to_user=True),
    )
    quality_results = [
        QuickPlanQualityReviewResult(
            status="repairable",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=8,
                pacing=7,
                local_specificity=4,
                user_fit=6,
                logistics_realism=8,
                fact_safety=8,
            ),
            issues=[
                QuickPlanQualityIssue(
                    dimension="local_specificity",
                    issue="The plan is too generic for Barcelona.",
                    repair_instruction="Use named Barcelona food and culture anchors.",
                )
            ],
            repair_instructions=["Rebuild around specific neighborhoods."],
            assistant_summary="Quality review found the first draft too generic.",
        ),
        _passing_quick_plan_quality_review(),
    ]
    monkeypatch.setattr(
        runner,
        "review_quick_plan_quality",
        lambda **_: quality_results.pop(0),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert captured["repair_goal"] == "quality"
    assert captured["repair_payload"]["quality_scores"]["local_specificity"] == 4
    assert captured["repair_payload"]["quality_issues"][0]["dimension"] == "local_specificity"
    assert result["trip_draft"]["timeline"][0]["title"] == (
        "El Born tapas route with Picasso Museum timing"
    )
    assert result["trip_draft"]["module_outputs"]["activities"][0]["id"] == (
        "quality_repair_activity"
    )
    assert "started a quick plan" in result["assistant_response"].lower()
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempted"] is True
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempt_count"] == 1
    assert observability["provider_activation"]["quick_plan_repair"]["repair_goal"] == "quality"
    assert observability["provider_activation"]["quick_plan_repair"]["first_quality_review"]["status"] == "repairable"
    assert observability["provider_activation"]["quick_plan_repair"]["final_quality_review"]["status"] == "pass"
    assert observability["provider_activation"]["quick_plan_repair"]["final_visible"] is True
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is True
    assert observability["provider_activation"]["quick_plan_acceptance"]["quality_status"] == "pass"


def test_incomplete_quick_plan_review_repairs_once_and_merges_complete_candidate(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "review_trip_brief_intelligence",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "review_profile_origin_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            to_location="Barcelona",
            start_date="2026-10-02",
            end_date="2026-10-04",
            adults=2,
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            confirmed_fields=[
                "to_location",
                "start_date",
                "end_date",
                "adults",
                "selected_modules",
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="start_date", confidence="high"),
                TripFieldConfidenceUpdate(field="end_date", confidence="high"),
                TripFieldConfidenceUpdate(field="adults", confidence="high"),
                TripFieldConfidenceUpdate(field="selected_modules", confidence="high"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="start_date", source="user_explicit"),
                TripFieldSourceUpdate(field="end_date", source="user_explicit"),
                TripFieldSourceUpdate(field="adults", source="user_explicit"),
                TripFieldSourceUpdate(field="selected_modules", source="user_explicit"),
            ],
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Incomplete first candidate",
                        day_label="Day 1",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    monkeypatch.setattr(
        runner,
        "run_quick_plan_repair",
        lambda **kwargs: QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(
                activities=[
                    ActivityDetail(
                        id="repair_activity",
                        title="Repaired Barcelona day plan",
                    )
                ]
            ),
            timeline_module_outputs=TripModuleOutputs(),
            draft=QuickPlanDraft(
                board_summary="Repaired Barcelona quick plan is ready.",
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Repaired Barcelona day plan",
                        day_label="Day 1",
                        start_at="2026-10-02T10:00:00Z",
                        end_at="2026-10-02T14:00:00Z",
                        timing_source="planner_estimate",
                    )
                ],
            ),
            assumptions=kwargs["dossier"].assumptions,
        ),
    )
    review_results = [
        QuickPlanReviewResult(
            status="incomplete",
            show_to_user=False,
            missing_outputs=["timing"],
            review_notes=["The candidate is missing usable timing."],
        ),
        QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
            assistant_summary="Repair passed review.",
        ),
    ]
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: review_results.pop(0),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Build the activities-only Quick Plan.",
            "trip_draft": {
                "title": "Barcelona trip",
                "configuration": {
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    observability = result["metadata"]["planner_observability"]

    assert result["trip_draft"]["timeline"][0]["title"] == "Repaired Barcelona day plan"
    assert result["trip_draft"]["module_outputs"]["activities"][0]["id"] == "repair_activity"
    assert result["trip_draft"]["budget_estimate"]["categories"]
    assert "started a quick plan" in result["assistant_response"].lower()
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempted"] is True
    assert observability["provider_activation"]["quick_plan_repair"]["repair_attempt_count"] == 1
    assert observability["provider_activation"]["quick_plan_repair"]["first_review_result"]["status"] == "incomplete"
    assert observability["provider_activation"]["quick_plan_repair"]["final_review_result"]["status"] == "complete"
    assert observability["provider_activation"]["quick_plan_repair"]["final_visible"] is True
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is True


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


def test_first_prompt_preserves_destination_discovery_before_planning_mode_gate(
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
    assert conversation["suggestion_board"]["mode"] == "timing_choice"
    assert "how long" in result["assistant_response"].lower()
    assert "quick plan" not in result["assistant_response"].lower()
    assert "advanced planning" not in result["assistant_response"].lower()


def test_destination_discovery_stays_before_planning_mode_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            destination_suggestions=[
                DestinationSuggestionCandidate(
                    id="destination_lisbon",
                    destination_name="Lisbon",
                    country_or_region="Portugal",
                    image_url="https://example.com/lisbon.jpg",
                    short_reason="Food, mild weather, and walkable neighborhoods.",
                    practicality_label="Easy short-haul option",
                ),
                DestinationSuggestionCandidate(
                    id="destination_marrakesh",
                    destination_name="Marrakesh",
                    country_or_region="Morocco",
                    image_url="https://example.com/marrakesh.jpg",
                    short_reason="Warmth, markets, and bold food culture.",
                    practicality_label="Warmer weather option",
                ),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Somewhere warm with amazing food.",
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
    board = conversation["suggestion_board"]

    assert conversation["planning_mode"] is None
    assert board["mode"] == "destination_suggestions"
    assert [card["destination_name"] for card in board["cards"]] == [
        "Lisbon",
        "Marrakesh",
    ]
    assert "quick plan" not in result["assistant_response"].lower()
    assert "advanced planning" not in result["assistant_response"].lower()


def test_destination_discovery_renders_advisor_comparison(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            travel_window="late September",
            trip_length="4 nights",
            weather_preference="warm",
            inferred_fields=["travel_window", "trip_length", "weather_preference"],
            discovery_turn_kind="start",
            destination_comparison_summary=(
                "All four keep the trip warm and city-led, but they differ on pace and history."
            ),
            leading_destination_recommendation=(
                "Athens leads if history matters most; Lisbon is the softer all-rounder."
            ),
            destination_suggestions=[
                DestinationSuggestionCandidate(
                    id="destination_athens",
                    destination_name="Athens",
                    country_or_region="Greece",
                    short_reason="Warm late-season evenings and the deepest ancient-history fit.",
                    practicality_label="Warmest history fit",
                    fit_label="Best history fit",
                    best_for="ancient sites and warm evenings",
                    tradeoffs=["Busier and more intense than the other options."],
                    recommendation_note="Current leader for a historic warm break.",
                ),
                DestinationSuggestionCandidate(
                    id="destination_lisbon",
                    destination_name="Lisbon",
                    country_or_region="Portugal",
                    short_reason="Warm, scenic, and easy to fill over four nights.",
                    practicality_label="Best all-rounder",
                    fit_label="Balanced pick",
                    best_for="food, viewpoints, and neighbourhood wandering",
                    tradeoffs=["Less ancient-history led than Athens."],
                    recommendation_note="Best if you want balance over pure history.",
                ),
                DestinationSuggestionCandidate(
                    id="destination_valencia",
                    destination_name="Valencia",
                    country_or_region="Spain",
                    short_reason="Sunny, relaxed, and easy with beach time close by.",
                    practicality_label="Relaxed sunshine",
                    fit_label="Easiest pace",
                    best_for="sun, food, and a slower city break",
                    tradeoffs=["Not as strong for historic atmosphere."],
                    recommendation_note="Good if warmth and ease matter most.",
                ),
                DestinationSuggestionCandidate(
                    id="destination_nice",
                    destination_name="Nice",
                    country_or_region="France",
                    short_reason="Warm Riviera base with old-town texture and day trips.",
                    practicality_label="Scenic base",
                    fit_label="Polished wildcard",
                    best_for="coast, old town, and elegant day trips",
                    tradeoffs=["Can feel less immersive for a history-first trip."],
                    recommendation_note="Best if the coast is part of the appeal.",
                ),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "I have 4 nights in late September. Suggest warm European cities and help me choose.",
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

    assert board["mode"] == "destination_suggestions"
    assert board["discovery_turn_kind"] == "start"
    assert len(board["cards"]) == 4
    assert board["cards"][0]["fit_label"] == "Best history fit"
    assert board["cards"][0]["tradeoffs"] == [
        "Busier and more intense than the other options."
    ]
    assert result["trip_draft"]["configuration"]["to_location"] is None
    assert "**Athens, Greece**" in result["assistant_response"]
    assert "Athens leads" in result["assistant_response"]
    assert "My lean:" in result["assistant_response"]
    assert "**Quick read**" not in result["assistant_response"]


def test_destination_discovery_uses_llm_advisor_response(monkeypatch) -> None:
    llm_response = (
        "Vijay, I’d compare these by pace first.\n\n"
        "- **Singapore** if you want warmth and low friction.\n"
        "- **Bangkok** if you want temples, food, and more atmosphere.\n\n"
        "I’d start with Singapore unless you want the trip to feel more vivid."
    )
    monkeypatch.setattr(
        runner,
        "review_destination_discovery_update",
        lambda **kwargs: kwargs["llm_update"],
    )
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            discovery_turn_kind="pivot",
            destination_suggestions=[
                DestinationSuggestionCandidate(
                    id="destination_singapore",
                    destination_name="Singapore",
                    country_or_region="Singapore",
                    short_reason="Warm, food-led, and easy for four nights.",
                    practicality_label="Smoothest short break",
                ),
                DestinationSuggestionCandidate(
                    id="destination_bangkok",
                    destination_name="Bangkok",
                    country_or_region="Thailand",
                    short_reason="Temples, street food, and a lively rhythm.",
                    practicality_label="Atmospheric wildcard",
                ),
            ],
            assistant_response=llm_response,
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "can you suggest me asian cities",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    assert result["assistant_response"] == llm_response


def test_destination_discovery_pivot_replaces_visible_shortlist(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            travel_window="late September",
            trip_length="4 nights",
            weather_preference="warm",
            discovery_turn_kind="pivot",
            destination_comparison_summary=(
                "I’m shifting from warm Europe to warm-ish Asian cities with stronger history."
            ),
            leading_destination_recommendation="Kyoto leads for polished culture and temples.",
            destination_suggestions=[
                DestinationSuggestionCandidate(
                    id="destination_kyoto",
                    destination_name="Kyoto",
                    country_or_region="Japan",
                    short_reason="Temple-heavy, beautiful, and strong for a four-night culture trip.",
                    practicality_label="Culture-first",
                    fit_label="Best culture fit",
                    best_for="temples, tradition, and a polished historic trip",
                    tradeoffs=["Not as warm as Southeast Asia in late September."],
                    recommendation_note="The strongest fit for a historic Asian trip.",
                    change_note="New leader after the Asia pivot.",
                ),
                DestinationSuggestionCandidate(
                    id="destination_hanoi",
                    destination_name="Hanoi",
                    country_or_region="Vietnam",
                    short_reason="Layered history, food, and street energy in a compact stay.",
                    practicality_label="Warm and vivid",
                    fit_label="Most atmospheric",
                    best_for="food, old-quarter atmosphere, and layered history",
                    tradeoffs=["More intense and less polished than Kyoto."],
                    recommendation_note="Best if you want energy and street life.",
                ),
            ],
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "somewhere Asian.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "travel_window": "late September",
                    "trip_length": "4 nights",
                    "weather_preference": "warm",
                },
                "conversation": {
                    "suggestion_board": {
                        "mode": "destination_suggestions",
                        "cards": [
                            {
                                "id": "destination_lisbon",
                                "destination_name": "Lisbon",
                                "country_or_region": "Portugal",
                                "image_url": "https://example.com/lisbon.jpg",
                                "short_reason": "Warm and easy.",
                                "practicality_label": "All-rounder",
                                "selection_status": "suggested",
                            }
                        ],
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {
                    "confirmed_fields": [
                        "from_location",
                        "to_location",
                        "travel_window",
                        "trip_length",
                        "adults",
                    ],
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert board["discovery_turn_kind"] == "pivot"
    assert [card["destination_name"] for card in board["cards"]] == ["Kyoto", "Hanoi"]
    assert "shifted the shortlist" in result["assistant_response"].lower()
    assert result["trip_draft"]["configuration"]["to_location"] is None


def test_destination_card_click_marks_leading_without_locking_destination(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_1",
                "type": "select_destination_suggestion",
                "destination_name": "Lisbon",
                "country_or_region": "Portugal",
                "suggestion_id": "destination_lisbon",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "conversation": {
                    "suggestion_board": {
                        "mode": "destination_suggestions",
                        "cards": [
                            {
                                "id": "destination_lisbon",
                                "destination_name": "Lisbon",
                                "country_or_region": "Portugal",
                                "image_url": "https://example.com/lisbon.jpg",
                                "short_reason": "Warm, scenic, and easy.",
                                "practicality_label": "Best all-rounder",
                                "recommendation_note": "Best if you want a balanced four-night trip.",
                                "selection_status": "suggested",
                            }
                        ],
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert result["trip_draft"]["configuration"]["to_location"] is None
    assert board["cards"][0]["selection_status"] == "leading"
    assert "front-runner" in result["assistant_response"].lower()
    assert "lock it as the destination" in result["assistant_response"].lower()


def test_confirm_destination_suggestion_locks_destination_without_confirming_brief(
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
                "action_id": "action_2",
                "type": "confirm_destination_suggestion",
                "destination_name": "Lisbon",
                "country_or_region": "Portugal",
                "suggestion_id": "destination_lisbon",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {},
                "conversation": {
                    "suggestion_board": {
                        "mode": "destination_suggestions",
                        "cards": [
                            {
                                "id": "destination_lisbon",
                                "destination_name": "Lisbon",
                                "country_or_region": "Portugal",
                                "image_url": "https://example.com/lisbon.jpg",
                                "short_reason": "Warm, scenic, and easy.",
                                "practicality_label": "Best all-rounder",
                                "selection_status": "leading",
                            }
                        ],
                    }
                },
                "timeline": [],
                "module_outputs": {},
                "status": {},
            },
        }
    )

    status = result["trip_draft"]["status"]

    assert result["trip_draft"]["configuration"]["to_location"] == "Lisbon, Portugal"
    assert status["confirmed_fields"] == ["to_location"]
    assert result["trip_draft"]["conversation"]["suggestion_board"]["mode"] != "destination_suggestions"
    assert result["trip_draft"]["conversation"]["planning_mode_status"] == "not_selected"


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
    assert "brief" in result["assistant_response"].lower()
    assert "guided anchor choice" in result["assistant_response"].lower()


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
        raise AssertionError("Quick Plan generation should not run for advanced mode.")

    monkeypatch.setattr(runner, "run_quick_plan_generation", _fail_quick_plan)

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
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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


def test_trip_style_anchor_opens_direction_workspace_and_completion_returns_to_anchor_choice(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    anchor_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_trip_style",
                "type": "select_advanced_anchor",
                "advanced_anchor": "trip_style",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "activity_styles": ["culture"],
                    "custom_style": "slow temple mornings and market-heavy afternoons",
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

    anchor_board = anchor_result["trip_draft"]["conversation"]["suggestion_board"]
    assert anchor_board["mode"] == "advanced_trip_style_direction"
    assert anchor_board["selected_trip_style_primary"] is None
    assert "main character" in anchor_board["subtitle"].lower()

    confirm_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_confirm_trip_style",
                "type": "confirm_trip_style_direction",
                "trip_style_direction_primary": "food_led",
                "trip_style_direction_accent": "relaxed",
            },
            "trip_draft": anchor_result["trip_draft"],
        }
    )

    conversation = confirm_result["trip_draft"]["conversation"]
    board = conversation["suggestion_board"]

    assert conversation["trip_style_planning"]["selection_status"] == "selected"
    assert conversation["trip_style_planning"]["substep"] == "pace"
    assert conversation["trip_style_planning"]["selected_primary_direction"] == "food_led"
    assert board["mode"] == "advanced_trip_style_pace"
    assert board["selected_trip_style_primary"] == "food_led"
    assert board["trip_style_recommended_paces"]

    pace_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_confirm_trip_style_pace",
                "type": "confirm_trip_style_pace",
                "trip_style_pace": "slow",
            },
            "trip_draft": confirm_result["trip_draft"],
        }
    )

    conversation = pace_result["trip_draft"]["conversation"]
    board = conversation["suggestion_board"]

    assert conversation["trip_style_planning"]["selection_status"] == "selected"
    assert conversation["trip_style_planning"]["substep"] == "tradeoffs"
    assert conversation["trip_style_planning"]["selected_pace"] == "slow"
    assert conversation["trip_style_planning"]["recommended_tradeoff_cards"]
    assert board["mode"] == "advanced_trip_style_tradeoffs"
    assert board["selected_trip_style_primary"] == "food_led"
    assert board["selected_trip_style_pace"] == "slow"

    tradeoff_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_confirm_trip_style_tradeoffs",
                "type": "confirm_trip_style_tradeoffs",
            },
            "trip_draft": pace_result["trip_draft"],
        }
    )

    conversation = tradeoff_result["trip_draft"]["conversation"]
    board = conversation["suggestion_board"]

    assert conversation["trip_style_planning"]["selection_status"] == "completed"
    assert conversation["trip_style_planning"]["substep"] == "completed"
    assert conversation["trip_style_planning"]["tradeoff_status"] == "completed"
    assert board["mode"] == "advanced_anchor_choice"
    assert len(board["subtitle"]) <= 320
    recommended_card = next(
        card for card in board["advanced_anchor_cards"] if card["recommended"]
    )
    assert recommended_card["id"] == "activities"
    assert "activities" in tradeoff_result["assistant_response"].lower()


def test_flight_anchor_opens_workspace_and_confirmation_returns_to_anchor_choice(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    captured_allowed_modules: list[set[str]] = []

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        *,
        allowed_modules,
    ):
        captured_allowed_modules.append(set(allowed_modules))
        return TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="flight_outbound",
                    direction="outbound",
                    carrier="Working Air",
                    departure_airport="LHR",
                    arrival_airport="KIX",
                    departure_time=runner.datetime(
                        2027, 3, 23, 9, 0, tzinfo=runner.timezone.utc
                    ),
                    arrival_time=runner.datetime(
                        2027, 3, 24, 8, 0, tzinfo=runner.timezone.utc
                    ),
                    duration_text="14h",
                ),
                FlightDetail(
                    id="flight_outbound_unselected",
                    direction="outbound",
                    carrier="Other Air",
                    departure_airport="LGW",
                    arrival_airport="KIX",
                    departure_time=runner.datetime(
                        2027, 3, 23, 18, 0, tzinfo=runner.timezone.utc
                    ),
                    arrival_time=runner.datetime(
                        2027, 3, 24, 18, 0, tzinfo=runner.timezone.utc
                    ),
                    duration_text="16h",
                ),
                FlightDetail(
                    id="flight_return",
                    direction="return",
                    carrier="Working Air",
                    departure_airport="KIX",
                    arrival_airport="LHR",
                    departure_time=runner.datetime(
                        2027, 3, 29, 13, 0, tzinfo=runner.timezone.utc
                    ),
                    arrival_time=runner.datetime(
                        2027, 3, 29, 19, 0, tzinfo=runner.timezone.utc
                    ),
                    duration_text="14h",
                ),
            ]
        )

    monkeypatch.setattr(runner, "build_module_outputs", _fake_build_module_outputs)

    anchor_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_flight",
                "type": "select_advanced_anchor",
                "advanced_anchor": "flight",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "from_location": "London",
                    "to_location": "Kyoto",
                    "start_date": "2027-03-23",
                    "end_date": "2027-03-29",
                    "travel_window": "late March",
                    "trip_length": "6 nights",
                    "travelers": {"adults": 2, "children": 0},
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

    board = anchor_result["trip_draft"]["conversation"]["suggestion_board"]
    assert captured_allowed_modules[-1] == {"flights"}
    assert board["mode"] == "advanced_flights_workspace"
    assert board["outbound_flight_options"][0]["id"] == "flight_outbound"
    assert board["return_flight_options"][0]["id"] == "flight_return"

    outbound_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_select_outbound",
                "type": "select_outbound_flight",
                "flight_option_id": "flight_outbound",
            },
            "trip_draft": anchor_result["trip_draft"],
        }
    )
    return_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_select_return",
                "type": "select_return_flight",
                "flight_option_id": "flight_return",
            },
            "trip_draft": outbound_result["trip_draft"],
        }
    )
    completed_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_confirm_flights",
                "type": "confirm_flight_selection",
            },
            "trip_draft": return_result["trip_draft"],
        }
    )

    conversation = completed_result["trip_draft"]["conversation"]
    assert conversation["flight_planning"]["selection_status"] == "completed"
    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"
    flight_timeline_ids = [
        item["id"]
        for item in completed_result["trip_draft"]["timeline"]
        if item["type"] == "flight"
    ]
    assert flight_timeline_ids == [
        "timeline_selected_flight_outbound",
        "timeline_selected_flight_return",
    ]
    assert any(
        card["id"] == "flight" and card["status"] == "completed"
        for card in conversation["suggestion_board"]["advanced_anchor_cards"]
    )
    assert "flight" in completed_result["assistant_response"].lower()


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
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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
    assert len(stay_planning["recommended_hotels"]) == 4
    assert stay_planning["hotel_results_status"] == "ready"
    assert "hotel recommendations" in stay_planning["hotel_results_summary"].lower()
    assert stay_planning["hotel_filters"]["max_nightly_rate"] is None
    assert stay_planning["hotel_filters"]["area_filter"] is None
    assert stay_planning["hotel_filters"]["style_filter"] is None
    assert stay_planning["available_hotel_areas"] == []
    assert stay_planning["available_hotel_styles"] == []
    assert stay_planning["recommended_hotels"][0]["hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["recommended_hotels"][0]["image_url"]
    assert stay_planning["recommended_hotels"][0]["address"]
    assert stay_planning["recommended_hotels"][0]["nightly_rate_amount"] == 164
    assert stay_planning["recommended_hotels"][0]["rate_provider_name"] == "Vio.com"
    assert stay_planning["recommended_hotels"][0]["style_tags"]
    assert "Daily travel can need more planning" not in stay_planning["recommended_hotels"][0]["tradeoffs"]
    assert stay_planning["compatibility_status"] == "fit"
    assert "hotel" not in (stay_planning["selection_rationale"] or "").lower()
    assert any(
        event["title"] == "Stay strategy selected"
        and event["selected_option"] == "stay_central_base"
        for event in decision_history
    )
    assert "hotel recommendations inside that base" in result["assistant_response"].lower()


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
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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

    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"
    assert stay_planning["selected_hotel_id"] == "hotel_station_stay"
    assert stay_planning["selected_hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["hotel_selection_status"] == "selected"
    assert stay_planning["hotel_substep"] == "hotel_selected"
    assert conversation["suggestion_board"]["advanced_anchor_cards"][-1]["id"] == "stay"
    assert (
        conversation["suggestion_board"]["advanced_anchor_cards"][-1]["status"]
        == "completed"
    )
    assert any(
        event["title"] == "Stay hotel selected"
        and event["selected_option"] == "hotel_station_stay"
        for event in decision_history
    )
    assert "strong choice" in result["assistant_response"].lower()
    assert "next" in result["assistant_response"].lower()


def test_stay_hotel_actions_do_not_break_curated_recommendations(monkeypatch) -> None:
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
                "action_id": "action_filter_hotels",
                "type": "set_stay_hotel_filters",
                "stay_hotel_max_nightly_rate": 170,
                "stay_hotel_area_filter": "Shimogyo-ku",
                "stay_hotel_style_filter": "practical",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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
                        "selected_stay_option_id": "stay_central_base",
                        "selected_stay_direction": "Central base for Kyoto",
                        "selection_status": "selected",
                        "selection_rationale": "Stay central.",
                        "selection_assumptions": [
                            "Short trips that need easy orientation",
                        ],
                    },
                },
            },
        }
    )

    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]
    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert board["mode"] == "advanced_stay_hotel_choice"
    assert stay_planning["hotel_filters"]["max_nightly_rate"] is None
    assert stay_planning["hotel_filters"]["area_filter"] is None
    assert stay_planning["hotel_filters"]["style_filter"] is None
    assert len(stay_planning["recommended_hotels"]) == 4
    assert stay_planning["recommended_hotels"][0]["hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["hotel_results_status"] == "ready"
    assert "hotel recommendations" in stay_planning["hotel_results_summary"].lower()

    sort_result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_sort_hotels",
                "type": "set_stay_hotel_sort",
                "stay_hotel_sort_order": "highest_price",
            },
            "trip_draft": result["trip_draft"],
        }
    )

    sorted_board = sort_result["trip_draft"]["conversation"]["suggestion_board"]
    assert sort_result["trip_draft"]["conversation"]["stay_planning"]["hotel_sort_order"] == "best_fit"
    assert sorted_board["hotel_cards"][0]["hotel_name"] == "Kyoto Station Stay"


def test_chat_can_select_working_hotel_and_return_to_next_anchor_cards(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_stay_hotel_name="Kyoto Station Stay",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: _sample_hotel_outputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "I'd like to proceed with Kyoto Station Stay.",
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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

    assert stay_planning["selected_hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["selected_hotel_id"] == "hotel_station_stay"
    assert conversation["suggestion_board"]["mode"] == "advanced_anchor_choice"
    assert conversation["suggestion_board"]["advanced_anchor_cards"][-1]["id"] == "stay"
    assert (
        conversation["suggestion_board"]["advanced_anchor_cards"][-1]["status"]
        == "completed"
    )
    assert any(
        event["title"] == "Stay hotel selected"
        and event["selected_option"] == "kyoto station stay"
        for event in decision_history
    )
    assert "strong choice" in result["assistant_response"].lower()


def test_selected_hotel_stays_visible_when_filters_no_longer_match(monkeypatch) -> None:
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
                "action_id": "action_exclude_selected_hotel",
                "type": "set_stay_hotel_filters",
                "stay_hotel_area_filter": "Higashiyama-ku",
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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
                        "hotel_substep": "hotel_selected",
                        "selected_stay_option_id": "stay_central_base",
                        "selected_stay_direction": "Central base for Kyoto",
                        "selection_status": "selected",
                        "selection_rationale": "Stay central.",
                        "selection_assumptions": [
                            "Short trips that need easy orientation",
                        ],
                        "selected_hotel_id": "hotel_station_stay",
                        "selected_hotel_name": "Kyoto Station Stay",
                        "hotel_selection_status": "selected",
                        "hotel_selection_rationale": "Practical for transfers.",
                    },
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    board = conversation["suggestion_board"]
    stay_planning = conversation["stay_planning"]

    assert board["mode"] == "advanced_anchor_choice"
    assert stay_planning["selected_hotel_name"] == "Kyoto Station Stay"
    assert stay_planning["hotel_selection_status"] == "selected"
    assert board["advanced_anchor_cards"][-1]["id"] == "stay"
    assert board["advanced_anchor_cards"][-1]["status"] == "completed"


def test_stay_hotel_shortlist_stays_curated_to_four_recommendations(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: _sample_paginated_hotel_outputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_page_hotels",
                "type": "set_stay_hotel_page",
                "stay_hotel_page": 2,
            },
            "trip_draft": {
                "title": "Trip planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-27",
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
                "module_outputs": _sample_paginated_hotel_outputs().model_dump(mode="json"),
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
                        "selected_stay_option_id": "stay_central_base",
                        "selected_stay_direction": "Central base for Kyoto",
                        "selection_status": "selected",
                        "selection_rationale": "Stay central.",
                        "selection_assumptions": [
                            "Short trips that need easy orientation",
                        ],
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["hotel_page"] == 1
    assert board["hotel_total_pages"] == 1
    assert board["hotel_total_results"] == 4
    assert len(board["hotel_cards"]) == 4
    assert stay_planning["hotel_page"] == 1


def test_hotel_workspace_blocks_when_exact_dates_are_missing(monkeypatch) -> None:
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
                "action_id": "action_select_stay_without_dates",
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
                "module_outputs": _sample_hotel_outputs().model_dump(mode="json"),
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

    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]
    board = result["trip_draft"]["conversation"]["suggestion_board"]

    assert board["mode"] == "advanced_stay_hotel_choice"
    assert stay_planning["hotel_results_status"] == "blocked"
    assert "exact hotel comparison needs fixed dates" in stay_planning["hotel_results_summary"].lower()
    assert result["assistant_response"].lower().count("fixed dates") >= 1

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


def test_trip_style_advanced_anchor_opens_direction_workspace(monkeypatch) -> None:
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
    assert conversation["suggestion_board"]["mode"] == "advanced_trip_style_direction"
    assert "main direction first" in result["assistant_response"].lower()


def test_activities_anchor_initially_stays_in_workspace_until_user_shapes_it(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Music | Jazz | Blue Note Kyoto, Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": runner.datetime(2027, 3, 24, 19, 30, tzinfo=runner.timezone.utc),
                "end_at": runner.datetime(2027, 3, 24, 22, 0, tzinfo=runner.timezone.utc),
            }
        ],
    )

    expected_module_outputs = _sample_dense_activity_outputs()

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules,
    ):
        assert allowed_modules == {"activities", "weather"}
        return expected_module_outputs

    monkeypatch.setattr(runner, "build_module_outputs", _fake_build_module_outputs)

    existing_timeline = [
        {
            "id": "timeline_keep_me",
            "type": "note",
            "title": "Existing timeline stays put",
            "status": "draft",
        }
    ]
    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_activities",
                "type": "select_advanced_anchor",
                "advanced_anchor": "activities",
            },
            "trip_draft": {
                "title": "Kyoto Food Escape",
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
                "timeline": existing_timeline,
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
    board = conversation["suggestion_board"]
    activity_planning = conversation["activity_planning"]

    assert conversation["advanced_anchor"] == "activities"
    assert board["mode"] == "advanced_activities_workspace"
    assert activity_planning["workspace_touched"] is False
    assert activity_planning["completion_status"] == "in_progress"
    assert activity_planning["completion_summary"] is None
    timeline = result["trip_draft"]["timeline"]
    assert timeline[0]["id"] == "timeline_keep_me"
    assert any(item["source_module"] == "activities" for item in timeline)
    assert any(item["type"] == "event" for item in timeline)
    event_item = next(item for item in timeline if item["type"] == "event")
    assert event_item["source_url"] == "https://example.com/jazz"
    assert all(
        item["id"] != "timeline_keep_me" or item["title"] == "Existing timeline stays put"
        for item in timeline
    )
    assert "strongest time-specific moment" in board["subtitle"].lower()
    assert "strongest time-specific moment" in result["assistant_response"].lower()


def test_activities_anchor_stays_in_workspace_when_plan_is_still_thin(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(
            activities=[
                ActivityDetail(
                    id="activity_walk",
                    title="Temple garden walk",
                    category="tourism.sights",
                    location_label="Higashiyama, Kyoto",
                    time_label="Morning",
                )
            ]
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_anchor_activities",
                "type": "select_advanced_anchor",
                "advanced_anchor": "activities",
            },
            "trip_draft": {
                "title": "Kyoto Quiet Escape",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "selected_modules": {
                        "flights": False,
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
    board = conversation["suggestion_board"]

    assert conversation["advanced_anchor"] == "activities"
    assert conversation["activity_planning"]["completion_status"] == "in_progress"
    assert board["mode"] == "advanced_activities_workspace"
    assert board["activity_workspace_summary"]
    assert {candidate["kind"] for candidate in board["activity_candidates"]} == {"activity"}


def test_stay_and_activities_can_both_show_as_completed(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": runner.datetime(2027, 3, 24, 20, 0, tzinfo=runner.timezone.utc),
                "end_at": runner.datetime(2027, 3, 24, 22, 0, tzinfo=runner.timezone.utc),
            }
        ],
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "trip_draft": {
                "title": "Kyoto Finished Base",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-24",
                    "end_date": "2027-03-24",
                    "travel_window": "late March",
                    "trip_length": "1 night",
                    "selected_modules": {
                        "flights": False,
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
                        "advanced_anchor": "activities",
                        "activity_planning": {
                            "workspace_touched": True,
                        },
                        "stay_planning": {
                            "recommended_stay_options": [
                                {
                                    "id": "stay_food_forward",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Food-forward neighbourhood base",
                                "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                                "area_label": "Dining-led Kyoto pockets",
                                "areas": [],
                                "best_for": ["Food and evening structure"],
                                "tradeoffs": ["Less purely practical than a station-led base"],
                                "recommended": True,
                            }
                        ],
                        "selected_stay_option_id": "stay_food_forward",
                        "selected_stay_direction": "Food-forward neighbourhood base",
                        "selection_status": "selected",
                        "compatibility_status": "fit",
                        "selected_hotel_id": "hotel_gion_house",
                        "selected_hotel_name": "Gion House Hotel",
                        "hotel_selection_status": "selected",
                        "hotel_compatibility_status": "fit",
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    statuses = {
        card["id"]: card["status"] for card in board["advanced_anchor_cards"]
    }

    assert board["mode"] == "advanced_anchor_choice"
    assert statuses["stay"] == "completed"
    assert statuses["activities"] == "completed"


def test_activities_anchor_switches_into_stay_review_when_activity_plan_conflicts(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": runner.datetime(2027, 3, 24, 20, 0, tzinfo=runner.timezone.utc),
                "end_at": runner.datetime(2027, 3, 24, 22, 0, tzinfo=runner.timezone.utc),
            }
        ],
    )

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules,
    ):
        assert allowed_modules == {"activities", "weather"}
        return TripModuleOutputs()

    monkeypatch.setattr(runner, "build_module_outputs", _fake_build_module_outputs)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "trip_draft": {
                "title": "Kyoto Night Trip",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-24",
                    "end_date": "2027-03-24",
                    "travel_window": "late March",
                    "trip_length": "1 night",
                    "selected_modules": {
                        "flights": False,
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
                    "advanced_anchor": "activities",
                    "stay_planning": {
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
                            }
                        ],
                        "selected_stay_option_id": "stay_quiet_local",
                        "selected_stay_direction": "Quieter local base",
                        "selection_status": "selected",
                        "compatibility_status": "fit",
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_stay_review"
    assert stay_planning["selection_status"] == "needs_review"
    assert "Kyoto Jazz Night" in stay_planning["compatibility_notes"][0]
    assert "re-ranked the stay directions" in board["subtitle"]
    assert "Food-forward neighbourhood base" in board["subtitle"]
    assert "activities are still leading" in result["assistant_response"].lower()
    assert "silently replacing" in result["assistant_response"].lower()


def test_activities_anchor_switches_into_hotel_review_when_only_hotel_fit_weakens(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules,
    ):
        assert allowed_modules == {"activities", "weather"}
        return TripModuleOutputs(
            hotels=_sample_hotel_outputs().hotels,
            activities=[
                ActivityDetail(
                    id="activity_market",
                    title="Nishiki Market tasting walk",
                    category="catering.restaurant",
                    location_label="Nishiki Market, Kyoto",
                    time_label="Evening",
                )
            ]
        )

    monkeypatch.setattr(runner, "build_module_outputs", _fake_build_module_outputs)

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_market_essential",
                "type": "set_activity_candidate_disposition",
                "activity_candidate_id": "activity_market",
                "activity_candidate_title": "Nishiki Market tasting walk",
                "activity_candidate_disposition": "essential",
            },
            "trip_draft": {
                "title": "Kyoto Food Trip",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "selected_modules": {
                        "flights": False,
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
                    "advanced_anchor": "activities",
                    "stay_planning": {
                        "recommended_stay_options": [
                            {
                                "id": "stay_food_forward",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Food-forward neighbourhood base",
                                "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                                "area_label": "Dining-led Kyoto pockets",
                                "areas": [],
                                "best_for": ["Food and evening structure"],
                                "tradeoffs": ["Less purely practical than a station-led base"],
                                "recommended": True,
                            }
                        ],
                        "selected_stay_option_id": "stay_food_forward",
                        "selected_stay_direction": "Food-forward neighbourhood base",
                        "selection_status": "selected",
                        "compatibility_status": "fit",
                        "selected_hotel_id": "hotel_station_stay",
                        "selected_hotel_name": "Kyoto Station Stay",
                        "hotel_selection_status": "selected",
                        "hotel_compatibility_status": "fit",
                        "selected_hotel_card": {
                            "id": "hotel_station_stay",
                            "hotel_name": "Kyoto Station Stay",
                            "area": "Central Kyoto Station",
                            "summary": "A practical station hotel.",
                            "why_it_fits": "Easy for transport-heavy movement.",
                        },
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_stay_hotel_review"
    assert stay_planning["selection_status"] == "selected"
    assert stay_planning["hotel_selection_status"] == "needs_review"
    assert "Nishiki Market tasting walk" in stay_planning["hotel_compatibility_notes"][0]
    assert "re-ranked the hotel options" in board["subtitle"]
    assert stay_planning["recommended_hotels"][0]["hotel_name"] != "Kyoto Station Stay"
    assert "hotel visible" in result["assistant_response"].lower()


def test_keep_current_stay_review_returns_to_activities_workspace(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": runner.datetime(2027, 3, 24, 20, 0, tzinfo=runner.timezone.utc),
                "end_at": runner.datetime(2027, 3, 24, 22, 0, tzinfo=runner.timezone.utc),
            }
        ],
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_keep_stay",
                "type": "keep_current_stay_choice",
            },
            "trip_draft": {
                "title": "Kyoto Night Trip",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-24",
                    "end_date": "2027-03-24",
                    "travel_window": "late March",
                    "trip_length": "1 night",
                    "selected_modules": {
                        "flights": False,
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
                    "advanced_anchor": "activities",
                    "stay_planning": {
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
                            }
                        ],
                        "selected_stay_option_id": "stay_quiet_local",
                        "selected_stay_direction": "Quieter local base",
                        "selection_status": "needs_review",
                        "compatibility_status": "conflicted",
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_anchor_choice"
    assert stay_planning["selection_status"] == "selected"
    assert stay_planning["compatibility_status"] == "fit"
    assert result["trip_draft"]["conversation"]["activity_planning"]["completion_status"] == "completed"
    assert "keep quieter local base as the working base" in result["assistant_response"].lower()
    assert any(item["source_module"] == "activities" for item in result["trip_draft"]["timeline"])


def test_chat_keep_current_hotel_review_returns_to_activities_workspace(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_activity_decisions=[
                {
                    "candidate_title": "Nishiki Market tasting walk",
                    "disposition": "essential",
                }
            ],
            requested_review_resolutions=[RequestedReviewResolution(scope="hotel")],
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(
            hotels=_sample_hotel_outputs().hotels,
            activities=[
                ActivityDetail(
                    id="activity_market",
                    title="Nishiki Market tasting walk",
                    category="catering.restaurant",
                    location_label="Nishiki Market, Kyoto",
                    time_label="Evening",
                )
            ],
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Keep the current hotel.",
            "trip_draft": {
                "title": "Kyoto Food Trip",
                "configuration": {
                    "to_location": "Kyoto",
                    "travel_window": "late March",
                    "trip_length": "5 nights",
                    "selected_modules": {
                        "flights": False,
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
                    "advanced_anchor": "activities",
                    "stay_planning": {
                        "recommended_stay_options": [
                            {
                                "id": "stay_food_forward",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Food-forward neighbourhood base",
                                "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                                "area_label": "Dining-led Kyoto pockets",
                                "areas": [],
                                "best_for": ["Food and evening structure"],
                                "tradeoffs": ["Less purely practical than a station-led base"],
                                "recommended": True,
                            }
                        ],
                        "selected_stay_option_id": "stay_food_forward",
                        "selected_stay_direction": "Food-forward neighbourhood base",
                        "selection_status": "selected",
                        "compatibility_status": "fit",
                        "selected_hotel_id": "hotel_station_stay",
                        "selected_hotel_name": "Kyoto Station Stay",
                        "hotel_selection_status": "needs_review",
                        "hotel_compatibility_status": "strained",
                        "selected_hotel_card": {
                            "id": "hotel_station_stay",
                            "hotel_name": "Kyoto Station Stay",
                            "area": "Central Kyoto Station",
                            "summary": "A practical station hotel.",
                            "why_it_fits": "Easy for transport-heavy movement.",
                        },
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_activities_workspace"
    assert stay_planning["hotel_selection_status"] == "selected"
    assert stay_planning["hotel_compatibility_status"] == "fit"
    assert result["trip_draft"]["conversation"]["activity_planning"]["completion_status"] == "in_progress"
    assert "keep kyoto station stay as the working hotel" in result["assistant_response"].lower()


def test_chat_switching_stay_direction_from_review_returns_to_activities(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_stay_option_title="Food-forward neighbourhood base",
            assistant_response="",
        ),
    )
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": runner.datetime(2027, 3, 24, 20, 0, tzinfo=runner.timezone.utc),
                "end_at": runner.datetime(2027, 3, 24, 22, 0, tzinfo=runner.timezone.utc),
            }
        ],
    )
    monkeypatch.setattr(
        runner,
        "build_module_outputs",
        lambda *_, **__: TripModuleOutputs(hotels=_sample_hotel_outputs().hotels),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Switch to Food-forward neighbourhood base.",
            "trip_draft": {
                "title": "Kyoto Night Trip",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-24",
                    "end_date": "2027-03-24",
                    "travel_window": "late March",
                    "trip_length": "1 night",
                    "selected_modules": {
                        "flights": False,
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
                    "advanced_anchor": "activities",
                    "stay_planning": {
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
                                "recommended": False,
                            },
                            {
                                "id": "stay_food_forward",
                                "segment_id": "segment_primary",
                                "strategy_type": "single_base",
                                "title": "Food-forward neighbourhood base",
                                "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                                "area_label": "Dining-led Kyoto pockets",
                                "areas": [],
                                "best_for": ["Food and evening structure"],
                                "tradeoffs": ["Less purely practical than a station-led base"],
                                "recommended": True,
                            },
                        ],
                        "selected_stay_option_id": "stay_quiet_local",
                        "selected_stay_direction": "Quieter local base",
                        "selection_status": "needs_review",
                        "compatibility_status": "conflicted",
                    },
                },
            },
        }
    )

    board = result["trip_draft"]["conversation"]["suggestion_board"]
    stay_planning = result["trip_draft"]["conversation"]["stay_planning"]

    assert board["mode"] == "advanced_anchor_choice"
    assert stay_planning["selected_stay_option_id"] == "stay_food_forward"
    assert stay_planning["compatibility_status"] == "fit"
    assert result["trip_draft"]["conversation"]["activity_planning"]["completion_status"] == "completed"
    assert "switched the working stay direction" in result["assistant_response"].lower()


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
        "adult traveler count is required when flights or hotels are included"
    ]
    assert observability["provider_activation"]["blocked_modules"]["hotels"] == [
        "adult traveler count is required when flights or hotels are included"
    ]


def test_brief_confirmation_quick_request_defaults_implicit_scope_to_full_trip(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            confirmed_trip_brief=True,
            requested_planning_mode="quick",
            assistant_response="",
        ),
    )
    def _fake_run_quick_plan_generation(**kwargs):
        draft = QuickPlanDraft(
            board_summary="Valencia now has a complete quick draft.",
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Arrival evening around Ciutat Vella",
                    day_label="Day 1",
                    summary="A light first evening after travel.",
                )
            ],
        )
        return QuickPlanGenerationAttempt(
            status="generated",
            module_outputs=TripModuleOutputs(),
            timeline_module_outputs=TripModuleOutputs(),
            draft=draft,
            assumptions=kwargs["dossier"].assumptions,
        )

    monkeypatch.setattr(
        runner,
        "run_quick_plan_generation",
        _fake_run_quick_plan_generation,
    )
    monkeypatch.setattr(
        runner,
        "review_quick_plan_generation",
        lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
            assistant_summary="Quick Plan passed review.",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "yes please everything is good.",
            "trip_draft": {
                "title": "Valencia Conference Trip",
                "configuration": {
                    "from_location": "Coventry",
                    "to_location": "Valencia, Spain",
                    "travel_window": "late September",
                    "trip_length": "4 nights",
                    "weather_preference": "warm",
                    "travelers": {"adults": 1},
                    "custom_style": "business conference",
                    "budget_posture": "mid_range",
                    "budget_currency": "GBP",
                },
                "timeline": [],
                "module_outputs": {},
                "status": {
                    "confirmed_fields": [
                        "from_location",
                        "to_location",
                        "travel_window",
                        "trip_length",
                        "adults",
                    ],
                },
            },
        }
    )

    conversation = result["trip_draft"]["conversation"]
    observability = result["metadata"]["planner_observability"]
    assistant_response = result["assistant_response"].lower()

    assert conversation["planning_mode"] == "quick"
    assert observability["provider_activation"]["quick_plan_ready"] is True
    assert observability["provider_activation"]["quick_plan_readiness"]["module_scope_source"] == "default_full_trip"
    assert observability["provider_activation"]["quick_plan_review"]["status"] == "complete"
    assert observability["provider_activation"]["quick_plan_acceptance"]["accepted"] is True
    assert observability["provider_activation"]["quick_plan_acceptance"]["quality_status"] == "pass"
    assert observability["provider_activation"]["allowed_modules"] == [
        "flights",
        "hotels",
        "activities",
        "weather",
    ]
    assert "started a quick plan" in assistant_response
    assert "valencia, spain" in assistant_response


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
        "adult traveler count is required when flights or hotels are included"
    ]
    assert observability["provider_activation"]["blocked_modules"]["hotels"] == [
        "adult traveler count is required when flights or hotels are included"
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


def test_advanced_review_opens_when_enabled_anchors_are_complete(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Okay, what do we have?",
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
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
                    "advanced_step": "anchor_flow",
                    "advanced_anchor": "activities",
                    "trip_style_planning": {
                        "substep": "completed",
                        "selection_status": "completed",
                        "tradeoff_status": "completed",
                        "selected_primary_direction": "culture_led",
                        "selected_pace": "balanced",
                        "completion_summary": "Culture-led, balanced days are set.",
                    },
                    "activity_planning": {
                        "completion_status": "completed",
                        "schedule_status": "ready",
                        "completion_summary": "Temples, markets, and an evening walk are planned.",
                        "workspace_touched": True,
                        "recommended_candidates": [
                            {
                                "id": "activity_temple",
                                "title": "Temple morning",
                                "disposition": "essential",
                            },
                            {
                                "id": "activity_market",
                                "title": "Market afternoon",
                                "disposition": "essential",
                            },
                        ],
                        "visible_candidates": [
                            {
                                "id": "activity_temple",
                                "title": "Temple morning",
                                "disposition": "essential",
                            },
                            {
                                "id": "activity_market",
                                "title": "Market afternoon",
                                "disposition": "essential",
                            },
                        ],
                        "timeline_blocks": [
                            {
                                "id": "block_temple",
                                "type": "activity",
                                "candidate_id": "activity_temple",
                                "title": "Temple morning",
                                "day_index": 1,
                                "day_label": "Day 1",
                            },
                            {
                                "id": "block_market",
                                "type": "activity",
                                "candidate_id": "activity_market",
                                "title": "Market afternoon",
                                "day_index": 2,
                                "day_label": "Day 2",
                            },
                        ],
                        "reserved_candidate_ids": ["activity_extra"],
                    },
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
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
    section_titles = {section["title"] for section in board["advanced_review_section_cards"]}

    assert conversation["advanced_step"] == "review"
    assert board["mode"] == "advanced_review_workspace"
    assert board["advanced_review_readiness_status"] == "ready"
    assert {"Trip character", "Planned experiences"}.issubset(section_titles)
    assert "finalize" not in json.dumps(board).lower()


def test_chat_can_request_advanced_review_before_everything_is_set(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_advanced_review=True,
            assistant_response="",
        ),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "Can we review the plan so far?",
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
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
                    "advanced_step": "choose_anchor",
                    "trip_style_planning": {
                        "substep": "completed",
                        "selection_status": "completed",
                        "completion_summary": "Food-led and local is the working trip character.",
                    },
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
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
    sections = {section["id"]: section for section in board["advanced_review_section_cards"]}

    assert conversation["advanced_step"] == "review"
    assert board["mode"] == "advanced_review_workspace"
    assert board["advanced_review_readiness_status"] == "flexible"
    assert sections["activities"]["status"] == "flexible"


def test_advanced_review_revision_action_routes_to_existing_workspace(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_review_stay",
                "type": "revise_advanced_review_section",
                "advanced_anchor": "stay",
            },
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
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
                    "advanced_step": "review",
                    "advanced_anchor": None,
                    "stay_planning": {
                        "selected_hotel_id": "hotel_gion",
                        "selected_hotel_name": "Gion House",
                        "hotel_selection_status": "selected",
                        "hotel_selection_rationale": "Gion House keeps the evenings walkable.",
                    },
                    "trip_style_planning": {
                        "substep": "completed",
                        "selection_status": "completed",
                        "tradeoff_status": "completed",
                        "completion_summary": "Culture-led, balanced days are set.",
                    },
                    "activity_planning": {
                        "completion_status": "completed",
                        "completion_summary": "Experiences are selected.",
                    },
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
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

    assert conversation["advanced_step"] == "anchor_flow"
    assert conversation["advanced_anchor"] == "stay"
    assert board["mode"].startswith("advanced_stay")


def test_finalize_advanced_plan_from_review_marks_trip_finalized(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_finalize_advanced",
                "type": "finalize_advanced_plan",
            },
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
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
                    "advanced_step": "review",
                    "trip_style_planning": {
                        "substep": "completed",
                        "selection_status": "completed",
                        "tradeoff_status": "completed",
                        "completion_summary": "Culture-led, balanced days are set.",
                    },
                    "activity_planning": {
                        "completion_status": "completed",
                        "completion_summary": "Temples and markets are planned.",
                        "schedule_status": "ready",
                    },
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
                                "options": [],
                                "selected_option": "confirm_trip_details",
                            }
                        ]
                    },
                },
            },
        }
    )

    status = result["trip_draft"]["status"]
    conversation = result["trip_draft"]["conversation"]

    assert status["confirmation_status"] == "finalized"
    assert status["brochure_ready"] is True
    assert conversation["confirmation_status"] == "finalized"
    assert conversation["finalized_via"] == "board"
    assert "reviewed Advanced plan" in result["assistant_response"]
    assert any(
        event["title"] == "Advanced plan finalized"
        for event in conversation["memory"]["decision_history"]
    )


def test_finalize_advanced_plan_allows_needs_review_notes(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_finalize_advanced_with_warning",
                "type": "finalize_advanced_plan",
            },
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
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
                    "advanced_step": "review",
                    "stay_planning": {
                        "selected_hotel_id": "hotel_gion",
                        "selected_hotel_name": "Gion House",
                        "hotel_selection_status": "needs_review",
                        "hotel_compatibility_status": "strained",
                        "hotel_compatibility_notes": [
                            "The stay is a little far from the strongest evening plan."
                        ],
                    },
                    "trip_style_planning": {
                        "substep": "completed",
                        "selection_status": "completed",
                        "tradeoff_status": "completed",
                        "completion_summary": "Culture-led, balanced days are set.",
                    },
                    "activity_planning": {
                        "completion_status": "completed",
                        "completion_summary": "Experiences are selected.",
                    },
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
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
    review = conversation["advanced_review_planning"]

    assert result["trip_draft"]["status"]["confirmation_status"] == "finalized"
    assert review["readiness_status"] == "needs_review"
    assert "far from the strongest evening plan" in " ".join(review["review_notes"])


def test_finalize_advanced_plan_does_not_finalize_quick_plan(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_wrong_finalizer",
                "type": "finalize_advanced_plan",
            },
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    },
                },
                "timeline": [
                    {
                        "id": "day_1",
                        "day": 1,
                        "type": "activity",
                        "title": "Temple walk",
                    }
                ],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "quick",
                    "planning_mode_status": "selected",
                },
            },
        }
    )

    assert result["trip_draft"]["status"]["confirmation_status"] == "unconfirmed"


def test_finalize_quick_plan_blocks_loose_timeline_without_acceptance(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_finalize_loose_quick",
                "type": "finalize_quick_plan",
            },
            "trip_draft": {
                "title": "Lisbon planner",
                "configuration": {
                    "to_location": "Lisbon",
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    },
                },
                "timeline": [
                    {
                        "id": "activity_1",
                        "type": "activity",
                        "title": "Alfama walk",
                        "start_at": "2027-05-01T10:00:00Z",
                        "end_at": "2027-05-01T12:00:00Z",
                        "source_module": "activities",
                    }
                ],
                "module_outputs": {},
                "status": {},
                "conversation": {
                    "planning_mode": "quick",
                    "planning_mode_status": "selected",
                },
            },
        }
    )

    finalization = result["trip_draft"]["conversation"]["quick_plan_finalization"]
    assert result["trip_draft"]["status"]["confirmation_status"] == "unconfirmed"
    assert finalization["brochure_eligible"] is False
    assert "reviewed and accepted" in finalization["blocked_reasons"][0]
    assert "did not save a brochure snapshot" in result["assistant_response"]


def test_finalize_quick_plan_blocks_full_trip_missing_required_logistics(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_finalize_missing_logistics",
                "type": "finalize_quick_plan",
            },
            "trip_draft": {
                "title": "Rome planner",
                "configuration": {
                    "to_location": "Rome",
                    "selected_modules": {
                        "flights": True,
                        "weather": True,
                        "activities": True,
                        "hotels": True,
                    },
                },
                "timeline": [
                    {
                        "id": "activity_1",
                        "type": "activity",
                        "title": "Forum morning",
                        "start_at": "2027-06-02T10:00:00Z",
                        "end_at": "2027-06-02T12:00:00Z",
                        "source_module": "activities",
                    }
                ],
                "module_outputs": {
                    "activities": [
                        {
                            "id": "activity_1",
                            "title": "Forum morning",
                        }
                    ]
                },
                "status": {},
                "conversation": {
                    "planning_mode": "quick",
                    "planning_mode_status": "selected",
                    "quick_plan_finalization": {
                        "accepted": True,
                        "review_status": "complete",
                        "quality_status": "pass",
                        "brochure_eligible": True,
                        "accepted_modules": ["flights", "weather", "activities", "hotels"],
                        "assumptions": [],
                        "blocked_reasons": [],
                        "review_result": {"status": "complete"},
                        "quality_result": {"status": "pass"},
                    },
                },
            },
        }
    )

    finalization = result["trip_draft"]["conversation"]["quick_plan_finalization"]
    assert result["trip_draft"]["status"]["confirmation_status"] == "unconfirmed"
    assert finalization["brochure_eligible"] is False
    assert any("flight" in reason for reason in finalization["blocked_reasons"])
    assert any("stay" in reason for reason in finalization["blocked_reasons"])
    assert finalization["quality_status"] == "pass"


def test_finalize_quick_plan_blocks_without_quality_pass(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_finalize_quality_missing",
                "type": "finalize_quick_plan",
            },
            "trip_draft": {
                "title": "Porto planner",
                "configuration": {
                    "to_location": "Porto",
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    },
                },
                "timeline": [
                    {
                        "id": "activity_1",
                        "type": "activity",
                        "title": "Ribeira food walk",
                        "start_at": "2027-04-04T10:00:00Z",
                        "end_at": "2027-04-04T12:00:00Z",
                        "source_module": "activities",
                    }
                ],
                "module_outputs": {
                    "activities": [
                        {
                            "id": "activity_1",
                            "title": "Ribeira food walk",
                        }
                    ]
                },
                "status": {},
                "conversation": {
                    "planning_mode": "quick",
                    "planning_mode_status": "selected",
                    "quick_plan_finalization": {
                        "accepted": True,
                        "review_status": "complete",
                        "quality_status": "repairable",
                        "brochure_eligible": True,
                        "accepted_modules": ["activities"],
                        "assumptions": [],
                        "blocked_reasons": [],
                        "review_result": {"status": "complete"},
                        "quality_result": {"status": "repairable"},
                    },
                },
            },
        }
    )

    finalization = result["trip_draft"]["conversation"]["quick_plan_finalization"]
    assert result["trip_draft"]["status"]["confirmation_status"] == "unconfirmed"
    assert finalization["brochure_eligible"] is False
    assert finalization["quality_status"] == "repairable"
    assert any("quality review" in reason for reason in finalization["blocked_reasons"])


def test_finalize_quick_plan_allows_accepted_activities_only_scope(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(assistant_response=""),
    )

    result = bootstrap.process_trip_turn(
        {
            "user_input": "",
            "board_action": {
                "action_id": "action_finalize_activities_only",
                "type": "finalize_quick_plan",
            },
            "trip_draft": {
                "title": "Porto planner",
                "configuration": {
                    "to_location": "Porto",
                    "selected_modules": {
                        "flights": False,
                        "weather": False,
                        "activities": True,
                        "hotels": False,
                    },
                },
                "timeline": [
                    {
                        "id": "activity_1",
                        "type": "activity",
                        "title": "Ribeira food walk",
                        "start_at": "2027-04-04T10:00:00Z",
                        "end_at": "2027-04-04T12:00:00Z",
                        "source_module": "activities",
                    }
                ],
                "module_outputs": {
                    "activities": [
                        {
                            "id": "activity_1",
                            "title": "Ribeira food walk",
                        }
                    ]
                },
                "status": {},
                "conversation": {
                    "planning_mode": "quick",
                    "planning_mode_status": "selected",
                    "quick_plan_finalization": {
                        "accepted": True,
                        "review_status": "complete",
                        "quality_status": "pass",
                        "brochure_eligible": True,
                        "accepted_modules": ["activities"],
                        "assumptions": [],
                        "blocked_reasons": [],
                        "review_result": {"status": "complete"},
                        "quality_result": {"status": "pass"},
                    },
                },
            },
        }
    )

    finalization = result["trip_draft"]["conversation"]["quick_plan_finalization"]
    assert result["trip_draft"]["status"]["confirmation_status"] == "finalized"
    assert result["trip_draft"]["status"]["brochure_ready"] is True
    assert finalization["brochure_eligible"] is True
    assert finalization["quality_status"] == "pass"
    assert finalization["accepted_modules"] == ["activities"]


def test_chat_advanced_finalization_only_finalizes_from_review(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "generate_llm_trip_update",
        lambda **_: TripTurnUpdate(
            requested_advanced_finalization=True,
            assistant_response="",
        ),
    )

    early_result = bootstrap.process_trip_turn(
        {
            "user_input": "Make this brochure-ready.",
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
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
                    "advanced_step": "choose_anchor",
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
                                "options": [],
                                "selected_option": "confirm_trip_details",
                            }
                        ]
                    },
                },
            },
        }
    )

    assert early_result["trip_draft"]["status"]["confirmation_status"] == "unconfirmed"
    assert early_result["trip_draft"]["conversation"]["advanced_step"] == "review"

    review_result = bootstrap.process_trip_turn(
        {
            "user_input": "Make this brochure-ready.",
            "trip_draft": {
                "title": "Kyoto planner",
                "configuration": {
                    "to_location": "Kyoto",
                    "start_date": "2027-03-22",
                    "end_date": "2027-03-26",
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
                    "advanced_step": "review",
                    "memory": {
                        "decision_history": [
                            {
                                "id": "decision_confirmed",
                                "title": "Trip details confirmed",
                                "description": "The user confirmed the working trip details.",
                                "options": [],
                                "selected_option": "confirm_trip_details",
                            }
                        ]
                    },
                },
            },
        }
    )

    assert review_result["trip_draft"]["status"]["confirmation_status"] == "finalized"
    assert review_result["trip_draft"]["conversation"]["finalized_via"] == "chat"


def _passing_quick_plan_quality_review() -> QuickPlanQualityReviewResult:
    return QuickPlanQualityReviewResult(
        status="pass",
        show_to_user=True,
        scorecard=QuickPlanQualityScorecard(
            geography=8,
            pacing=8,
            local_specificity=8,
            user_fit=8,
            logistics_realism=8,
            fact_safety=8,
        ),
    )
