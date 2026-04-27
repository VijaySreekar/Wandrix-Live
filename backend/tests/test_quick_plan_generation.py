from datetime import datetime, timezone

import pytest

from app.graph.planner import quick_plan_day_architecture
from app.graph.planner import quick_plan_generation
from app.graph.planner import quick_plan_provider_brief
from app.graph.planner import quick_plan_strategy
from app.graph.planner.quick_plan_dossier import QuickPlanDossier, QuickPlanReadiness
from app.graph.planner.quick_plan_day_architecture import (
    QuickPlanDayArchitecture,
    QuickPlanDayPlan,
)
from app.graph.planner.quick_plan_generation import (
    QuickPlanGenerationAttempt,
    accept_quick_plan_candidate,
    build_quick_plan_quality_repair_context,
    build_quick_plan_repair_context,
    run_quick_plan_generation,
    run_quick_plan_repair,
)
from app.graph.planner.quick_plan_provider_brief import (
    QuickPlanProviderBrief,
    QuickPlanProviderFlightAnchor,
    QuickPlanProviderStayAnchor,
)
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityIssue,
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
)
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.quick_plan_strategy import (
    QuickPlanModulePriority,
    QuickPlanStrategyBrief,
)
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


class _FakeStructuredModel:
    def __init__(self, captured: dict, response) -> None:
        self._captured = captured
        self._response = response

    def invoke(self, messages):
        self._captured["messages"] = messages
        return self._response


class _FakeChatModel:
    def __init__(self, captured: dict, response) -> None:
        self._captured = captured
        self._response = response

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _FakeStructuredModel(self._captured, self._response)


@pytest.fixture(autouse=True)
def _patch_quick_plan_intelligence(monkeypatch) -> None:
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_strategy_brief",
        lambda **_: _strategy_brief(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_provider_brief",
        lambda **_: _provider_brief(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_day_architecture",
        lambda **_: _day_architecture(),
    )


def test_quick_plan_generation_uses_dossier_allowed_modules(monkeypatch) -> None:
    captured: dict = {}

    def _fake_build_outputs(
        *,
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules,
    ):
        del configuration, previous_configuration, existing_module_outputs
        captured["allowed_modules"] = allowed_modules
        return TripModuleOutputs()

    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        _fake_build_outputs,
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "generate_quick_plan_draft",
        lambda **_: QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="El Born food walk",
                    day_label="Day 1",
                )
            ]
        ),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "schedule_quick_plan_draft",
        lambda **kwargs: kwargs["draft"],
    )

    attempt = run_quick_plan_generation(
        dossier=_dossier(allowed_modules=["activities", "weather"]),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
    )

    assert captured["allowed_modules"] == {"activities", "weather"}
    assert attempt.status == "generated"


def test_quick_plan_generation_passes_same_dossier_to_draft_and_scheduler(
    monkeypatch,
) -> None:
    captured: dict = {}
    dossier = _dossier(allowed_modules=["activities"])

    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(),
    )

    def _fake_generate(**kwargs):
        captured["draft_dossier"] = kwargs["dossier"]
        captured["strategy_brief"] = kwargs["strategy_brief"]
        captured["provider_brief"] = kwargs["provider_brief"]
        captured["day_architecture"] = kwargs["day_architecture"]
        return QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Gothic Quarter first evening",
                    day_label="Day 1",
                )
            ]
        )

    def _fake_schedule(**kwargs):
        captured["scheduler_dossier"] = kwargs["dossier"]
        captured["scheduler_draft"] = kwargs["draft"]
        return kwargs["draft"]

    monkeypatch.setattr(quick_plan_generation, "generate_quick_plan_draft", _fake_generate)
    monkeypatch.setattr(quick_plan_generation, "schedule_quick_plan_draft", _fake_schedule)

    attempt = run_quick_plan_generation(
        dossier=dossier,
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
    )

    assert captured["draft_dossier"] is dossier
    assert captured["scheduler_dossier"] is dossier
    assert captured["strategy_brief"].trip_thesis == "Calm food and culture rhythm."
    assert captured["provider_brief"].activity_clusters == ["old town food"]
    assert len(captured["day_architecture"].days) == 4
    assert captured["scheduler_draft"].timeline_preview
    assert attempt.status == "generated"


