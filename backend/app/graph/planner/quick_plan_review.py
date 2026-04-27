from __future__ import annotations

from datetime import date
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_generation import QuickPlanGenerationAttempt
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.graph.planner.turn_models import ProposedTimelineItem
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_planning import TripConfiguration


logger = logging.getLogger(__name__)

QuickPlanReviewStatus = Literal["complete", "incomplete", "failed"]
QuickPlanMissingOutput = Literal[
    "flights",
    "stay",
    "activities",
    "weather",
    "timing",
    "day_coverage",
    "provider_fact_safety",
]


class QuickPlanReviewResult(BaseModel):
    status: QuickPlanReviewStatus
    show_to_user: bool = False
    missing_outputs: list[QuickPlanMissingOutput] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list, max_length=8)
    assistant_summary: str | None = Field(default=None, max_length=320)


def review_quick_plan_generation(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
) -> QuickPlanReviewResult:
    if attempt.status == "empty" or not attempt.draft.timeline_preview:
        return QuickPlanReviewResult(
            status="failed",
            show_to_user=False,
            missing_outputs=["day_coverage"],
            review_notes=["Generation did not return visible itinerary rows."],
            assistant_summary=(
                "I tried to build the Quick Plan, but that run did not return a usable day-by-day itinerary, "
                "so I kept the current board unchanged."
            ),
        )

    structural_result = _review_structural_completeness(
        dossier=dossier,
        attempt=attempt,
        configuration=configuration,
    )
    if structural_result is not None:
        return structural_result

    llm_result = _run_structured_llm_review(
        dossier=dossier,
        attempt=attempt,
        configuration=configuration,
    )
    if llm_result is None:
        return QuickPlanReviewResult(
            status="failed",
            show_to_user=False,
            missing_outputs=["provider_fact_safety"],
            review_notes=["The review model did not return a usable completeness decision."],
            assistant_summary=(
                "I generated a Quick Plan candidate, but I could not complete the safety review, "
                "so I kept the current board unchanged."
            ),
        )

    normalized = _normalize_review_result(llm_result)
    if (
        normalized.status != "complete"
        and not _has_hard_safety_or_timing_failure(normalized)
    ):
        return QuickPlanReviewResult(
            status="complete",
            show_to_user=True,
            missing_outputs=[],
            review_notes=[
                "Deterministic structural completeness passed; non-safety LLM review concerns were deferred to quality review.",
                *normalized.review_notes[:7],
            ],
            assistant_summary="Quick Plan passed the private structural completeness review.",
        )
    return normalized


def _review_structural_completeness(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
) -> QuickPlanReviewResult | None:
    missing: list[QuickPlanMissingOutput] = []
    notes: list[str] = []
    items = attempt.draft.timeline_preview
    allowed_modules = set(dossier.readiness.allowed_modules)

    if "flights" in allowed_modules and not (
        _has_outbound_flight_representation(items)
        and _has_return_flight_representation(items)
    ):
        missing.append("flights")
        notes.append(
            "Flights are in scope but the candidate is missing visible outbound or return flight logistics."
        )

    if "hotels" in allowed_modules and not _has_stay_representation(items):
        missing.append("stay")
        notes.append("Hotels are in scope but the candidate has no visible stay row or stay-area anchor.")

    if "activities" in allowed_modules and not _has_activity_representation(items):
        missing.append("activities")
        notes.append("Activities are in scope but the candidate has no visible activity or event rows.")

    if not _has_expected_day_coverage(
        items,
        configuration=configuration,
        activities_in_scope="activities" in allowed_modules,
    ):
        missing.append("day_coverage")
        notes.append(
            "The candidate does not cover every expected trip day with meaningful visible itinerary content."
        )

    untimed_titles = [
        item.title
        for item in items
        if not (item.start_at and item.end_at and item.end_at > item.start_at)
    ]
    if untimed_titles:
        missing.append("timing")
        notes.append(
            "Visible rows are missing usable start/end times: "
            + ", ".join(untimed_titles[:3])
        )

    missing = list(dict.fromkeys(missing))
    if not missing:
        return None

    return QuickPlanReviewResult(
        status="incomplete",
        show_to_user=False,
        missing_outputs=missing,
        review_notes=notes,
        assistant_summary=_build_incomplete_summary(missing),
    )


