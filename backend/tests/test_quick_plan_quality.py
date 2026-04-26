from datetime import datetime, timezone

from app.graph.planner import quick_plan
from app.graph.planner.quick_plan_dossier import (
    QuickPlanReadiness,
    build_quick_plan_dossier,
    evaluate_quick_plan_readiness,
)
from app.graph.planner.quick_plan_dates import (
    QuickPlanWorkingDateDecision,
    apply_quick_plan_working_dates,
)
from app.graph.planner.quick_plan_selection import (
    build_quick_plan_timeline_module_outputs,
    prioritize_quick_plan_module_outputs,
)
from app.graph.planner.provider_enrichment import build_timeline
from app.graph.planner.quick_plan import generate_quick_plan_draft
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft, TripTurnUpdate
from app.schemas.trip_conversation import (
    ConversationDecisionEvent,
    ConversationFieldMemory,
    ConversationOptionMemory,
    ConversationTurnSummary,
    TripConversationState,
)
from app.schemas.trip_planning import (
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


class _FakeStructuredModel:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def invoke(self, messages):
        self._captured["messages"] = messages
        return QuickPlanDraft()


class _FakeChatModel:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _FakeStructuredModel(self._captured)


def test_quick_plan_prompt_pushes_for_thematic_day_shape(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan,
        "create_quick_plan_chat_model",
        lambda temperature=0.2: _FakeChatModel(captured),
    )

    generate_quick_plan_draft(
        title="Lisbon Food Escape",
        configuration=TripConfiguration(
            to_location="Lisbon",
            travel_window="late September",
            trip_length="4 nights",
            activity_styles=["food", "culture"],
        ),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
    )

    prompt = captured["messages"][1][1]

    assert captured["method"] == "json_schema"
    assert "Make each day feel intentionally different." in prompt
    assert "Give each day a clear center of gravity" in prompt
    assert "Avoid generic filler blocks like" in prompt
    assert "Connect blocks together so the day reads like a real route through the city" in prompt
    assert "If weather data exists, adapt the shape of the day around it" in prompt
    assert "Include meal rhythm" in prompt
    assert "return-to-stay or back-to-hotel" in prompt
    assert "protect conference time" in prompt


def test_quick_plan_readiness_defaults_implicit_scope_to_full_trip() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            from_location="London",
            start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
            adults=2,
            confirmed_fields=[
                "to_location",
                "from_location",
                "start_date",
                "end_date",
                "adults",
            ],
            field_sources=[
                {"field": "to_location", "source": "user_explicit"},
                {"field": "from_location", "source": "user_explicit"},
                {"field": "start_date", "source": "assistant_derived"},
                {"field": "end_date", "source": "assistant_derived"},
                {"field": "adults", "source": "user_explicit"},
            ],
            field_confidences=[
                {"field": "to_location", "confidence": "high"},
                {"field": "from_location", "confidence": "high"},
                {"field": "start_date", "confidence": "medium"},
                {"field": "end_date", "confidence": "medium"},
                {"field": "adults", "confidence": "high"},
            ],
        ),
        configuration=TripConfiguration(
            to_location="Lisbon",
            from_location="London",
            start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
            travelers={"adults": 2},
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={"action_id": "quick", "type": "select_quick_plan"},
    )

    assert readiness["quick_plan_ready"] is True
    assert readiness["quick_plan_readiness"]["module_scope_source"] == "default_full_trip"
    assert readiness["quick_plan_readiness"]["allowed_modules"] == [
        "flights",
        "hotels",
        "activities",
        "weather",
    ]


def test_quick_plan_readiness_trusts_present_fields_in_confirmed_brief() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(requested_planning_mode="quick"),
        configuration=TripConfiguration(
            to_location="Kyoto",
            from_location="London",
            start_date=datetime(2026, 5, 8, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 5, 12, tzinfo=timezone.utc).date(),
            travelers={"adults": 2},
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={},
    )

    assert readiness["quick_plan_ready"] is True
    assert readiness["origin_ready"] is True
    assert readiness["traveler_ready"] is True
    assert readiness["field_readiness"]["origin"]["source"] == "confirmed_brief"
    assert readiness["quick_plan_readiness"]["missing_requirements"] == []