def test_quick_plan_generation_returns_generated_with_scheduled_rows(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(
            activities=[
                ActivityDetail(
                    id="activity_food_walk",
                    title="El Born food walk",
                )
            ]
        ),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "generate_quick_plan_draft",
        lambda **_: QuickPlanDraft(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "schedule_quick_plan_draft",
        lambda **_: QuickPlanDraft(
            board_summary="A compact activities-first Barcelona draft.",
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="El Born food walk",
                    day_label="Day 1",
                    start_at=datetime(2026, 10, 2, 18, tzinfo=timezone.utc),
                    end_at=datetime(2026, 10, 2, 20, tzinfo=timezone.utc),
                    timing_source="planner_estimate",
                )
            ],
        ),
    )

    attempt = run_quick_plan_generation(
        dossier=_dossier(allowed_modules=["activities"]),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
    )

    assert attempt.status == "generated"
    assert attempt.draft.timeline_preview[0].title == "El Born food walk"
    assert attempt.timeline_module_outputs.activities[0].title == "El Born food walk"


def test_quick_plan_generation_returns_empty_without_scheduled_rows(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "generate_quick_plan_draft",
        lambda **_: QuickPlanDraft(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "schedule_quick_plan_draft",
        lambda **kwargs: kwargs["draft"],
    )

    attempt = run_quick_plan_generation(
        dossier=_dossier(allowed_modules=["activities"]),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
    )

    assert attempt.status == "empty"
    assert attempt.draft.timeline_preview == []


def test_quick_plan_generation_preserves_dossier_assumptions(monkeypatch) -> None:
    assumptions = [
        {
            "type": "assistant_chosen_working_dates",
            "start_date": "2026-10-02",
            "end_date": "2026-10-05",
        }
    ]
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "generate_quick_plan_draft",
        lambda **_: QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Montjuic morning",
                    day_label="Day 2",
                )
            ]
        ),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "schedule_quick_plan_draft",
        lambda **kwargs: kwargs["draft"],
    )

    attempt = run_quick_plan_generation(
        dossier=_dossier(allowed_modules=["activities"], assumptions=assumptions),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
    )

    assert attempt.assumptions == assumptions


def test_quick_plan_generation_returns_empty_when_intelligence_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(),
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_strategy_brief",
        lambda **_: None,
    )
    monkeypatch.setattr(
        quick_plan_generation,
        "generate_quick_plan_draft",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("draft should not run")
        ),
    )

    attempt = run_quick_plan_generation(
        dossier=_dossier(allowed_modules=["activities"]),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
    )

    assert attempt.status == "empty"
    assert attempt.draft.timeline_preview == []


def test_strategy_brief_uses_dossier_context(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan_strategy,
        "create_quick_plan_chat_model",
        lambda **_: _FakeChatModel(captured, _strategy_brief()),
    )

    result = quick_plan_strategy.build_quick_plan_strategy_brief(
        dossier=_dossier(
            allowed_modules=["activities", "weather"],
            assumptions=[{"type": "assistant_chosen_working_dates"}],
        ),
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
    )

    prompt = captured["messages"][1][1]

    assert result is not None
    assert result.trip_thesis == "Calm food and culture rhythm."
    assert "assistant_chosen_working_dates" in prompt
    assert "activities" in prompt
    assert "weather" in prompt


