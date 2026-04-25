from app.graph.planner import brief_intelligence
from app.graph.planner.brief_intelligence import review_trip_brief_intelligence
from app.graph.planner.turn_models import (
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration


class _FakeStructuredModel:
    def __init__(self, update: TripTurnUpdate, captured: dict) -> None:
        self._update = update
        self._captured = captured

    def invoke(self, messages):
        self._captured["messages"] = messages
        return self._update


class _FakeChatModel:
    def __init__(self, update: TripTurnUpdate, captured: dict) -> None:
        self._update = update
        self._captured = captured

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _FakeStructuredModel(self._update, self._captured)


def test_brief_intelligence_prefills_currency_without_amount(monkeypatch) -> None:
    captured: dict = {}
    reviewed_update = TripTurnUpdate(
        to_location="Lisbon",
        trip_length="long weekend",
        budget_currency="GBP",
        activity_styles=["relaxed"],
        confirmed_fields=["budget_currency"],
        inferred_fields=["trip_length", "activity_styles"],
        field_confidences=[
            TripFieldConfidenceUpdate(field="budget_currency", confidence="high"),
            TripFieldConfidenceUpdate(field="trip_length", confidence="medium"),
            TripFieldConfidenceUpdate(field="activity_styles", confidence="medium"),
        ],
        field_sources=[
            TripFieldSourceUpdate(field="budget_currency", source="user_explicit"),
            TripFieldSourceUpdate(field="trip_length", source="user_inferred"),
            TripFieldSourceUpdate(field="activity_styles", source="user_inferred"),
        ],
    )
    monkeypatch.setattr(
        brief_intelligence,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(reviewed_update, captured),
    )

    result = review_trip_brief_intelligence(
        user_input="around june 15th please.",
        title="Lisbon trip",
        configuration=TripConfiguration(),
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[
            {"role": "user", "content": "Compare Lisbon and Porto, relaxed long weekend, budget in GBP."},
            {"role": "assistant", "content": "Porto is easier, Lisbon has more variety."},
            {"role": "user", "content": "I want to go ahead with Lisbon please."},
            {"role": "assistant", "content": "What month or window?"},
        ],
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            travel_window="around June 15th",
            confirmed_fields=["to_location"],
            inferred_fields=["travel_window"],
        ),
    )

    assert captured["method"] == "json_schema"
    assert result.budget_currency == "GBP"
    assert result.budget_amount is None
    assert result.budget_gbp is None
    assert result.trip_length == "long weekend"
    assert result.activity_styles == ["relaxed"]
    assert "budget_currency" in result.confirmed_fields
    assert "activity_styles" in result.inferred_fields


def test_brief_intelligence_prompt_bans_deterministic_extraction(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        brief_intelligence,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(TripTurnUpdate(), captured),
    )

    review_trip_brief_intelligence(
        user_input="around june 15th please.",
        title="Lisbon trip",
        configuration=TripConfiguration(to_location="Lisbon"),
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[
            {"role": "user", "content": "Compare Lisbon and Porto, relaxed long weekend, budget in GBP."},
            {"role": "assistant", "content": "Lisbon works."},
        ],
        llm_update=TripTurnUpdate(travel_window="around June 15th"),
    )

    prompt = captured["messages"][1][1]
    assert "Do not use regex, keyword matching, or deterministic extraction." in prompt
    assert "set budget_currency to that 3-letter code without inventing budget_amount" in prompt
