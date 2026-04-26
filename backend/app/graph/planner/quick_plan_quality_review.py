from __future__ import annotations

import logging

from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_quality_models import (
    QuickPlanQualityIssue,
    QuickPlanQualityReviewResult,
    QuickPlanQualityScorecard,
    QuickPlanSpecialistReviewSummary,
)
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_planning import TripConfiguration


logger = logging.getLogger(__name__)


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

    result = _run_combined_quality_review(
        dossier=dossier,
        attempt=attempt,
        configuration=configuration,
        completeness_review=completeness_review,
    )
    if result is None:
        return QuickPlanQualityReviewResult(
            status="fail",
            show_to_user=False,
            scorecard=QuickPlanQualityScorecard(),
            issues=[
                QuickPlanQualityIssue(
                    dimension="fact_safety",
                    severity="high",
                    issue="The combined quality review did not return a usable decision.",
                    repair_instruction="Re-run private quality review before showing the plan.",
                )
            ],
            review_notes=["The combined quality review did not return a usable output."],
            repair_instructions=["Re-run quality review before accepting the candidate."],
            assistant_summary=_clamp_assistant_summary(
                "I generated a complete Quick Plan, but the private quality review "
                "could not verify it well enough to show, so I kept the board unchanged."
            ),
            specialist_results=_build_specialist_summaries(
                QuickPlanQualityScorecard(),
                [],
                status="fail",
            ),
        )

    return result.model_copy(
        update={
            "show_to_user": result.status == "pass",
            "review_notes": _merge_text(result.review_notes),
            "repair_instructions": _merge_text(result.repair_instructions),
            "assistant_summary": _clamp_assistant_summary(
                result.assistant_summary
                or _assistant_summary(status=result.status, issues=result.issues)
            ),
            "specialist_results": _build_specialist_summaries(
                result.scorecard,
                result.issues,
                status=result.status,
            ),
        }
    )


def _run_combined_quality_review(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: QuickPlanReviewResult,
) -> QuickPlanQualityReviewResult | None:
    prompt = f"""
You are Wandrix's private Quick Plan quality reviewer.

Judge the candidate across all six quality dimensions together:
- geography
- pacing
- local_specificity
- user_fit
- logistics_realism
- fact_safety

Return:
- pass only when the candidate is safe and strong enough to show as the editable first draft
- repairable when the itinerary is structurally usable but needs a better regeneration pass
- fail when the draft is misleading, unsafe, or not trustworthy enough to show

Rules:
- Do not rewrite the itinerary.
- Score every dimension from 0 to 10.
- Use issues only for real problems; each issue must name the affected dimension.
- Use severity high for unsafe fact handling, impossible logistics, or severe route/pacing problems.
- Keep review_notes and repair_instructions concise and actionable.
- assistant_summary should briefly explain why the draft is or is not being shown.

Trip configuration:
{configuration.model_dump(mode="json")}

Quick Plan dossier:
{dossier.model_dump(mode="json")}

Completeness review:
{completeness_review.model_dump(mode="json")}

Generation attempt:
{attempt.model_dump(mode="json")}
""".strip()

    try:
        model = create_quick_plan_chat_model(
            temperature=0.0,
            timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
            max_retries=1,
        )
        return model.with_structured_output(
            QuickPlanQualityReviewResult,
            method="json_schema",
        ).invoke(
            [
                (
                    "system",
                    "Review Quick Plan quality privately across geography, pacing, local specificity, user fit, logistics realism, and fact safety. Do not rewrite the itinerary.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning(
            "Quick Plan combined quality review returned no usable output.",
            exc_info=True,
        )
        return None


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


def _merge_text(values) -> list[str]:
    merged: list[str] = []
    for value in values:
        if not value or value in merged:
            continue
        merged.append(value)
    return merged[:12]


def _build_specialist_summaries(
    scorecard: QuickPlanQualityScorecard,
    issues: list[QuickPlanQualityIssue],
    *,
    status: str,
) -> list[QuickPlanSpecialistReviewSummary]:
    grouped_issues = {
        "geography": [
            issue for issue in issues if issue.dimension in {"geography"}
        ],
        "pacing": [issue for issue in issues if issue.dimension in {"pacing"}],
        "local_quality": [
            issue
            for issue in issues
            if issue.dimension in {"local_specificity", "user_fit"}
        ],
        "logistics_quality": [
            issue
            for issue in issues
            if issue.dimension in {"logistics_realism", "fact_safety"}
        ],
    }
    score_groups = {
        "geography": [scorecard.geography],
        "pacing": [scorecard.pacing],
        "local_quality": [scorecard.local_specificity, scorecard.user_fit],
        "logistics_quality": [scorecard.logistics_realism, scorecard.fact_safety],
    }

    summaries: list[QuickPlanSpecialistReviewSummary] = []
    for specialist in [
        "geography",
        "pacing",
        "local_quality",
        "logistics_quality",
    ]:
        specialist_issues = grouped_issues[specialist]
        specialist_status = _specialist_status(
            status=status,
            scores=score_groups[specialist],
            issues=specialist_issues,
        )
        summaries.append(
            QuickPlanSpecialistReviewSummary(
                specialist=specialist,
                status=specialist_status,
                show_to_user=specialist_status == "pass",
                review_notes=[issue.issue for issue in specialist_issues[:6]],
                issue_count=len(specialist_issues),
            )
        )
    return summaries


def _specialist_status(
    *,
    status: str,
    scores: list[int],
    issues: list[QuickPlanQualityIssue],
) -> str:
    min_score = min(scores) if scores else 0
    if any(issue.severity == "high" for issue in issues) or min_score <= 3:
        return "fail"
    if issues or min_score < 7:
        return "repairable"
    return "pass" if status == "pass" else "repairable"