def test_provider_brief_interprets_ranked_primary_anchors(monkeypatch) -> None:
    captured: dict = {}
    response = QuickPlanProviderBrief(
        selected_outbound_flight=QuickPlanProviderFlightAnchor(id="outbound"),
        selected_return_flight=QuickPlanProviderFlightAnchor(id="return"),
        selected_stay_base=QuickPlanProviderStayAnchor(id="hotel_one", area="Gion"),
        activity_clusters=["Gion food walk"],
        missing_provider_facts=[],
        fact_safety_caveats=[],
    )
    monkeypatch.setattr(
        quick_plan_provider_brief,
        "create_quick_plan_chat_model",
        lambda **_: _FakeChatModel(captured, response),
    )

    result = quick_plan_provider_brief.build_quick_plan_provider_brief(
        dossier=_dossier(allowed_modules=["flights", "hotels", "activities"]),
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="outbound",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="KIX",
                ),
                FlightDetail(
                    id="return",
                    direction="return",
                    carrier="BA",
                    departure_airport="KIX",
                    arrival_airport="LHR",
                    price_text="GBP 640",
                ),
            ],
            hotels=[
                HotelStayDetail(id="hotel_one", hotel_name="Gion Stay", area="Gion")
            ],
            activities=[
                ActivityDetail(id="activity_gion", title="Gion food walk")
            ],
        ),
        strategy_brief=_strategy_brief(),
    )

    assert result is not None
    assert result.selected_outbound_flight is not None
    assert result.selected_outbound_flight.id == "outbound"
    assert result.selected_return_flight is not None
    assert result.selected_return_flight.id == "return"
    assert result.selected_stay_base is not None
    assert result.selected_stay_base.id == "hotel_one"
    assert "outbound flight departure time" in result.missing_provider_facts
    assert result.fact_safety_caveats
    assert captured["schema"] is QuickPlanProviderBrief


def test_generation_normalization_adds_missing_required_anchors() -> None:
    draft = QuickPlanDraft(
        board_summary="A Kyoto draft.",
        timeline_preview=[
            ProposedTimelineItem(
                type="meal",
                title="Nishiki Market breakfast",
                day_label="Day 2",
                start_at=datetime(2026, 7, 15, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            )
        ],
    )

    result = quick_plan_generation._ensure_required_quick_plan_rows(
        draft,
        configuration=TripConfiguration(
            from_location="London",
            to_location="Kyoto",
            start_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 18, tzinfo=timezone.utc).date(),
            trip_length="5 days",
        ),
        module_outputs=TripModuleOutputs(),
        allowed_modules=["flights", "hotels", "activities", "weather"],
    )

    assert len(result.timeline_preview) <= 16
    flight_titles = [
        item.title for item in result.timeline_preview if item.source_module == "flights"
    ]
    assert any("Outbound flight" in title for title in flight_titles)
    assert any("Return flight" in title for title in flight_titles)
    assert any(item.source_module == "hotels" for item in result.timeline_preview)
    assert any(item.source_module == "activities" for item in result.timeline_preview)
    assert {item.day_label for item in result.timeline_preview} >= {
        "Day 1",
        "Day 2",
        "Day 3",
        "Day 4",
        "Day 5",
    }
    assert all(item.start_at and item.end_at for item in result.timeline_preview)


def test_generation_normalization_adds_return_anchor_when_only_outbound_exists() -> None:
    draft = QuickPlanDraft(
        board_summary="A Kyoto draft.",
        timeline_preview=[
            ProposedTimelineItem(
                type="flight",
                title="Outbound flight planning block: London to Kyoto",
                day_label="Day 1",
                start_at=datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
                source_module="flights",
            ),
            ProposedTimelineItem(
                type="activity",
                title="Kyoto first evening walk",
                day_label="Day 1",
                start_at=datetime(2026, 7, 14, 19, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
                source_module="activities",
            ),
        ],
    )

    result = quick_plan_generation._ensure_required_quick_plan_rows(
        draft,
        configuration=TripConfiguration(
            from_location="London",
            to_location="Kyoto",
            start_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 18, tzinfo=timezone.utc).date(),
        ),
        module_outputs=TripModuleOutputs(),
        allowed_modules=["flights", "activities"],
    )

    flight_titles = [
        item.title for item in result.timeline_preview if item.source_module == "flights"
    ]
    assert any("Outbound flight" in title for title in flight_titles)
    assert any("Return flight" in title for title in flight_titles)


