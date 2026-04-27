import logging
from typing import Any

from app.graph.planner.quick_plan_context import (
    build_quick_plan_configuration_payload,
    build_quick_plan_generation_context,
    build_quick_plan_module_payload,
)
from app.graph.planner.quick_plan_day_architecture import QuickPlanDayArchitecture
from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_provider_brief import QuickPlanProviderBrief
from app.graph.planner.quick_plan_strategy import QuickPlanStrategyBrief
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.graph.planner.turn_models import QuickPlanDraft
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


logger = logging.getLogger(__name__)


def generate_quick_plan_draft(
    *,
    title: str,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    conversation: TripConversationState,
    dossier: QuickPlanDossier | None = None,
    strategy_brief: QuickPlanStrategyBrief | None = None,
    provider_brief: QuickPlanProviderBrief | None = None,
    day_architecture: QuickPlanDayArchitecture | None = None,
    repair_context: dict[str, Any] | None = None,
) -> QuickPlanDraft:
    generation_context = build_quick_plan_generation_context(
        conversation=conversation,
        dossier=dossier,
    )
    configuration_payload = build_quick_plan_configuration_payload(configuration)
    module_payload = build_quick_plan_module_payload(module_outputs)
    repair_instruction = ""
    if repair_context:
        repair_instruction = f"""

Private repair context:
{repair_context}

Repair rules:
- Regenerate a full fresh Quick Plan candidate, not a patch.
- Explicitly address every missing output, reviewer note, quality issue, quality
  score gap, and repair instruction in the repair context.
- Preserve confirmed inputs, accepted module scope, working dates, and provider
  fact caveats.
- Do not invent provider facts to satisfy quality feedback. If missing provider
  facts caused the failure, create honest planning blocks or caveats instead.
- If quality feedback conflicts with the user brief, follow the user brief and
  handle the constraint honestly in the plan.
- If final_repair_chance is true, this is the last private repair attempt:
  resolve the named unresolved dimensions directly and do not leave avoidable
  quality gaps for another pass.
- Do not mention that this is a repair attempt to the traveller.
""".rstrip()
    prompt = f"""
You are Wandrix's itinerary drafting engine.

Create a concrete first-pass travel itinerary for the confirmed trip brief.

Rules:
- Build a specific, city-aware draft itinerary rather than a vague outline.
- Return 10 to 14 timeline_preview items for a 4-5 day trip, unless the trip is shorter.
- Cover the full trip span. If the trip is 5 days, make sure the draft reaches Day 5 and includes a sensible closing or return block.
- Make each day feel intentionally different. Avoid repeating the same shape of "arrive, wander, dinner" across multiple days.
- Give each day a clear center of gravity such as arrival-and-settle, neighborhood immersion, museum-heavy core sights, food crawl, coastline reset, or departure wind-down.
- Make the plan feel operational, not just inspirational: include travel between the stay, conference/activities, and evening areas when that movement matters.
- Include meal rhythm. For full days, add at least one useful breakfast, lunch, or dinner anchor; for business/conference trips, protect conference time, add lunch near the venue, and add easy dinner/evening plans.
- Close loops. When a day ends away from the stay area, include a short return-to-stay or back-to-hotel detail in the final activity or transfer.
- Use activity_styles, budget posture, traveller makeup, and module focus to shape the pacing instead of generating a one-size-fits-all city break.
- Prefer exact, concrete item titles over generic wording. Named streets, stations, markets, neighborhoods, landmarks, and transit hubs are better than broad labels.
- Use real neighborhoods, landmarks, markets, museums, food halls, promenades, or districts when helpful.
- Avoid generic titles like "Old town day", "Slow time", "Central stay", "Celebratory dinner", or "Culture day".
- Avoid generic filler blocks like "Explore the city", "Dinner in town", "Sightseeing", or "Free time" unless you make them destination-specific and purposeful.
- If provider outputs are available, ground the itinerary in them first.
- Provider outputs are already ranked for Quick Plan fit. Treat the first outbound flight, first return flight, and first hotel as the working recommendations unless there is an obvious contradiction.
- If flights data is available, include the actual outbound and return flight blocks using the provided departure and arrival times.
- If flights data is missing, do not invent flight numbers or exact departure times. Keep the flight block strategic and honest.
- If hotels data is available, use the recommended hotel or stay area as a concrete anchor and explain why it fits the route.
- If hotels data is missing, recommend a specific neighborhood or stay style, not a fabricated hotel name.
- Do not invent reservation details, live prices, opening hours, or exact provider facts unless they already exist in the module outputs.
- If exact dates were chosen from a rough travel window, treat them as editable working dates and make the plan strong enough that the user can ask to change them later.
- Keep meal blocks and activity blocks actionable and destination-specific.
- Prefer concrete meal titles such as "Breakfast near Russafa before the venue" or "Low-key dinner around Ciutat Vella" over generic "Meal" labels.
- Connect blocks together so the day reads like a real route through the city rather than isolated bullets.
- Use details to explain why the sequence makes sense: proximity, weather fit, recovery after travel, nightlife timing, market hours, or slower pacing for a short trip.
- Include travel-time context whenever movement matters, such as airport transfers, train rides, metro hops, or cross-city moves.
- When you know a transfer is short or long, say so in the details. Example styles: "20-minute taxi from the airport", "15-minute metro hop", "short riverside walk".
- Use start_at and end_at when exact timing is known from provider data or clearly implied by the itinerary structure.
- Reflect the weather outlook when it should affect pacing or time-of-day choices.
- If weather data exists, adapt the shape of the day around it instead of dropping in detached weather notes.
- Make the pacing feel like a real 5-day travel plan someone would actually follow.
- The board_summary should read like a short editorial summary of the first draft, not generic system text.
- Keep board_summary to one complete sentence under 220 characters.
- Do not use markdown formatting in the output.

Current trip title:
{title}

Confirmed configuration:
{configuration_payload}

Current conversation state:
{generation_context}

Current provider-backed module outputs:
{module_payload}

Private strategy brief:
{strategy_brief.model_dump(mode="json") if strategy_brief else {}}

Private provider interpretation:
{provider_brief.model_dump(mode="json") if provider_brief else {}}

Private day architecture:
{day_architecture.model_dump(mode="json") if day_architecture else {}}

Drafting instruction:
Write timeline rows from the private day architecture instead of inventing the trip structure from scratch.
Only deviate when provider facts or fact-safety caveats make the architecture unsafe.
{repair_instruction}
""".strip()

    try:
        return _invoke_quick_plan_draft_model(
            prompt,
            temperature=0.2,
            timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
            max_retries=0,
            reasoning_effort="medium",
        )
    except Exception:
        logger.warning(
            "Quick Plan draft generation returned no usable output on medium reasoning.",
            exc_info=True,
        )

    try:
        return _invoke_quick_plan_draft_model(
            prompt,
            temperature=0.2,
            timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
            max_retries=1,
        )
    except Exception:
        logger.warning(
            "Quick Plan draft generation returned no usable output on configured reasoning fallback.",
            exc_info=True,
        )
        return QuickPlanDraft()


def _invoke_quick_plan_draft_model(
    prompt: str,
    *,
    temperature: float,
    timeout: float,
    max_retries: int,
    reasoning_effort: str | None = None,
) -> QuickPlanDraft:
    try:
        model = create_quick_plan_chat_model(
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
            reasoning_effort=reasoning_effort,
        )
    except TypeError:
        model = create_quick_plan_chat_model(temperature=temperature)
    structured_model = model.with_structured_output(
        QuickPlanDraft,
        method="json_schema",
    )
    return structured_model.invoke(
        [
            (
                "system",
                "Write a concrete first-pass itinerary for Wandrix using the confirmed brief, provider data, meal rhythm, and route logistics.",
            ),
            ("human", prompt),
        ]
    )
