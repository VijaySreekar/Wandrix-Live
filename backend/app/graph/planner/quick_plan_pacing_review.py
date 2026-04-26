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


def review_quick_plan_pacing(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: QuickPlanReviewResult,
) -> QuickPlanQualityReviewResult | None:
    prompt = f"""
You are Wandrix's private Quick Plan pacing reviewer.

Judge only pacing quality: calm/relaxed fit, daily density, arrival/departure load,
buffers, and whether the schedule feels realistic for the user's style. Do not repair.

Return pass only when pacing is good enough to show to the user.
Return repairable when issues are actionable. Return fail when the candidate is unsafe or unusable.

Scorecard requirements:
- Set pacing to the main score.
- Also score user_fit when pacing conflicts with the stated trip style.
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
                    "Review Quick Plan pacing quality privately. Do not rewrite the itinerary.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning("Quick Plan pacing review returned no usable output.", exc_info=True)
        return None
