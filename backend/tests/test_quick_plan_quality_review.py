from datetime import datetime, timezone

from app.graph.planner import quick_plan_quality_review
from app.graph.planner.quick_plan_dossier import QuickPlanDossier, QuickPlanReadiness
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityIssue,
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
)
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_planning import TripConfiguration


def test_quality_review_passes_coherent_complete_candidate(monkeypatch) -> None:
    _patch_specialists(
        monkeypatch,
        geography=_quality_result("pass", geography=8),
        pacing=_quality_result("pass", pacing=8),
        local_quality=_quality_result("pass", local_specificity=8, user_fit=8),
        logistics=_quality_result("pass", logistics_realism=8, fact_safety=8),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Nishiki Market breakfast and Higashiyama temples"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert result is not None
    assert result.status == "pass"
    assert result.show_to_user is True
    assert result.scorecard.local_specificity == 8
    assert any(
        summary.specialist == "local_quality"
        for summary in result.specialist_results
    )


def test_quality_review_blocks_generic_itinerary(monkeypatch) -> None:
    _patch_specialists(
        monkeypatch,
        geography=_quality_result("pass", geography=8),
        pacing=_quality_result("pass", pacing=8),
        local_quality=_quality_result(
            "repairable",
            local_specificity=4,
            user_fit=6,
            issue=QuickPlanQualityIssue(
                dimension="local_specificity",
                issue="Activities are generic and not Kyoto-specific.",
                repair_instruction="Use named Kyoto food and culture places.",
            ),
        ),
        logistics=_quality_result("pass", logistics_realism=8, fact_safety=8),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Museum visit and dinner"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert result is not None
    assert result.status == "repairable"
    assert result.show_to_user is False
    assert result.issues[0].dimension == "local_specificity"


def test_quality_review_blocks_geographically_incoherent_itinerary(monkeypatch) -> None:
    _patch_specialists(
        monkeypatch,
        geography=_quality_result(
            "repairable",
            geography=3,
            issue=QuickPlanQualityIssue(
                dimension="geography",
                issue="The day zigzags across distant areas without a route idea.",
            ),
        ),
        pacing=_quality_result("pass", pacing=8),
        local_quality=_quality_result("pass", local_specificity=8, user_fit=8),
        logistics=_quality_result("pass", logistics_realism=8, fact_safety=8),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Arashiyama, Fushimi Inari, and Gion repeatedly in one day"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert result is not None
    assert result.status == "fail"
    assert result.show_to_user is False


def test_quality_review_blocks_overpacked_calm_itinerary(monkeypatch) -> None:
    _patch_specialists(
        monkeypatch,
        geography=_quality_result("pass", geography=8),
        pacing=_quality_result(
            "repairable",
            pacing=5,
            user_fit=5,
            issue=QuickPlanQualityIssue(
                dimension="pacing",
                issue="The calm trip has too many timed stops and no buffers.",
            ),
        ),
        local_quality=_quality_result("pass", local_specificity=8, user_fit=8),
        logistics=_quality_result("pass", logistics_realism=8, fact_safety=8),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Eight temples, three meals, and two markets in one day"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert result is not None
    assert result.status == "repairable"
    assert result.show_to_user is False


def test_quality_review_blocks_unsafe_provider_fact_copy(monkeypatch) -> None:
    _patch_specialists(
        monkeypatch,
        geography=_quality_result("pass", geography=8),
        pacing=_quality_result("pass", pacing=8),
        local_quality=_quality_result("pass", local_specificity=8, user_fit=8),
        logistics=_quality_result(
            "fail",
            logistics_realism=4,
            fact_safety=2,
            issue=QuickPlanQualityIssue(
                dimension="fact_safety",
                severity="high",
                issue="The draft presents missing prices and opening hours as confirmed.",
            ),
        ),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Confirmed prices and reservations for all activities"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert result is not None
    assert result.status == "fail"
    assert result.show_to_user is False


def test_quality_review_clamps_long_assistant_summary(monkeypatch) -> None:
    issues = [
        QuickPlanQualityIssue(
            dimension="local_specificity",
            issue=f"The itinerary is generic and weakly local issue {index}.",
        )
        for index in range(12)
    ]
    _patch_specialists(
        monkeypatch,
        geography=_quality_result("pass", geography=8),
        pacing=_quality_result("pass", pacing=8),
        local_quality=QuickPlanQualityReviewResult(
            status="repairable",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(
                geography=8,
                pacing=8,
                local_specificity=4,
                user_fit=7,
                logistics_realism=8,
                fact_safety=8,
            ),
            issues=issues,
        ),
        logistics=_quality_result("pass", logistics_realism=8, fact_safety=8),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Private candidate"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="complete", show_to_user=True),
    )

    assert result is not None
    assert result.status == "repairable"
    assert result.assistant_summary is not None
    assert len(result.assistant_summary) <= 420


def test_quality_review_skips_when_completeness_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        quick_plan_quality_review,
        "review_quick_plan_geography",
        lambda **_: (_ for _ in ()).throw(AssertionError("quality should not run")),
    )

    result = quick_plan_quality_review.review_quick_plan_quality(
        dossier=_dossier(["activities"]),
        attempt=_attempt("Private candidate"),
        configuration=_configuration(),
        completeness_review=QuickPlanReviewResult(status="incomplete", show_to_user=False),
    )

    assert result is None


def _patch_specialists(
    monkeypatch,
    *,
    geography: QuickPlanQualityReviewResult,
    pacing: QuickPlanQualityReviewResult,
    local_quality: QuickPlanQualityReviewResult,
    logistics: QuickPlanQualityReviewResult,
) -> None:
    monkeypatch.setattr(
        quick_plan_quality_review,
        "review_quick_plan_geography",
        lambda **_: geography,
    )
    monkeypatch.setattr(
        quick_plan_quality_review,
        "review_quick_plan_pacing",
        lambda **_: pacing,
    )
    monkeypatch.setattr(
        quick_plan_quality_review,
        "review_quick_plan_local_quality",
        lambda **_: local_quality,
    )
    monkeypatch.setattr(
        quick_plan_quality_review,
        "review_quick_plan_logistics_quality",
        lambda **_: logistics,
    )


def _quality_result(
    status: str,
    *,
    geography: int = 7,
    pacing: int = 7,
    local_specificity: int = 7,
    user_fit: int = 7,
    logistics_realism: int = 7,
    fact_safety: int = 7,
    issue: QuickPlanQualityIssue | None = None,
) -> QuickPlanQualityReviewResult:
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
        issues=[issue] if issue else [],
        repair_instructions=[issue.repair_instruction]
        if issue and issue.repair_instruction
        else [],
    )


def _dossier(allowed_modules: list[str]) -> QuickPlanDossier:
    return QuickPlanDossier(
        readiness=QuickPlanReadiness(
            ready=True,
            allowed_modules=allowed_modules,
            module_scope_source="user_explicit",
        ),
        trip_configuration={
            "confirmed_or_derived": _configuration().model_dump(mode="json")
        },
        module_scope={"allowed_modules": allowed_modules},
        module_scope_source="user_explicit",
    )


def _attempt(title: str) -> QuickPlanGenerationAttempt:
    return QuickPlanGenerationAttempt(
        status="generated",
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
