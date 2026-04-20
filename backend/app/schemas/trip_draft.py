from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.trip_conversation import (
    ChatPlannerPhase,
    PlannerConfirmationStatus,
    PlannerFinalizedVia,
    TripConversationState,
    TripFieldKey,
)
from app.schemas.trip_planning import (
    ActivityDetail,
    ActivityStyle,
    FlightDetail,
    HotelStayDetail,
    PlannerTravelerDetails,
    PlanningModuleKey,
    TimelineItem,
    TimelineItemStatus,
    TimelineItemType,
    TripConfiguration,
    TripModuleOutputs,
    TripModuleSelection,
    WeatherDetail,
)


TripPlanningPhase = ChatPlannerPhase


class TripDraftStatus(BaseModel):
    phase: TripPlanningPhase = "opening"
    confirmation_status: PlannerConfirmationStatus = "unconfirmed"
    finalized_at: datetime | None = None
    finalized_via: PlannerFinalizedVia | None = None
    missing_fields: list[str] = Field(default_factory=list)
    confirmed_fields: list[TripFieldKey] = Field(default_factory=list)
    inferred_fields: list[TripFieldKey] = Field(default_factory=list)
    brochure_ready: bool = False
    last_updated_at: datetime | None = None


class TripDraft(BaseModel):
    trip_id: str
    thread_id: str
    title: str
    configuration: TripConfiguration = Field(default_factory=TripConfiguration)
    timeline: list[TimelineItem] = Field(default_factory=list)
    module_outputs: TripModuleOutputs = Field(default_factory=TripModuleOutputs)
    status: TripDraftStatus = Field(default_factory=TripDraftStatus)
    conversation: TripConversationState = Field(default_factory=TripConversationState)


class TripDraftUpsertRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    configuration: TripConfiguration = Field(default_factory=TripConfiguration)
    timeline: list[TimelineItem] = Field(default_factory=list)
    module_outputs: TripModuleOutputs = Field(default_factory=TripModuleOutputs)
    status: TripDraftStatus = Field(default_factory=TripDraftStatus)
    conversation: TripConversationState = Field(default_factory=TripConversationState)
