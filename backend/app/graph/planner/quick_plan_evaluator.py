from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.trip_draft import TripDraft
from app.schemas.trip_planning import PlanningModuleKey, TimelineItem


QuickPlanEvaluationSeverity = Literal["error", "warning", "info"]


class QuickPlanEvaluationFinding(BaseModel):
    code: str
    severity: QuickPlanEvaluationSeverity = "error"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    @property
    def check(self) -> str:
        return self.code


class QuickPlanEvaluationCase(BaseModel):
    id: str
    category: str
    prompt: str
    expected_modules: list[PlanningModuleKey] = Field(default_factory=list)
    excluded_modules: list[PlanningModuleKey] = Field(default_factory=list)
    expected_days: int | None = None
    require_acceptance: bool = True
    require_budget_when_accepted: bool = True
    require_assumptions_or_exclusions: bool = True
    notes: str | None = None
    qualitative_hooks: dict[str, Any] = Field(default_factory=dict)


class QuickPlanEvaluationResult(BaseModel):
    case_id: str
    passed: bool
    accepted: bool
    accepted_modules: list[PlanningModuleKey] = Field(default_factory=list)
    review_status: str | None = None
    quality_status: str | None = None
    repair_count: int = 0
    final_visible: bool = False
    findings: list[QuickPlanEvaluationFinding] = Field(default_factory=list)

    def report_payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "accepted": self.accepted,
            "accepted_modules": self.accepted_modules,
            "review_status": self.review_status,
            "quality_status": self.quality_status,
            "repair_count": self.repair_count,
            "final_visible": self.final_visible,
            "findings": [
                finding.model_dump(mode="json") for finding in self.findings
            ],
        }


def evaluate_quick_plan_case(
    case: QuickPlanEvaluationCase,
    draft: TripDraft,
    *,
    observability: dict[str, Any] | None = None,
) -> QuickPlanEvaluationResult:
    finalization = draft.conversation.quick_plan_finalization
    accepted = bool(finalization.accepted and finalization.brochure_eligible)
    findings: list[QuickPlanEvaluationFinding] = []

    if case.require_acceptance and not accepted:
        findings.append(
            QuickPlanEvaluationFinding(
                code="not_accepted",
                message="Quick Plan was expected to be accepted and brochure-eligible.",
                details={
                    "accepted": finalization.accepted,
                    "brochure_eligible": finalization.brochure_eligible,
                    "blocked_reasons": finalization.blocked_reasons,
                },
            )
        )

    _check_required_modules(case, draft, findings)
    _check_excluded_modules(case, draft.timeline, findings)
    _check_day_coverage(case, draft.timeline, findings)
    _check_visible_timing(draft.timeline, findings)
    _check_day_themes(case, finalization.intelligence_summary, findings)
    _check_assumptions_and_exclusions(case, finalization, findings)
    _check_budget_estimate(case, draft, accepted, findings)

    return QuickPlanEvaluationResult(
        case_id=case.id,
        passed=not any(finding.severity == "error" for finding in findings),
        accepted=accepted,
        accepted_modules=list(finalization.accepted_modules),
        review_status=finalization.review_status,
        quality_status=finalization.quality_status,
        repair_count=_repair_count(observability),
        final_visible=accepted,
        findings=findings,
    )


def build_quick_plan_evaluation_report(
    results: list[QuickPlanEvaluationResult],
) -> dict[str, Any]:
    passed = [result for result in results if result.passed]
    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(results) - len(passed),
        "cases": [result.report_payload() for result in results],
    }


