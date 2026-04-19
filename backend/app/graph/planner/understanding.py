from app.graph.planner.turn_models import TripTurnUpdate
from app.integrations.llm.client import create_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration


def generate_llm_trip_update(
    *,
    user_input: str,
    configuration: TripConfiguration,
    title: str,
    status: TripDraftStatus,
    conversation: TripConversationState,
    profile_context: dict,
    raw_messages: list[dict],
) -> TripTurnUpdate:
    if not user_input.strip():
        return TripTurnUpdate()

    recent_messages = raw_messages[-6:]
    prompt = f"""
You are Wandrix's structured trip-planning extraction engine.

Update the trip conservatively using the latest user turn in context.

Rules:
- Be warm, a little chatty, precise, and planner-like.
- Never let profile defaults override explicit trip details.
- Do not infer traveler counts from vague social phrasing alone.
- Explicit user statements become confirmed_fields.
- Plausible but not explicit details stay inferred_fields.
- Rejected or corrected options go into rejected_options.
- Mentioned but unchosen possibilities go into mentioned_options.
- Use travel_window for rough timing like "late September".
- Use trip_length for rough duration like "4 or 5 nights".
- Only use exact start_date or end_date when the user gave fixed dates.
- Keep open_questions short and useful.
- Use decision_cards only when they help the user make the next concrete choice.
- Use active_goals for the current short planning agenda.
- last_turn_summary should be a compact planner summary of what changed this turn.
- Keep assistant_response warm, grounded in what actually changed, and conversational enough that it feels like a real travel planner rather than a terse extraction bot.

Allowed field keys:
["from_location", "to_location", "start_date", "end_date", "travel_window", "trip_length", "budget_gbp", "adults", "children", "activity_styles", "selected_modules"]

Current draft title:
{title}

Current configuration:
{configuration.model_dump(mode="json")}

Current planner status:
{status.model_dump(mode="json")}

Current conversation state:
{conversation.model_dump(mode="json")}

Saved profile context:
{profile_context}

Recent raw messages:
{recent_messages}

Latest user message:
{user_input}
""".strip()

    try:
        model = create_chat_model(temperature=0.1)
        structured_model = model.with_structured_output(
            TripTurnUpdate,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                (
                    "system",
                    "Update the Wandrix trip planner using careful structured extraction.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return TripTurnUpdate()
