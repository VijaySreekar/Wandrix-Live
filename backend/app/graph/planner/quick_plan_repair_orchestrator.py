from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_generation import (
    AcceptedQuickPlan,
    QuickPlanGenerationAttempt,
    build_quick_plan_completeness_repair_context,
    build_quick_plan_quality_repair_context,
    accept_quick_plan_candidate,
    is_quick_plan_quality_blocking,
)
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


MAX_QUICK_PLAN_REPAIR_ATTEMPTS = 2


class QuickPlanRepairAttemptRecord(BaseModel):
    attempt_index: int
    repair_goal: str
    generation_status: str
    completeness_review: dict[str, Any] | None = None
    quality_review: dict[str, Any] | None = None
    final_repair_chance: bool = False


class QuickPlanRepairLoopResult(BaseModel):
    attempt: QuickPlanGenerationAttempt
    accepted_plan: AcceptedQuickPlan | None = None
    first_completeness_review: Any | None = None
    first_quality_review: Any | None = None
    final_completeness_review: Any | None = None
    final_quality_review: Any | None = None
    repair_metadata: dict[str, Any] = Field(default_factory=dict)


def run_quick_plan_repair_loop(
    *,
    dossier: QuickPlanDossier,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    trip_title: str,
    conversation: TripConversationState,
    run_generation: Callable[..., QuickPlanGenerationAttempt],
    run_repair: Callable[..., QuickPlanGenerationAttempt],
    review_completeness: Callable[..., Any],
    review_quality: Callable[..., Any],
) -> QuickPlanRepairLoopResult:
    original_attempt = run_generation(
        dossier=dossier,
        configuration=configuration,
        previous_configuration=previous_configuration,
        existing_module_outputs=existing_module_outputs,
        trip_title=trip_title,
        conversation=conversation,
    )
    current_attempt = original_attempt
    repaired_attempts: list[QuickPlanGenerationAttempt] = []
    repair_attempt_records: list[QuickPlanRepairAttemptRecord] = []
    repair_goals: list[str] = []

    current_completeness = _review_completeness(
        review_completeness=review_completeness,
        dossier=dossier,
        attempt=current_attempt,
        configuration=configuration,
    )
    first_completeness = current_completeness
    current_quality = _review_quality_if_complete(
        review_quality=review_quality,
        dossier=dossier,
        attempt=current_attempt,
        configuration=configuration,
        completeness_review=current_completeness,
    )
    first_quality = current_quality
    stopped_reason = _stopped_reason(
        attempt=current_attempt,
        completeness_review=current_completeness,
        quality_review=current_quality,
        repair_count=0,
    )

    while _should_repair(
        attempt=current_attempt,
        completeness_review=current_completeness,
        quality_review=current_quality,
        repair_count=len(repair_attempt_records),
    ):
        next_index = len(repair_attempt_records) + 1
        final_repair_chance = next_index >= MAX_QUICK_PLAN_REPAIR_ATTEMPTS
        repair_context = _build_repair_context(
            original_attempt=original_attempt,
            current_attempt=current_attempt,
            repaired_attempts=repaired_attempts,
            completeness_review=current_completeness,
            quality_review=current_quality,
            repair_attempt_index=next_index,
            final_repair_chance=final_repair_chance,
        )
        repair_goals.append(repair_context.repair_goal)
        current_attempt = run_repair(
            dossier=dossier,
            configuration=configuration,
            previous_configuration=previous_configuration,
            existing_module_outputs=existing_module_outputs,
            trip_title=trip_title,
            conversation=conversation,
            repair_context=repair_context,
        )
        repaired_attempts.append(current_attempt)
        current_completeness = _review_completeness(
            review_completeness=review_completeness,
            dossier=dossier,
            attempt=current_attempt,
            configuration=configuration,
        )
        current_quality = _review_quality_if_complete(
            review_quality=review_quality,
            dossier=dossier,
            attempt=current_attempt,
            configuration=configuration,
            completeness_review=current_completeness,
        )
        repair_attempt_records.append(
            QuickPlanRepairAttemptRecord(
                attempt_index=next_index,
                repair_goal=repair_context.repair_goal,
                generation_status=current_attempt.status,
                completeness_review=_dump_model(current_completeness),
                quality_review=_dump_model(current_quality),
                final_repair_chance=final_repair_chance,
            )
        )
        stopped_reason = _stopped_reason(
            attempt=current_attempt,
            completeness_review=current_completeness,
            quality_review=current_quality,
            repair_count=len(repair_attempt_records),
        )

    repair_metadata = _build_repair_metadata(
        repair_attempt_records=repair_attempt_records,
        repair_goals=repair_goals,
        first_completeness_review=first_completeness,
        first_quality_review=first_quality,
        final_completeness_review=current_completeness,
        final_quality_review=current_quality,
        stopped_reason=stopped_reason,
    )
    accepted_plan = accept_quick_plan_candidate(
        attempt=current_attempt,
        review_result=current_completeness,
        quality_review_result=current_quality,
        repair_metadata=repair_metadata,
    )
    repair_metadata["final_visible"] = accepted_plan is not None
    if accepted_plan is not None:
        accepted_plan.review_metadata["final_visible"] = True

    return QuickPlanRepairLoopResult(
        attempt=current_attempt,
        accepted_plan=accepted_plan,
        first_completeness_review=first_completeness,
        first_quality_review=first_quality,
        final_completeness_review=current_completeness,
        final_quality_review=current_quality,
        repair_metadata=repair_metadata,
    )


