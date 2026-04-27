from app.core import config
from app.graph.planner import quick_plan
from app.graph.planner import quick_plan_day_architecture
from app.graph.planner import quick_plan_logistics_quality_review
from app.graph.planner import quick_plan_provider_brief
from app.graph.planner import quick_plan_review
from app.graph.planner import quick_plan_scheduler
from app.graph.planner import quick_plan_strategy
from app.graph.planner import understanding
from app.graph.planner.quick_plan_day_architecture import (
    QuickPlanDayArchitecture,
    QuickPlanDayPlan,
)
from app.graph.planner.quick_plan_dossier import QuickPlanDossier, QuickPlanReadiness
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_provider_brief import QuickPlanProviderBrief
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
)
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.quick_plan_strategy import QuickPlanStrategyBrief
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.graph.planner.turn_models import TripTurnUpdate
from app.integrations.llm import client as llm_client
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


class _CapturedChatOpenAI:
    calls: list[dict] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.__class__.calls.append(kwargs)


class _StructuredModel:
    def invoke(self, messages):
        del messages
        return TripTurnUpdate(title="Default model update")


class _DefaultChatModel:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _StructuredModel()


class _QuickPlanStructuredModel:
    def __init__(self, response) -> None:
        self._response = response

    def invoke(self, messages):
        del messages
        return self._response


class _QuickPlanChatModel:
    def __init__(self, captured: dict, response) -> None:
        self._captured = captured
        self._response = response

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _QuickPlanStructuredModel(self._response)


def test_settings_load_quick_plan_model_defaults(monkeypatch) -> None:
    monkeypatch.delenv("QUICK_PLAN_MODEL", raising=False)
    monkeypatch.delenv("QUICK_PLAN_REASONING_EFFORT", raising=False)
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.quick_plan_model == "gpt-5.5"
    assert settings.quick_plan_reasoning_effort == "medium"


