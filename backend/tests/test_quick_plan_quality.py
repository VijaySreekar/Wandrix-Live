from datetime import datetime, timezone

from app.graph.planner import quick_plan
from app.graph.planner.provider_enrichment import build_timeline
from app.graph.planner.quick_plan import generate_quick_plan_draft
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import FlightDetail, TripConfiguration, TripModuleOutputs


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
        "create_chat_model",
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


def test_build_timeline_drops_generic_arrival_filler_when_flight_anchor_exists() -> None:
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
        ],
        module_outputs=module_outputs,
        include_derived_when_preview_present=False,
    )

    titles = [item.title for item in timeline]

    assert "Outbound flight" in titles
    assert "Arrival in Lisbon" not in titles
    assert "Sunset walk through Alfama" in titles
