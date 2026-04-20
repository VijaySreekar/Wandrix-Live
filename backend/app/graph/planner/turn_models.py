from datetime import date

from pydantic import BaseModel, Field

from app.schemas.trip_conversation import (
    ConversationOptionKind,
    PlannerDecisionCard,
    TripFieldKey,
)
from app.schemas.trip_planning import (
    ActivityStyle,
    BudgetPosture,
    PlanningModuleKey,
    TimelineItemType,
)


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


class DestinationSuggestionCandidate(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    destination_name: str = Field(..., min_length=1, max_length=120)
    country_or_region: str = Field(..., min_length=1, max_length=120)
    image_url: str = Field(..., min_length=1, max_length=500)
    short_reason: str = Field(..., min_length=1, max_length=240)
    practicality_label: str = Field(..., min_length=1, max_length=120)


class TripTurnUpdate(BaseModel):
    title: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    budget_posture: BudgetPosture | None = None
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
    destination_suggestion_title: str | None = Field(default=None, max_length=160)
    destination_suggestion_subtitle: str | None = Field(default=None, max_length=320)
    location_source_summary: str | None = Field(default=None, max_length=240)
    destination_suggestions: list[DestinationSuggestionCandidate] = Field(
        default_factory=list,
        max_length=4,
    )
    confirmed_trip_brief: bool = False
    assistant_response: str = ""
