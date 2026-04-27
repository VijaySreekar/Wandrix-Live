from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from app.graph.planner.date_resolution import build_advanced_date_options
from app.graph.planner.turn_models import (
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration


class QuickPlanWorkingDateDecision(BaseModel):
    start_date: date
    end_date: date
    confidence: Literal["medium", "high"] = "medium"
    rationale: str = Field(..., min_length=1, max_length=260)


def apply_quick_plan_working_dates(
    *,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    conversation: TripConversationState,
    today: date | None = None,
) -> tuple[TripConfiguration, TripTurnUpdate, QuickPlanWorkingDateDecision | None]:
    decision = resolve_quick_plan_working_dates(
        configuration=configuration,
        conversation=conversation,
        today=today,
    )
    if decision is None:
        return configuration, llm_update, None

    next_configuration = configuration.model_copy(deep=True)
    next_configuration.start_date = decision.start_date
    next_configuration.end_date = decision.end_date

    next_update = llm_update.model_copy(deep=True)
    next_update.start_date = decision.start_date
    next_update.end_date = decision.end_date
    next_update.last_turn_summary = (
        f"{next_update.last_turn_summary} {decision.rationale}"
        if next_update.last_turn_summary
        else decision.rationale
    )
    _mark_assistant_derived_date(next_update, "start_date", decision.confidence)
    _mark_assistant_derived_date(next_update, "end_date", decision.confidence)
    return next_configuration, next_update, decision


def resolve_quick_plan_working_dates(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    today: date | None = None,
) -> QuickPlanWorkingDateDecision | None:
    del conversation
    current_day = today or date.today()
    if configuration.start_date and configuration.end_date:
        return None
    if not (configuration.travel_window or configuration.trip_length):
        return None

    return _fallback_working_dates(configuration=configuration, today=current_day)


def _fallback_working_dates(
    *,
    configuration: TripConfiguration,
    today: date,
) -> QuickPlanWorkingDateDecision | None:
    options = _future_date_options(configuration, today=today)
    rolled_forward = False
    if not options:
        weekend_decision = _rolled_forward_weekend_dates(
            configuration=configuration,
            today=today,
        )
        if weekend_decision is not None:
            return weekend_decision
        next_configuration = configuration.model_copy(deep=True)
        next_configuration.travel_window = _next_month_window_label(configuration)
        options = _future_date_options(next_configuration, today=today)
        rolled_forward = bool(options)

    selected = None if rolled_forward else next(
        (option for option in options if option.recommended),
        None,
    )
    selected = selected or (options[0] if options else None)
    if selected is None:
        return None
    start_date = selected.start_date
    end_date = selected.end_date
    nights = max((selected.end_date - selected.start_date).days, 1)

    if configuration.start_date and not configuration.end_date:
        start_date = configuration.start_date
        end_date = start_date + timedelta(days=nights)
    elif configuration.end_date and not configuration.start_date:
        end_date = configuration.end_date
        start_date = end_date - timedelta(days=nights)

    decision = QuickPlanWorkingDateDecision(
        start_date=start_date,
        end_date=end_date,
        confidence="medium",
        rationale=_build_fallback_rationale(
            selected_title=selected.title,
            selected_reason=selected.reason,
            rolled_forward=rolled_forward,
            configuration=configuration,
        ),
    )
    decision = _repair_decision_trip_length(decision, configuration=configuration)
    if not _date_decision_is_usable(decision, today=today):
        return None
    return decision


def _future_date_options(configuration: TripConfiguration, *, today: date):
    return [
        option
        for option in build_advanced_date_options(configuration, today=today)
        if option.start_date > today and option.end_date > option.start_date
    ]


def _next_month_window_label(configuration: TripConfiguration) -> str:
    combined = (
        f"{configuration.travel_window or ''} {configuration.trip_length or ''}".lower()
    )
    if "weekend" in combined:
        return "next month weekend"
    return "next month"


def _rolled_forward_weekend_dates(
    *,
    configuration: TripConfiguration,
    today: date,
) -> QuickPlanWorkingDateDecision | None:
    combined = f"{configuration.travel_window or ''} {configuration.trip_length or ''}"
    if "weekend" not in combined.lower():
        return None

    days_until_friday = (4 - today.weekday()) % 7
    days_until_friday = days_until_friday or 7
    start_date = today + timedelta(days=days_until_friday)
    nights = _expected_nights_from_trip_length(configuration.trip_length)
    if nights is None:
        nights = 3 if "long weekend" in combined.lower() else 2
    end_date = start_date + timedelta(days=nights)
    title = f"{start_date.strftime('%a %d %b')} - {end_date.strftime('%a %d %b')}"
    decision = QuickPlanWorkingDateDecision(
        start_date=start_date,
        end_date=end_date,
        confidence="medium",
        rationale=(
            f"I chose {title} as an editable working window because "
            f"the rough timing did not leave a reliable future "
            f"{configuration.trip_length or 'weekend'} slot."
        ),
    )
    if not _date_decision_is_usable(decision, today=today):
        return None
    return decision


def _build_fallback_rationale(
    *,
    selected_title: str,
    selected_reason: str,
    rolled_forward: bool,
    configuration: TripConfiguration,
) -> str:
    if rolled_forward:
        length = configuration.trip_length or "the requested trip length"
        return (
            f"I chose {selected_title} as an editable working window because "
            f"the rough timing did not leave a reliable future {length} slot."
        )
    return (
        f"I chose {selected_title} as an editable working window because "
        f"{selected_reason.lower()}"
    )


def _repair_decision_trip_length(
    decision: QuickPlanWorkingDateDecision,
    *,
    configuration: TripConfiguration,
) -> QuickPlanWorkingDateDecision:
    expected_nights = _expected_nights_from_trip_length(configuration.trip_length)
    if expected_nights is None:
        return decision
    actual_nights = (decision.end_date - decision.start_date).days
    if actual_nights == expected_nights:
        return decision
    repaired_end = decision.start_date + timedelta(days=expected_nights)
    timing_label = configuration.trip_length or "the requested trip length"
    window_label = configuration.travel_window or "the requested timing"
    return decision.model_copy(
        update={
            "end_date": repaired_end,
            "confidence": decision.confidence,
            "rationale": (
                f"I set an editable {timing_label} window inside {window_label} "
                "so provider checks and the day-by-day rhythm use matching dates."
            ),
        }
    )


def _expected_nights_from_trip_length(trip_length: str | None) -> int | None:
    if not trip_length:
        return None
    normalized = trip_length.lower()
    nights_match = re.search(r"(\d+)\s*nights?", normalized)
    if nights_match:
        return max(1, min(30, int(nights_match.group(1))))
    days_match = re.search(r"(\d+)\s*days?", normalized)
    if days_match:
        return max(1, min(30, int(days_match.group(1)) - 1))
    return None


def _date_decision_is_usable(
    decision: QuickPlanWorkingDateDecision,
    *,
    today: date,
) -> bool:
    if decision.start_date <= today:
        return False
    nights = (decision.end_date - decision.start_date).days
    return 1 <= nights <= 30


def _mark_assistant_derived_date(
    llm_update: TripTurnUpdate,
    field: Literal["start_date", "end_date"],
    confidence: Literal["medium", "high"],
) -> None:
    if field not in llm_update.inferred_fields:
        llm_update.inferred_fields.append(field)
    llm_update.confirmed_fields = [
        confirmed for confirmed in llm_update.confirmed_fields if confirmed != field
    ]
    llm_update.field_sources = [
        source for source in llm_update.field_sources if source.field != field
    ]
    llm_update.field_confidences = [
        item for item in llm_update.field_confidences if item.field != field
    ]
    llm_update.field_sources.append(
        TripFieldSourceUpdate(field=field, source="assistant_derived")
    )
    llm_update.field_confidences.append(
        TripFieldConfidenceUpdate(field=field, confidence=confidence)
    )