def _run_structured_llm_review(
    *,
    dossier: QuickPlanDossier,
    attempt: QuickPlanGenerationAttempt,
    configuration: TripConfiguration,
) -> QuickPlanReviewResult | None:
    prompt = f"""
You are Wandrix's private Quick Plan completeness reviewer.

Review the generated Quick Plan candidate before it can update the live trip board.

Return complete only when all required scope is represented and the user can safely see the draft.

Checks:
- If flights are in scope, visible itinerary rows must represent outbound/return flight logistics or honest flight planning blocks.
- If hotels are in scope, visible itinerary rows must represent a hotel, stay, or stay-area anchor.
- If activities are in scope, visible itinerary rows must include concrete activities or events.
- Expected trip days must be covered.
- Every visible itinerary row must have usable start_at and end_at timing.
- Generated copy must not imply estimated timing, missing provider facts, prices, reservations, opening hours, or availability are confirmed facts.
- Do not judge polish or taste. This is a completeness and safety gate only.

Trip configuration:
{configuration.model_dump(mode="json")}

Quick Plan dossier:
{dossier.model_dump(mode="json")}

Generation attempt:
{attempt.model_dump(mode="json")}
""".strip()

    try:
        try:
            model = create_quick_plan_chat_model(
                temperature=0.0,
                timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
                max_retries=1,
            )
        except TypeError:
            model = create_quick_plan_chat_model(temperature=0.0)
        structured_model = model.with_structured_output(
            QuickPlanReviewResult,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                (
                    "system",
                    "Privately review Quick Plan completeness and safety. Do not repair or rewrite the itinerary.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning("Quick Plan review returned no usable output.", exc_info=True)
        return None


def _normalize_review_result(result: QuickPlanReviewResult) -> QuickPlanReviewResult:
    if result.status == "complete":
        return result.model_copy(
            update={
                "show_to_user": True,
                "missing_outputs": [],
                "assistant_summary": result.assistant_summary
                or "Quick Plan passed the private completeness review.",
            }
        )
    return result.model_copy(
        update={
            "show_to_user": False,
            "assistant_summary": result.assistant_summary
            or _build_incomplete_summary(result.missing_outputs),
        }
    )


def _has_hard_safety_or_timing_failure(result: QuickPlanReviewResult) -> bool:
    hard_missing = {"timing", "provider_fact_safety"}
    return any(output in hard_missing for output in result.missing_outputs)


def _has_outbound_flight_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(
        _is_flight_like(item)
        and not _contains_any(item, {"return", "flight home"})
        for item in items
    )


def _has_return_flight_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(
        _is_flight_like(item)
        and _contains_any(item, {"return", "departure", "flight home"})
        for item in items
    )


def _is_flight_like(item: ProposedTimelineItem) -> bool:
    return (
        item.type == "flight"
        or item.source_module == "flights"
        or _contains_any(item, {"flight", "airport"})
    )


def _has_stay_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(
        item.type == "hotel"
        or item.source_module == "hotels"
        or _contains_any(item, {"hotel", "stay", "check-in", "check in", "base"})
        for item in items
    )


def _has_activity_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(item.type in {"activity", "event"} for item in items)


def _contains_any(item: ProposedTimelineItem, needles: set[str]) -> bool:
    haystack = " ".join(
        [
            item.title,
            item.summary or "",
            item.location_label or "",
            " ".join(item.details),
        ]
    ).lower()
    return any(needle in haystack for needle in needles)


def _has_expected_day_coverage(
    items: list[ProposedTimelineItem],
    *,
    configuration: TripConfiguration,
    activities_in_scope: bool = False,
) -> bool:
    expected_days = _expected_trip_days(configuration)
    if expected_days is None:
        return bool(items)

    covered_days = _covered_day_indexes(
        items,
        start_date=configuration.start_date,
        activities_in_scope=activities_in_scope,
        expected_days=expected_days,
    )
    return set(range(1, expected_days + 1)).issubset(covered_days)


def _expected_trip_days(configuration: TripConfiguration) -> int | None:
    if configuration.start_date and configuration.end_date:
        days = (configuration.end_date - configuration.start_date).days + 1
        return max(days, 1)
    return None


def _covered_day_indexes(
    items: list[ProposedTimelineItem],
    *,
    start_date: date | None,
    activities_in_scope: bool = False,
    expected_days: int | None = None,
) -> set[int]:
    covered: set[int] = set()
    for item in items:
        if not _counts_for_day_coverage(
            item,
            activities_in_scope=activities_in_scope,
            expected_days=expected_days,
        ):
            continue
        if item.day_label:
            match = re.search(r"\bday\s*(\d+)\b", item.day_label, flags=re.IGNORECASE)
            if match:
                covered.add(int(match.group(1)))
                continue
        if start_date and item.start_at:
            covered.add((item.start_at.date() - start_date).days + 1)
    return {day for day in covered if day > 0}


def _counts_for_day_coverage(
    item: ProposedTimelineItem,
    *,
    activities_in_scope: bool,
    expected_days: int | None,
) -> bool:
    if item.type in {"note", "weather"}:
        return False
    if not activities_in_scope or expected_days is None:
        return True
    day_number = _day_number(item.day_label)
    if day_number is None or day_number in {1, expected_days}:
        return True
    return item.type in {"activity", "event"} or item.source_module == "activities"


def _day_number(day_label: str | None) -> int | None:
    if not day_label:
        return None
    match = re.search(r"\bday\s*(\d+)\b", day_label, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _build_incomplete_summary(missing: list[str]) -> str:
    if not missing:
        return (
            "I generated a Quick Plan candidate, but the private review did not mark it complete, "
            "so I kept the current board unchanged."
        )
    readable = ", ".join(missing)
    return (
        f"I generated a Quick Plan candidate, but the private review found missing {readable}, "
        "so I kept the current board unchanged instead of showing a partial draft."
    )
