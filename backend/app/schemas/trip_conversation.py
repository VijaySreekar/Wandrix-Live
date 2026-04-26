from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.trip_planning import (
    ActivityStyle,
    BudgetPosture,
    FlightLegDetail,
    PlanningModuleKey,
    TripModuleSelection,
)


calendar_date = date


ChatPlannerPhase = Literal[
    "opening",
    "collecting_requirements",
    "shaping_trip",
    "enriching_modules",
    "reviewing",
    "finalized",
]
PlannerPlanningMode = Literal["quick", "advanced"]
PlannerIntent = Literal["none", "confirm_plan", "reopen_plan"]
PlannerConfirmationStatus = Literal["unconfirmed", "finalized"]
PlannerFinalizedVia = Literal["chat", "board"]
QuickPlanReviewStatus = Literal["complete", "incomplete", "failed"]
PlannerPlanningModeStatus = Literal[
    "not_selected",
    "selected",
    "advanced_unavailable_fallback",
]
PlannerAdvancedStep = Literal[
    "intake",
    "resolve_dates",
    "choose_anchor",
    "anchor_flow",
    "review",
]
PlannerAdvancedAnchor = Literal["flight", "stay", "trip_style", "activities"]
PlannerFlightStrategy = Literal[
    "smoothest_route",
    "best_timing",
    "best_value",
    "keep_flexible",
]
PlannerFlightSelectionStatus = Literal["none", "selected", "completed", "kept_open"]
PlannerFlightResultsStatus = Literal["blocked", "ready", "placeholder"]
PlannerFlightOptionSource = Literal["provider", "placeholder"]
PlannerWeatherResultsStatus = Literal["ready", "unavailable", "not_requested"]
PlannerAdvancedReviewReadinessStatus = Literal["ready", "needs_review", "flexible"]
PlannerStaySelectionStatus = Literal["none", "selected", "needs_review"]
PlannerStayCompatibilityStatus = Literal["fit", "strained", "conflicted"]
PlannerStayStrategyType = Literal["single_base", "split_stay"]
PlannerActivityCandidateKind = Literal["activity", "event"]
PlannerActivityDisposition = Literal["essential", "maybe", "pass"]
PlannerActivityDaypart = Literal["morning", "afternoon", "evening"]
PlannerReviewResolutionScope = Literal["stay", "hotel"]
PlannerActivityScheduleStatus = Literal["none", "ready"]
PlannerActivityCompletionStatus = Literal["in_progress", "completed"]
PlannerActivityTimelineBlockType = Literal["activity", "event", "transfer"]
PlannerTripStyleSelectionStatus = Literal["none", "selected", "review", "completed"]
PlannerTripStyleSubstep = Literal["direction", "pace", "tradeoffs", "completed"]
PlannerTripPace = Literal["slow", "balanced", "full"]
PlannerTripStyleTradeoffAxis = Literal[
    "must_sees_vs_wandering",
    "convenience_vs_atmosphere",
    "early_starts_vs_evening_energy",
    "polished_vs_hidden_gems",
]
PlannerTripStyleTradeoffChoice = Literal[
    "must_sees",
    "wandering",
    "convenience",
    "atmosphere",
    "early_starts",
    "evening_energy",
    "polished",
    "hidden_gems",
    "balanced",
]
PlannerTripDirectionPrimary = Literal[
    "food_led",
    "culture_led",
    "nightlife_led",
    "outdoors_led",
    "balanced",
]
PlannerTripDirectionAccent = Literal[
    "local",
    "classic",
    "polished",
    "romantic",
    "relaxed",
]
PlannerHotelStyleTag = Literal[
    "calm",
    "central",
    "design",
    "luxury",
    "food_access",
    "practical",
    "traditional",
    "nightlife",
    "walkable",
    "value",
]
PlannerHotelSortOrder = Literal[
    "best_fit",
    "lowest_price",
    "highest_price",
    "best_area_fit",
]
PlannerHotelResultsStatus = Literal["blocked", "ready", "empty"]
PlannerDateResolutionStatus = Literal["none", "selected", "confirmed"]
PlannerStayHotelSubstep = Literal[
    "strategy_choice",
    "hotel_shortlist",
    "hotel_selected",
    "hotel_review",
]
TripDetailsStepKey = Literal[
    "modules",
    "route",
    "timing",
    "travellers",
    "vibe",
    "budget",
]
TripSuggestionBoardMode = Literal[
    "idle",
    "destination_suggestions",
    "timing_choice",
    "decision_cards",
    "details_collection",
    "planning_mode_choice",
    "advanced_date_resolution",
    "advanced_anchor_choice",
    "advanced_next_step",
    "advanced_flights_workspace",
    "advanced_trip_style_direction",
    "advanced_trip_style_pace",
    "advanced_trip_style_tradeoffs",
    "advanced_activities_workspace",
    "advanced_stay_choice",
    "advanced_stay_selected",
    "advanced_stay_review",
    "advanced_stay_hotel_choice",
    "advanced_stay_hotel_selected",
    "advanced_stay_hotel_review",
    "advanced_review_workspace",
    "helper",
]
DestinationSuggestionSelectionStatus = Literal[
    "suggested",
    "leading",
    "confirmed",
]
DiscoveryTurnKind = Literal[
    "none",
    "start",
    "refine",
    "pivot",
    "narrow",
    "expand",
    "compare",
]
PlanningModeCardStatus = Literal["available", "in_development"]
AdvancedAnchorCardStatus = Literal["available", "completed"]

