from datetime import datetime, timezone
from types import SimpleNamespace

from app.graph.planner import quick_plan_scheduler
from app.graph.planner.quick_plan_scheduler import schedule_quick_plan_draft
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import (
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


class _FailingStructuredModel:
    def invoke(self, messages):
        del messages
        raise TimeoutError("scheduler timeout")


class _FailingChatModel:
    def with_structured_output(self, schema, method):
        del schema, method
        return _FailingStructuredModel()


def test_scheduler_clocks_valencia_conference_rhythm(monkeypatch) -> None:
    captured: dict = {}
    scheduled = quick_plan_scheduler.ScheduledQuickPlanDraft(
        board_summary="A work-led Valencia plan with timed travel, conference rhythm, and easy evenings.",
        timeline_preview=[
            ProposedTimelineItem(
                type="meal",
                title="Breakfast near the hotel before the venue",
                day_label="Day 2",
                start_at=datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 25, 8, 45, tzinfo=timezone.utc),
                timing_source="planner_estimate",
                timing_note="Estimated to protect the conference start.",
            ),
            ProposedTimelineItem(
                type="transfer",
                title="Transfer to the conference venue",
                day_label="Day 2",
                start_at=datetime(2026, 9, 25, 8, 45, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 25, 9, 15, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            ),
            ProposedTimelineItem(
                type="event",
                title="Conference block",
                day_label="Day 2",
                start_at=datetime(2026, 9, 25, 9, 30, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 25, 17, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            ),
            ProposedTimelineItem(
                type="meal",
                title="Lunch near the venue",
                day_label="Day 2",
                start_at=datetime(2026, 9, 25, 12, 30, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            ),
            ProposedTimelineItem(
                type="meal",
                title="Low-key dinner in Ciutat Vella",
                day_label="Day 2",
                start_at=datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 25, 21, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            ),
            ProposedTimelineItem(
                type="transfer",
                title="Back to the hotel",
                day_label="Day 2",
                start_at=datetime(2026, 9, 25, 21, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 25, 21, 25, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            ),
        ],
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=18.0, max_retries=0: _FakeChatModel(
            captured,
            scheduled,
        ),
    )

    result = schedule_quick_plan_draft(
        title="Valencia conference trip",
        configuration=_valencia_configuration(),
        module_outputs=_valencia_module_outputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            board_summary="Draft",
            timeline_preview=[
                ProposedTimelineItem(type="note", title="Conference day", day_label="Day 2")
            ],
        ),
    )

    prompt = captured["messages"][1][1]
    titles = [item.title for item in result.timeline_preview]

    assert captured["method"] == "json_schema"
    assert "Every visible timeline item must have start_at and end_at." in prompt
    assert "Business or conference trips should protect work blocks" in prompt
    assert all(item.start_at and item.end_at for item in result.timeline_preview)
    assert all(item.timing_source for item in result.timeline_preview)
    assert "Lunch near the venue" in titles
    assert "Back to the hotel" in titles


def test_scheduler_shifts_arrival_day_items_after_landing(monkeypatch) -> None:
    early_item = quick_plan_scheduler.ScheduledQuickPlanDraft(
        timeline_preview=[
            ProposedTimelineItem(
                type="activity",
                title="Too-early museum plan",
                day_label="Day 1",
                start_at=datetime(2026, 9, 24, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 24, 10, 30, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            )
        ],
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=18.0, max_retries=0: _FakeChatModel(
            {},
            early_item,
        ),
    )

    result = schedule_quick_plan_draft(
        title="Valencia",
        configuration=_valencia_configuration(),
        module_outputs=_valencia_module_outputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(type="activity", title="Museum", day_label="Day 1")
            ],
        ),
    )

    assert result.timeline_preview[0].start_at >= datetime(
        2026,
        9,
        24,
        11,
        25,
        tzinfo=timezone.utc,
    )


def test_scheduler_pins_final_day_items_before_return_flight(monkeypatch) -> None:
    late_item = quick_plan_scheduler.ScheduledQuickPlanDraft(
        timeline_preview=[
            ProposedTimelineItem(
                type="activity",
                title="Late final wander",
                day_label="Day 5",
                start_at=datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 28, 20, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            )
        ],
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=18.0, max_retries=0: _FakeChatModel(
            {},
            late_item,
        ),
    )

    result = schedule_quick_plan_draft(
        title="Valencia",
        configuration=_valencia_configuration(),
        module_outputs=_valencia_module_outputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(type="activity", title="Final wander", day_label="Day 5")
            ],
        ),
    )

    final_item = next(
        item for item in result.timeline_preview if item.title == "Late final wander"
    )
    assert final_item.end_at <= datetime(
        2026,
        9,
        28,
        16,
        0,
        tzinfo=timezone.utc,
    )


