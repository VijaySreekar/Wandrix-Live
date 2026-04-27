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


def review_quick_plan_local_quality(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: QuickPlanReviewResult,
) -> QuickPlanQualityReviewResult | None:
    prompt = f"""
You are Wandrix's private local-quality reviewer.

Judge local trip quality: destination-specific food/culture choices, named places,
non-generic activities, and fit to the user's stated interests and budget posture.
Do not repair the plan.

Return pass only when the candidate reads like a credible trip for this destination.
Return repairable when generic or weak content can be fixed. Return fail when it is not trustworthy.

Scorecard requirements:
- Set local_specificity and user_fit as the main scores.
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
                    "Review Quick Plan destination specificity and user fit privately. Do not rewrite.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning("Quick Plan local quality review returned no usable output.", exc_info=True)
        return None
