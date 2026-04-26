from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan import generate_quick_plan_draft
from app.graph.planner.quick_plan_day_architecture import (
    QuickPlanDayArchitecture,
    build_quick_plan_day_architecture,
)
from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_enrichment import build_quick_plan_module_outputs
from app.graph.planner.quick_plan_provider_brief import (
    QuickPlanProviderBrief,
    build_quick_plan_provider_brief,
)
from app.graph.planner.quick_plan_quality_models import QuickPlanQualityReviewResult
from app.graph.planner.quick_plan_scheduler import schedule_quick_plan_draft
from app.graph.planner.quick_plan_selection import (
    build_quick_plan_timeline_module_outputs,
    prioritize_quick_plan_module_outputs,
)
from app.graph.planner.quick_plan_strategy import (
    QuickPlanStrategyBrief,
    build_quick_plan_strategy_brief,
)
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import (
    TimelineTimingSource,
    TripConfiguration,
    TripModuleOutputs,
)


QuickPlanGenerationStatus = Literal["generated", "empty"]
QuickPlanRepairGoal = Literal[
    "completeness",
    "quality",
    "completeness_and_quality",
]
QUICK_PLAN_TIMELINE_MAX_ITEMS = 16


class QuickPlanGenerationAttempt(BaseModel):
    status: QuickPlanGenerationStatus
    module_outputs: TripModuleOutputs = Field(default_factory=TripModuleOutputs)
    timeline_module_outputs: TripModuleOutputs = Field(default_factory=TripModuleOutputs)
    draft: QuickPlanDraft = Field(default_factory=QuickPlanDraft)
    strategy_brief: QuickPlanStrategyBrief | None = None
    provider_brief: QuickPlanProviderBrief | None = None
    day_architecture: QuickPlanDayArchitecture | None = None
    assumptions: list[dict[str, Any]] = Field(default_factory=list)


class QuickPlanRepairContext(BaseModel):
    previous_attempt: QuickPlanGenerationAttempt
    original_attempt: QuickPlanGenerationAttempt | None = None
    previous_repair_attempts: list[QuickPlanGenerationAttempt] = Field(
        default_factory=list
    )
    failed_review: dict[str, Any] = Field(default_factory=dict)
    failed_completeness_review: dict[str, Any] | None = None
    failed_quality_review: dict[str, Any] | None = None
    quality_issues: list[dict[str, Any]] = Field(default_factory=list)
    quality_scores: dict[str, Any] = Field(default_factory=dict)
    unresolved_quality_dimensions: list[str] = Field(default_factory=list)
    repair_goal: QuickPlanRepairGoal = "completeness"
    repair_attempt_index: int = 1
    max_repair_attempts: int = 1
    final_repair_chance: bool = False
    missing_outputs: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)

    def prompt_payload(self) -> dict[str, Any]:
        return {
            "repair_goal": self.repair_goal,
            "repair_attempt_index": self.repair_attempt_index,
            "max_repair_attempts": self.max_repair_attempts,
            "final_repair_chance": self.final_repair_chance,
            "missing_outputs": self.missing_outputs,
            "review_notes": self.review_notes,
            "failed_review": self.failed_review,
            "failed_completeness_review": self.failed_completeness_review,
            "failed_quality_review": self.failed_quality_review,
            "quality_issues": self.quality_issues,
            "quality_scores": self.quality_scores,
            "unresolved_quality_dimensions": self.unresolved_quality_dimensions,
            "repair_instructions": _quality_repair_instructions(
                self.failed_quality_review
            ),
            "previous_strategy_brief": self.previous_attempt.strategy_brief.model_dump(
                mode="json"
            )
            if self.previous_attempt.strategy_brief
            else None,
            "previous_provider_brief": self.previous_attempt.provider_brief.model_dump(
                mode="json"
            )
            if self.previous_attempt.provider_brief
            else None,
            "previous_day_architecture": self.previous_attempt.day_architecture.model_dump(
                mode="json"
            )
            if self.previous_attempt.day_architecture
            else None,
            "original_attempt": self.original_attempt.model_dump(mode="json")
            if self.original_attempt
            else None,
            "previous_repair_attempts": [
                attempt.model_dump(mode="json")
                for attempt in self.previous_repair_attempts
            ],
            "previous_attempt": self.previous_attempt.model_dump(mode="json"),
        }