def test_generation_normalization_treats_note_only_days_as_uncovered_for_activities() -> None:
    draft = QuickPlanDraft(
        board_summary="A Kyoto draft.",
        timeline_preview=[
            ProposedTimelineItem(
                type="activity",
                title="Kyoto arrival walk",
                day_label="Day 1",
                start_at=datetime(2026, 7, 14, 18, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 7, 14, 20, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
                source_module="activities",
            ),
            ProposedTimelineItem(
                type="note",
                title="Kyoto pacing anchor",
                day_label="Day 4",
                start_at=datetime(2026, 7, 17, 11, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 7, 17, 14, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            ),
        ],
    )

    result = quick_plan_generation._ensure_required_quick_plan_rows(
        draft,
        configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 18, tzinfo=timezone.utc).date(),
        ),
        module_outputs=TripModuleOutputs(),
        allowed_modules=["activities"],
    )

    activity_days = {
        item.day_label
        for item in result.timeline_preview
        if item.type == "activity" or item.source_module == "activities"
    }
    assert activity_days >= {"Day 1", "Day 2", "Day 3", "Day 4", "Day 5"}


def test_generation_normalization_uses_day_architecture_for_missing_activity_days() -> None:
    draft = QuickPlanDraft(
        board_summary="A Kyoto draft.",
        timeline_preview=[
            ProposedTimelineItem(
                type="meal",
                title="Breakfast near the hotel",
                day_label="Day 3",
                start_at=datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            )
        ],
    )
    day_architecture = QuickPlanDayArchitecture(
        route_logic="Central base with one west Kyoto excursion.",
        days=[
            QuickPlanDayPlan(
                day_index=1,
                day_label="Day 1",
                theme="Arrival and central Kyoto reset",
                geography_focus="Nakagyo-ku",
                pacing_target="light arrival",
                food_culture_intent="Easy first dinner near the hotel.",
            ),
            QuickPlanDayPlan(
                day_index=2,
                day_label="Day 2",
                theme="Higashiyama lanes and Gion tea culture",
                geography_focus="Higashiyama / Gion",
                pacing_target="calm east-side culture day",
                food_culture_intent="Temple lanes, lunch, and a tea pause.",
            ),
            QuickPlanDayPlan(
                day_index=3,
                day_label="Day 3",
                theme="Arashiyama bamboo, river, and west Kyoto lunch",
                geography_focus="Arashiyama / west Kyoto",
                pacing_target="single westbound excursion with no cross-city stacking",
                food_culture_intent="West Kyoto lunch and tea without rushing.",
                logistics_anchors=[
                    "Transfer Nakagyo-ku to Arashiyama in the morning.",
                    "Return to central Kyoto before dinner.",
                ],
            ),
        ],
    )

    result = quick_plan_generation._ensure_required_quick_plan_rows(
        draft,
        configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 16, tzinfo=timezone.utc).date(),
        ),
        module_outputs=TripModuleOutputs(),
        allowed_modules=["activities"],
        day_architecture=day_architecture,
    )

    day_three_activity = next(
        item
        for item in result.timeline_preview
        if item.day_label == "Day 3" and item.source_module == "activities"
    )
    assert day_three_activity.title == "Arashiyama bamboo, river, and west Kyoto lunch"
    assert day_three_activity.location_label == "Arashiyama / west Kyoto"
    assert "Transfer Nakagyo-ku to Arashiyama" in " ".join(day_three_activity.details)


def test_day_architecture_covers_configured_trip_days(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan_day_architecture,
        "create_quick_plan_chat_model",
        lambda **_: _FakeChatModel(captured, _day_architecture()),
    )

    result = quick_plan_day_architecture.build_quick_plan_day_architecture(
        dossier=_dossier(allowed_modules=["activities"]),
        configuration=_configuration(),
        strategy_brief=_strategy_brief(),
        provider_brief=_provider_brief(),
    )

    assert result is not None
    assert [day.day_index for day in result.days] == [1, 2, 3, 4]
    assert result.days[0].pacing_target == "light arrival"
    assert result.days[-1].pacing_target == "light departure"
    assert "calm" in result.days[1].must_avoid
    assert captured["schema"] is QuickPlanDayArchitecture


def test_day_architecture_rejects_missing_trip_day(monkeypatch) -> None:
    incomplete = _day_architecture().model_copy(
        update={"days": _day_architecture().days[:-1]}
    )
    monkeypatch.setattr(
        quick_plan_day_architecture,
        "create_quick_plan_chat_model",
        lambda **_: _FakeChatModel({}, incomplete),
    )

    result = quick_plan_day_architecture.build_quick_plan_day_architecture(
        dossier=_dossier(allowed_modules=["activities"]),
        configuration=_configuration(),
        strategy_brief=_strategy_brief(),
        provider_brief=_provider_brief(),
    )

    assert result is None


