from pydantic import BaseModel, Field

from app.schemas.trip_draft import TripPlanningPhase


class TripConversationMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class TripConversationMessageResponse(BaseModel):
    trip_id: str
    thread_id: str
    draft_phase: TripPlanningPhase
    message: str