def test_scheduler_repairs_single_missing_end_time(monkeypatch) -> None:
    missing_end = quick_plan_scheduler.ScheduledQuickPlanDraft(
        timeline_preview=[
            ProposedTimelineItem(
                type="meal",
                title="Breakfast before check-out",
                day_label="Day 5",
                start_at=datetime(2026, 9, 28, 8, 30, tzinfo=timezone.utc),
            )
        ],
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=18.0, max_retries=0: _FakeChatModel(
            {},
            missing_end,
        ),
    )

    result = schedule_quick_plan_draft(
        title="Valencia",
        configuration=_valencia_configuration(),
        module_outputs=_valencia_module_outputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(type="meal", title="Breakfast", day_label="Day 5")
            ],
        ),
    )

    item = result.timeline_preview[0]

    assert item.end_at is not None
    assert item.end_at > item.start_at
    assert item.timing_source == "planner_estimate"
    assert item.timing_note


def test_scheduler_clocks_items_when_model_omits_all_times(monkeypatch) -> None:
    unclocked = quick_plan_scheduler.ScheduledQuickPlanDraft(
        timeline_preview=[
            ProposedTimelineItem(
                type="activity",
                title="Arrival settle-in and Pontochō evening walk",
                day_label="Day 1",
                timing_source="planner_estimate",
            ),
            ProposedTimelineItem(
                type="meal",
                title="Lunch near the covered arcade",
                day_label="Day 2",
                timing_source="planner_estimate",
            ),
        ],
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=18.0, max_retries=0: _FakeChatModel(
            {},
            unclocked,
        ),
    )

    result = schedule_quick_plan_draft(
        title="Kyoto summer food trip",
        configuration=TripConfiguration(
            from_location="Coventry",
            to_location="Kyoto",
            start_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 18, tzinfo=timezone.utc).date(),
            travel_window="summer",
            trip_length="5 days",
        ),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(type="activity", title="Arrival", day_label="Day 1")
            ],
        ),
    )

    assert len(result.timeline_preview) == 5
    assert all(item.start_at and item.end_at for item in result.timeline_preview)
    assert all(item.end_at > item.start_at for item in result.timeline_preview)
    assert result.timeline_preview[0].start_at.date().isoformat() == "2026-07-14"
    assert result.timeline_preview[1].start_at.date().isoformat() == "2026-07-15"
    assert {item.day_label for item in result.timeline_preview} == {
        "Day 1",
        "Day 2",
        "Day 3",
        "Day 4",
        "Day 5",
    }


