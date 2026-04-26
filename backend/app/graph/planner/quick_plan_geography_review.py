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


def review_quick_plan_geography(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: QuickPlanReviewResult,
) -> QuickPlanQualityReviewResult | None:
    prompt = f"""
You are Wandrix's private Quick Plan geography reviewer.

Judge only geography quality: route flow, area clustering, neighborhood/day coherence,
and whether the candidate avoids obvious cross-city zigzags. Do not repair the plan.

Return pass only when geography is coherent enough to show to the user.
Return repairable when issues are actionable. Return fail when the route logic cannot be trusted.

Scorecard requirements:
- Set geography to the main score.
- Also score user_fit if geography conflicts with stated style/module scope.
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
                    "Review Quick Plan geography quality privately. Do not rewrite the itinerary.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning("Quick Plan geography review returned no usable output.", exc_info=True)
        return None