def test_quick_plan_readiness_allows_origin_when_flexibility_is_false() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(
            requested_planning_mode="quick",
            confirmed_trip_brief=True,
            confirmed_fields=[
                "to_location",
                "from_location",
                "from_location_flexible",
                "start_date",
                "end_date",
                "adults",
            ],
            field_sources=[
                {"field": "to_location", "source": "user_explicit"},
                {"field": "from_location", "source": "user_explicit"},
                {"field": "from_location_flexible", "source": "user_explicit"},
                {"field": "start_date", "source": "assistant_derived"},
                {"field": "end_date", "source": "assistant_derived"},
                {"field": "adults", "source": "user_explicit"},
            ],
            field_confidences=[
                {"field": "to_location", "confidence": "high"},
                {"field": "from_location", "confidence": "high"},
                {"field": "from_location_flexible", "confidence": "high"},
                {"field": "start_date", "confidence": "medium"},
                {"field": "end_date", "confidence": "medium"},
                {"field": "adults", "confidence": "high"},
            ],
        ),
        configuration=TripConfiguration(
            to_location="Kyoto",
            from_location="London",
            from_location_flexible=False,
            start_date=datetime(2026, 5, 7, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 5, 11, tzinfo=timezone.utc).date(),
            travelers={"adults": 2},
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={},
    )

    assert readiness["quick_plan_ready"] is True
    assert readiness["origin_ready"] is True
    assert readiness["blocked_modules"] == {}


def test_quick_plan_readiness_blocks_full_trip_without_origin() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
            adults=2,
            confirmed_fields=["to_location", "start_date", "end_date", "adults"],
            field_sources=[
                {"field": "to_location", "source": "user_explicit"},
                {"field": "start_date", "source": "assistant_derived"},
                {"field": "end_date", "source": "assistant_derived"},
                {"field": "adults", "source": "user_explicit"},
            ],
            field_confidences=[
                {"field": "to_location", "confidence": "high"},
                {"field": "start_date", "confidence": "medium"},
                {"field": "end_date", "confidence": "medium"},
                {"field": "adults", "confidence": "high"},
            ],
        ),
        configuration=TripConfiguration(
            to_location="Lisbon",
            start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
            travelers={"adults": 2},
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={},
    )

    assert readiness["quick_plan_ready"] is False
    assert readiness["quick_plan_readiness"]["missing_requirements"] == ["origin"]
    assert readiness["blocked_modules"]["flights"] == [
        "origin is required when flights are included"
    ]


def test_quick_plan_readiness_requires_working_dates_not_rough_timing_only() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            from_location="London",
            travel_window="late September",
            trip_length="4 nights",
            adults=2,
            confirmed_fields=[
                "to_location",
                "from_location",
                "travel_window",
                "trip_length",
                "adults",
            ],
            field_sources=[
                {"field": "to_location", "source": "user_explicit"},
                {"field": "from_location", "source": "user_explicit"},
                {"field": "travel_window", "source": "user_explicit"},
                {"field": "trip_length", "source": "user_explicit"},
                {"field": "adults", "source": "user_explicit"},
            ],
            field_confidences=[
                {"field": "to_location", "confidence": "high"},
                {"field": "from_location", "confidence": "high"},
                {"field": "travel_window", "confidence": "high"},
                {"field": "trip_length", "confidence": "high"},
                {"field": "adults", "confidence": "high"},
            ],
        ),
        configuration=TripConfiguration(
            to_location="Lisbon",
            from_location="London",
            travel_window="late September",
            trip_length="4 nights",
            travelers={"adults": 2},
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={},
    )

    assert readiness["quick_plan_ready"] is False
    assert readiness["quick_plan_readiness"]["missing_requirements"] == [
        "working_dates"
    ]