def test_quick_plan_chat_model_uses_quick_plan_settings(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("QUICK_PLAN_MODEL", "gpt-5.5")
    monkeypatch.setenv("QUICK_PLAN_REASONING_EFFORT", "medium")
    config.get_settings.cache_clear()
    _CapturedChatOpenAI.calls = []
    monkeypatch.setattr(llm_client, "ChatOpenAI", _CapturedChatOpenAI)

    llm_client.create_quick_plan_chat_model(
        temperature=0.1,
        timeout=12.0,
        max_retries=0,
    )

    call = _CapturedChatOpenAI.calls[0]
    assert call["model"] == "gpt-5.5"
    assert call["model"] != "gpt-5.4-mini"
    assert call["reasoning_effort"] == "medium"
    assert call["temperature"] == 0.1
    assert call["timeout"] == 12.0
    assert call["max_retries"] == 0


def test_quick_plan_chat_model_allows_reasoning_override(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("QUICK_PLAN_MODEL", "gpt-5.5")
    monkeypatch.setenv("QUICK_PLAN_REASONING_EFFORT", "medium")
    config.get_settings.cache_clear()
    _CapturedChatOpenAI.calls = []
    monkeypatch.setattr(llm_client, "ChatOpenAI", _CapturedChatOpenAI)

    llm_client.create_quick_plan_chat_model(reasoning_effort="medium")

    call = _CapturedChatOpenAI.calls[0]
    assert call["model"] == "gpt-5.5"
    assert call["reasoning_effort"] == "medium"


def test_default_chat_model_still_uses_openai_model(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("QUICK_PLAN_MODEL", "gpt-5.5")
    monkeypatch.setenv("QUICK_PLAN_REASONING_EFFORT", "medium")
    config.get_settings.cache_clear()
    _CapturedChatOpenAI.calls = []
    monkeypatch.setattr(llm_client, "ChatOpenAI", _CapturedChatOpenAI)

    llm_client.create_chat_model(temperature=0.1)

    call = _CapturedChatOpenAI.calls[0]
    assert call["model"] == "gpt-5.4-mini"
    assert "reasoning_effort" not in call


def test_planner_understanding_uses_default_chat_factory(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _DefaultChatModel(captured),
    )

    update = understanding.generate_llm_trip_update(
        user_input="Plan a Lisbon weekend.",
        title="Trip planner",
        configuration=TripConfiguration(),
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    assert captured["schema"] is TripTurnUpdate
    assert captured["method"] == "json_schema"
    assert update.title == "Default model update"


def test_quick_plan_draft_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    call: dict = {}

    def _fake_quick_plan_model(**kwargs):
        call.update(kwargs)
        return _QuickPlanChatModel(
            captured,
            QuickPlanDraft(
                timeline_preview=[
                    ProposedTimelineItem(
                        type="activity",
                        title="Food walk",
                        day_label="Day 1",
                    )
                ]
            ),
        )

    monkeypatch.setattr(
        quick_plan,
        "create_quick_plan_chat_model",
        _fake_quick_plan_model,
    )

    draft = quick_plan.generate_quick_plan_draft(
        title="Lisbon",
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
    )

    assert captured["schema"] is QuickPlanDraft
    assert call["timeout"] == QUICK_PLAN_LLM_TIMEOUT_SECONDS
    assert draft.timeline_preview[0].title == "Food walk"


def test_quick_plan_strategy_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan_strategy,
        "create_quick_plan_chat_model",
        lambda **_: _QuickPlanChatModel(
            captured,
            QuickPlanStrategyBrief(trip_thesis="Calm food strategy."),
        ),
    )

    result = quick_plan_strategy.build_quick_plan_strategy_brief(
        dossier=_dossier(["activities"]),
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
    )

    assert captured["schema"] is QuickPlanStrategyBrief
    assert result.trip_thesis == "Calm food strategy."


def test_quick_plan_provider_brief_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan_provider_brief,
        "create_quick_plan_chat_model",
        lambda **_: _QuickPlanChatModel(
            captured,
            QuickPlanProviderBrief(activity_clusters=["Gion food"]),
        ),
    )

    result = quick_plan_provider_brief.build_quick_plan_provider_brief(
        dossier=_dossier(["activities"]),
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(),
        strategy_brief=QuickPlanStrategyBrief(trip_thesis="Calm food strategy."),
    )

    assert captured["schema"] is QuickPlanProviderBrief
    assert result.activity_clusters == ["Gion food"]


def test_quick_plan_day_architecture_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan_day_architecture,
        "create_quick_plan_chat_model",
        lambda **_: _QuickPlanChatModel(
            captured,
            QuickPlanDayArchitecture(
                route_logic="Compact route.",
                days=[
                    QuickPlanDayPlan(
                        day_index=1,
                        day_label="Day 1",
                        theme="Arrival",
                        geography_focus="Old town",
                        pacing_target="light",
                        food_culture_intent="First meal.",
                    ),
                    QuickPlanDayPlan(
                        day_index=2,
                        day_label="Day 2",
                        theme="Culture",
                        geography_focus="Museum district",
                        pacing_target="calm",
                        food_culture_intent="Market lunch.",
                    ),
                    QuickPlanDayPlan(
                        day_index=3,
                        day_label="Day 3",
                        theme="Departure",
                        geography_focus="Stay area",
                        pacing_target="light",
                        food_culture_intent="Breakfast.",
                    ),
                ],
            ),
        ),
    )

    result = quick_plan_day_architecture.build_quick_plan_day_architecture(
        dossier=_dossier(["activities"]),
        configuration=_configuration(),
        strategy_brief=QuickPlanStrategyBrief(trip_thesis="Calm food strategy."),
        provider_brief=QuickPlanProviderBrief(activity_clusters=["Gion food"]),
    )

    assert captured["schema"] is QuickPlanDayArchitecture
    assert len(result.days) == 3


def test_quick_plan_scheduler_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    call: dict = {}
    scheduled = quick_plan_scheduler.ScheduledQuickPlanDraft(
        timeline_preview=[
            ProposedTimelineItem(
                type="activity",
                title="Timed food walk",
                day_label="Day 1",
                start_at="2026-09-18T10:00:00Z",
                end_at="2026-09-18T12:00:00Z",
                timing_source="planner_estimate",
            )
        ]
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda **kwargs: (
            call.update(kwargs) or _QuickPlanChatModel(captured, scheduled)
        ),
    )

    draft = quick_plan_scheduler.schedule_quick_plan_draft(
        title="Lisbon",
        configuration=_configuration(),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Food walk",
                    day_label="Day 1",
                )
            ]
        ),
    )

    assert captured["schema"] is quick_plan_scheduler.ScheduledQuickPlanDraft
    assert call["timeout"] == QUICK_PLAN_LLM_TIMEOUT_SECONDS
    assert draft.timeline_preview[0].title == "Timed food walk"