def _build_repair_context(
    *,
    original_attempt: QuickPlanGenerationAttempt,
    current_attempt: QuickPlanGenerationAttempt,
    repaired_attempts: list[QuickPlanGenerationAttempt],
    completeness_review: Any,
    quality_review: Any | None,
    repair_attempt_index: int,
    final_repair_chance: bool,
):
    common = {
        "previous_attempt": current_attempt,
        "original_attempt": original_attempt,
        "previous_repair_attempts": repaired_attempts,
        "repair_attempt_index": repair_attempt_index,
        "max_repair_attempts": MAX_QUICK_PLAN_REPAIR_ATTEMPTS,
        "final_repair_chance": final_repair_chance,
    }
    if _is_complete(completeness_review) and _is_quality_repairable(quality_review):
        return build_quick_plan_quality_repair_context(
            failed_quality_review=quality_review,
            completeness_review=completeness_review,
            **common,
        )
    return build_quick_plan_completeness_repair_context(
        failed_completeness_review=completeness_review,
        **common,
    )


def _should_repair(
    *,
    attempt: QuickPlanGenerationAttempt,
    completeness_review: Any,
    quality_review: Any | None,
    repair_count: int,
) -> bool:
    if repair_count >= MAX_QUICK_PLAN_REPAIR_ATTEMPTS:
        return False
    if not _is_complete(completeness_review):
        return repair_count == 0 and _can_repair_completeness(
            attempt=attempt,
            completeness_review=completeness_review,
        )
    if _is_quality_pass(quality_review):
        return False
    if repair_count >= 1 and not _quality_allows_second_repair(quality_review):
        return False
    return _is_quality_repairable(quality_review)


def _can_repair_completeness(
    *,
    attempt: QuickPlanGenerationAttempt,
    completeness_review: Any,
) -> bool:
    if not completeness_review:
        return False
    if completeness_review.status == "incomplete":
        return True
    return completeness_review.status == "failed" and attempt.status == "empty"


def _quality_allows_second_repair(quality_review: Any | None) -> bool:
    if not _is_quality_repairable(quality_review):
        return False
    payload = _dump_model(quality_review) or {}
    scorecard = payload.get("scorecard") or {}
    if scorecard.get("fact_safety", 10) <= 3:
        return False
    for issue in payload.get("issues") or []:
        if issue.get("severity") == "high" and issue.get("dimension") in {
            "fact_safety",
            "logistics_realism",
        }:
            return False
    return True


def _review_completeness(
    *,
    review_completeness: Callable[..., Any],
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
) -> Any:
    return review_completeness(
        dossier=dossier,
        attempt=attempt,
        configuration=configuration,
    )


def _review_quality_if_complete(
    *,
    review_quality: Callable[..., Any],
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
    completeness_review: Any,
) -> Any | None:
    if not _is_complete(completeness_review):
        return None
    return review_quality(
        dossier=dossier,
        attempt=attempt,
        configuration=configuration,
        completeness_review=completeness_review,
    )


def _build_repair_metadata(
    *,
    repair_attempt_records: list[QuickPlanRepairAttemptRecord],
    repair_goals: list[str],
    first_completeness_review: Any,
    first_quality_review: Any | None,
    final_completeness_review: Any,
    final_quality_review: Any | None,
    stopped_reason: str,
) -> dict[str, Any]:
    repair_count = len(repair_attempt_records)
    return {
        "repair_attempted": repair_count > 0,
        "repair_attempt_count": repair_count,
        "repair_attempts": [
            record.model_dump(mode="json") for record in repair_attempt_records
        ],
        "repair_goal": repair_goals[-1] if repair_goals else "not_attempted",
        "repair_goals": repair_goals,
        "repair_status": (
            final_quality_review.status
            if final_quality_review
            else final_completeness_review.status
            if final_completeness_review
            else "not_attempted"
        ),
        "first_completeness_review": _dump_model(first_completeness_review),
        "first_quality_review": _dump_model(first_quality_review),
        "final_completeness_review": _dump_model(final_completeness_review),
        "final_quality_review": _dump_model(final_quality_review),
        "first_review_result": _dump_model(first_completeness_review),
        "final_review_result": _dump_model(final_completeness_review),
        "final_visible": _is_complete(final_completeness_review)
        and not is_quick_plan_quality_blocking(final_quality_review),
        "quality_blocking": is_quick_plan_quality_blocking(final_quality_review),
        "stopped_reason": stopped_reason,
    }


def _stopped_reason(
    *,
    attempt: QuickPlanGenerationAttempt,
    completeness_review: Any,
    quality_review: Any | None,
    repair_count: int,
) -> str:
    if _is_complete(completeness_review) and not is_quick_plan_quality_blocking(
        quality_review
    ):
        return "accepted"
    if not _is_complete(completeness_review):
        if attempt.status == "empty":
            return "empty_generation"
        if repair_count > 0:
            return "completeness_failed_after_repair"
        return "completeness_not_repairable"
    if quality_review is None:
        return "quality_not_reviewed"
    if quality_review.status == "fail":
        return "quality_failed"
    if quality_review.status == "repairable":
        if repair_count >= MAX_QUICK_PLAN_REPAIR_ATTEMPTS:
            return "quality_repair_limit_reached"
        if repair_count >= 1 and not _quality_allows_second_repair(quality_review):
            return "quality_second_repair_not_allowed"
        return "quality_repairable"
    return "not_accepted"


def _is_complete(review: Any) -> bool:
    return bool(review and review.status == "complete" and review.show_to_user)


def _is_quality_pass(review: Any | None) -> bool:
    return bool(review and review.status == "pass" and review.show_to_user)


def _is_quality_repairable(review: Any | None) -> bool:
    return bool(review and review.status == "repairable")


def _dump_model(value: Any | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value)