def test_quick_plan_readiness_blocks_logistics_without_traveler_count() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            from_location="London",
            start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
            confirmed_fields=["to_location", "from_location", "start_date", "end_date"],
            field_sources=[
                {"field": "to_location", "source": "user_explicit"},
                {"field": "from_location", "source": "user_explicit"},
                {"field": "start_date", "source": "assistant_derived"},
                {"field": "end_date", "source": "assistant_derived"},
            ],
            field_confidences=[
                {"field": "to_location", "confidence": "high"},
                {"field": "from_location", "confidence": "high"},
                {"field": "start_date", "confidence": "medium"},
                {"field": "end_date", "confidence": "medium"},
            ],
        ),
        configuration=TripConfiguration(
            to_location="Lisbon",
            from_location="London",
            start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={},
    )

    assert readiness["quick_plan_ready"] is False
    assert readiness["quick_plan_readiness"]["missing_requirements"] == [
        "adult_traveler_count"
    ]
    assert readiness["blocked_modules"]["flights"] == [
        "adult traveler count is required when flights or hotels are included"
    ]
    assert readiness["blocked_modules"]["hotels"] == [
        "adult traveler count is required when flights or hotels are included"
    ]


def test_quick_plan_readiness_allows_explicit_activities_only_without_logistics() -> None:
    readiness = evaluate_quick_plan_readiness(
        current_conversation=TripConversationState(),
        llm_update=TripTurnUpdate(
            to_location="Barcelona",
            start_date=datetime(2026, 10, 2, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 10, 5, tzinfo=timezone.utc).date(),
            selected_modules={
                "flights": False,
                "hotels": False,
                "activities": True,
                "weather": False,
            },
            confirmed_fields=["to_location", "start_date", "end_date", "selected_modules"],
            field_sources=[
                {"field": "to_location", "source": "user_explicit"},
                {"field": "start_date", "source": "assistant_derived"},
                {"field": "end_date", "source": "assistant_derived"},
                {"field": "selected_modules", "source": "user_explicit"},
            ],
            field_confidences=[
                {"field": "to_location", "confidence": "high"},
                {"field": "start_date", "confidence": "medium"},
                {"field": "end_date", "confidence": "medium"},
                {"field": "selected_modules", "confidence": "high"},
            ],
        ),
        configuration=TripConfiguration(
            to_location="Barcelona",
            start_date=datetime(2026, 10, 2, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 10, 5, tzinfo=timezone.utc).date(),
            selected_modules={
                "flights": False,
                "hotels": False,
                "activities": True,
                "weather": False,
            },
        ),
        brief_confirmed=True,
        planning_mode="quick",
        board_action={},
    )

    assert readiness["quick_plan_ready"] is True
    assert readiness["quick_plan_readiness"]["module_scope_source"] == "user_explicit"
    assert readiness["quick_plan_readiness"]["allowed_modules"] == ["activities"]