class AcceptedQuickPlan(BaseModel):
    generation_attempt: QuickPlanGenerationAttempt
    final_completeness_review: dict[str, Any]
    final_quality_review: dict[str, Any]
    repair_metadata: dict[str, Any] = Field(default_factory=dict)
    intelligence_metadata: dict[str, Any] = Field(default_factory=dict)
    review_result: dict[str, Any]
    quality_review_result: dict[str, Any] = Field(default_factory=dict)
    module_outputs: TripModuleOutputs
    timeline_module_outputs: TripModuleOutputs
    timeline_preview: list[ProposedTimelineItem] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    review_metadata: dict[str, Any] = Field(default_factory=dict)


def accept_quick_plan_candidate(
    *,
    attempt: QuickPlanGenerationAttempt,
    review_result: Any,
    quality_review_result: QuickPlanQualityReviewResult | None = None,
    repair_metadata: dict[str, Any] | None = None,
) -> AcceptedQuickPlan | None:
    if not (
        review_result
        and review_result.status == "complete"
        and review_result.show_to_user
        and quality_review_result
        and not is_quick_plan_quality_blocking(quality_review_result)
        and attempt.draft.timeline_preview
    ):
        return None
    quality_blocking = is_quick_plan_quality_blocking(quality_review_result)
    merged_repair_metadata = dict(repair_metadata or {})
    merged_repair_metadata["quality_blocking"] = quality_blocking
    return AcceptedQuickPlan(
        generation_attempt=attempt,
        final_completeness_review=review_result.model_dump(mode="json"),
        final_quality_review=quality_review_result.model_dump(mode="json"),
        repair_metadata=merged_repair_metadata,
        intelligence_metadata=_build_intelligence_metadata(attempt),
        review_result=review_result.model_dump(mode="json"),
        quality_review_result=quality_review_result.model_dump(mode="json"),
        module_outputs=attempt.module_outputs,
        timeline_module_outputs=attempt.timeline_module_outputs,
        timeline_preview=attempt.draft.timeline_preview,
        assumptions=attempt.assumptions,
        review_metadata=merged_repair_metadata,
    )


def is_quick_plan_quality_blocking(
    quality_review_result: QuickPlanQualityReviewResult | None,
) -> bool:
    if quality_review_result is None:
        return True
    if quality_review_result.status == "pass" and quality_review_result.show_to_user:
        return False

    hard_blocking_dimensions = {"fact_safety", "logistics_realism"}
    for issue in quality_review_result.issues:
        if (
            issue.dimension in hard_blocking_dimensions
            and issue.severity == "high"
        ):
            return True
        if issue.severity == "high" and issue.dimension in {
            "geography",
            "pacing",
            "local_specificity",
            "user_fit",
        }:
            return True

    scorecard = quality_review_result.scorecard
    if min(
        scorecard.geography,
        scorecard.pacing,
        scorecard.local_specificity,
        scorecard.user_fit,
    ) <= 3:
        return True
    hard_dimension_issues = {
        issue.dimension
        for issue in quality_review_result.issues
        if issue.dimension in hard_blocking_dimensions
    }
    if "fact_safety" in hard_dimension_issues and scorecard.fact_safety <= 3:
        return True
    if (
        "logistics_realism" in hard_dimension_issues
        and scorecard.logistics_realism <= 3
    ):
        return True
    return bool(
        not quality_review_result.issues
        and quality_review_result.status == "fail"
        and (scorecard.fact_safety <= 3 or scorecard.logistics_realism <= 3)
    )


