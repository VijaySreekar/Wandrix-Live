from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.trip_planning import ActivityStyle, BudgetPosture, TripModuleSelection


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
PlannerStaySelectionStatus = Literal["none", "selected", "needs_review"]
PlannerStayCompatibilityStatus = Literal["fit", "strained", "conflicted"]
PlannerStayStrategyType = Literal["single_base", "split_stay"]
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
    "decision_cards",
    "details_collection",
    "planning_mode_choice",
    "advanced_date_resolution",
    "advanced_anchor_choice",
    "advanced_next_step",
    "advanced_stay_choice",
    "advanced_stay_selected",
    "advanced_stay_review",
    "advanced_stay_hotel_choice",
    "advanced_stay_hotel_selected",
    "advanced_stay_hotel_review",
    "helper",
]
DestinationSuggestionSelectionStatus = Literal[
    "suggested",
    "leading",
    "confirmed",
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


class DestinationSuggestionCard(BaseModel):
    id: str
    destination_name: str = Field(..., min_length=1, max_length=120)
    country_or_region: str = Field(..., min_length=1, max_length=120)
    image_url: str = Field(..., min_length=1, max_length=500)
    short_reason: str = Field(..., min_length=1, max_length=240)
    practicality_label: str = Field(..., min_length=1, max_length=120)
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
    budget_gbp: float | None = Field(default=None, gt=0)


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


class TripSuggestionBoardState(BaseModel):
    mode: TripSuggestionBoardMode = "helper"
    source_context: str | None = Field(default=None, max_length=240)
    title: str | None = Field(default=None, max_length=160)
    subtitle: str | None = Field(default=None, max_length=320)
    cards: list[DestinationSuggestionCard] = Field(default_factory=list, max_length=4)
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
    stay_cards: list[AdvancedStayOptionCard] = Field(default_factory=list, max_length=4)
    hotel_cards: list[AdvancedStayHotelOptionCard] = Field(default_factory=list, max_length=8)
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
    mentioned_options: list[ConversationOptionMemory] = Field(default_factory=list)
    rejected_options: list[ConversationOptionMemory] = Field(default_factory=list)
    decision_history: list[ConversationDecisionEvent] = Field(default_factory=list)
    turn_summaries: list[ConversationTurnSummary] = Field(default_factory=list)


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
    advanced_date_resolution: AdvancedDateResolutionState = Field(
        default_factory=AdvancedDateResolutionState
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