TripFieldKey = Literal[
    "from_location",
    "from_location_flexible",
    "to_location",
    "start_date",
    "end_date",
    "travel_window",
    "trip_length",
    "weather_preference",
    "budget_posture",
    "budget_amount",
    "budget_currency",
    "budget_gbp",
    "adults",
    "children",
    "travelers_flexible",
    "activity_styles",
    "custom_style",
    "selected_modules",
]

ConversationFieldSource = Literal[
    "user_explicit",
    "user_inferred",
    "profile_default",
    "assistant_derived",
    "board_action",
]
ConversationFieldConfidence = Literal["low", "medium", "high"]
PlannerDecisionMemoryKey = Literal[
    "destination",
    "origin",
    "date_window",
    "travelers",
    "budget",
    "module_scope",
    "trip_style_direction",
    "trip_style_pace",
    "trip_style_tradeoffs",
    "selected_flights",
    "selected_stay",
    "selected_activities",
    "weather_context",
    "advanced_review",
    "conflict_resolution",
]
PlannerDecisionSource = Literal[
    "user_explicit",
    "board_action",
    "assistant_inferred",
    "profile_default",
    "provider",
    "system",
]
PlannerDecisionConfidence = Literal["low", "medium", "high"]
PlannerDecisionStatus = Literal[
    "working",
    "confirmed",
    "needs_review",
    "superseded",
]
PlannerConflictSeverity = Literal["info", "warning", "important"]
PlannerConflictCategory = Literal[
    "style_pace",
    "logistics",
    "stay_fit",
    "weather",
    "schedule_density",
    "provider_confidence",
]
PlannerConflictRevisionTarget = Literal[
    "flight",
    "stay",
    "trip_style",
    "activities",
    "review",
]
PlannerConflictStatus = Literal["open", "resolved", "deferred"]
PlannerConflictPriority = Literal["watch", "worth_resolving", "resolve_first"]
PlannerConflictResolutionAction = Literal[
    "review_section",
    "safe_edit",
    "defer",
    "resolve",
]
PlannerConflictSafeEdit = Literal[
    "reserve_maybe_activity_extras",
    "keep_flights_open",
    "mark_stay_for_review",
    "keep_indoor_backup_notes",
    "defer_as_caution",
]

ConversationOptionKind = Literal[
    "destination",
    "origin",
    "timing_window",
    "trip_length",
    "activity_style",
    "planning_module",
    "budget_posture",
]

ConversationQuestionStatus = Literal["open", "answered", "dismissed"]
PlannerChecklistStatus = Literal["known", "needed"]


class PlannerDecisionCard(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=240)
    options: list[str] = Field(default_factory=list, max_length=5)


class PlannerChecklistItem(BaseModel):
    id: str
    label: str = Field(..., min_length=1, max_length=80)
    status: PlannerChecklistStatus = "needed"
    value: str | None = Field(default=None, max_length=200)


class TripDetailsFieldMeta(BaseModel):
    field: TripFieldKey
    source: ConversationFieldSource | None = None
    confidence_level: ConversationFieldConfidence | None = None
    label: str | None = Field(default=None, max_length=80)


class DestinationSuggestionCard(BaseModel):
    id: str
    destination_name: str = Field(..., min_length=1, max_length=120)
    country_or_region: str = Field(..., min_length=1, max_length=120)
    image_url: str = Field(..., min_length=1, max_length=500)
    short_reason: str = Field(..., min_length=1, max_length=240)
    practicality_label: str = Field(..., min_length=1, max_length=120)
    fit_label: str | None = Field(default=None, max_length=80)
    best_for: str | None = Field(default=None, max_length=160)
    tradeoffs: list[str] = Field(default_factory=list, max_length=3)
    recommendation_note: str | None = Field(default=None, max_length=200)
    change_note: str | None = Field(default=None, max_length=200)
    selection_status: DestinationSuggestionSelectionStatus = "suggested"


class TripDetailsCollectionFormState(BaseModel):
    from_location: str | None = Field(default=None, max_length=160)
    from_location_flexible: bool | None = None
    to_location: str | None = Field(default=None, max_length=160)
    selected_modules: TripModuleSelection = Field(default_factory=TripModuleSelection)
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    weather_preference: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    end_date: date | None = None
    adults: int | None = Field(default=None, ge=0)
    children: int | None = Field(default=None, ge=0)
    travelers_flexible: bool | None = None
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    custom_style: str | None = Field(default=None, max_length=160)
    budget_posture: BudgetPosture | None = None
    budget_amount: float | None = Field(default=None, gt=0)
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3)
    budget_gbp: float | None = Field(default=None, gt=0)

    @field_validator("budget_currency", mode="before")
    @classmethod
    def normalize_budget_currency(cls, value):
        if value in (None, ""):
            return None
        normalized = str(value).strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("budget_currency must be a 3-letter ISO currency code")
        return normalized


class PlanningModeChoiceCard(BaseModel):
    id: PlannerPlanningMode
    title: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=240)
    bullets: list[str] = Field(default_factory=list, max_length=5)
    status: PlanningModeCardStatus = "available"
    badge: str | None = Field(default=None, max_length=80)
    cta_label: str | None = Field(default=None, max_length=80)


class AdvancedAnchorChoiceCard(BaseModel):
    id: PlannerAdvancedAnchor
    title: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=240)
    bullets: list[str] = Field(default_factory=list, max_length=5)
    status: AdvancedAnchorCardStatus = "available"
    recommended: bool = False
    badge: str | None = Field(default=None, max_length=80)
    cta_label: str | None = Field(default=None, max_length=80)


class AdvancedDateOptionCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    start_date: date
    end_date: date
    nights: int = Field(..., ge=1, le=30)
    reason: str = Field(..., min_length=1, max_length=160)
    recommended: bool = False
    cta_label: str | None = Field(default=None, max_length=80)


class AdvancedDateResolutionState(BaseModel):
    source_timing_text: str | None = Field(default=None, max_length=120)
    source_trip_length_text: str | None = Field(default=None, max_length=120)
    recommended_date_options: list[AdvancedDateOptionCard] = Field(
        default_factory=list,
        max_length=3,
    )
    selected_date_option_id: str | None = Field(default=None, max_length=80)
    selected_start_date: date | None = None
    selected_end_date: date | None = None
    selection_status: PlannerDateResolutionStatus = "none"
    selection_rationale: str | None = Field(default=None, max_length=200)
    requires_confirmation: bool = True


class AdvancedFlightStrategyCard(BaseModel):
    id: PlannerFlightStrategy
    title: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=240)
    bullets: list[str] = Field(default_factory=list, max_length=4)
    recommended: bool = False


class AdvancedFlightOptionCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    direction: Literal["outbound", "return"]
    carrier: str = Field(..., min_length=1, max_length=120)
    flight_number: str | None = Field(default=None, max_length=80)
    departure_airport: str = Field(..., min_length=1, max_length=40)
    arrival_airport: str = Field(..., min_length=1, max_length=40)
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    duration_text: str | None = Field(default=None, max_length=80)
    price_text: str | None = Field(default=None, max_length=80)
    fare_amount: float | None = Field(default=None, ge=0)
    fare_currency: str | None = Field(default=None, min_length=3, max_length=3)
    stop_count: int | None = Field(default=None, ge=0, le=8)
    stop_details_available: bool | None = None
    layover_summary: str | None = Field(default=None, max_length=200)
    legs: list[FlightLegDetail] = Field(default_factory=list, max_length=8)
    timing_quality: str | None = Field(default=None, max_length=120)
    inventory_notice: str | None = Field(default=None, max_length=200)
    inventory_source: Literal["live", "cached", "placeholder"] | None = None
    summary: str = Field(..., min_length=1, max_length=240)
    tradeoffs: list[str] = Field(default_factory=list, max_length=4)
    source_kind: PlannerFlightOptionSource = "provider"
    recommended: bool = False


class AdvancedFlightPlanningState(BaseModel):
    strategy_cards: list[AdvancedFlightStrategyCard] = Field(
        default_factory=list,
        max_length=4,
    )
    outbound_options: list[AdvancedFlightOptionCard] = Field(
        default_factory=list,
        max_length=6,
    )
    return_options: list[AdvancedFlightOptionCard] = Field(
        default_factory=list,
        max_length=6,
    )
    selected_strategy: PlannerFlightStrategy | None = None
    selected_outbound_flight_id: str | None = Field(default=None, max_length=120)
    selected_return_flight_id: str | None = Field(default=None, max_length=120)
    selected_outbound_flight: AdvancedFlightOptionCard | None = None
    selected_return_flight: AdvancedFlightOptionCard | None = None
    selection_status: PlannerFlightSelectionStatus = "none"
    results_status: PlannerFlightResultsStatus = "blocked"
    missing_requirements: list[str] = Field(default_factory=list, max_length=5)
    workspace_summary: str | None = Field(default=None, max_length=240)
    selection_summary: str | None = Field(default=None, max_length=240)
    downstream_notes: list[str] = Field(default_factory=list, max_length=4)
    arrival_day_impact_summary: str | None = Field(default=None, max_length=240)
    departure_day_impact_summary: str | None = Field(default=None, max_length=240)
    timing_review_notes: list[str] = Field(default_factory=list, max_length=4)
    workspace_touched: bool = False
    completion_summary: str | None = Field(default=None, max_length=240)


class AdvancedWeatherPlanningState(BaseModel):
    results_status: PlannerWeatherResultsStatus = "not_requested"
    workspace_summary: str | None = Field(default=None, max_length=240)
    day_impact_summaries: list[str] = Field(default_factory=list, max_length=7)
    activity_influence_notes: list[str] = Field(default_factory=list, max_length=4)


class AdvancedReviewSectionCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    status: PlannerAdvancedReviewReadinessStatus = "flexible"
    summary: str = Field(..., min_length=1, max_length=280)
    notes: list[str] = Field(default_factory=list, max_length=4)
    revision_anchor: PlannerAdvancedAnchor | None = None
    cta_label: str | None = Field(default=None, max_length=80)