def test_scheduler_caps_oversized_repaired_timeline_without_crashing(monkeypatch) -> None:
    oversized = SimpleNamespace(
        board_summary="Oversized but usable plan.",
        timeline_preview=[
            ProposedTimelineItem(
                type="activity",
                title=f"Timed Kyoto block {index}",
                day_label=f"Day {((index - 1) % 5) + 1}",
                start_at=datetime(
                    2026,
                    7,
                    14 + ((index - 1) % 5),
                    8 + ((index - 1) % 8),
                    0,
                    tzinfo=timezone.utc,
                ),
                end_at=datetime(
                    2026,
                    7,
                    14 + ((index - 1) % 5),
                    9 + ((index - 1) % 8),
                    0,
                    tzinfo=timezone.utc,
                ),
                timing_source="planner_estimate",
            )
            for index in range(1, 19)
        ],
    )
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=18.0, max_retries=0: _FakeChatModel(
            {},
            oversized,
        ),
    )

    result = schedule_quick_plan_draft(
        title="Kyoto food trip",
        configuration=TripConfiguration(
            from_location="London",
            to_location="Kyoto",
            start_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 18, tzinfo=timezone.utc).date(),
            travel_window="summer",
            trip_length="5 days",
        ),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(type="activity", title="Kyoto draft", day_label="Day 1")
            ],
        ),
    )

    assert len(result.timeline_preview) == 16
    assert {item.day_label for item in result.timeline_preview} == {
        "Day 1",
        "Day 2",
        "Day 3",
        "Day 4",
        "Day 5",
    }


def test_scheduler_repairs_original_draft_when_model_times_out(monkeypatch) -> None:
    monkeypatch.setattr(
        quick_plan_scheduler,
        "create_quick_plan_chat_model",
        lambda temperature=0.1, timeout=24.0, max_retries=0: _FailingChatModel(),
    )

    result = schedule_quick_plan_draft(
        title="Kyoto summer food trip",
        configuration=TripConfiguration(
            from_location="Coventry",
            to_location="Kyoto",
            start_date=datetime(2026, 7, 10, tzinfo=timezone.utc).date(),
            end_date=datetime(2026, 7, 14, tzinfo=timezone.utc).date(),
            travel_window="summer",
            trip_length="5 days",
        ),
        module_outputs=TripModuleOutputs(),
        conversation=TripConversationState(),
        draft=QuickPlanDraft(
            board_summary="A compact Kyoto draft.",
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title="Nishiki Market and Teramachi arcade food-first morning",
                    day_label="Day 2",
                ),
                ProposedTimelineItem(
                    type="meal",
                    title="Lunch around Nishiki Market",
                    day_label="Day 2",
                ),
            ],
        ),
    )

    assert len(result.timeline_preview) == 6
    assert all(item.start_at and item.end_at for item in result.timeline_preview)
    assert all(item.timing_source == "planner_estimate" for item in result.timeline_preview)
    original_activity = next(
        item
        for item in result.timeline_preview
        if item.title == "Nishiki Market and Teramachi arcade food-first morning"
    )
    assert original_activity.start_at.date().isoformat() == "2026-07-11"
    assert {item.day_label for item in result.timeline_preview} == {
        "Day 1",
        "Day 2",
        "Day 3",
        "Day 4",
        "Day 5",
    }


def _valencia_configuration() -> TripConfiguration:
    return TripConfiguration(
        from_location="Coventry",
        to_location="Valencia, Spain",
        start_date=datetime(2026, 9, 24, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 9, 28, tzinfo=timezone.utc).date(),
        trip_length="4 nights",
        weather_preference="warm",
        budget_currency="GBP",
        budget_posture="mid_range",
        custom_style="business conference",
    )


def _valencia_module_outputs() -> TripModuleOutputs:
    return TripModuleOutputs(
        flights=[
            FlightDetail(
                id="outbound",
                direction="outbound",
                carrier="BA",
                departure_airport="LHR",
                arrival_airport="VLC",
                departure_time=datetime(2026, 9, 24, 8, 30, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 9, 24, 11, 25, tzinfo=timezone.utc),
            ),
            FlightDetail(
                id="return",
                direction="return",
                carrier="BA",
                departure_airport="VLC",
                arrival_airport="LHR",
                departure_time=datetime(2026, 9, 28, 16, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 9, 28, 18, 30, tzinfo=timezone.utc),
            ),
        ],
        hotels=[
            HotelStayDetail(
                id="hotel",
                hotel_name="Valencia Centre Hotel",
                area="Ciutat Vella",
            )
        ],
    )
