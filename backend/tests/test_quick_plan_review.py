from datetime import datetime, timezone

from app.graph.planner import quick_plan_review
from app.graph.planner.quick_plan_dossier import QuickPlanDossier, QuickPlanReadiness
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_review import (
    QuickPlanReviewResult,
    review_quick_plan_generation,
)
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_planning import (
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


class _FakeStructuredReviewModel:
    def __init__(self, captured: dict, response: QuickPlanReviewResult) -> None:
        self._captured = captured
        self._response = response

    def invoke(self, messages):
        self._captured["messages"] = messages
        return self._response


class _FakeReviewModel:
    def __init__(self, captured: dict, response: QuickPlanReviewResult) -> None:
        self._captured = captured
        self._response = response

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _FakeStructuredReviewModel(self._captured, self._response)


def test_quick_plan_review_complete_candidate_passes(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        quick_plan_review,
        "create_quick_plan_chat_model",
        lambda temperature=0.0, timeout=14.0, max_retries=0: _FakeReviewModel(
            captured,
            QuickPlanReviewResult(
                status="complete",
                show_to_user=True,
                review_notes=["Candidate covers required scope."],
            ),
        ),
    )

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(_complete_items()),
        configuration=_configuration(),
    )

    assert captured["method"] == "json_schema"
    assert result.status == "complete"
    assert result.show_to_user is True
    assert result.missing_outputs == []


def test_quick_plan_review_fails_empty_attempt_without_llm(monkeypatch) -> None:
    monkeypatch.setattr(
        quick_plan_review,
        "create_quick_plan_chat_model",
        lambda **_: (_ for _ in ()).throw(AssertionError("LLM should not run")),
    )

    result = review_quick_plan_generation(
        dossier=_dossier(["activities"]),
        attempt=QuickPlanGenerationAttempt(status="empty"),
        configuration=_configuration(),
    )

    assert result.status == "failed"
    assert result.show_to_user is False
    assert "day_coverage" in result.missing_outputs


def test_quick_plan_review_missing_flights_fails_when_flights_in_scope() -> None:
    items = [
        item for item in _complete_items() if item.type != "flight"
    ]

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "flights" in result.missing_outputs
    assert result.show_to_user is False


def test_quick_plan_review_missing_return_flight_fails_when_flights_in_scope() -> None:
    items = [
        item
        for item in _complete_items()
        if not (item.type == "flight" and "Return" in item.title)
    ]

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "flights" in result.missing_outputs
    assert result.show_to_user is False


def test_quick_plan_review_missing_stay_fails_when_hotels_in_scope() -> None:
    items = [
        item for item in _complete_items() if item.type != "hotel"
    ]

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "stay" in result.missing_outputs


def test_quick_plan_review_missing_activities_fails_when_activities_in_scope() -> None:
    items = [
        item for item in _complete_items() if item.type != "activity"
    ]

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "activities" in result.missing_outputs


def test_quick_plan_review_missing_day_coverage_fails() -> None:
    items = [
        item for item in _complete_items() if item.day_label != "Day 2"
    ]

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "day_coverage" in result.missing_outputs


def test_quick_plan_review_note_only_interior_day_fails_activity_day_coverage() -> None:
    items = [
        item for item in _complete_items() if item.day_label != "Day 2"
    ]
    items.append(
        ProposedTimelineItem(
            type="note",
            title="Generic Barcelona pacing anchor",
            day_label="Day 2",
            start_at=datetime(2026, 10, 3, 11, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, 3, 14, tzinfo=timezone.utc),
            timing_source="planner_estimate",
        )
    )

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "day_coverage" in result.missing_outputs


def test_quick_plan_review_untimed_visible_rows_fail() -> None:
    items = [
        *_complete_items(),
        ProposedTimelineItem(
            type="activity",
            title="Untimed extra wander",
            day_label="Day 2",
        ),
    ]

    result = review_quick_plan_generation(
        dossier=_dossier(["flights", "hotels", "activities"]),
        attempt=_attempt(items),
        configuration=_configuration(),
    )

    assert result.status == "incomplete"
    assert "timing" in result.missing_outputs