class AdvancedReviewDecisionSignal(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    value_summary: str = Field(..., min_length=1, max_length=240)
    source: PlannerDecisionSource = "system"
    source_label: str = Field(..., min_length=1, max_length=80)
    confidence: PlannerDecisionConfidence = "medium"
    confidence_label: str = Field(..., min_length=1, max_length=80)
    status: PlannerDecisionStatus = "working"
    note: str | None = Field(default=None, max_length=220)
    related_anchor: PlannerAdvancedAnchor | None = None


class PlannerConflictResolutionOption(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=80)
    action: PlannerConflictResolutionAction
    description: str = Field(..., min_length=1, max_length=220)
    revision_target: PlannerConflictRevisionTarget | None = None
    safe_edit: PlannerConflictSafeEdit | None = None


class PlannerConflictRecord(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    severity: PlannerConflictSeverity = "warning"
    category: PlannerConflictCategory
    affected_areas: list[str] = Field(default_factory=list, max_length=4)
    summary: str = Field(..., min_length=1, max_length=280)
    evidence: list[str] = Field(default_factory=list, max_length=4)
    source_decision_ids: list[str] = Field(default_factory=list, max_length=6)
    suggested_repair: str = Field(..., min_length=1, max_length=220)
    revision_target: PlannerConflictRevisionTarget | None = None
    priority_score: int = Field(default=50, ge=0, le=100)
    priority_label: PlannerConflictPriority = "worth_resolving"
    recommended_repair: str | None = Field(default=None, max_length=240)
    why_it_matters: str | None = Field(default=None, max_length=260)
    proactive_summary: str | None = Field(default=None, max_length=280)
    status: PlannerConflictStatus = "open"
    resolution_summary: str | None = Field(default=None, max_length=280)
    resolved_at: datetime | None = None
    resolution_action: PlannerConflictResolutionAction | None = None
    resolution_options: list[PlannerConflictResolutionOption] = Field(
        default_factory=list,
        max_length=4,
    )


class AdvancedReviewPlanningState(BaseModel):
    readiness_status: PlannerAdvancedReviewReadinessStatus = "flexible"
    workspace_summary: str | None = Field(default=None, max_length=280)
    completed_summary: str | None = Field(default=None, max_length=240)
    open_summary: str | None = Field(default=None, max_length=240)
    section_cards: list[AdvancedReviewSectionCard] = Field(
        default_factory=list,
        max_length=8,
    )
    review_notes: list[str] = Field(default_factory=list, max_length=6)
    decision_signals: list[AdvancedReviewDecisionSignal] = Field(
        default_factory=list,
        max_length=8,
    )


class AdvancedStayPlanningSegment(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    destination_name: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=240)


class AdvancedStayOptionCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    segment_id: str = Field(..., min_length=1, max_length=80)
    strategy_type: PlannerStayStrategyType = "single_base"
    title: str = Field(..., min_length=1, max_length=120)
    summary: str = Field(..., min_length=1, max_length=280)
    area_label: str | None = Field(default=None, max_length=120)
    areas: list[str] = Field(default_factory=list, max_length=4)
    best_for: list[str] = Field(default_factory=list, max_length=4)
    tradeoffs: list[str] = Field(default_factory=list, max_length=4)
    recommended: bool = False
    badge: str | None = Field(default=None, max_length=80)
    cta_label: str | None = Field(default=None, max_length=80)


class AdvancedStayHotelOptionCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    hotel_name: str = Field(..., min_length=1, max_length=160)
    area: str | None = Field(default=None, max_length=160)
    image_url: str | None = Field(default=None, max_length=1000)
    address: str | None = Field(default=None, max_length=240)
    source_url: str | None = Field(default=None, max_length=1000)
    source_label: str | None = Field(default=None, max_length=80)
    summary: str = Field(..., min_length=1, max_length=320)
    why_it_fits: str = Field(..., min_length=1, max_length=320)
    tradeoffs: list[str] = Field(default_factory=list, max_length=4)
    style_tags: list[PlannerHotelStyleTag] = Field(default_factory=list, max_length=5)
    fit_score: int = Field(default=0, ge=0, le=100)
    outside_active_filters: bool = False
    price_signal: str | None = Field(default=None, max_length=80)
    nightly_rate_amount: float | None = Field(default=None, ge=0)
    nightly_rate_currency: str | None = Field(default=None, max_length=8)
    nightly_tax_amount: float | None = Field(default=None, ge=0)
    rate_provider_name: str | None = Field(default=None, max_length=120)
    rate_note: str | None = Field(default=None, max_length=160)
    check_in: datetime | None = None
    check_out: datetime | None = None
    recommended: bool = False
    cta_label: str | None = Field(default=None, max_length=80)


class AdvancedStayHotelFilters(BaseModel):
    max_nightly_rate: float | None = Field(default=None, ge=0)
    area_filter: str | None = Field(default=None, max_length=160)
    style_filter: PlannerHotelStyleTag | None = None


class AdvancedActivityCandidateCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=160)
    kind: PlannerActivityCandidateKind = "activity"
    title: str = Field(..., min_length=1, max_length=160)
    latitude: float | None = None
    longitude: float | None = None
    venue_name: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=320)
    source_label: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=1000)
    availability_text: str | None = Field(default=None, max_length=120)
    price_text: str | None = Field(default=None, max_length=120)
    status_text: str | None = Field(default=None, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, ge=15, le=480)
    time_label: str | None = Field(default=None, max_length=40)
    start_at: datetime | None = None
    end_at: datetime | None = None
    recommended: bool = False
    disposition: PlannerActivityDisposition = "maybe"
    ranking_reasons: list[str] = Field(default_factory=list, max_length=4)


class AdvancedActivityPlacementPreference(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=160)
    day_index: int | None = Field(default=None, ge=1, le=30)
    daypart: PlannerActivityDaypart | None = None
    reserved: bool = False


class AdvancedActivityTimelineBlock(BaseModel):
    id: str = Field(..., min_length=1, max_length=160)
    type: PlannerActivityTimelineBlockType
    candidate_id: str | None = Field(default=None, max_length=160)
    title: str = Field(..., min_length=1, max_length=160)
    day_index: int = Field(..., ge=1, le=30)
    day_label: str = Field(..., min_length=1, max_length=40)
    daypart: PlannerActivityDaypart | None = None
    venue_name: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=240)
    start_at: datetime | None = None
    end_at: datetime | None = None
    summary: str | None = Field(default=None, max_length=320)
    details: list[str] = Field(default_factory=list, max_length=6)
    source_label: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=1000)
    availability_text: str | None = Field(default=None, max_length=120)
    price_text: str | None = Field(default=None, max_length=120)
    status_text: str | None = Field(default=None, max_length=120)
    fixed_time: bool = False
    manual_override: bool = False


