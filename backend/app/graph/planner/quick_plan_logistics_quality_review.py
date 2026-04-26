from __future__ import annotations

import logging

from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_quality_models import QuickPlanQualityReviewResult
from app.graph.planner.quick_plan_review import QuickPlanReviewResult
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_planning import TripConfiguration


logger = logging.getLogger(__name__)


def review_quick_plan_logistics_quality(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: QuickPlanReviewResult,
) -> QuickPlanQualityReviewResult | None:
    prompt = f"""
You are Wandrix's private logistics and fact-safety reviewer.

Judge logistics realism and fact safety: flight/stay integration, provider-backed facts
versus planner estimates, wording around prices/timings/availability, and whether
missing provider facts are treated honestly. Do not repair the plan.

Return pass only when logistics and fact wording are safe to show.
Return repairable when issues are actionable. Return fail when facts are misleading or unsafe.

Scorecard requirements:
- Set logistics_realism and fact_safety as the main scores.
- Leave unrelated dimensions at reasonable neutral scores if not judged.

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
                    "Review Quick Plan logistics realism and fact safety privately. Do not rewrite.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning("Quick Plan logistics quality review returned no usable output.", exc_info=True)
        return None