def test_quick_plan_repair_passes_review_feedback_to_generation_and_scheduler(
    monkeypatch,
) -> None:
    captured: dict = {}
    previous_attempt = QuickPlanGenerationAttempt(
        status="generated",
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Too small first candidate",
                    day_label="Day 1",
                )
            ]
        ),
    )
    repair_context = build_quick_plan_repair_context(
        previous_attempt=previous_attempt,
        failed_review={
            "status": "incomplete",
            "missing_outputs": ["day_coverage", "timing"],
            "review_notes": [
                "The candidate only covers Day 1.",
                "Visible rows are missing usable start/end times.",
            ],
        },
    )

    monkeypatch.setattr(
        quick_plan_generation,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(),
    )

    def _fake_generate(**kwargs):
        captured["draft_repair_context"] = kwargs["repair_context"]
        return QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Repaired day route",
                    day_label="Day 1",
                )
            ]
        )

    def _fake_schedule(**kwargs):
        captured["scheduler_repair_context"] = kwargs["repair_context"]
        return kwargs["draft"]

    monkeypatch.setattr(quick_plan_generation, "generate_quick_plan_draft", _fake_generate)
    monkeypatch.setattr(quick_plan_generation, "schedule_quick_plan_draft", _fake_schedule)

    attempt = run_quick_plan_repair(
        dossier=_dossier(allowed_modules=["activities"]),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Barcelona quick plan",
        conversation=TripConversationState(),
        repair_context=repair_context,
    )

    assert attempt.status == "generated"
    assert captured["draft_repair_context"]["missing_outputs"] == [
        "day_coverage",
        "timing",
    ]
    assert captured["scheduler_repair_context"]["review_notes"] == [
        "The candidate only covers Day 1.",
        "Visible rows are missing usable start/end times.",
    ]


def test_quality_repair_context_includes_scores_issues_and_previous_intelligence() -> None:
    previous_attempt = QuickPlanGenerationAttempt(
        status="generated",
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Generic private candidate",
                    day_label="Day 1",
                )
            ]
        ),
        strategy_brief=_strategy_brief(),
        provider_brief=_provider_brief(),
        day_architecture=_day_architecture(),
    )
    quality_review = QuickPlanQualityReviewResult(
        status="repairable",
        show_to_user=False,
        scorecard=QuickPlanQualityScorecard(
            geography=8,
            pacing=5,
            local_specificity=4,
            user_fit=6,
            logistics_realism=8,
            fact_safety=8,
        ),
        issues=[
            QuickPlanQualityIssue(
                dimension="local_specificity",
                issue="The plan is too generic for the destination.",
                repair_instruction="Use named food and culture anchors.",
            )
        ],
        review_notes=["Local quality is below the bar."],
        repair_instructions=["Rebuild the day plan around specific neighborhoods."],
    )

    repair_context = build_quick_plan_quality_repair_context(
        previous_attempt=previous_attempt,
        failed_quality_review=quality_review,
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )
    payload = repair_context.prompt_payload()

    assert payload["repair_goal"] == "quality"
    assert payload["quality_scores"]["local_specificity"] == 4
    assert payload["quality_issues"][0]["dimension"] == "local_specificity"
    assert "Use named food and culture anchors." in payload["repair_instructions"]
    assert payload["previous_strategy_brief"]["trip_thesis"] == "Calm food and culture rhythm."
    assert payload["previous_provider_brief"]["activity_clusters"] == ["old town food"]
    assert payload["previous_day_architecture"]["route_logic"] == (
        "Cluster each day around one compact area."
    )
    assert payload["previous_attempt"]["draft"]["timeline_preview"][0]["title"] == (
        "Generic private candidate"
    )


