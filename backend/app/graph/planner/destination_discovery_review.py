from app.graph.planner.turn_models import TripTurnUpdate
from app.integrations.llm.client import create_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration


def review_destination_discovery_update(
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
    llm_update: TripTurnUpdate,
) -> TripTurnUpdate:
    if (
        not llm_update.destination_suggestions
        or not llm_update.assistant_response.strip()
    ):
        return llm_update
    proposed_destination_names = [
        suggestion.destination_name
        for suggestion in llm_update.destination_suggestions
        if suggestion.destination_name
    ]

    prompt = f"""
You are Wandrix's destination discovery QA reviewer.

Review the proposed structured planner update and return a corrected TripTurnUpdate.
Preserve good work. Only revise fields when needed to keep destination discovery coherent.

Rules:
- This is still LLM-first planning. Do not invent hidden deterministic rules; reason from the latest user message, conversation, and proposed update.
- destination_suggestions and assistant_response must tell the same story.
- In your final answer, assistant_response must not name or recommend any destination that is absent from your final destination_suggestions.
- This applies to optional future ideas, examples, backups, wildcards, replacements, "one more", "if you want", and "what else" destinations too.
- If you want to keep any named destination in assistant_response, add it to final destination_suggestions and keep the final list between 2 and 6 cards. Otherwise remove the named mention and describe the idea generically.
- Before returning, silently audit the final assistant_response against the final destination_suggestions and remove any uncarded destination name.
- If the user asks for more than 6 destinations, return at most 6 destination_suggestions and say the shortlist is capped to the strongest six. Do not say "here are ten" or imply the larger requested count is being shown.
- Explicit exclusions must be honored in destination_suggestions and assistant_response.
- If the user says "not Spain", do not include Spanish cities.
- If the user asks to compare one named destination with alternatives, keep destination discovery active and do not set to_location unless the user clearly chose it.
- If the latest user named a small set of destinations and asked which one, or said they were not sure, keep the final destination_suggestions focused on those named options unless the user asked for alternatives or a labelled wildcard is genuinely useful.
- If the latest user asked to avoid obvious picks, replace common default city-break answers with less expected places that still fit the brief, unless a familiar baseline is explicitly useful and explained.
- If the latest user message rejects a destination and asks for "what else", "replace it", or similar, include at least one replacement destination in final destination_suggestions instead of only shrinking to the remaining old cards. Preserve the requested shortlist size when it still makes sense.
- Saved profile home-base context can personalize wording, but do not set from_location unless the latest user message adopts that base for this trip.
- Avoid "Quick read", "The choice", "Tradeoff:", "Verdict:", "Board:", and "on the board" in assistant_response.
- Keep assistant_response warm, concise, and useful for choosing.
- Preserve non-discovery fields from the proposed update unless they clearly conflict with these rules.

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
{raw_messages[-6:]}

Latest user message:
{user_input}

Proposed destination card names:
{proposed_destination_names}

Proposed TripTurnUpdate:
{llm_update.model_dump(mode="json")}
""".strip()

    try:
        model = create_chat_model(temperature=0.1)
        structured_model = model.with_structured_output(
            TripTurnUpdate,
            method="json_schema",
        )
        reviewed_update = structured_model.invoke(
            [
                (
                    "system",
                    "Review and repair Wandrix destination discovery output.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return llm_update

    return reviewed_update
