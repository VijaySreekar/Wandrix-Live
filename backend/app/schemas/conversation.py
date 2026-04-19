from pydantic import BaseModel, Field

from app.schemas.trip_conversation import (
    CheckpointConversationMessage,
    ChatPlannerPhase,
)


class PlannerProfileContext(BaseModel):
    display_name: str | None = None
    first_name: str | None = None
    home_airport: str | None = None
    preferred_currency: str | None = None
    home_city: str | None = None
    home_country: str | None = None
    trip_pace: str | None = None
    preferred_styles: list[str] = Field(default_factory=list)
    location_summary: str | None = None
    location_assist_enabled: bool | None = None


class TripConversationMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    profile_context: PlannerProfileContext | None = None


class TripConversationMessageResponse(BaseModel):
    trip_id: str
    thread_id: str
    draft_phase: ChatPlannerPhase
    message: str


class CheckpointConversationHistoryResponse(BaseModel):
    trip_id: str
    thread_id: str
    messages: list[CheckpointConversationMessage] = Field(default_factory=list)
