from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_provider_brief import QuickPlanProviderBrief
from app.graph.planner.quick_plan_strategy import QuickPlanStrategyBrief
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_planning import TripConfiguration


logger = logging.getLogger(__name__)


class QuickPlanDayPlan(BaseModel):
    day_index: int = Field(..., ge=1, le=30)
    day_label: str = Field(..., min_length=1, max_length=40)
    date: str | None = None
    theme: str = Field(..., min_length=1, max_length=180)
    geography_focus: str = Field(..., min_length=1, max_length=180)
    pacing_target: str = Field(..., min_length=1, max_length=160)
    food_culture_intent: str = Field(..., min_length=1, max_length=220)
    logistics_anchors: list[str] = Field(default_factory=list, max_length=8)
    must_avoid: list[str] = Field(default_factory=list, max_length=8)
    expected_row_types: list[str] = Field(default_factory=list, max_length=8)


class QuickPlanDayArchitecture(BaseModel):
    route_logic: str = Field(..., min_length=1, max_length=360)
    days: list[QuickPlanDayPlan] = Field(default_factory=list, max_length=30)
    coverage_notes: list[str] = Field(default_factory=list, max_length=8)


def build_quick_plan_day_architecture(
    *,
    dossier: QuickPlanDossier,
    configuration: TripConfiguration,
    strategy_brief: QuickPlanStrategyBrief,
    provider_brief: QuickPlanProviderBrief,
    repair_context: dict[str, Any] | None = None,
) -> QuickPlanDayArchitecture | None:
    expected_days = _expected_trip_days(configuration)
    if expected_days is None:
        return None

    prompt = f"""
You are Wandrix's private day-architecture planner.

Create the structured day-by-day architecture before itinerary rows are written.
Do not write final timeline rows.

Rules:
- Return exactly {expected_days} day plans, covering Day 1 through Day {expected_days}.
- Arrival and departure days should be lighter when logistics are in scope.
- Honor selected module scope. Activities-only plans must not require flights or hotels.
- Include calm/relaxed pacing targets when requested by the strategy.
- Each day should name a geography/area focus, food/culture intent, logistics
  anchors, must-avoid issues, and expected row types.
- Expected row types should guide final drafting, e.g. flight, hotel, transfer,
  meal, activity, event, note.
- During quality repair, explicitly address failed dimensions named in the
  repair context: geography, pacing, local_specificity, user_fit,
  logistics_realism, and fact_safety.
- Preserve confirmed user inputs, accepted module scope, working dates, and
  provider fact caveats. If feedback conflicts with the user brief, the user
  brief wins and the constraint should be reflected internally.

Trip configuration:
{configuration.model_dump(mode="json")}

Selected module scope:
{dossier.readiness.allowed_modules}

Strategy brief:
{strategy_brief.model_dump(mode="json")}

Provider brief:
{provider_brief.model_dump(mode="json")}

Repair context, if any:
{repair_context or {}}
""".strip()

    try:
        model = create_quick_plan_chat_model(
            temperature=0.1,
            timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
            max_retries=1,
        )
        structured_model = model.with_structured_output(
            QuickPlanDayArchitecture,
            method="json_schema",
        )
        architecture = structured_model.invoke(
            [
                (
                    "system",
                    "Create complete private day architecture for a Quick Plan itinerary.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning(
            "Quick Plan day architecture returned no usable output.",
            exc_info=True,
        )
        return None

    return _normalize_day_architecture(
        architecture,
        configuration=configuration,
        expected_days=expected_days,
    )


def _normalize_day_architecture(
    architecture: QuickPlanDayArchitecture,
    *,
    configuration: TripConfiguration,
    expected_days: int,
) -> QuickPlanDayArchitecture | None:
    by_index = {day.day_index: day for day in architecture.days}
    expected_indexes = set(range(1, expected_days + 1))
    if set(by_index) != expected_indexes:
        return None

    normalized_days: list[QuickPlanDayPlan] = []
    for day_index in range(1, expected_days + 1):
        day = by_index[day_index]
        date_value = day.date
        if configuration.start_date:
            date_value = (
                configuration.start_date + timedelta(days=day_index - 1)
            ).isoformat()
        normalized_days.append(
            day.model_copy(
                update={
                    "day_label": f"Day {day_index}",
                    "date": date_value,
                }
            )
        )

    return architecture.model_copy(update={"days": normalized_days})


def _expected_trip_days(configuration: TripConfiguration) -> int | None:
    if not (configuration.start_date and configuration.end_date):
        return None
    return max((configuration.end_date - configuration.start_date).days + 1, 1)
