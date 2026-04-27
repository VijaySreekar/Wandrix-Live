import json
from datetime import date, datetime, timedelta
from pathlib import Path

from app.graph.planner.quick_plan_evaluator import (
    QuickPlanEvaluationCase,
    build_quick_plan_evaluation_report,
    evaluate_quick_plan_case,
)
from app.schemas.trip_conversation import (
    QuickPlanFinalizationState,
    TripConversationState,
)
from app.schemas.trip_draft import TripDraft
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    PlanningModuleKey,
    TimelineItem,
    TripBudgetEstimate,
    TripBudgetEstimateCategory,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "quick_plan_evaluation_cases.json"
)


def test_quick_plan_evaluation_fixture_validates_required_cases() -> None:
    raw_cases = json.loads(FIXTURE_PATH.read_text())
    cases = [QuickPlanEvaluationCase.model_validate(item) for item in raw_cases]

    assert len(cases) == 6
    assert {case.id for case in cases} == {
        "kyoto_calm_food_culture_full_trip",
        "activities_only_city_plan",
        "beach_rest_weather_scope",
        "long_haul_arrival_recovery",
        "family_hotels_activities",
        "rough_dates_assistant_working_dates",
    }
    assert all(case.category for case in cases)
    assert all(case.expected_modules for case in cases)


def test_evaluator_passes_complete_accepted_full_trip() -> None:
    case = _case(expected_modules=["flights", "hotels", "activities", "weather"])
    draft = _accepted_draft(
        expected_modules=case.expected_modules,
        expected_days=case.expected_days or 5,
    )

    result = evaluate_quick_plan_case(
        case,
        draft,
        observability={"provider_activation": {"quick_plan_repair": {"repair_attempt_count": 1}}},
    )

    assert result.passed is True
    assert result.accepted is True
    assert result.repair_count == 1
    assert result.findings == []


def test_evaluator_fails_missing_flights_when_expected() -> None:
    case = _case(expected_modules=["flights", "hotels", "activities", "weather"])
    draft = _accepted_draft(
        expected_modules=case.expected_modules,
        expected_days=case.expected_days or 5,
        include_flights=False,
    )

    result = evaluate_quick_plan_case(case, draft)

    assert result.passed is False
    assert _finding_codes(result) == {"missing_flight_anchors"}


def test_evaluator_fails_missing_stay_when_expected() -> None:
    case = _case(expected_modules=["hotels", "activities", "weather"])
    draft = _accepted_draft(
        expected_modules=case.expected_modules,
        expected_days=case.expected_days or 5,
        include_hotels=False,
    )

    result = evaluate_quick_plan_case(case, draft)

    assert result.passed is False
    assert "missing_stay_anchor" in _finding_codes(result)


def test_evaluator_fails_missing_day_coverage() -> None:
    case = _case(expected_modules=["activities"], excluded_modules=["flights", "hotels"])
    draft = _accepted_draft(
        expected_modules=case.expected_modules,
        excluded_modules=case.excluded_modules,
        expected_days=case.expected_days or 5,
        covered_days=3,
    )

    result = evaluate_quick_plan_case(case, draft)

    assert result.passed is False
    assert "missing_day_coverage" in _finding_codes(result)


def test_evaluator_fails_visible_untimed_rows() -> None:
    case = _case(expected_modules=["activities"], excluded_modules=["flights", "hotels"])
    draft = _accepted_draft(
        expected_modules=case.expected_modules,
        excluded_modules=case.excluded_modules,
        expected_days=case.expected_days or 5,
        timed=False,
    )

    result = evaluate_quick_plan_case(case, draft)

    assert result.passed is False
    assert "visible_untimed_rows" in _finding_codes(result)


def test_evaluator_passes_activities_only_without_logistics() -> None:
    case = _case(
        expected_modules=["activities"],
        excluded_modules=["flights", "hotels", "weather"],
        require_budget_when_accepted=False,
    )
    draft = _accepted_draft(
        expected_modules=case.expected_modules,
        excluded_modules=case.excluded_modules,
        expected_days=case.expected_days or 5,
    )

    result = evaluate_quick_plan_case(case, draft)

    assert result.passed is True
    assert result.accepted_modules == ["activities"]


def test_evaluation_report_includes_actionable_failure_reasons() -> None:
    case = _case(expected_modules=["flights", "activities"])
    result = evaluate_quick_plan_case(
        case,
        _accepted_draft(
            expected_modules=case.expected_modules,
            expected_days=case.expected_days or 5,
            include_flights=False,
        ),
    )
    report = build_quick_plan_evaluation_report([result])

    assert report["total"] == 1
    assert report["failed"] == 1
    assert report["cases"][0]["findings"][0]["code"] == "missing_flight_anchors"
    json.dumps(report)


def _case(
    *,
    expected_modules: list[PlanningModuleKey],
    excluded_modules: list[PlanningModuleKey] | None = None,
    require_budget_when_accepted: bool = True,
) -> QuickPlanEvaluationCase:
    return QuickPlanEvaluationCase(
        id="test_case",
        category="test",
        prompt="Plan a test trip.",
        expected_modules=expected_modules,
        excluded_modules=excluded_modules or [],
        expected_days=5,
        require_acceptance=True,
        require_budget_when_accepted=require_budget_when_accepted,
    )