def _check_required_modules(
    case: QuickPlanEvaluationCase,
    draft: TripDraft,
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    timeline = draft.timeline
    module_outputs = draft.module_outputs
    expected_modules = set(case.expected_modules)

    if "flights" in expected_modules:
        directions = {flight.direction for flight in module_outputs.flights}
        flight_rows = _rows_for_module(timeline, "flights")
        if not {"outbound", "return"}.issubset(directions) or len(flight_rows) < 2:
            findings.append(
                QuickPlanEvaluationFinding(
                    code="missing_flight_anchors",
                    message="Expected outbound and return flight anchors in module outputs and visible timeline.",
                    details={
                        "directions": sorted(directions),
                        "flight_row_count": len(flight_rows),
                    },
                )
            )

    if "hotels" in expected_modules:
        hotel_rows = _rows_for_module(timeline, "hotels")
        if not module_outputs.hotels or not hotel_rows:
            findings.append(
                QuickPlanEvaluationFinding(
                    code="missing_stay_anchor",
                    message="Expected a stay/hotel anchor in module outputs and visible timeline.",
                    details={
                        "hotel_count": len(module_outputs.hotels),
                        "hotel_row_count": len(hotel_rows),
                    },
                )
            )

    if "activities" in expected_modules:
        activity_rows = [
            item
            for item in timeline
            if item.source_module == "activities"
            or item.type in {"activity", "event", "meal"}
        ]
        if not module_outputs.activities and not activity_rows:
            findings.append(
                QuickPlanEvaluationFinding(
                    code="missing_activity_anchors",
                    message="Expected activity, food, or culture anchors in the structured plan.",
                )
            )

    if "weather" in expected_modules and not module_outputs.weather:
        findings.append(
            QuickPlanEvaluationFinding(
                code="missing_weather_context",
                message="Expected weather context in module outputs.",
            )
        )


def _check_excluded_modules(
    case: QuickPlanEvaluationCase,
    timeline: list[TimelineItem],
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    for module in case.excluded_modules:
        rows = _rows_for_module(timeline, module)
        if rows:
            findings.append(
                QuickPlanEvaluationFinding(
                    code="excluded_module_visible",
                    message=f"Module '{module}' was excluded but has visible timeline rows.",
                    details={
                        "module": module,
                        "row_ids": [row.id for row in rows],
                    },
                )
            )


def _check_day_coverage(
    case: QuickPlanEvaluationCase,
    timeline: list[TimelineItem],
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    if not case.expected_days:
        return
    represented_days = {
        day
        for item in timeline
        if item.type not in {"note", "weather"}
        for day in [_day_index(item.day_label)]
        if day is not None
    }
    expected_days = set(range(1, case.expected_days + 1))
    missing_days = sorted(expected_days - represented_days)
    if missing_days:
        findings.append(
            QuickPlanEvaluationFinding(
                code="missing_day_coverage",
                message="Expected every configured trip day to have visible itinerary coverage.",
                details={
                    "expected_days": sorted(expected_days),
                    "represented_days": sorted(represented_days),
                    "missing_days": missing_days,
                },
            )
        )


def _check_visible_timing(
    timeline: list[TimelineItem],
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    timed_types = {"flight", "transfer", "hotel", "activity", "event", "meal"}
    untimed = [
        item
        for item in timeline
        if item.type in timed_types
        and (item.start_at is None or item.end_at is None)
    ]
    reversed_timing = [
        item
        for item in timeline
        if item.start_at is not None
        and item.end_at is not None
        and item.end_at <= item.start_at
    ]
    if untimed or reversed_timing:
        findings.append(
            QuickPlanEvaluationFinding(
                code="visible_untimed_rows",
                message="Visible itinerary rows must have usable start and end timing.",
                details={
                    "untimed_row_ids": [item.id for item in untimed],
                    "invalid_order_row_ids": [item.id for item in reversed_timing],
                },
            )
        )


def _check_day_themes(
    case: QuickPlanEvaluationCase,
    intelligence_summary: dict[str, Any],
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    highlights = intelligence_summary.get("day_architecture_highlights") or []
    themes = [
        str(highlight.get("theme") or highlight.get("title") or "").strip().lower()
        for highlight in highlights
        if isinstance(highlight, dict)
    ]
    themes = [theme for theme in themes if theme]
    if len(themes) < 2:
        return
    expected_unique = min(case.expected_days or len(themes), len(themes))
    if len(set(themes)) < expected_unique:
        findings.append(
            QuickPlanEvaluationFinding(
                code="duplicative_day_themes",
                message="Accepted day-architecture themes should not be duplicated across trip days.",
                details={
                    "themes": themes,
                    "unique_theme_count": len(set(themes)),
                },
            )
        )


def _check_assumptions_and_exclusions(
    case: QuickPlanEvaluationCase,
    finalization: Any,
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    if not case.require_assumptions_or_exclusions:
        return
    intelligence_summary = finalization.intelligence_summary or {}
    assumption_notes = intelligence_summary.get("assumption_notes") or []
    assumptions = finalization.assumptions or []
    excluded_modules = intelligence_summary.get("excluded_modules") or []
    has_assumptions = bool(assumptions or assumption_notes)

    if case.excluded_modules:
        explicit_exclusions = {
            item.get("module")
            for item in excluded_modules
            if isinstance(item, dict) and item.get("module")
        }
        missing_exclusions = sorted(set(case.excluded_modules) - explicit_exclusions)
        if missing_exclusions:
            findings.append(
                QuickPlanEvaluationFinding(
                    code="missing_explicit_exclusions",
                    message="Expected explicitly excluded modules to be carried into accepted plan reasoning.",
                    details={"missing_exclusions": missing_exclusions},
                )
            )
        return

    if not has_assumptions:
        findings.append(
            QuickPlanEvaluationFinding(
                code="missing_assumptions",
                message="Expected accepted plan assumptions or working-date notes to be explicit.",
            )
        )


def _check_budget_estimate(
    case: QuickPlanEvaluationCase,
    draft: TripDraft,
    accepted: bool,
    findings: list[QuickPlanEvaluationFinding],
) -> None:
    if not accepted or not case.require_budget_when_accepted:
        return
    if not _has_priced_provider_context(draft) or draft.budget_estimate is not None:
        return
    findings.append(
        QuickPlanEvaluationFinding(
            code="missing_budget_estimate",
            message="Accepted Quick Plan has structured prices but no budget estimate.",
        )
    )


def _rows_for_module(
    timeline: list[TimelineItem],
    module: PlanningModuleKey,
) -> list[TimelineItem]:
    if module == "flights":
        return [
            item
            for item in timeline
            if item.source_module == "flights" or item.type == "flight"
        ]
    if module == "hotels":
        return [
            item
            for item in timeline
            if item.source_module == "hotels" or item.type == "hotel"
        ]
    if module == "activities":
        return [
            item
            for item in timeline
            if item.source_module == "activities"
            or item.type in {"activity", "event", "meal"}
        ]
    return [
        item
        for item in timeline
        if item.source_module == "weather" or item.type == "weather"
    ]


def _day_index(day_label: str | None) -> int | None:
    if not day_label:
        return None
    match = re.search(r"\bday\s+(\d+)\b", day_label, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _has_priced_provider_context(draft: TripDraft) -> bool:
    outputs = draft.module_outputs
    if any(
        flight.fare_amount is not None and flight.fare_currency
        for flight in outputs.flights
    ):
        return True
    if any(
        hotel.nightly_rate_amount is not None and hotel.nightly_rate_currency
        for hotel in outputs.hotels
    ):
        return True
    return any(activity.price_text for activity in outputs.activities)


def _repair_count(observability: dict[str, Any] | None) -> int:
    if not observability:
        return 0
    provider_activation = observability.get("provider_activation") or observability
    repair = provider_activation.get("quick_plan_repair") or {}
    count = repair.get("repair_attempt_count")
    if isinstance(count, int):
        return count
    attempts = repair.get("repair_attempts")
    if isinstance(attempts, list):
        return len(attempts)
    return 0