class AdvancedActivityDayPlan(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    day_index: int = Field(..., ge=1, le=30)
    day_label: str = Field(..., min_length=1, max_length=40)
    date: calendar_date | None = None
    blocks: list[AdvancedActivityTimelineBlock] = Field(default_factory=list, max_length=12)


class AdvancedActivityPlanningState(BaseModel):
    recommended_candidates: list[AdvancedActivityCandidateCard] = Field(
        default_factory=list,
        max_length=20,
    )
    visible_candidates: list[AdvancedActivityCandidateCard] = Field(
        default_factory=list,
        max_length=20,
    )
    placement_preferences: list[AdvancedActivityPlacementPreference] = Field(
        default_factory=list,
        max_length=20,
    )
    essential_ids: list[str] = Field(default_factory=list, max_length=20)
    maybe_ids: list[str] = Field(default_factory=list, max_length=20)
    passed_ids: list[str] = Field(default_factory=list, max_length=20)
    selected_event_ids: list[str] = Field(default_factory=list, max_length=20)
    reserved_candidate_ids: list[str] = Field(default_factory=list, max_length=20)
    workspace_summary: str | None = Field(default=None, max_length=240)
    day_plans: list[AdvancedActivityDayPlan] = Field(default_factory=list, max_length=30)
    timeline_blocks: list[AdvancedActivityTimelineBlock] = Field(
        default_factory=list,
        max_length=120,
    )
    unscheduled_candidate_ids: list[str] = Field(default_factory=list, max_length=20)
    schedule_summary: str | None = Field(default=None, max_length=240)
    schedule_notes: list[str] = Field(default_factory=list, max_length=4)
    schedule_status: PlannerActivityScheduleStatus = "none"
    workspace_touched: bool = False
    completion_status: PlannerActivityCompletionStatus = "in_progress"
    completion_summary: str | None = Field(default=None, max_length=240)
    completion_anchor_ids: list[str] = Field(default_factory=list, max_length=8)


class TripStyleTradeoffOption(BaseModel):
    value: PlannerTripStyleTradeoffChoice
    label: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=240)
    recommended: bool = False


class TripStyleTradeoffCard(BaseModel):
    axis: PlannerTripStyleTradeoffAxis
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=280)
    options: list[TripStyleTradeoffOption] = Field(default_factory=list, max_length=3)


class TripStyleTradeoffDecision(BaseModel):
    axis: PlannerTripStyleTradeoffAxis
    selected_value: PlannerTripStyleTradeoffChoice


class TripStylePlanningState(BaseModel):
    substep: PlannerTripStyleSubstep = "direction"
    recommended_primary_directions: list[PlannerTripDirectionPrimary] = Field(
        default_factory=list,
        max_length=5,
    )
    recommended_accents: list[PlannerTripDirectionAccent] = Field(
        default_factory=list,
        max_length=5,
    )
    selected_primary_direction: PlannerTripDirectionPrimary | None = None
    selected_accent: PlannerTripDirectionAccent | None = None
    selection_status: PlannerTripStyleSelectionStatus = "none"
    workspace_summary: str | None = Field(default=None, max_length=240)
    selection_rationale: str | None = Field(default=None, max_length=320)
    downstream_influence_summary: str | None = Field(default=None, max_length=240)
    recommended_paces: list[PlannerTripPace] = Field(
        default_factory=list,
        max_length=3,
    )
    selected_pace: PlannerTripPace | None = None
    pace_status: PlannerTripStyleSelectionStatus = "none"
    pace_rationale: str | None = Field(default=None, max_length=320)
    pace_downstream_influence_summary: str | None = Field(
        default=None,
        max_length=240,
    )
    recommended_tradeoff_cards: list[TripStyleTradeoffCard] = Field(
        default_factory=list,
        max_length=3,
    )
    selected_tradeoffs: list[TripStyleTradeoffDecision] = Field(
        default_factory=list,
        max_length=4,
    )
    tradeoff_status: PlannerTripStyleSelectionStatus = "none"
    tradeoff_rationale: str | None = Field(default=None, max_length=320)
    tradeoff_downstream_influence_summary: str | None = Field(
        default=None,
        max_length=320,
    )
    workspace_touched: bool = False
    completion_summary: str | None = Field(default=None, max_length=240)