def _build_intelligence_metadata(
    attempt: QuickPlanGenerationAttempt,
) -> dict[str, Any]:
    return {
        "strategy_brief": attempt.strategy_brief.model_dump(mode="json")
        if attempt.strategy_brief
        else None,
        "provider_brief": attempt.provider_brief.model_dump(mode="json")
        if attempt.provider_brief
        else None,
        "day_architecture": attempt.day_architecture.model_dump(mode="json")
        if attempt.day_architecture
        else None,
    }


def run_quick_plan_generation(
    *,
    dossier: QuickPlanDossier,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    trip_title: str,
    conversation: TripConversationState,
    repair_context: QuickPlanRepairContext | None = None,
) -> QuickPlanGenerationAttempt:
    repair_payload = repair_context.prompt_payload() if repair_context else None
    module_outputs = build_quick_plan_module_outputs(
        configuration=configuration,
        previous_configuration=previous_configuration,
        existing_module_outputs=existing_module_outputs,
        allowed_modules=set(dossier.readiness.allowed_modules),
    )
    module_outputs = prioritize_quick_plan_module_outputs(
        configuration=configuration,
        module_outputs=module_outputs,
    )
    timeline_module_outputs = build_quick_plan_timeline_module_outputs(module_outputs)
    strategy_brief = build_quick_plan_strategy_brief(
        dossier=dossier,
        configuration=configuration,
        module_outputs=timeline_module_outputs,
        conversation=conversation,
        repair_context=repair_payload,
    )
    if strategy_brief is None:
        return _empty_generation_attempt(
            module_outputs=module_outputs,
            timeline_module_outputs=timeline_module_outputs,
            assumptions=dossier.assumptions,
        )

    provider_brief = build_quick_plan_provider_brief(
        dossier=dossier,
        configuration=configuration,
        module_outputs=timeline_module_outputs,
        strategy_brief=strategy_brief,
        repair_context=repair_payload,
    )
    if provider_brief is None:
        return _empty_generation_attempt(
            module_outputs=module_outputs,
            timeline_module_outputs=timeline_module_outputs,
            strategy_brief=strategy_brief,
            assumptions=dossier.assumptions,
        )

    day_architecture = build_quick_plan_day_architecture(
        dossier=dossier,
        configuration=configuration,
        strategy_brief=strategy_brief,
        provider_brief=provider_brief,
        repair_context=repair_payload,
    )
    if day_architecture is None:
        return _empty_generation_attempt(
            module_outputs=module_outputs,
            timeline_module_outputs=timeline_module_outputs,
            strategy_brief=strategy_brief,
            provider_brief=provider_brief,
            assumptions=dossier.assumptions,
        )

    draft = generate_quick_plan_draft(
        title=trip_title,
        configuration=configuration,
        module_outputs=timeline_module_outputs,
        conversation=conversation,
        dossier=dossier,
        strategy_brief=strategy_brief,
        provider_brief=provider_brief,
        day_architecture=day_architecture,
        repair_context=repair_payload,
    )
    draft = schedule_quick_plan_draft(
        title=trip_title,
        configuration=configuration,
        module_outputs=timeline_module_outputs,
        conversation=conversation,
        draft=draft,
        dossier=dossier,
        repair_context=repair_payload,
    )
    draft = _ensure_required_quick_plan_rows(
        draft,
        configuration=configuration,
        module_outputs=timeline_module_outputs,
        allowed_modules=dossier.readiness.allowed_modules,
        day_architecture=day_architecture,
    )
    return QuickPlanGenerationAttempt(
        status="generated" if draft.timeline_preview else "empty",
        module_outputs=module_outputs,
        timeline_module_outputs=timeline_module_outputs,
        draft=draft,
        strategy_brief=strategy_brief,
        provider_brief=provider_brief,
        day_architecture=day_architecture,
        assumptions=dossier.assumptions,
    )


