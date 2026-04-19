from datetime import date

from pydantic import BaseModel, Field

from app.schemas.trip_conversation import (
    ConversationOptionKind,
    PlannerDecisionCard,
    TripFieldKey,
)
from app.schemas.trip_planning import ActivityStyle, PlanningModuleKey, TimelineItemType


class TripModuleSelectionUpdate(BaseModel):
    flights: bool | None = None
    weather: bool | None = None
    activities: bool | None = None
    hotels: bool | None = None


class ProposedTimelineItem(BaseModel):
    type: TimelineItemType
    title: str
    day_label: str | None = None
    location_label: str | None = None
    summary: str | None = None
    details: list[str] = Field(default_factory=list)
    source_module: PlanningModuleKey | None = None


class ConversationOptionCandidate(BaseModel):
    kind: ConversationOptionKind
    value: str = Field(..., min_length=1, max_length=160)


class TripTurnUpdate(BaseModel):
    title: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    budget_gbp: float | None = None
    adults: int | None = Field(default=None, ge=0)
    children: int | None = Field(default=None, ge=0)
    selected_modules: TripModuleSelectionUpdate = Field(
        default_factory=TripModuleSelectionUpdate
    )
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    confirmed_fields: list[TripFieldKey] = Field(default_factory=list)
    inferred_fields: list[TripFieldKey] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    decision_cards: list[PlannerDecisionCard] = Field(default_factory=list)
    timeline_preview: list[ProposedTimelineItem] = Field(default_factory=list)
    mentioned_options: list[ConversationOptionCandidate] = Field(default_factory=list)
    rejected_options: list[ConversationOptionCandidate] = Field(default_factory=list)
    active_goals: list[str] = Field(default_factory=list)
    last_turn_summary: str | None = Field(default=None, max_length=400)
    assistant_response: str = ""
