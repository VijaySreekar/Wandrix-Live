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
    current_location_context: dict,
    board_action: dict,
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
- If there is enough trip signal, generate a concise sidebar-style title in 2 to 6 words.
- Titles should feel like a human summary of the trip direction, such as "Kyoto Food Escape" or "Lisbon Spring Weekend".
- Even if the trip is still broad, prefer a grounded working title from the user's real intent, such as "Warm Getaway", "Sunny June Escape", or "Luxury City Break".
- Only leave title empty when there is truly no meaningful travel intent in the latest turn.
- Never return generic placeholders like "Trip", "Trip planner", "Travel plan", or raw id-like labels.
- Never let profile defaults override explicit trip details.
- Do not infer traveler counts from vague social phrasing alone.
- If the user has not chosen a destination and their ask is broad, you may proactively suggest destination options.
- When you suggest destinations, return exactly 4 destination_suggestions with image_url, short_reason, and one practicality_label each.
- For each destination suggestion image_url, use a real HTTPS image URL. A good default format is https://source.unsplash.com/1200x900/?DESTINATION+travel
- Destination suggestions should optimize for fit plus travel practicality from the location context you were given.
- If no browser location or saved home-base context is available, ask for the user's departure city, home base, or airport before giving practicality-weighted destination suggestions.
- If browser location context is available and the ask is still broad, do not stop at asking for origin. Suggest destinations first, then invite the user to correct the departure point if needed.
- If browser location is available, say so clearly in location_source_summary.
- If browser location is unavailable and saved home base context is available, say that clearly in location_source_summary.
- Do not generate destination suggestion cards when the user already gave a concrete destination.
- If you used browser location for the shortlist, mention that the user can correct it if they are not actually leaving from there.
- A board_action of select_destination_suggestion means the user is leaning toward that place, but it is not confirmed yet.
- A board_action of own_choice means the user wants to type their own destination in chat.
- A board_action of confirm_trip_details means the user has explicitly confirmed the structured details from the board.
- A board_action of confirm_trip_brief means the user has explicitly confirmed the full working trip brief from the board.
- If the user says they are not travelling from the detected place, treat that as a correction to the origin context and update the next suggestions accordingly.
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
- Once route direction is usable, shift toward collecting the remaining trip details.
- The checklist-style details stage should cover timing, trip length, traveller count, trip style, budget, and module scope.
- Module scope can be explicit. If the user says they only want one area like activities, respect that and keep other modules inactive.
- If the planner has already gathered the full working brief and is asking for confirmation, set confirmed_trip_brief to true only when the user clearly confirms it with language like yes, looks good, proceed, go ahead, or confirm.
- If the user is still correcting any field, do not set confirmed_trip_brief.
- Do not use markdown styling in assistant_response. Avoid **bold**, headings, inline code, or decorative formatting markers.

Allowed field keys:
["from_location", "to_location", "start_date", "end_date", "travel_window", "trip_length", "budget_posture", "budget_gbp", "adults", "children", "activity_styles", "selected_modules"]

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

Current location context:
{current_location_context}

Latest board action:
{board_action}

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