def test_quick_plan_review_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    call: dict = {}
    monkeypatch.setattr(
        quick_plan_review,
        "create_quick_plan_chat_model",
        lambda **kwargs: call.update(kwargs) or _QuickPlanChatModel(
            captured,
            QuickPlanReviewResult(status="complete", show_to_user=True),
        ),
    )

    result = quick_plan_review.review_quick_plan_generation(
        dossier=_dossier(["activities"]),
        attempt=QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(timeline_preview=_complete_activity_items()),
        ),
        configuration=_configuration(),
    )

    assert captured["schema"] is QuickPlanReviewResult
    assert call["timeout"] == QUICK_PLAN_LLM_TIMEOUT_SECONDS
    assert result.status == "complete"


def test_quick_plan_quality_specialist_uses_quick_plan_factory(monkeypatch) -> None:
    captured: dict = {}
    call: dict = {}
    monkeypatch.setattr(
        quick_plan_logistics_quality_review,
        "create_quick_plan_chat_model",
        lambda **kwargs: call.update(kwargs)
        or _QuickPlanChatModel(
            captured,
            QuickPlanQualityReviewResult(
                status="pass",
                show_to_user=True,
                scorecard=QuickPlanQualityScorecard(
                    logistics_realism=8,
                    fact_safety=8,
                ),
            ),
        ),
    )

    result = quick_plan_logistics_quality_review.review_quick_plan_logistics_quality(
        dossier=_dossier(["activities"]),
        attempt=QuickPlanGenerationAttempt(
            status="generated",
            draft=QuickPlanDraft(timeline_preview=_complete_activity_items()),
        ),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert captured["schema"] is QuickPlanQualityReviewResult
    assert call["timeout"] == QUICK_PLAN_LLM_TIMEOUT_SECONDS
    assert result is not None
    assert result.status == "pass"


def _configuration() -> TripConfiguration:
    return TripConfiguration(
        to_location="Lisbon",
        start_date="2026-09-18",
        end_date="2026-09-20",
        travelers={"adults": 2},
    )


def _dossier(allowed_modules: list[str]) -> QuickPlanDossier:
    configuration = _configuration()
    return QuickPlanDossier(
        readiness=QuickPlanReadiness(
            ready=True,
            allowed_modules=allowed_modules,
            module_scope_source="user_explicit",
        ),
        trip_configuration={
            "confirmed_or_derived": configuration.model_dump(mode="json"),
        },
        module_scope={
            "modules": configuration.selected_modules.model_dump(mode="json"),
            "allowed_modules": allowed_modules,
            "blocked_modules": {},
        },
        module_scope_source="user_explicit",
    )


def _complete_activity_items() -> list[ProposedTimelineItem]:
    return [
        ProposedTimelineItem(
            type="activity",
            title="Alfama food walk",
            day_label="Day 1",
            start_at="2026-09-18T10:00:00Z",
            end_at="2026-09-18T12:00:00Z",
            timing_source="planner_estimate",
        ),
        ProposedTimelineItem(
            type="activity",
            title="Baixa market route",
            day_label="Day 2",
            start_at="2026-09-19T10:00:00Z",
            end_at="2026-09-19T12:00:00Z",
            timing_source="planner_estimate",
        ),
        ProposedTimelineItem(
            type="activity",
            title="Final riverside walk",
            day_label="Day 3",
            start_at="2026-09-20T10:00:00Z",
            end_at="2026-09-20T12:00:00Z",
            timing_source="planner_estimate",
        ),
    ]