def test_accept_quick_plan_candidate_returns_atomic_merge_payload() -> None:
    attempt = QuickPlanGenerationAttempt(
        status="generated",
        module_outputs=TripModuleOutputs(
            activities=[
                ActivityDetail(
                    id="activity_food_walk",
                    title="El Born food walk",
                )
            ]
        ),
        timeline_module_outputs=TripModuleOutputs(),
        draft=QuickPlanDraft(
            board_summary="Accepted draft.",
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="El Born food walk",
                    day_label="Day 1",
                )
            ],
        ),
        assumptions=[{"type": "assistant_chosen_working_dates"}],
    )

    accepted = accept_quick_plan_candidate(
        attempt=attempt,
        review_result=QuickPlanReviewResult(status="complete", show_to_user=True),
        quality_review_result=_passing_quality_review(),
        repair_metadata={"repair_attempted": False, "final_visible": True},
    )

    assert accepted is not None
    assert accepted.module_outputs.activities[0].id == "activity_food_walk"
    assert accepted.timeline_preview[0].title == "El Born food walk"
    assert accepted.assumptions == [{"type": "assistant_chosen_working_dates"}]
    assert accepted.final_completeness_review["status"] == "complete"
    assert accepted.final_quality_review["status"] == "pass"
    assert accepted.quality_review_result["status"] == "pass"
    assert accepted.repair_metadata["final_visible"] is True
    assert accepted.review_metadata["final_visible"] is True


def test_accept_quick_plan_candidate_rejects_incomplete_review() -> None:
    accepted = accept_quick_plan_candidate(
        attempt=QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Private partial candidate",
                        day_label="Day 1",
                    )
                ]
            ),
        ),
        review_result=QuickPlanReviewResult(
            status="incomplete",
            show_to_user=False,
            missing_outputs=["day_coverage"],
        ),
        quality_review_result=_passing_quality_review(),
        repair_metadata={"repair_attempted": True, "final_visible": False},
    )

    assert accepted is None


def test_accept_quick_plan_candidate_rejects_blocking_quality_failure() -> None:
    accepted = accept_quick_plan_candidate(
        attempt=QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Generic museum and dinner",
                        day_label="Day 1",
                    )
                ]
            ),
        ),
        review_result=QuickPlanReviewResult(status="complete", show_to_user=True),
        quality_review_result=QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=7,
                pacing=7,
                local_specificity=4,
                user_fit=6,
                logistics_realism=2,
                fact_safety=7,
            ),
            issues=[
                QuickPlanQualityIssue(
                    dimension="logistics_realism",
                    severity="high",
                    issue="Flight timing makes the itinerary impossible.",
                )
            ],
        ),
        repair_metadata={"repair_attempted": False, "final_visible": False},
    )

    assert accepted is None


def test_accept_quick_plan_candidate_accepts_non_blocking_quality_failure() -> None:
    accepted = accept_quick_plan_candidate(
        attempt=QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Generic museum and dinner",
                        day_label="Day 1",
                    )
                ]
            ),
        ),
        review_result=QuickPlanReviewResult(status="complete", show_to_user=True),
        quality_review_result=QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=5,
                pacing=7,
                local_specificity=4,
                user_fit=6,
                logistics_realism=7,
                fact_safety=8,
            ),
            issues=[
                QuickPlanQualityIssue(
                    dimension="local_specificity",
                    severity="medium",
                    issue="The plan needs more destination-specific food anchors.",
                )
            ],
        ),
        repair_metadata={"repair_attempted": True, "final_visible": False},
    )

    assert accepted is not None
    assert accepted.quality_review_result["status"] == "fail"
    assert accepted.repair_metadata["quality_blocking"] is False


def test_accept_quick_plan_candidate_accepts_non_blocking_quality_issue_with_unset_hard_scores() -> None:
    accepted = accept_quick_plan_candidate(
        attempt=QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Arashiyama morning route",
                        day_label="Day 3",
                    )
                ]
            ),
        ),
        review_result=QuickPlanReviewResult(status="complete", show_to_user=True),
        quality_review_result=QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=4,
                pacing=7,
                local_specificity=5,
                user_fit=7,
                logistics_realism=0,
                fact_safety=0,
            ),
            issues=[
                QuickPlanQualityIssue(
                    dimension="geography",
                    severity="medium",
                    issue="The west Kyoto day needs clearer route flow.",
                )
            ],
        ),
        repair_metadata={"repair_attempted": True, "final_visible": False},
    )

    assert accepted is not None
    assert accepted.repair_metadata["quality_blocking"] is False


