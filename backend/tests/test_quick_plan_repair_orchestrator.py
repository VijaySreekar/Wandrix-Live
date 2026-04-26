from datetime import datetime, timezone

from app.graph.planner.quick_plan_dossier import QuickPlanDossier, QuickPlanReadiness
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityIssue,
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
)
from app.graph.planner.quick_plan_repair_orchestrator import (
    run_quick_plan_repair_loop,
)
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import ActivityDetail, TripConfiguration, TripModuleOutputs


def test_repair_loop_accepts_first_candidate_without_repair() -> None:
    repair_calls: list = []

    result = run_quick_plan_repair_loop(
        dossier=_dossier(),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Kyoto",
        conversation=TripConversationState(),
        run_generation=lambda **_: _attempt("initial", activity_id="initial_activity"),
        run_repair=lambda **kwargs: repair_calls.append(kwargs) or _attempt("repair"),
        review_completeness=lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
        ),
        review_quality=lambda **_: _quality("pass"),
    )

    assert result.accepted_plan is not None
    assert result.accepted_plan.module_outputs.activities[0].id == "initial_activity"
    assert result.repair_metadata["repair_attempt_count"] == 0
    assert result.repair_metadata["stopped_reason"] == "accepted"
    assert repair_calls == []


def test_repair_loop_runs_second_quality_repair_and_accepts_latest_attempt() -> None:
    repair_payloads: list[dict] = []
    repair_attempts = [_attempt("repair one", activity_id="repair_one")]
    quality_results = [
        _quality("repairable", local_specificity=4),
        _quality("pass"),
    ]

    def _repair(**kwargs):
        repair_payloads.append(kwargs["repair_context"].prompt_payload())
        return repair_attempts.pop(0)

    result = run_quick_plan_repair_loop(
        dossier=_dossier(),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Kyoto",
        conversation=TripConversationState(),
        run_generation=lambda **_: _attempt("initial", activity_id="initial"),
        run_repair=_repair,
        review_completeness=lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
        ),
        review_quality=lambda **_: quality_results.pop(0),
    )

    assert result.accepted_plan is not None
    assert result.accepted_plan.module_outputs.activities[0].id == "repair_one"
    assert result.repair_metadata["repair_attempt_count"] == 1
    assert result.repair_metadata["repair_goals"] == ["quality"]
    assert result.repair_metadata["stopped_reason"] == "accepted"
    assert repair_payloads[0]["final_repair_chance"] is True
    assert repair_payloads[0]["original_attempt"]["draft"]["timeline_preview"][0]["title"] == "initial"
    assert repair_payloads[0]["unresolved_quality_dimensions"] == ["local_specificity"]
    assert result.repair_metadata["timing_ms"]["overall"] >= 0


def test_repair_loop_accepts_non_blocking_repairable_after_repair_limit() -> None:
    quality_results = [
        _quality("repairable", local_specificity=4),
        _quality("repairable", pacing=5),
    ]
    repair_attempts = [_attempt("repair one")]

    result = run_quick_plan_repair_loop(
        dossier=_dossier(),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Kyoto",
        conversation=TripConversationState(),
        run_generation=lambda **_: _attempt("initial"),
        run_repair=lambda **_: repair_attempts.pop(0),
        review_completeness=lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
        ),
        review_quality=lambda **_: quality_results.pop(0),
    )

    assert result.accepted_plan is not None
    assert result.accepted_plan.timeline_preview[0].title == "repair one"
    assert result.repair_metadata["repair_attempt_count"] == 1
    assert result.repair_metadata["final_visible"] is True
    assert result.repair_metadata["quality_blocking"] is False
    assert result.repair_metadata["stopped_reason"] == "accepted"


def test_repair_loop_skips_second_repair_for_quality_fail() -> None:
    repair_calls = 0
    quality_results = [
        _quality("repairable", local_specificity=4),
        _quality("fail", fact_safety=2),
    ]

    def _repair(**_):
        nonlocal repair_calls
        repair_calls += 1
        return _attempt("repair one")

    result = run_quick_plan_repair_loop(
        dossier=_dossier(),
        configuration=_configuration(),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        trip_title="Kyoto",
        conversation=TripConversationState(),
        run_generation=lambda **_: _attempt("initial"),
        run_repair=_repair,
        review_completeness=lambda **_: QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
        ),
        review_quality=lambda **_: quality_results.pop(0),
    )

    assert repair_calls == 1
    assert result.accepted_plan is None
    assert result.repair_metadata["repair_attempt_count"] == 1
    assert result.repair_metadata["stopped_reason"] == "quality_failed"


def _attempt(title: str, *, activity_id: str = "activity") -> QuickPlanGenerationAttempt:
    return QuickPlanGenerationAttempt(
        status="generated",
        module_outputs=TripModuleOutputs(
            activities=[ActivityDetail(id=activity_id, title=title)]
        ),
        timeline_module_outputs=TripModuleOutputs(),
        draft=QuickPlanDraft(
            timeline_preview=[
                ProposedTimelineItem(
                    type="activity",
                    title=title,
                    day_label="Day 1",
                    start_at=datetime(2026, 5, 1, 10, tzinfo=timezone.utc),
                    end_at=datetime(2026, 5, 1, 12, tzinfo=timezone.utc),
                    timing_source="planner_estimate",
                )
            ]
        ),
    )


def _quality(
    status: str,
    *,
    geography: int = 8,
    pacing: int = 8,
    local_specificity: int = 8,
    user_fit: int = 8,
    logistics_realism: int = 8,
    fact_safety: int = 8,
) -> QuickPlanQualityReviewResult:
    issues = []
    if status == "repairable":
        issues.append(
            QuickPlanQualityIssue(
                dimension="pacing" if pacing < 7 else "local_specificity",
                issue="Quality dimension remains below the bar.",
                repair_instruction="Regenerate with the unresolved dimension fixed.",
            )
        )
    if status == "fail":
        issues.append(
            QuickPlanQualityIssue(
                dimension="fact_safety",
                severity="high",
                issue="Unsafe fact handling.",
            )
        )
    return QuickPlanQualityReviewResult(
        status=status,
        show_to_user=status == "pass",
        scorecard=QuickPlanQualityScorecard(
            geography=geography,
            pacing=pacing,
            local_specificity=local_specificity,
            user_fit=user_fit,
            logistics_realism=logistics_realism,
            fact_safety=fact_safety,
        ),
        issues=issues,
    )


def _dossier() -> QuickPlanDossier:
    return QuickPlanDossier(
        readiness=QuickPlanReadiness(
            ready=True,
            allowed_modules=["activities"],
            module_scope_source="user_explicit",
        ),
        trip_configuration={
            "confirmed_or_derived": _configuration().model_dump(mode="json")
        },
        module_scope={"allowed_modules": ["activities"]},
        module_scope_source="user_explicit",
    )


def _configuration() -> TripConfiguration:
    return TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2026, 5, 1, tzinfo=timezone.utc).date(),
        end_date=datetime(2026, 5, 5, tzinfo=timezone.utc).date(),
        selected_modules={
            "flights": False,
            "hotels": False,
            "activities": True,
            "weather": True,
        },
    )