def _accepted_draft(
    *,
    expected_modules: list[PlanningModuleKey],
    expected_days: int,
    excluded_modules: list[PlanningModuleKey] | None = None,
    include_flights: bool = True,
    include_hotels: bool = True,
    timed: bool = True,
    covered_days: int | None = None,
) -> TripDraft:
    excluded_modules = excluded_modules or []
    base = datetime(2026, 10, 10, 9, 0)
    day_count = covered_days or expected_days
    timeline: list[TimelineItem] = []
    module_outputs = TripModuleOutputs()

    if "flights" in expected_modules and include_flights:
        module_outputs.flights = [
            FlightDetail(
                id="outbound",
                direction="outbound",
                carrier="BA",
                departure_airport="LHR",
                arrival_airport="KIX",
                departure_time=base,
                arrival_time=base + timedelta(hours=14),
                fare_amount=640,
                fare_currency="GBP",
            ),
            FlightDetail(
                id="return",
                direction="return",
                carrier="BA",
                departure_airport="KIX",
                arrival_airport="LHR",
                departure_time=base + timedelta(days=expected_days - 1, hours=12),
                arrival_time=base + timedelta(days=expected_days, hours=2),
                fare_amount=620,
                fare_currency="GBP",
            ),
        ]
        timeline.extend(
            [
                _timeline_item(
                    item_id="flight_out",
                    item_type="flight",
                    title="Outbound flight to Kyoto",
                    day=1,
                    start=base if timed else None,
                    end=base + timedelta(hours=14) if timed else None,
                    module="flights",
                ),
                _timeline_item(
                    item_id="flight_return",
                    item_type="flight",
                    title="Return flight to London",
                    day=expected_days,
                    start=base + timedelta(days=expected_days - 1, hours=12)
                    if timed
                    else None,
                    end=base + timedelta(days=expected_days, hours=2)
                    if timed
                    else None,
                    module="flights",
                ),
            ]
        )

    if "hotels" in expected_modules and include_hotels:
        module_outputs.hotels = [
            HotelStayDetail(
                id="hotel_1",
                hotel_name="Kyoto Riverside Stay",
                area="Higashiyama",
                nightly_rate_amount=180,
                nightly_rate_currency="GBP",
                check_in=base + timedelta(hours=16),
                check_out=base + timedelta(days=expected_days - 1, hours=10),
            )
        ]
        timeline.append(
            _timeline_item(
                item_id="stay_anchor",
                item_type="hotel",
                title="Check in at Kyoto Riverside Stay",
                day=1,
                start=base + timedelta(hours=16) if timed else None,
                end=base + timedelta(hours=17) if timed else None,
                module="hotels",
            )
        )

    if "weather" in expected_modules:
        module_outputs.weather = [
            WeatherDetail(
                id=f"weather_{day}",
                day_label=f"Day {day}",
                summary="Mild and dry planning window.",
                forecast_date=date(2026, 10, 9 + day),
            )
            for day in range(1, expected_days + 1)
        ]

    if "activities" in expected_modules:
        module_outputs.activities = [
            ActivityDetail(
                id=f"activity_{day}",
                title=f"Kyoto food and culture stop {day}",
                price_text="GBP 25",
                day_label=f"Day {day}",
            )
            for day in range(1, day_count + 1)
        ]
        for day in range(1, day_count + 1):
            start = base + timedelta(days=day - 1, hours=2)
            timeline.append(
                _timeline_item(
                    item_id=f"activity_{day}",
                    item_type="activity",
                    title=f"Kyoto food and culture stop {day}",
                    day=day,
                    start=start if timed else None,
                    end=start + timedelta(hours=2) if timed else None,
                    module="activities",
                )
            )

    finalization = QuickPlanFinalizationState(
        accepted=True,
        review_status="complete",
        quality_status="pass",
        brochure_eligible=True,
        accepted_modules=expected_modules,
        assumptions=[{"kind": "working_dates", "summary": "Used a calm autumn window."}],
        review_result={"status": "complete", "show_to_user": True},
        quality_result={"status": "pass", "show_to_user": True},
        intelligence_summary={
            "plan_rationale": "Compact calm food and culture plan.",
            "accepted_module_scope": expected_modules,
            "excluded_modules": [
                {"module": module, "reason": "Excluded by request"}
                for module in excluded_modules
            ],
            "assumption_notes": ["Used assistant-derived working dates."],
            "day_architecture_highlights": [
                {"day_label": f"Day {day}", "theme": f"Area focus {day}"}
                for day in range(1, expected_days + 1)
            ],
            "review_outcome": {
                "review_status": "complete",
                "quality_status": "pass",
            },
        },
    )

    return TripDraft(
        trip_id="trip_eval",
        thread_id="thread_eval",
        title="Evaluation Trip",
        configuration=TripConfiguration(
            from_location="London",
            to_location="Kyoto",
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 14),
            travelers={"adults": 2},
        ),
        timeline=timeline,
        module_outputs=module_outputs,
        budget_estimate=_budget_estimate()
        if any(module in expected_modules for module in ["flights", "hotels"])
        else None,
        conversation=TripConversationState(
            planning_mode="quick",
            quick_plan_finalization=finalization,
        ),
    )


def _timeline_item(
    *,
    item_id: str,
    item_type,
    title: str,
    day: int,
    start: datetime | None,
    end: datetime | None,
    module: PlanningModuleKey,
) -> TimelineItem:
    return TimelineItem(
        id=item_id,
        type=item_type,
        title=title,
        day_label=f"Day {day}",
        start_at=start,
        end_at=end,
        timing_source="provider_exact" if module == "flights" else "planner_estimate",
        source_module=module,
    )


def _budget_estimate() -> TripBudgetEstimate:
    return TripBudgetEstimate(
        total_low_amount=1200,
        total_high_amount=1600,
        currency="GBP",
        categories=[
            TripBudgetEstimateCategory(
                category="flights",
                label="Flights",
                low_amount=1200,
                high_amount=1260,
                currency="GBP",
                source="provider_price",
            )
        ],
    )


def _finding_codes(result) -> set[str]:
    return {finding.code for finding in result.findings}