def _dossier(
    *,
    allowed_modules: list[str],
    assumptions: list[dict] | None = None,
) -> QuickPlanDossier:
    readiness = QuickPlanReadiness(
        ready=True,
        allowed_modules=allowed_modules,
        module_scope_source="user_explicit",
    )
    return QuickPlanDossier(
        readiness=readiness,
        trip_configuration={"confirmed_or_derived": _configuration().model_dump(mode="json")},
        module_scope={
            "modules": _configuration().selected_modules.model_dump(mode="json"),
            "allowed_modules": allowed_modules,
            "blocked_modules": {},
        },
        module_scope_source="user_explicit",
        assumptions=assumptions or [],
    )


def _passing_quality_review() -> QuickPlanQualityReviewResult:
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


def _strategy_brief() -> QuickPlanStrategyBrief:
    return QuickPlanStrategyBrief(
        trip_thesis="Calm food and culture rhythm.",
        user_intent=["food", "culture", "calm"],
        pacing_rules=["Keep arrival day light.", "Avoid rushed cross-city days."],
        module_priorities=[
            QuickPlanModulePriority(module="activities", priority="lead"),
            QuickPlanModulePriority(module="weather", priority="context"),
        ],
        assumptions=["Working dates are editable."],
        exclusions=["No nightlife-heavy pacing."],
        quality_bar=["Each day has a clear area focus."],
    )


def _provider_brief() -> QuickPlanProviderBrief:
    return QuickPlanProviderBrief(
        selected_outbound_flight=QuickPlanProviderFlightAnchor(id="outbound"),
        selected_return_flight=QuickPlanProviderFlightAnchor(id="return"),
        selected_stay_base=QuickPlanProviderStayAnchor(
            id="hotel_one",
            area="Gothic Quarter",
        ),
        activity_clusters=["old town food"],
        weather_constraints=["Use weather as context only."],
        missing_provider_facts=["activity opening hours"],
        fact_safety_caveats=["Do not claim opening hours are confirmed."],
        planner_context=["Keep logistics honest."],
    )


def _day_architecture() -> QuickPlanDayArchitecture:
    return QuickPlanDayArchitecture(
        route_logic="Cluster each day around one compact area.",
        coverage_notes=["All configured days are covered."],
        days=[
            QuickPlanDayPlan(
                day_index=1,
                day_label="Day 1",
                theme="Arrival and old-town orientation",
                geography_focus="Gothic Quarter",
                pacing_target="light arrival",
                food_culture_intent="Easy tapas and first walk.",
                logistics_anchors=["arrival buffer"],
                must_avoid=["late-night overload"],
                expected_row_types=["note", "meal", "activity"],
            ),
            QuickPlanDayPlan(
                day_index=2,
                day_label="Day 2",
                theme="Food markets and culture core",
                geography_focus="El Born",
                pacing_target="calm full day",
                food_culture_intent="Market lunch and museum rhythm.",
                logistics_anchors=["stay base"],
                must_avoid=["calm"],
                expected_row_types=["meal", "activity"],
            ),
            QuickPlanDayPlan(
                day_index=3,
                day_label="Day 3",
                theme="Neighborhood contrast",
                geography_focus="Montjuic",
                pacing_target="moderate",
                food_culture_intent="Culture block with slow dinner.",
                logistics_anchors=[],
                must_avoid=["backtracking"],
                expected_row_types=["activity", "meal"],
            ),
            QuickPlanDayPlan(
                day_index=4,
                day_label="Day 4",
                theme="Departure wind-down",
                geography_focus="Stay area",
                pacing_target="light departure",
                food_culture_intent="Short final breakfast.",
                logistics_anchors=["departure buffer"],
                must_avoid=["rushed final route"],
                expected_row_types=["meal", "note"],
            ),
        ],
    )


def _configuration() -> TripConfiguration:
    return TripConfiguration(
        to_location="Barcelona",
        start_date=datetime(2026, 10, 2, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 10, 5, tzinfo=timezone.utc).date(),
        selected_modules={
            "flights": False,
            "hotels": False,
            "activities": True,
            "weather": True,
        },
    )