def _ensure_required_quick_plan_rows(
    draft: QuickPlanDraft,
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    allowed_modules: list[str],
    day_architecture: QuickPlanDayArchitecture | None = None,
) -> QuickPlanDraft:
    items = list(draft.timeline_preview)
    if not items:
        return draft

    allowed_module_set = set(allowed_modules)
    if "flights" in allowed_module_set and not _has_outbound_flight_representation(items):
        items.extend(
            _build_flight_anchors(
                configuration=configuration,
                module_outputs=module_outputs,
                directions=["outbound"],
            )
        )
    if "flights" in allowed_module_set and not _has_return_flight_representation(items):
        items.extend(
            _build_flight_anchors(
                configuration=configuration,
                module_outputs=module_outputs,
                directions=["return"],
            )
        )
    if "hotels" in allowed_module_set and not _has_stay_representation(items):
        items.append(
            _build_stay_anchor(
                configuration=configuration,
                module_outputs=module_outputs,
            )
        )
    items = _ensure_generation_day_coverage(
        items,
        configuration=configuration,
        activities_in_scope="activities" in allowed_module_set,
        day_architecture=day_architecture,
    )
    if "activities" in allowed_module_set and not _has_activity_representation(items):
        items.append(
            _build_activity_anchor(
                configuration=configuration,
                day_index=2,
                day_plan=_day_plan_for_index(day_architecture, 2),
            )
        )
    if "weather" in allowed_module_set and not _has_weather_representation(items):
        items.append(_build_weather_anchor(configuration=configuration))

    items = _sort_timeline_items(items)
    items = _cap_generation_items(
        items,
        configuration=configuration,
        max_items=QUICK_PLAN_TIMELINE_MAX_ITEMS,
    )
    return QuickPlanDraft(
        board_summary=draft.board_summary,
        timeline_preview=items,
    )


def _build_flight_anchors(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    directions: list[str] | None = None,
) -> list[ProposedTimelineItem]:
    anchors: list[ProposedTimelineItem] = []
    requested_directions = set(directions or ["outbound", "return"])
    outbound = next(
        (flight for flight in module_outputs.flights if flight.direction == "outbound"),
        None,
    )
    returning = next(
        (flight for flight in module_outputs.flights if flight.direction == "return"),
        None,
    )
    destination = configuration.to_location or "the destination"
    origin = configuration.from_location or "the origin"

    outbound_start = outbound.departure_time if outbound and outbound.departure_time else _datetime_for_day(
        configuration=configuration,
        day_index=1,
        at=time(9, 0),
    )
    outbound_end = (
        outbound.arrival_time
        if outbound and outbound.arrival_time
        else outbound_start + timedelta(hours=12)
    )
    outbound_timing_source: TimelineTimingSource = (
        "provider_exact"
        if outbound and outbound.departure_time and outbound.arrival_time
        else "planner_estimate"
    )
    if "outbound" in requested_directions:
        anchors.append(
            ProposedTimelineItem(
                type="flight",
                title=f"Outbound flight planning block: {origin} to {destination}",
                day_label="Day 1",
                start_at=outbound_start,
                end_at=outbound_end,
                timing_source=outbound_timing_source,
                timing_note="Planner-estimated flight window until provider flight times are available."
                if outbound_timing_source == "planner_estimate"
                else None,
                location_label=f"{origin} to {destination}",
                details=[
                    "Use this as an honest flight logistics anchor; exact airline, fare, and live availability still need provider confirmation."
                ],
                source_module="flights",
            )
        )

    expected_days = _expected_trip_days(configuration) or 1
    return_start = returning.departure_time if returning and returning.departure_time else _datetime_for_day(
        configuration=configuration,
        day_index=expected_days,
        at=time(16, 0),
    )
    return_end = (
        returning.arrival_time
        if returning and returning.arrival_time
        else return_start + timedelta(hours=12)
    )
    return_timing_source: TimelineTimingSource = (
        "provider_exact"
        if returning and returning.departure_time and returning.arrival_time
        else "planner_estimate"
    )
    if "return" in requested_directions:
        anchors.append(
            ProposedTimelineItem(
                type="flight",
                title=f"Return flight planning block: {destination} to {origin}",
                day_label=f"Day {expected_days}",
                start_at=return_start,
                end_at=return_end,
                timing_source=return_timing_source,
                timing_note="Planner-estimated flight window until provider flight times are available."
                if return_timing_source == "planner_estimate"
                else None,
                location_label=f"{destination} to {origin}",
                details=[
                    "Keep the final day light around airport transfer and return-flight timing."
                ],
                source_module="flights",
            )
        )
    return anchors


