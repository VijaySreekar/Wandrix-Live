from app.graph.planner.turn_models import QuickPlanDraft
from app.integrations.llm.client import create_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


def generate_quick_plan_draft(
    *,
    title: str,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    conversation: TripConversationState,
) -> QuickPlanDraft:
    prompt = f"""
You are Wandrix's itinerary drafting engine.

Create a concrete first-pass travel itinerary for the confirmed trip brief.

Rules:
- Build a specific, city-aware draft itinerary rather than a vague outline.
- Return 6 to 10 timeline_preview items.
- Cover the full trip span. If the trip is 5 days, make sure the draft reaches Day 5 and includes a sensible closing or return block.
- Prefer exact, concrete item titles over generic wording. Named streets, stations, markets, neighborhoods, landmarks, and transit hubs are better than broad labels.
- Use real neighborhoods, landmarks, markets, museums, food halls, promenades, or districts when helpful.
- Avoid generic titles like "Old town day", "Slow time", "Central stay", "Celebratory dinner", or "Culture day".
- If provider outputs are available, ground the itinerary in them first.
- If flights data is available, include the actual outbound and return flight blocks using the provided departure and arrival times.
- If flights data is missing, do not invent flight numbers or exact departure times. Keep the flight block strategic and honest.
- If hotels data is missing, recommend a specific neighborhood or stay style, not a fabricated hotel name.
- Do not invent reservation details, live prices, opening hours, or exact provider facts unless they already exist in the module outputs.
- Keep meal blocks and activity blocks actionable and destination-specific.
- Include travel-time context whenever movement matters, such as airport transfers, train rides, metro hops, or cross-city moves.
- When you know a transfer is short or long, say so in the details. Example styles: "20-minute taxi from the airport", "15-minute metro hop", "short riverside walk".
- Use start_at and end_at when exact timing is known from provider data or clearly implied by the itinerary structure.
- Reflect the weather outlook when it should affect pacing or time-of-day choices.
- Make the pacing feel like a real 5-day travel plan someone would actually follow.
- The board_summary should read like a short editorial summary of the first draft, not generic system text.
- Keep board_summary to one complete sentence under 220 characters.
- Do not use markdown formatting in the output.

Current trip title:
{title}

Confirmed configuration:
{configuration.model_dump(mode="json")}

Current conversation state:
{conversation.model_dump(mode="json")}

Current provider-backed module outputs:
{module_outputs.model_dump(mode="json")}
""".strip()

    try:
        model = create_chat_model(temperature=0.2)
        structured_model = model.with_structured_output(
            QuickPlanDraft,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                (
                    "system",
                    "Write a concrete first-pass itinerary for Wandrix using the confirmed brief and any available provider data.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return QuickPlanDraft()