def test_quick_plan_dossier_includes_context_and_assumptions() -> None:
    conversation = TripConversationState(
        active_goals=["Keep the trip food-led."],
        memory={
            "field_memory": {
                "to_location": ConversationFieldMemory(
                    field="to_location",
                    value="Lisbon",
                    source="user_explicit",
                    confidence_level="high",
                )
            },
            "turn_summaries": [
                ConversationTurnSummary(
                    turn_id="turn_old",
                    user_message="I want Lisbon.",
                    summary_text="The user wants Lisbon.",
                )
            ],
            "decision_history": [
                ConversationDecisionEvent(
                    id="decision_scope",
                    title="Planning mode selected",
                    description="The user chose Quick Plan.",
                    options=["quick", "advanced"],
                    selected_option="quick",
                )
            ],
            "mentioned_options": [
                ConversationOptionMemory(kind="destination", value="Lisbon")
            ],
            "rejected_options": [
                ConversationOptionMemory(kind="destination", value="Porto")
            ],
        },
    )
    llm_update = TripTurnUpdate(active_goals=["Avoid overpacking the days."])
    readiness = QuickPlanReadiness(
        ready=True,
        allowed_modules=["activities"],
        module_scope_source="user_explicit",
    )
    provider_activation = {
        "field_readiness": {"destination": {"has_value": True}},
    }
    decision = QuickPlanWorkingDateDecision(
        start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
        confidence="medium",
        rationale="I chose an editable late-September window.",
    )

    dossier = build_quick_plan_dossier(
        current_conversation=conversation,
        llm_update=llm_update,
        configuration=TripConfiguration(
            to_location="Lisbon",
            start_date=decision.start_date,
            end_date=decision.end_date,
            selected_modules={
                "flights": False,
                "hotels": False,
                "activities": True,
                "weather": False,
            },
        ),
        readiness=readiness,
        provider_activation=provider_activation,
        raw_messages=[
            {"role": "user", "content": "Old"},
            {"role": "assistant", "content": "Earlier answer"},
        ],
        user_input="Build activities only.",
        board_action={},
        working_date_decision=decision,
    )

    assert dossier.recent_raw_messages[-1]["content"] == "Build activities only."
    assert dossier.compact_memory["field_memory"]["to_location"]["value"] == "Lisbon"
    assert dossier.decision_history[0]["selected_option"] == "quick"
    assert dossier.module_scope_source == "user_explicit"
    assert dossier.assumptions[0]["type"] == "assistant_chosen_working_dates"
    assert {option["value"] for option in dossier.mentioned_options} == {"Lisbon"}
    assert {option["value"] for option in dossier.rejected_options} == {"Porto"}


def test_quick_plan_build_timeline_keeps_scheduled_preview_authoritative() -> None:
    configuration = TripConfiguration(
        to_location="Lisbon",
        start_date=datetime(2026, 9, 18, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 9, 21, tzinfo=timezone.utc).date(),
    )
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="flight_outbound",
                direction="outbound",
                carrier="TAP",
                departure_airport="LHR",
                arrival_airport="LIS",
                departure_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 9, 18, 10, 45, tzinfo=timezone.utc),
                duration_text="2h 45m",
                notes=["Direct morning flight."],
            )
        ]
    )

    timeline = build_timeline(
        configuration=configuration,
        llm_preview=[
            ProposedTimelineItem(
                type="note",
                title="Arrival in Lisbon",
                day_label="Day 1",
                summary="Land, transfer in, and settle after the flight.",
                details=["Airport transfer and arrival buffer."],
            ),
            ProposedTimelineItem(
                type="activity",
                title="Sunset walk through Alfama",
                day_label="Day 1",
                summary="Ease into the city with a slower first evening.",
                details=["Short tram hop to start the trip softly."],
            ),
            ProposedTimelineItem(
                type="transfer",
                title="Airport transfer to Baixa",
                day_label="Day 1",
                start_at=datetime(2026, 9, 18, 11, 15, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 18, 11, 55, tzinfo=timezone.utc),
                timing_source="planner_estimate",
                details=["Estimated transfer after landing."],
            ),
        ],
        module_outputs=module_outputs,
        include_derived_when_preview_present=False,
    )

    titles = [item.title for item in timeline]

    assert "Outbound flight option" not in titles
    assert "Arrival in Lisbon" not in titles
    assert "Airport transfer to Baixa" in titles
    assert "Sunset walk through Alfama" in titles


def test_quick_plan_auto_dates_are_assistant_derived_working_dates() -> None:
    configuration = TripConfiguration(
        to_location="Lisbon",
        travel_window="late September 2026",
        trip_length="4 nights",
    )

    next_configuration, next_update, decision = apply_quick_plan_working_dates(
        configuration=configuration,
        llm_update=TripTurnUpdate(),
        conversation=TripConversationState(),
        today=datetime(2026, 4, 25, tzinfo=timezone.utc).date(),
    )

    assert decision is not None
    assert next_configuration.start_date is not None
    assert next_configuration.end_date is not None
    assert next_configuration.end_date > next_configuration.start_date
    assert "start_date" in next_update.inferred_fields
    assert "end_date" in next_update.inferred_fields
    assert {
        (source.field, source.source)
        for source in next_update.field_sources
    } >= {
        ("start_date", "assistant_derived"),
        ("end_date", "assistant_derived"),
    }


