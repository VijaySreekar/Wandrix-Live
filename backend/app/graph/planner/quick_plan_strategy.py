from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_context import (
    build_quick_plan_configuration_payload,
    build_quick_plan_generation_context,
)
from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


logger = logging.getLogger(__name__)


class QuickPlanModulePriority(BaseModel):
    module: str = Field(..., min_length=1, max_length=40)
    priority: str = Field(..., min_length=1, max_length=220)


class QuickPlanStrategyBrief(BaseModel):
    trip_thesis: str = Field(..., min_length=1, max_length=360)
    user_intent: list[str] = Field(default_factory=list, max_length=8)
    pacing_rules: list[str] = Field(default_factory=list, max_length=8)
    module_priorities: list[QuickPlanModulePriority] = Field(
        default_factory=list,
        max_length=8,
    )
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    exclusions: list[str] = Field(default_factory=list, max_length=8)
    quality_bar: list[str] = Field(default_factory=list, max_length=8)


def build_quick_plan_strategy_brief(
    *,
    dossier: QuickPlanDossier,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    conversation: TripConversationState,
    repair_context: dict[str, Any] | None = None,
) -> QuickPlanStrategyBrief | None:
    prompt = f"""
You are Wandrix's private Quick Plan strategist.

Decide the trip strategy before itinerary rows are written. Do not write the itinerary.

Return a compact strategy brief with:
- user intent and style signals from the dossier, not raw chat alone
- pacing rules such as arrival/departure lightness and calm/relaxed rhythm
- trip thesis with geography/route logic where possible
- module priorities for the selected scope as typed module/priority entries
- assumptions and exclusions
- quality bar the draft must satisfy
- When repair_goal is quality and the feedback names weak geography, pacing,
  local specificity, or user fit, revise the planning thesis and quality bar
  instead of repeating the previous strategy.
- Preserve confirmed user inputs, selected module scope, working dates, and
  provider fact caveats even when repairing.

Confirmed configuration:
{build_quick_plan_configuration_payload(configuration)}

Generation context:
{build_quick_plan_generation_context(conversation=conversation, dossier=dossier)}

Allowed modules:
{dossier.readiness.allowed_modules}

Provider availability summary:
{_provider_availability_summary(module_outputs)}

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
            QuickPlanStrategyBrief,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                (
                    "system",
                    "Create a concise private trip strategy for Quick Plan generation.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        logger.warning(
            "Quick Plan strategy brief returned no usable output.",
            exc_info=True,
        )
        return None


def _provider_availability_summary(
    module_outputs: TripModuleOutputs,
) -> dict[str, int]:
    return {
        "flights": len(module_outputs.flights),
        "hotels": len(module_outputs.hotels),
        "activities": len(module_outputs.activities),
        "weather": len(module_outputs.weather),
    }