class AdvancedStayPlanningState(BaseModel):
    active_segment_id: str | None = Field(default=None, max_length=80)
    segments: list[AdvancedStayPlanningSegment] = Field(default_factory=list)
    hotel_substep: PlannerStayHotelSubstep = "strategy_choice"
    recommended_stay_options: list[AdvancedStayOptionCard] = Field(
        default_factory=list,
        max_length=4,
    )
    selected_stay_option_id: str | None = Field(default=None, max_length=80)
    selected_stay_direction: str | None = Field(default=None, max_length=160)
    selection_status: PlannerStaySelectionStatus = "none"
    selection_rationale: str | None = Field(default=None, max_length=320)
    selection_assumptions: list[str] = Field(default_factory=list, max_length=4)
    compatibility_status: PlannerStayCompatibilityStatus = "fit"
    compatibility_notes: list[str] = Field(default_factory=list, max_length=4)
    recommended_hotels: list[AdvancedStayHotelOptionCard] = Field(
        default_factory=list,
        max_length=24,
    )
    selected_hotel_id: str | None = Field(default=None, max_length=120)
    selected_hotel_name: str | None = Field(default=None, max_length=160)
    hotel_selection_status: PlannerStaySelectionStatus = "none"
    hotel_selection_rationale: str | None = Field(default=None, max_length=320)
    hotel_selection_assumptions: list[str] = Field(default_factory=list, max_length=4)
    hotel_compatibility_status: PlannerStayCompatibilityStatus = "fit"
    hotel_compatibility_notes: list[str] = Field(default_factory=list, max_length=4)
    hotel_filters: AdvancedStayHotelFilters = Field(
        default_factory=AdvancedStayHotelFilters
    )
    hotel_sort_order: PlannerHotelSortOrder = "best_fit"
    hotel_results_status: PlannerHotelResultsStatus = "blocked"
    hotel_results_summary: str | None = Field(default=None, max_length=240)
    hotel_page: int = Field(default=1, ge=1, le=99)
    hotel_page_size: int = Field(default=6, ge=1, le=24)
    hotel_total_results: int = Field(default=0, ge=0, le=500)
    hotel_total_pages: int = Field(default=1, ge=1, le=99)
    available_hotel_areas: list[str] = Field(default_factory=list, max_length=12)
    available_hotel_styles: list[PlannerHotelStyleTag] = Field(
        default_factory=list,
        max_length=10,
    )
    selected_hotel_card: AdvancedStayHotelOptionCard | None = None
    accepted_stay_review_signature: str | None = Field(default=None, max_length=400)
    accepted_stay_review_summary: str | None = Field(default=None, max_length=240)
    accepted_hotel_review_signature: str | None = Field(default=None, max_length=400)
    accepted_hotel_review_summary: str | None = Field(default=None, max_length=240)