def test_quick_plan_auto_dates_use_requested_trip_length() -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="summer",
        trip_length="5 days",
    )

    next_configuration, _, decision = apply_quick_plan_working_dates(
        configuration=configuration,
        llm_update=TripTurnUpdate(),
        conversation=TripConversationState(),
        today=datetime(2026, 4, 25, tzinfo=timezone.utc).date(),
    )

    assert decision is not None
    assert (next_configuration.end_date - next_configuration.start_date).days == 4
    assert "5 days" in decision.rationale


def test_quick_plan_auto_dates_roll_this_month_forward_when_window_has_passed() -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="this month for weekend",
        trip_length="5 days",
    )

    next_configuration, _, decision = apply_quick_plan_working_dates(
        configuration=configuration,
        llm_update=TripTurnUpdate(),
        conversation=TripConversationState(),
        today=datetime(2026, 4, 25, tzinfo=timezone.utc).date(),
    )

    assert decision is not None
    assert next_configuration.start_date.isoformat() == "2026-05-01"
    assert (next_configuration.end_date - next_configuration.start_date).days == 4
    assert "did not leave a reliable future 5 days slot" in decision.rationale


def test_quick_plan_timeline_uses_selected_flights_and_hotel_only() -> None:
    configuration = TripConfiguration(
        to_location="Lisbon",
        start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
        budget_posture="mid_range",
    )
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="late_outbound",
                direction="outbound",
                carrier="Carrier B",
                departure_airport="LHR",
                arrival_airport="LIS",
                arrival_time=datetime(2026, 9, 24, 23, 0, tzinfo=timezone.utc),
                price_text="GBP 80",
                stop_count=1,
                timing_quality="Very late arrival",
            ),
            FlightDetail(
                id="good_outbound",
                direction="outbound",
                carrier="Carrier A",
                departure_airport="LHR",
                arrival_airport="LIS",
                arrival_time=datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc),
                price_text="GBP 120",
                stop_count=0,
                timing_quality="Useful arrival window",
            ),
            FlightDetail(
                id="early_return",
                direction="return",
                carrier="Carrier B",
                departure_airport="LIS",
                arrival_airport="LHR",
                departure_time=datetime(2026, 9, 28, 6, 0, tzinfo=timezone.utc),
                price_text="GBP 70",
                stop_count=0,
                timing_quality="Early return",
            ),
            FlightDetail(
                id="good_return",
                direction="return",
                carrier="Carrier A",
                departure_airport="LIS",
                arrival_airport="LHR",
                departure_time=datetime(2026, 9, 28, 16, 0, tzinfo=timezone.utc),
                price_text="GBP 130",
                stop_count=0,
            ),
        ],
        hotels=[
            HotelStayDetail(
                id="bare_hotel",
                hotel_name="Bare Hotel",
                nightly_rate_amount=90,
            ),
            HotelStayDetail(
                id="richer_hotel",
                hotel_name="Richer Hotel",
                area="Baixa",
                address="Rua Example",
                image_url="https://example.com/hotel.jpg",
                source_url="https://example.com",
                nightly_rate_amount=120,
            ),
        ],
    )

    prioritized = prioritize_quick_plan_module_outputs(
        configuration=configuration,
        module_outputs=module_outputs,
    )
    timeline_outputs = build_quick_plan_timeline_module_outputs(prioritized)

    assert [flight.id for flight in timeline_outputs.flights] == [
        "good_outbound",
        "good_return",
    ]
    assert [hotel.id for hotel in timeline_outputs.hotels] == ["richer_hotel"]