def test_quick_plan_review_allows_activities_only_without_flights_or_hotels(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        quick_plan_review,
        "create_quick_plan_chat_model",
        lambda temperature=0.0, timeout=14.0, max_retries=0: _FakeReviewModel(
            {},
            QuickPlanReviewResult(status="complete", show_to_user=True),
        ),
    )

    result = review_quick_plan_generation(
        dossier=_dossier(["activities"]),
        attempt=_attempt(_activities_only_items()),
        configuration=_configuration(),
    )

    assert result.status == "complete"
    assert result.show_to_user is True
    assert result.missing_outputs == []


def _configuration() -> TripConfiguration:
    return TripConfiguration(
        from_location="London",
        to_location="Barcelona",
        start_date=datetime(2026, 10, 2, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 10, 4, tzinfo=timezone.utc).date(),
        travelers={"adults": 2},
    )


def _dossier(allowed_modules: list[str]) -> QuickPlanDossier:
    readiness = QuickPlanReadiness(
        ready=True,
        allowed_modules=allowed_modules,
        module_scope_source="user_explicit",
    )
    configuration = _configuration()
    return QuickPlanDossier(
        readiness=readiness,
        trip_configuration={
            "confirmed_or_derived": configuration.model_dump(mode="json"),
        },
        module_scope={
            "modules": configuration.selected_modules.model_dump(mode="json"),
            "allowed_modules": allowed_modules,
            "blocked_modules": {},
        },
        module_scope_source="user_explicit",
        assumptions=[
            {
                "type": "assistant_chosen_working_dates",
                "start_date": "2026-10-02",
                "end_date": "2026-10-04",
            }
        ],
    )


def _attempt(items: list[ProposedTimelineItem]) -> QuickPlanGenerationAttempt:
    return QuickPlanGenerationAttempt(
        status="generated",
        module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="flight_out",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="BCN",
                )
            ],
            hotels=[HotelStayDetail(id="hotel_one", hotel_name="Barcelona stay")],
        ),
        timeline_module_outputs=TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="flight_out",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="BCN",
                )
            ],
            hotels=[HotelStayDetail(id="hotel_one", hotel_name="Barcelona stay")],
        ),
        draft=QuickPlanDraft(
            board_summary="A complete Barcelona quick plan.",
            timeline_preview=items,
        ),
    )


def _complete_items() -> list[ProposedTimelineItem]:
    return [
        ProposedTimelineItem(
            type="flight",
            title="Outbound flight to Barcelona",
            day_label="Day 1",
            start_at=datetime(2026, 10, 2, 8, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, 2, 11, tzinfo=timezone.utc),
            timing_source="provider_exact",
            source_module="flights",
        ),
        ProposedTimelineItem(
            type="hotel",
            title="Check in at Eixample stay",
            day_label="Day 1",
            start_at=datetime(2026, 10, 2, 15, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, 2, 16, tzinfo=timezone.utc),
            timing_source="planner_estimate",
            source_module="hotels",
        ),
        ProposedTimelineItem(
            type="activity",
            title="Gothic Quarter and El Born evening",
            day_label="Day 1",
            start_at=datetime(2026, 10, 2, 18, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, 2, 20, tzinfo=timezone.utc),
            timing_source="planner_estimate",
            source_module="activities",
        ),
        ProposedTimelineItem(
            type="activity",
            title="Montjuic and Poble-sec food route",
            day_label="Day 2",
            start_at=datetime(2026, 10, 3, 10, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, 3, 16, tzinfo=timezone.utc),
            timing_source="planner_estimate",
            source_module="activities",
        ),
        ProposedTimelineItem(
            type="flight",
            title="Return flight from Barcelona",
            day_label="Day 3",
            start_at=datetime(2026, 10, 4, 17, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, 4, 20, tzinfo=timezone.utc),
            timing_source="provider_exact",
            source_module="flights",
        ),
    ]


def _activities_only_items() -> list[ProposedTimelineItem]:
    return [
        ProposedTimelineItem(
            type="activity",
            title=f"Barcelona activity route day {day}",
            day_label=f"Day {day}",
            start_at=datetime(2026, 10, day + 1, 10, tzinfo=timezone.utc),
            end_at=datetime(2026, 10, day + 1, 14, tzinfo=timezone.utc),
            timing_source="planner_estimate",
            source_module="activities",
        )
        for day in [1, 2, 3]
    ]
