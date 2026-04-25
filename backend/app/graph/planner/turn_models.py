from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.trip_conversation import (
    PlannerAdvancedAnchor,
    PlannerFlightStrategy,
    PlannerActivityCandidateKind,
    PlannerActivityDaypart,
    PlannerActivityDisposition,
    PlannerTripPace,
    PlannerTripStyleTradeoffAxis,
    PlannerTripStyleTradeoffChoice,
    PlannerReviewResolutionScope,
    PlannerTripDirectionAccent,
    PlannerTripDirectionPrimary,
    ConversationFieldConfidence,
    ConversationFieldSource,
    ConversationOptionKind,
    DiscoveryTurnKind,
    PlannerIntent,
    PlannerPlanningMode,
    PlannerDecisionCard,
    TripDetailsStepKey,
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
    start_at: datetime | None = None
    end_at: datetime | None = None
    location_label: str | None = None
    summary: str | None = None
    details: list[str] = Field(default_factory=list)
    source_module: PlanningModuleKey | None = None


class QuickPlanDraft(BaseModel):
    board_summary: str | None = Field(default=None, max_length=400)
    timeline_preview: list[ProposedTimelineItem] = Field(
        default_factory=list,
        max_length=12,
    )


class ConversationOptionCandidate(BaseModel):
    kind: ConversationOptionKind
    value: str = Field(..., min_length=1, max_length=160)


class DestinationSuggestionCandidate(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    destination_name: str = Field(..., min_length=1, max_length=120)
    country_or_region: str = Field(..., min_length=1, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    short_reason: str = Field(..., min_length=1, max_length=240)
    practicality_label: str = Field(..., min_length=1, max_length=120)
    fit_label: str | None = Field(default=None, max_length=80)
    best_for: str | None = Field(default=None, max_length=160)
    tradeoffs: list[str] = Field(default_factory=list, max_length=3)
    recommendation_note: str | None = Field(default=None, max_length=200)
    change_note: str | None = Field(default=None, max_length=200)


class TripFieldConfidenceUpdate(BaseModel):
    field: TripFieldKey
    confidence: ConversationFieldConfidence


class TripFieldSourceUpdate(BaseModel):
    field: TripFieldKey
    source: ConversationFieldSource


class TripOpenQuestionUpdate(BaseModel):
    question: str = Field(..., min_length=1, max_length=240)
    field: TripFieldKey | None = None
    step: TripDetailsStepKey | None = None
    priority: int = Field(default=3, ge=1, le=5)
    why: str | None = Field(default=None, max_length=200)


class RequestedActivityDecision(BaseModel):
    candidate_title: str = Field(..., min_length=1, max_length=160)
    candidate_kind: PlannerActivityCandidateKind | None = None
    disposition: PlannerActivityDisposition


class RequestedActivityScheduleEdit(BaseModel):
    action: Literal[
        "move_to_day",
        "move_earlier",
        "move_later",
        "pin_daypart",
        "reserve",
        "restore",
    ]
    candidate_title: str = Field(..., min_length=1, max_length=160)
    candidate_kind: PlannerActivityCandidateKind | None = None
    candidate_id: str | None = Field(default=None, max_length=160)
    target_day_index: int | None = Field(default=None, ge=1, le=30)
    target_daypart: PlannerActivityDaypart | None = None


class RequestedTripStyleDirectionUpdate(BaseModel):
    action: Literal[
        "select_primary",
        "select_accent",
        "clear_accent",
        "confirm",
        "keep_current",
    ]
    primary: PlannerTripDirectionPrimary | None = None
    accent: PlannerTripDirectionAccent | None = None


class RequestedTripStylePaceUpdate(BaseModel):
    action: Literal[
        "select_pace",
        "confirm",
        "keep_current",
    ]
    pace: PlannerTripPace | None = None


class RequestedTripStyleTradeoffUpdate(BaseModel):
    action: Literal[
        "set_tradeoff",
        "confirm",
        "keep_current",
    ]
    axis: PlannerTripStyleTradeoffAxis | None = None
    value: PlannerTripStyleTradeoffChoice | None = None


class RequestedFlightUpdate(BaseModel):
    action: Literal[
        "select_strategy",
        "select_outbound",
        "select_return",
        "confirm",
        "keep_open",
    ]
    strategy: PlannerFlightStrategy | None = None
    flight_option_id: str | None = Field(default=None, max_length=120)


class RequestedReviewResolution(BaseModel):
    scope: PlannerReviewResolutionScope


class TripTurnUpdate(BaseModel):
    title: str | None = None
    from_location: str | None = None
    from_location_flexible: bool | None = None
    to_location: str | None = None
    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    weather_preference: str | None = Field(default=None, max_length=80)
    budget_posture: BudgetPosture | None = None
    budget_amount: float | None = None
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3)
    budget_gbp: float | None = None
    adults: int | None = Field(default=None, ge=0)
    children: int | None = Field(default=None, ge=0)
    travelers_flexible: bool | None = None
    selected_modules: TripModuleSelectionUpdate = Field(
        default_factory=TripModuleSelectionUpdate
    )
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    custom_style: str | None = Field(default=None, max_length=160)
    confirmed_fields: list[TripFieldKey] = Field(default_factory=list)
    inferred_fields: list[TripFieldKey] = Field(default_factory=list)
    field_confidences: list[TripFieldConfidenceUpdate] = Field(default_factory=list)
    field_sources: list[TripFieldSourceUpdate] = Field(default_factory=list)
    open_question_updates: list[TripOpenQuestionUpdate] = Field(default_factory=list)
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
    discovery_turn_kind: DiscoveryTurnKind = "none"
    destination_comparison_summary: str | None = Field(default=None, max_length=500)
    leading_destination_recommendation: str | None = Field(default=None, max_length=240)
    destination_suggestions: list[DestinationSuggestionCandidate] = Field(
        default_factory=list,
        max_length=6,
    )
    planner_intent: PlannerIntent = "none"
    requested_planning_mode: PlannerPlanningMode | None = None
    requested_advanced_anchor: PlannerAdvancedAnchor | None = None
    requested_advanced_review: bool = False
    requested_advanced_finalization: bool = False
    requested_stay_option_title: str | None = Field(default=None, max_length=160)
    requested_stay_hotel_name: str | None = Field(default=None, max_length=160)
    requested_trip_style_direction_updates: list[RequestedTripStyleDirectionUpdate] = Field(
        default_factory=list
    )
    requested_trip_style_pace_updates: list[RequestedTripStylePaceUpdate] = Field(
        default_factory=list
    )
    requested_trip_style_tradeoff_updates: list[RequestedTripStyleTradeoffUpdate] = Field(
        default_factory=list
    )
    requested_flight_updates: list[RequestedFlightUpdate] = Field(default_factory=list)
    requested_activity_decisions: list[RequestedActivityDecision] = Field(
        default_factory=list
    )
    requested_activity_schedule_edits: list[RequestedActivityScheduleEdit] = Field(
        default_factory=list
    )

    requested_review_resolutions: list[RequestedReviewResolution] = Field(
        default_factory=list
    )
    confirmed_trip_brief: bool = False
    assistant_response: str = ""

    @field_validator("budget_currency", mode="before")
    @classmethod
    def normalize_budget_currency(cls, value):
        if value in (None, ""):
            return None
        normalized = str(value).strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("budget_currency must be a 3-letter ISO currency code")
        return normalized