class TripSuggestionBoardState(BaseModel):
    mode: TripSuggestionBoardMode = "helper"
    source_context: str | None = Field(default=None, max_length=240)
    title: str | None = Field(default=None, max_length=160)
    subtitle: str | None = Field(default=None, max_length=320)
    cards: list[DestinationSuggestionCard] = Field(default_factory=list, max_length=6)
    discovery_turn_kind: DiscoveryTurnKind = "none"
    comparison_summary: str | None = Field(default=None, max_length=500)
    leading_recommendation: str | None = Field(default=None, max_length=240)
    planning_mode_cards: list[PlanningModeChoiceCard] = Field(
        default_factory=list,
        max_length=2,
    )
    date_option_cards: list[AdvancedDateOptionCard] = Field(
        default_factory=list,
        max_length=3,
    )
    selected_date_option_id: str | None = Field(default=None, max_length=80)
    selected_start_date: date | None = None
    selected_end_date: date | None = None
    date_selection_status: PlannerDateResolutionStatus | None = None
    date_selection_rationale: str | None = Field(default=None, max_length=200)
    date_requires_confirmation: bool = False
    source_timing_text: str | None = Field(default=None, max_length=120)
    source_trip_length_text: str | None = Field(default=None, max_length=120)
    advanced_anchor_cards: list[AdvancedAnchorChoiceCard] = Field(
        default_factory=list,
        max_length=4,
    )
    flight_strategy_cards: list[AdvancedFlightStrategyCard] = Field(
        default_factory=list,
        max_length=4,
    )
    outbound_flight_options: list[AdvancedFlightOptionCard] = Field(
        default_factory=list,
        max_length=6,
    )
    return_flight_options: list[AdvancedFlightOptionCard] = Field(
        default_factory=list,
        max_length=6,
    )
    selected_flight_strategy: PlannerFlightStrategy | None = None
    selected_outbound_flight_id: str | None = Field(default=None, max_length=120)
    selected_return_flight_id: str | None = Field(default=None, max_length=120)
    selected_outbound_flight: AdvancedFlightOptionCard | None = None
    selected_return_flight: AdvancedFlightOptionCard | None = None
    flight_selection_status: PlannerFlightSelectionStatus | None = None
    flight_results_status: PlannerFlightResultsStatus | None = None
    flight_missing_requirements: list[str] = Field(default_factory=list, max_length=5)
    flight_workspace_summary: str | None = Field(default=None, max_length=240)
    flight_selection_summary: str | None = Field(default=None, max_length=240)
    flight_downstream_notes: list[str] = Field(default_factory=list, max_length=4)
    flight_arrival_day_impact_summary: str | None = Field(default=None, max_length=240)
    flight_departure_day_impact_summary: str | None = Field(default=None, max_length=240)
    flight_timing_review_notes: list[str] = Field(default_factory=list, max_length=4)
    flight_completion_summary: str | None = Field(default=None, max_length=240)
    weather_results_status: PlannerWeatherResultsStatus | None = None
    weather_workspace_summary: str | None = Field(default=None, max_length=240)
    weather_day_impact_summaries: list[str] = Field(default_factory=list, max_length=7)
    weather_activity_influence_notes: list[str] = Field(default_factory=list, max_length=4)
    advanced_review_readiness_status: PlannerAdvancedReviewReadinessStatus | None = None
    advanced_review_summary: str | None = Field(default=None, max_length=280)
    advanced_review_completed_summary: str | None = Field(default=None, max_length=240)
    advanced_review_open_summary: str | None = Field(default=None, max_length=240)
    advanced_review_section_cards: list[AdvancedReviewSectionCard] = Field(
        default_factory=list,
        max_length=8,
    )
    advanced_review_notes: list[str] = Field(default_factory=list, max_length=6)
    advanced_review_decision_signals: list[AdvancedReviewDecisionSignal] = Field(
        default_factory=list,
        max_length=8,
    )
    planner_conflicts: list[PlannerConflictRecord] = Field(
        default_factory=list,
        max_length=8,
    )
    stay_cards: list[AdvancedStayOptionCard] = Field(default_factory=list, max_length=4)
    hotel_cards: list[AdvancedStayHotelOptionCard] = Field(default_factory=list, max_length=8)
    activity_candidates: list[AdvancedActivityCandidateCard] = Field(
        default_factory=list,
        max_length=20,
    )
    essential_ids: list[str] = Field(default_factory=list, max_length=20)
    maybe_ids: list[str] = Field(default_factory=list, max_length=20)
    passed_ids: list[str] = Field(default_factory=list, max_length=20)
    selected_event_ids: list[str] = Field(default_factory=list, max_length=20)
    reserved_candidate_ids: list[str] = Field(default_factory=list, max_length=20)
    activity_workspace_summary: str | None = Field(default=None, max_length=240)
    trip_style_recommended_primaries: list[PlannerTripDirectionPrimary] = Field(
        default_factory=list,
        max_length=5,
    )
    trip_style_recommended_accents: list[PlannerTripDirectionAccent] = Field(
        default_factory=list,
        max_length=5,
    )
    selected_trip_style_primary: PlannerTripDirectionPrimary | None = None
    selected_trip_style_accent: PlannerTripDirectionAccent | None = None
    trip_style_selection_status: PlannerTripStyleSelectionStatus | None = None
    trip_style_substep: PlannerTripStyleSubstep | None = None
    trip_style_workspace_summary: str | None = Field(default=None, max_length=240)
    trip_style_selection_rationale: str | None = Field(default=None, max_length=320)
    trip_style_downstream_influence_summary: str | None = Field(
        default=None,
        max_length=240,
    )
    trip_style_recommended_paces: list[PlannerTripPace] = Field(
        default_factory=list,
        max_length=3,
    )
    selected_trip_style_pace: PlannerTripPace | None = None
    trip_style_pace_status: PlannerTripStyleSelectionStatus | None = None
    trip_style_pace_rationale: str | None = Field(default=None, max_length=320)
    trip_style_pace_downstream_influence_summary: str | None = Field(
        default=None,
        max_length=240,
    )
    trip_style_recommended_tradeoff_cards: list[TripStyleTradeoffCard] = Field(
        default_factory=list,
        max_length=3,
    )
    selected_trip_style_tradeoffs: list[TripStyleTradeoffDecision] = Field(
        default_factory=list,
        max_length=4,
    )
    trip_style_tradeoff_status: PlannerTripStyleSelectionStatus | None = None
    trip_style_tradeoff_rationale: str | None = Field(default=None, max_length=320)
    trip_style_tradeoff_downstream_influence_summary: str | None = Field(
        default=None,
        max_length=320,
    )
    trip_style_completion_summary: str | None = Field(default=None, max_length=240)
    activity_day_plans: list[AdvancedActivityDayPlan] = Field(
        default_factory=list,
        max_length=30,
    )
    unscheduled_activity_candidate_ids: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    activity_schedule_summary: str | None = Field(default=None, max_length=240)
    activity_schedule_notes: list[str] = Field(default_factory=list, max_length=4)
    activity_schedule_status: PlannerActivityScheduleStatus = "none"
    selected_stay_option_id: str | None = Field(default=None, max_length=80)
    stay_selection_status: PlannerStaySelectionStatus | None = None
    stay_selection_rationale: str | None = Field(default=None, max_length=320)
    stay_selection_assumptions: list[str] = Field(default_factory=list, max_length=4)
    stay_compatibility_status: PlannerStayCompatibilityStatus | None = None
    stay_compatibility_notes: list[str] = Field(default_factory=list, max_length=4)
    selected_hotel_id: str | None = Field(default=None, max_length=120)
    selected_hotel_name: str | None = Field(default=None, max_length=160)
    hotel_selection_status: PlannerStaySelectionStatus | None = None
    hotel_selection_rationale: str | None = Field(default=None, max_length=320)
    hotel_selection_assumptions: list[str] = Field(default_factory=list, max_length=4)
    hotel_compatibility_status: PlannerStayCompatibilityStatus | None = None
    hotel_compatibility_notes: list[str] = Field(default_factory=list, max_length=4)
    hotel_filters: AdvancedStayHotelFilters = Field(
        default_factory=AdvancedStayHotelFilters
    )
    hotel_sort_order: PlannerHotelSortOrder = "best_fit"
    hotel_results_status: PlannerHotelResultsStatus | None = None
    hotel_results_summary: str | None = Field(default=None, max_length=240)
    hotel_page: int = Field(default=1, ge=1, le=99)
    hotel_page_size: int = Field(default=6, ge=1, le=24)
    hotel_total_results: int = Field(default=0, ge=0, le=500)
    hotel_total_pages: int = Field(default=1, ge=1, le=99)
    available_hotel_areas: list[str] = Field(default_factory=list, max_length=12)
    available_hotel_styles: list[PlannerHotelStyleTag] = Field(
        default_factory=list,
        max_length=10,
    )
    selected_hotel_card: AdvancedStayHotelOptionCard | None = None
    have_details: list[PlannerChecklistItem] = Field(default_factory=list)
    need_details: list[PlannerChecklistItem] = Field(default_factory=list)
    visible_steps: list[TripDetailsStepKey] = Field(default_factory=list)
    required_steps: list[TripDetailsStepKey] = Field(default_factory=list)
    suggested_step: TripDetailsStepKey | None = None
    details_field_meta: dict[TripFieldKey, TripDetailsFieldMeta] = Field(
        default_factory=dict
    )
    details_form: TripDetailsCollectionFormState | None = None
    confirm_cta_label: str | None = Field(default=None, max_length=120)
    own_choice_prompt: str | None = Field(default=None, max_length=240)


