from typing import Literal

from pydantic import BaseModel, Field

from app.graph.planner.turn_models import (
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripTurnUpdate,
)
from app.integrations.llm.client import create_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration

OriginReviewAction = Literal["keep", "clear", "replace"]
OriginReviewSource = Literal["user_explicit", "user_inferred"]
OriginReviewConfidence = Literal["low", "medium", "high"]
ORIGIN_FIELDS = {"from_location", "from_location_flexible"}


class ProfileOriginReviewDecision(BaseModel):
    action: OriginReviewAction
    from_location: str | None = Field(default=None, max_length=120)
    from_location_flexible: bool | None = None
    source: OriginReviewSource | None = None
    confidence: OriginReviewConfidence | None = None
    rationale: str = Field(..., min_length=1, max_length=320)


def review_profile_origin_update(
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
    if current_location_context.get("source") != "profile_home_base":
        return llm_update
    if not llm_update.from_location and llm_update.from_location_flexible is not True:
        return llm_update

    prompt = f"""
You are Wandrix's origin-safety reviewer.

Return a small structured origin decision. Do not rewrite the whole trip update.

Rules:
- This is LLM-first validation. Reason from the latest user message and the proposed update; do not use hidden keyword rules.
- Saved profile home-base context can personalize recommendations, but it must not become from_location unless the latest user message adopts it for this trip.
- A user-supplied origin/base/departure point always beats the saved profile home base.
- If the latest user says "Based near Birmingham", "from Birmingham", or similar, the origin decision should be replace with from_location "Birmingham", not the saved Coventry profile.
- If the latest user says they will already be in a place, that place is the working origin for this trip.
- from_location_flexible should be true only when the latest user says the departure point is flexible, open, undecided, or gives multiple workable origins.
- If the latest user did not adopt or provide an origin, choose clear and set from_location and from_location_flexible to null.
- Choose keep only when the proposed origin is already justified by the latest user message.

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

Proposed origin fields:
from_location={llm_update.from_location}
from_location_flexible={llm_update.from_location_flexible}
confirmed_fields={llm_update.confirmed_fields}
inferred_fields={llm_update.inferred_fields}
field_confidences={[item.model_dump(mode="json") for item in llm_update.field_confidences]}
field_sources={[item.model_dump(mode="json") for item in llm_update.field_sources]}
""".strip()

    try:
        model = create_chat_model(temperature=0.1)
        structured_model = model.with_structured_output(
            ProfileOriginReviewDecision,
            method="json_schema",
        )
        decision = structured_model.invoke(
            [
                (
                    "system",
                    "Decide whether Wandrix may save the proposed origin from profile context.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return llm_update

    return _apply_origin_decision(llm_update=llm_update, decision=decision)


def _apply_origin_decision(
    *,
    llm_update: TripTurnUpdate,
    decision: ProfileOriginReviewDecision,
) -> TripTurnUpdate:
    if decision.action == "keep":
        return llm_update

    reviewed = llm_update.model_copy(deep=True)
    _clear_origin_fields(reviewed)

    if decision.action != "replace":
        return reviewed

    if decision.from_location:
        reviewed.from_location = decision.from_location
        source = decision.source or "user_inferred"
        confidence = decision.confidence or "medium"
        if source == "user_explicit" and confidence == "high":
            reviewed.confirmed_fields.append("from_location")
        else:
            reviewed.inferred_fields.append("from_location")
        reviewed.field_confidences.append(
            TripFieldConfidenceUpdate(field="from_location", confidence=confidence)
        )
        reviewed.field_sources.append(
            TripFieldSourceUpdate(field="from_location", source=source)
        )

    if decision.from_location_flexible is True:
        reviewed.from_location_flexible = True
        reviewed.inferred_fields.append("from_location_flexible")
        reviewed.field_confidences.append(
            TripFieldConfidenceUpdate(
                field="from_location_flexible",
                confidence=decision.confidence or "medium",
            )
        )
        reviewed.field_sources.append(
            TripFieldSourceUpdate(
                field="from_location_flexible",
                source=decision.source or "user_inferred",
            )
        )

    reviewed.confirmed_fields = list(dict.fromkeys(reviewed.confirmed_fields))
    reviewed.inferred_fields = [
        field
        for field in dict.fromkeys(reviewed.inferred_fields)
        if field not in reviewed.confirmed_fields
    ]
    return reviewed


def _clear_origin_fields(llm_update: TripTurnUpdate) -> None:
    llm_update.from_location = None
    llm_update.from_location_flexible = None
    llm_update.confirmed_fields = [
        field for field in llm_update.confirmed_fields if field not in ORIGIN_FIELDS
    ]
    llm_update.inferred_fields = [
        field for field in llm_update.inferred_fields if field not in ORIGIN_FIELDS
    ]
    llm_update.field_confidences = [
        item for item in llm_update.field_confidences if item.field not in ORIGIN_FIELDS
    ]
    llm_update.field_sources = [
        item for item in llm_update.field_sources if item.field not in ORIGIN_FIELDS
    ]