def _build_stay_anchor(
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> ProposedTimelineItem:
    hotel = module_outputs.hotels[0] if module_outputs.hotels else None
    destination = configuration.to_location or "the destination"
    start_at = _datetime_for_day(configuration=configuration, day_index=1, at=time(15, 30))
    end_at = start_at + timedelta(hours=1)
    hotel_title = hotel.hotel_name if hotel and hotel.hotel_name else f"{destination} stay base"
    area = hotel.area if hotel and hotel.area else destination
    return ProposedTimelineItem(
        type="hotel",
        title=f"Stay anchor: {hotel_title}",
        day_label="Day 1",
        start_at=start_at,
        end_at=end_at,
        timing_source="planner_estimate",
        timing_note="Planner-estimated check-in/reset anchor for the accepted Quick Plan.",
        location_label=area,
        details=[
            "Use this as the stay/base anchor for routing the itinerary; exact room availability and booking status are not confirmed."
        ],
        source_module="hotels",
    )


def _ensure_generation_day_coverage(
    items: list[ProposedTimelineItem],
    *,
    configuration: TripConfiguration,
    activities_in_scope: bool,
    day_architecture: QuickPlanDayArchitecture | None = None,
) -> list[ProposedTimelineItem]:
    expected_days = _expected_trip_days(configuration)
    if expected_days is None or expected_days <= 0:
        return items

    covered = (
        _covered_activity_day_indexes(items, start_date=configuration.start_date)
        if activities_in_scope
        else _covered_day_indexes(items, start_date=configuration.start_date)
    )
    augmented = list(items)
    for day_index in range(1, expected_days + 1):
        if day_index in covered:
            continue
        augmented.append(
            _build_activity_anchor(
                configuration=configuration,
                day_index=day_index,
                item_type="activity" if activities_in_scope else "note",
                day_plan=_day_plan_for_index(day_architecture, day_index),
            )
        )
    return augmented


def _build_activity_anchor(
    *,
    configuration: TripConfiguration,
    day_index: int,
    item_type: str = "activity",
    day_plan: QuickPlanDayPlan | None = None,
) -> ProposedTimelineItem:
    destination = configuration.to_location or "the destination"
    start_at = _datetime_for_day(
        configuration=configuration,
        day_index=day_index,
        at=time(11, 0),
    )
    if day_plan is not None:
        details = [
            day_plan.food_culture_intent,
            *day_plan.logistics_anchors[:3],
            *[f"Avoid: {item}" for item in day_plan.must_avoid[:2]],
        ]
        return ProposedTimelineItem(
            type=item_type,
            title=day_plan.theme,
            day_label=f"Day {day_index}",
            start_at=start_at,
            end_at=start_at + timedelta(hours=3),
            timing_source="planner_estimate",
            timing_note="Planner-estimated coverage anchor based on the Quick Plan day architecture.",
            location_label=day_plan.geography_focus,
            summary=day_plan.pacing_target,
            details=[detail for detail in details if detail],
            source_module="activities" if item_type == "activity" else None,
        )
    themes = [
        f"{destination} arrival neighborhood food walk",
        f"{destination} market, lanes, and casual lunch block",
        f"{destination} heritage district and tea-culture block",
        f"{destination} craft, garden, and relaxed dinner block",
        f"Final {destination} morning culture and departure buffer",
    ]
    title = themes[min(max(day_index, 1), len(themes)) - 1]
    return ProposedTimelineItem(
        type=item_type,
        title=title,
        day_label=f"Day {day_index}",
        start_at=start_at,
        end_at=start_at + timedelta(hours=3),
        timing_source="planner_estimate",
        timing_note="Planner-estimated coverage anchor to keep the Quick Plan complete.",
        location_label=destination,
        details=[
            "Replace this with stronger live recommendations when provider activity details are available."
        ],
        source_module="activities" if item_type == "activity" else None,
    )


def _day_plan_for_index(
    day_architecture: QuickPlanDayArchitecture | None,
    day_index: int,
) -> QuickPlanDayPlan | None:
    if day_architecture is None:
        return None
    return next(
        (day for day in day_architecture.days if day.day_index == day_index),
        None,
    )


def _build_weather_anchor(
    *,
    configuration: TripConfiguration,
) -> ProposedTimelineItem:
    destination = configuration.to_location or "the destination"
    start_at = _datetime_for_day(configuration=configuration, day_index=2, at=time(8, 30))
    return ProposedTimelineItem(
        type="weather",
        title=f"{destination} weather and pacing check",
        day_label="Day 2",
        start_at=start_at,
        end_at=start_at + timedelta(minutes=30),
        timing_source="planner_estimate",
        timing_note="Planner-estimated weather check because live forecast data may be unavailable for these dates.",
        location_label=destination,
        details=[
            "Use weather as a pacing signal only; do not treat unavailable forecast details as confirmed."
        ],
        source_module="weather",
    )


def _has_outbound_flight_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(
        (item.type == "flight" or item.source_module == "flights")
        and not _contains_any(item, {"return", "departure buffer"})
        for item in items
    )


def _has_return_flight_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(
        (item.type == "flight" or item.source_module == "flights")
        and _contains_any(item, {"return", "departure", "flight home"})
        for item in items
    )


def _has_stay_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(item.type == "hotel" or item.source_module == "hotels" for item in items)


def _has_activity_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(
        item.type in {"activity", "event"} or item.source_module == "activities"
        for item in items
    )


def _has_weather_representation(items: list[ProposedTimelineItem]) -> bool:
    return any(item.type == "weather" or item.source_module == "weather" for item in items)


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


def _expected_trip_days(configuration: TripConfiguration) -> int | None:
    if configuration.start_date and configuration.end_date:
        return max((configuration.end_date - configuration.start_date).days + 1, 1)
    return None


def _covered_day_indexes(
    items: list[ProposedTimelineItem],
    *,
    start_date: date | None,
) -> set[int]:
    covered: set[int] = set()
    for item in items:
        if item.day_label:
            match = re.search(r"\bday\s*(\d+)\b", item.day_label, flags=re.IGNORECASE)
            if match:
                covered.add(int(match.group(1)))
                continue
        if start_date and item.start_at:
            covered.add((item.start_at.date() - start_date).days + 1)
    return {day for day in covered if day > 0}


def _covered_activity_day_indexes(
    items: list[ProposedTimelineItem],
    *,
    start_date: date | None,
) -> set[int]:
    activity_items = [
        item
        for item in items
        if item.type in {"activity", "event"} or item.source_module == "activities"
    ]
    return _covered_day_indexes(activity_items, start_date=start_date)


def _datetime_for_day(
    *,
    configuration: TripConfiguration,
    day_index: int,
    at: time,
) -> datetime:
    start_date = configuration.start_date or date.today()
    return datetime.combine(start_date + timedelta(days=day_index - 1), at)


def _sort_timeline_items(items: list[ProposedTimelineItem]) -> list[ProposedTimelineItem]:
    return sorted(
        items,
        key=lambda item: (
            _day_sort_value(item.day_label),
            item.start_at.isoformat() if item.start_at else "9999-12-31T23:59:59",
            item.title.lower(),
        ),
    )


def _day_sort_value(day_label: str | None) -> int:
    if not day_label:
        return 999
    match = re.search(r"\bday\s*(\d+)\b", day_label, flags=re.IGNORECASE)
    if not match:
        return 999
    return int(match.group(1))


def _cap_generation_items(
    items: list[ProposedTimelineItem],
    *,
    configuration: TripConfiguration,
    max_items: int,
) -> list[ProposedTimelineItem]:
    if len(items) <= max_items:
        return items
    expected_days = _expected_trip_days(configuration)
    if expected_days is None or expected_days <= 0 or expected_days > max_items:
        return items[:max_items]

    selected: list[ProposedTimelineItem] = []
    selected_ids: set[int] = set()

    def add_item(item: ProposedTimelineItem | None) -> None:
        if item is None or len(selected) >= max_items or id(item) in selected_ids:
            return
        selected.append(item)
        selected_ids.add(id(item))

    for flight_item in [
        item
        for item in items
        if item.type == "flight" or item.source_module == "flights"
    ][:2]:
        add_item(flight_item)

    add_item(
        next(
            (
                item
                for item in items
                if item.type == "hotel" or item.source_module == "hotels"
            ),
            None,
        )
    )

    for day_index in range(1, expected_days + 1):
        day_items = [
            item
            for item in items
            if _day_sort_value(item.day_label) == day_index
            and id(item) not in selected_ids
        ]
        day_item = next(
            (
                item
                for item in day_items
                if item.type in {"activity", "event"} or item.source_module == "activities"
            ),
            None,
        )
        add_item(day_item or (day_items[0] if day_items else None))

    for item in items:
        if len(selected) >= max_items:
            break
        if id(item) in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(id(item))

    return _sort_timeline_items(selected)


def _empty_generation_attempt(
    *,
    module_outputs: TripModuleOutputs,
    timeline_module_outputs: TripModuleOutputs,
    strategy_brief: QuickPlanStrategyBrief | None = None,
    provider_brief: QuickPlanProviderBrief | None = None,
    day_architecture: QuickPlanDayArchitecture | None = None,
    assumptions: list[dict[str, Any]] | None = None,
) -> QuickPlanGenerationAttempt:
    return QuickPlanGenerationAttempt(
        status="empty",
        module_outputs=module_outputs,
        timeline_module_outputs=timeline_module_outputs,
        strategy_brief=strategy_brief,
        provider_brief=provider_brief,
        day_architecture=day_architecture,
        assumptions=assumptions or [],
    )


def build_quick_plan_repair_context(
    *,
    previous_attempt: QuickPlanGenerationAttempt,
    failed_review: Any,
) -> QuickPlanRepairContext:
    return build_quick_plan_completeness_repair_context(
        previous_attempt=previous_attempt,
        failed_completeness_review=failed_review,
    )


def build_quick_plan_completeness_repair_context(
    *,
    previous_attempt: QuickPlanGenerationAttempt,
    failed_completeness_review: Any,
    original_attempt: QuickPlanGenerationAttempt | None = None,
    previous_repair_attempts: list[QuickPlanGenerationAttempt] | None = None,
    repair_attempt_index: int = 1,
    max_repair_attempts: int = 1,
    final_repair_chance: bool = False,
) -> QuickPlanRepairContext:
    review_payload = (
        failed_completeness_review.model_dump(mode="json")
        if hasattr(failed_completeness_review, "model_dump")
        else dict(failed_completeness_review or {})
    )
    return QuickPlanRepairContext(
        previous_attempt=previous_attempt,
        original_attempt=original_attempt,
        previous_repair_attempts=previous_repair_attempts or [],
        failed_review=review_payload,
        failed_completeness_review=review_payload,
        missing_outputs=list(review_payload.get("missing_outputs") or []),
        review_notes=list(review_payload.get("review_notes") or []),
        repair_goal="completeness",
        repair_attempt_index=repair_attempt_index,
        max_repair_attempts=max_repair_attempts,
        final_repair_chance=final_repair_chance,
    )


def build_quick_plan_quality_repair_context(
    *,
    previous_attempt: QuickPlanGenerationAttempt,
    failed_quality_review: Any,
    completeness_review: Any | None = None,
    original_attempt: QuickPlanGenerationAttempt | None = None,
    previous_repair_attempts: list[QuickPlanGenerationAttempt] | None = None,
    repair_attempt_index: int = 1,
    max_repair_attempts: int = 1,
    final_repair_chance: bool = False,
) -> QuickPlanRepairContext:
    quality_payload = (
        failed_quality_review.model_dump(mode="json")
        if hasattr(failed_quality_review, "model_dump")
        else dict(failed_quality_review or {})
    )
    completeness_payload = (
        completeness_review.model_dump(mode="json")
        if hasattr(completeness_review, "model_dump")
        else dict(completeness_review or {})
        if completeness_review
        else None
    )
    quality_issues = list(quality_payload.get("issues") or [])
    quality_scores = dict(quality_payload.get("scorecard") or {})
    unresolved_dimensions = _unresolved_quality_dimensions(
        quality_issues=quality_issues,
        quality_scores=quality_scores,
    )
    review_notes = list(quality_payload.get("review_notes") or [])
    review_notes.extend(_quality_repair_instructions(quality_payload))
    return QuickPlanRepairContext(
        previous_attempt=previous_attempt,
        original_attempt=original_attempt,
        previous_repair_attempts=previous_repair_attempts or [],
        failed_review=quality_payload,
        failed_completeness_review=completeness_payload,
        failed_quality_review=quality_payload,
        quality_issues=quality_issues,
        quality_scores=quality_scores,
        unresolved_quality_dimensions=unresolved_dimensions,
        review_notes=list(dict.fromkeys(review_notes)),
        repair_goal=(
            "completeness_and_quality"
            if completeness_payload
            and completeness_payload.get("status") != "complete"
            else "quality"
        ),
        repair_attempt_index=repair_attempt_index,
        max_repair_attempts=max_repair_attempts,
        final_repair_chance=final_repair_chance,
    )


def run_quick_plan_repair(
    *,
    dossier: QuickPlanDossier,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    trip_title: str,
    conversation: TripConversationState,
    repair_context: QuickPlanRepairContext,
) -> QuickPlanGenerationAttempt:
    return run_quick_plan_generation(
        dossier=dossier,
        configuration=configuration,
        previous_configuration=previous_configuration,
        existing_module_outputs=existing_module_outputs,
        trip_title=trip_title,
        conversation=conversation,
        repair_context=repair_context,
    )


def _quality_repair_instructions(
    failed_quality_review: dict[str, Any] | None,
) -> list[str]:
    if not failed_quality_review:
        return []
    instructions = list(failed_quality_review.get("repair_instructions") or [])
    for issue in failed_quality_review.get("issues") or []:
        instruction = issue.get("repair_instruction")
        if instruction:
            instructions.append(instruction)
    return list(dict.fromkeys(instructions))


def _unresolved_quality_dimensions(
    *,
    quality_issues: list[dict[str, Any]],
    quality_scores: dict[str, Any],
) -> list[str]:
    dimensions = [
        issue.get("dimension")
        for issue in quality_issues
        if issue.get("dimension")
    ]
    dimensions.extend(
        dimension
        for dimension, score in quality_scores.items()
        if isinstance(score, int | float) and score < 7
    )
    return list(dict.fromkeys(str(dimension) for dimension in dimensions))