class ConversationQuestion(BaseModel):
    id: str
    question: str = Field(..., min_length=1, max_length=240)
    field: TripFieldKey | None = None
    step: TripDetailsStepKey | None = None
    priority: int = Field(default=1, ge=1, le=5)
    why: str | None = Field(default=None, max_length=200)
    status: ConversationQuestionStatus = "open"


class ConversationFieldMemory(BaseModel):
    field: TripFieldKey
    value: Any = None
    confidence_level: ConversationFieldConfidence | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: ConversationFieldSource = "assistant_derived"
    source_turn_id: str | None = Field(default=None, max_length=80)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class ConversationOptionMemory(BaseModel):
    kind: ConversationOptionKind
    value: str = Field(..., min_length=1, max_length=160)
    source_turn_id: str | None = Field(default=None, max_length=80)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class ConversationDecisionEvent(BaseModel):
    id: str
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=240)
    options: list[str] = Field(default_factory=list, max_length=5)
    selected_option: str | None = Field(default=None, max_length=160)
    source_turn_id: str | None = Field(default=None, max_length=80)
    resolved_at: datetime | None = None


class PlannerDecisionMemoryRecord(BaseModel):
    key: PlannerDecisionMemoryKey
    value_summary: str = Field(..., min_length=1, max_length=240)
    source: PlannerDecisionSource = "system"
    confidence: PlannerDecisionConfidence = "medium"
    status: PlannerDecisionStatus = "working"
    rationale: str | None = Field(default=None, max_length=320)
    related_anchor: PlannerAdvancedAnchor | None = None
    updated_at: datetime | None = None


class ConversationTurnSummary(BaseModel):
    turn_id: str
    user_message: str = Field(..., min_length=1, max_length=4000)
    assistant_message: str | None = Field(default=None, max_length=4000)
    summary_text: str | None = Field(default=None, max_length=400)
    changed_fields: list[TripFieldKey] = Field(default_factory=list)
    open_fields: list[TripFieldKey] = Field(default_factory=list)
    next_open_question: str | None = Field(default=None, max_length=240)
    active_goal: str | None = Field(default=None, max_length=240)
    resulting_phase: ChatPlannerPhase = "opening"
    created_at: datetime | None = None


class TripConversationMemory(BaseModel):
    field_memory: dict[TripFieldKey, ConversationFieldMemory] = Field(
        default_factory=dict
    )
    decision_memory: list[PlannerDecisionMemoryRecord] = Field(
        default_factory=list,
        max_length=24,
    )
    mentioned_options: list[ConversationOptionMemory] = Field(default_factory=list)
    rejected_options: list[ConversationOptionMemory] = Field(default_factory=list)
    decision_history: list[ConversationDecisionEvent] = Field(default_factory=list)
    turn_summaries: list[ConversationTurnSummary] = Field(default_factory=list)


class QuickPlanFinalizationState(BaseModel):
    accepted: bool = False
    review_status: QuickPlanReviewStatus | None = None
    quality_status: str | None = None
    brochure_eligible: bool = False
    accepted_modules: list[PlanningModuleKey] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list, max_length=8)
    review_result: dict[str, Any] = Field(default_factory=dict)
    quality_result: dict[str, Any] = Field(default_factory=dict)
    intelligence_summary: dict[str, Any] = Field(default_factory=dict)


class TripConversationState(BaseModel):
    phase: ChatPlannerPhase = "opening"
    planning_mode: PlannerPlanningMode | None = None
    planning_mode_status: PlannerPlanningModeStatus = "not_selected"
    advanced_step: PlannerAdvancedStep | None = None
    advanced_anchor: PlannerAdvancedAnchor | None = None
    confirmation_status: PlannerConfirmationStatus = "unconfirmed"
    finalized_at: datetime | None = None
    finalized_via: PlannerFinalizedVia | None = None
    open_questions: list[ConversationQuestion] = Field(default_factory=list)
    decision_cards: list[PlannerDecisionCard] = Field(default_factory=list)
    last_turn_summary: str | None = Field(default=None, max_length=400)
    active_goals: list[str] = Field(default_factory=list)
    planner_conflicts: list[PlannerConflictRecord] = Field(
        default_factory=list,
        max_length=8,
    )
    quick_plan_finalization: QuickPlanFinalizationState = Field(
        default_factory=QuickPlanFinalizationState
    )
    advanced_date_resolution: AdvancedDateResolutionState = Field(
        default_factory=AdvancedDateResolutionState
    )
    flight_planning: AdvancedFlightPlanningState = Field(
        default_factory=AdvancedFlightPlanningState
    )
    weather_planning: AdvancedWeatherPlanningState = Field(
        default_factory=AdvancedWeatherPlanningState
    )
    advanced_review_planning: AdvancedReviewPlanningState = Field(
        default_factory=AdvancedReviewPlanningState
    )
    trip_style_planning: TripStylePlanningState = Field(
        default_factory=TripStylePlanningState
    )
    activity_planning: AdvancedActivityPlanningState = Field(
        default_factory=AdvancedActivityPlanningState
    )
    stay_planning: AdvancedStayPlanningState = Field(
        default_factory=AdvancedStayPlanningState
    )
    suggestion_board: TripSuggestionBoardState = Field(
        default_factory=TripSuggestionBoardState
    )
    memory: TripConversationMemory = Field(default_factory=TripConversationMemory)


class CheckpointConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=4000)
    created_at: datetime | None = None
