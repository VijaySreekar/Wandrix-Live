from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_geography_review import review_quick_plan_geography
from app.graph.planner.quick_plan_local_quality_review import (
    review_quick_plan_local_quality,
)
from app.graph.planner.quick_plan_logistics_quality_review import (
    review_quick_plan_logistics_quality,
)
from app.graph.planner.quick_plan_pacing_review import review_quick_plan_pacing
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityIssue,
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
    QuickPlanSpecialistReviewSummary,
)
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.schemas.trip_planning import TripConfiguration


def review_quick_plan_quality(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: QuickPlanReviewResult,
) -> QuickPlanQualityReviewResult | None:
    if not (
        completeness_review
        and completeness_review.status == "complete"
        and completeness_review.show_to_user
    ):
        return None

    specialist_calls = {
        "geography": review_quick_plan_geography,
        "pacing": review_quick_plan_pacing,
        "local_quality": review_quick_plan_local_quality,
        "logistics_quality": review_quick_plan_logistics_quality,
    }
    with ThreadPoolExecutor(max_workers=len(specialist_calls)) as executor:
        futures = {
            name: executor.submit(
                reviewer,
                dossier=dossier,
                attempt=attempt,
                configuration=configuration,
                completeness_review=completeness_review,
            )
            for name, reviewer in specialist_calls.items()
        }
        specialist_results = {name: future.result() for name, future in futures.items()}
    return combine_quick_plan_quality_reviews(specialist_results)


def combine_quick_plan_quality_reviews(
    specialist_results: dict[str, QuickPlanQualityReviewResult | None],
) -> QuickPlanQualityReviewResult:
    missing_specialists = [
        name for name, result in specialist_results.items() if result is None
    ]
    if missing_specialists:
        return QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(),
            issues=[
                QuickPlanQualityIssue(
                    dimension="fact_safety",
                    severity="high",
                    issue=(
                        "One or more quality specialists did not return a usable "
                        "decision."
                    ),
                    repair_instruction="Re-run private quality review before showing the plan.",
                )
            ],
            review_notes=[
                "Missing specialist review output: " + ", ".join(missing_specialists)
            ],
            repair_instructions=["Re-run quality review before accepting the candidate."],
        assistant_summary=_clamp_assistant_summary(
            "I generated a complete Quick Plan, but the private quality review "
            "could not verify it well enough to show, so I kept the board unchanged."
        ),
            specialist_results=_dump_specialist_results(specialist_results),
        )

    geography = specialist_results["geography"]
    pacing = specialist_results["pacing"]
    local_quality = specialist_results["local_quality"]
    logistics_quality = specialist_results["logistics_quality"]
    assert geography is not None
    assert pacing is not None
    assert local_quality is not None
    assert logistics_quality is not None

    scorecard = QuickPlanQualityScorecard(
        geography=geography.scorecard.geography,
        pacing=pacing.scorecard.pacing,
        local_specificity=local_quality.scorecard.local_specificity,
        user_fit=min(
            score
            for score in [
                geography.scorecard.user_fit,
                pacing.scorecard.user_fit,
                local_quality.scorecard.user_fit,
                logistics_quality.scorecard.user_fit,
            ]
            if score > 0
        )
        if any(
            score > 0
            for score in [
                geography.scorecard.user_fit,
                pacing.scorecard.user_fit,
                local_quality.scorecard.user_fit,
                logistics_quality.scorecard.user_fit,
            ]
        )
        else 0,
        logistics_realism=logistics_quality.scorecard.logistics_realism,
        fact_safety=logistics_quality.scorecard.fact_safety,
    )
    issues = _merge_issues(specialist_results.values())
    repair_instructions = _merge_text(
        instruction
        for result in specialist_results.values()
        if result is not None
        for instruction in result.repair_instructions
    )
    review_notes = _merge_text(
        note
        for result in specialist_results.values()
        if result is not None
        for note in result.review_notes
    )

    status = _combined_status(
        specialist_results=[geography, pacing, local_quality, logistics_quality],
        scorecard=scorecard,
        issues=issues,
    )
    return QuickPlanQualityReviewResult(
        status=status,
        show_to_user=status == "pass",
        scorecard=scorecard,
        issues=issues,
        review_notes=review_notes,
        repair_instructions=repair_instructions,
        assistant_summary=_clamp_assistant_summary(
            _assistant_summary(status=status, issues=issues)
        ),
        specialist_results=_dump_specialist_results(specialist_results),
    )


def _combined_status(
    *,
    specialist_results: list[QuickPlanQualityReviewResult],
    scorecard: QuickPlanQualityScorecard,
    issues: list[QuickPlanQualityIssue],
) -> str:
    scores = [
        scorecard.geography,
        scorecard.pacing,
        scorecard.local_specificity,
        scorecard.user_fit,
        scorecard.logistics_realism,
        scorecard.fact_safety,
    ]
    if (
        any(result.status == "fail" for result in specialist_results)
        or any(issue.severity == "high" for issue in issues)
        or min(scores) <= 3
    ):
        return "fail"
    if any(result.status == "repairable" for result in specialist_results) or min(scores) < 7:
        return "repairable"
    return "pass"


def _assistant_summary(
    *,
    status: str,
    issues: list[QuickPlanQualityIssue],
) -> str:
    if status == "pass":
        return "Quick Plan passed the private completeness and quality reviews."
    top_issues = "; ".join(issue.issue for issue in issues[:3])
    if not top_issues:
        top_issues = "the private quality review found it was not strong enough"
    return (
        "I generated a complete Quick Plan, but I did not show it because the "
        f"private quality review flagged: {top_issues}. I kept the current board unchanged."
    )


def _clamp_assistant_summary(summary: str) -> str:
    max_length = 420
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 1].rstrip() + "…"


def _merge_issues(
    results: list[QuickPlanQualityReviewResult | None],
) -> list[QuickPlanQualityIssue]:
    seen: set[tuple[str, str]] = set()
    merged: list[QuickPlanQualityIssue] = []
    for result in results:
        if result is None:
            continue
        for issue in result.issues:
            key = (issue.dimension, issue.issue)
            if key in seen:
                continue
            seen.add(key)
            merged.append(issue)
    return merged[:16]


def _merge_text(values) -> list[str]:
    merged: list[str] = []
    for value in values:
        if not value or value in merged:
            continue
        merged.append(value)
    return merged[:12]


def _dump_specialist_results(
    results: dict[str, QuickPlanQualityReviewResult | None],
) -> list[QuickPlanSpecialistReviewSummary]:
    summaries: list[QuickPlanSpecialistReviewSummary] = []
    for name, result in results.items():
        if result is None:
            summaries.append(
                QuickPlanSpecialistReviewSummary(
                    specialist=name,
                    status=None,
                    show_to_user=None,
                    review_notes=[],
                    issue_count=0,
                )
            )
            continue
        summaries.append(
            QuickPlanSpecialistReviewSummary(
                specialist=name,
                status=result.status,
                show_to_user=result.show_to_user,
                review_notes=list(result.review_notes[:6]),
                issue_count=len(result.issues),
            )
        )
    return summaries
