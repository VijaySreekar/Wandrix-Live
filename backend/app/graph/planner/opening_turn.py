from pydantic import BaseModel, Field

from app.integrations.llm.client import create_chat_model


class OpeningTurnDecision(BaseModel):
    should_start_trip: bool = False
    message: str = Field(..., min_length=1, max_length=4000)


def decide_opening_turn(
    *,
    user_message: str,
    profile_context: dict,
    current_location_context: dict,
) -> OpeningTurnDecision:
    prompt = f"""
You are Wandrix's opening-turn conversation gate.

Your job is to decide whether the latest user message is:
- still generic conversation, greeting, help-seeking, or broad small talk that should stay outside trip-planning mode
- or a real travel-planning start that should open a proper trip-planning session

Rules:
- Be warm, natural, and concise.
- `should_start_trip` must be true only when the user is clearly starting trip planning, travel planning, itinerary building, destination discovery, travel comparison, or a travel-specific request.
- `should_start_trip` must be false for greetings, hello messages, "what can you do", casual conversation, generic help requests, or meta questions about the assistant.
- If the message is generic, respond like a polished travel assistant introducing Wandrix and inviting the user to share their travel idea.
- If the message clearly starts trip planning, respond like a natural bridge into planning. Do not mention internal modes, hidden state, or system mechanics.
- Do not sound repetitive or scripted.
- Do not use markdown.

Examples:
- "hi" -> should_start_trip=false
- "hello, what can you help with?" -> should_start_trip=false
- "can you help me plan a trip?" -> should_start_trip=true
- "I want to go somewhere warm in June" -> should_start_trip=true
- "thinking about Japan for 10 days" -> should_start_trip=true
- "what's your name?" -> should_start_trip=false

Saved profile context:
{profile_context}

Current location context:
{current_location_context}

Latest user message:
{user_message}
""".strip()

    try:
        model = create_chat_model(temperature=0.2)
        structured_model = model.with_structured_output(
            OpeningTurnDecision,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                (
                    "system",
                    "Decide whether to keep the conversation in a light opening state or begin real travel planning.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return OpeningTurnDecision(
            should_start_trip=False,
            message=(
                "Hi, I'm Wandrix. I can help with anything from a rough travel idea to a fully planned trip. "
                "Tell me where you're thinking of going, roughly when, or the kind of getaway you want."
            ),
        )
