from pydantic import BaseModel, Field

from app.schemas.trip_conversation import (
    CheckpointConversationMessage,
    ChatPlannerPhase,
)
from app.schemas.trip_draft import TripDraft


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


class PlannerLocationContext(BaseModel):
    source: str = Field(..., min_length=1, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    summary: str | None = Field(default=None, max_length=240)
    latitude: float | None = None
    longitude: float | None = None


class ConversationBoardAction(BaseModel):
    action_id: str = Field(..., min_length=1, max_length=80)
    type: str = Field(..., min_length=1, max_length=40)
    destination_name: str | None = Field(default=None, max_length=120)
    country_or_region: str | None = Field(default=None, max_length=120)
    suggestion_id: str | None = Field(default=None, max_length=80)


class TripConversationMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    profile_context: PlannerProfileContext | None = None
    current_location_context: PlannerLocationContext | None = None
    board_action: ConversationBoardAction | None = None


class TripConversationMessageResponse(BaseModel):
    trip_id: str
    thread_id: str
    draft_phase: ChatPlannerPhase
    message: str
    trip_draft: TripDraft


class CheckpointConversationHistoryResponse(BaseModel):
    trip_id: str
    thread_id: str
    messages: list[CheckpointConversationMessage] = Field(default_factory=list)
