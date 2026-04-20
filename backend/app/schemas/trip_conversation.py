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
    "helper",
]
DestinationSuggestionSelectionStatus = Literal[
    "suggested",
    "leading",
    "confirmed",
]
PlanningModeCardStatus = Literal["available", "in_development"]

TripFieldKey = Literal[
    "from_location",
    "to_location",
    "start_date",
    "end_date",
    "travel_window",
    "trip_length",
    "budget_posture",
    "budget_gbp",
    "adults",
    "children",
    "activity_styles",
    "selected_modules",
]

ConversationFieldSource = Literal[
    "user_explicit",
    "user_inferred",
    "profile_default",
    "assistant_derived",
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
    to_location: str | None = Field(default=None, max_length=160)
    selected_modules: TripModuleSelection = Field(default_factory=TripModuleSelection)
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    adults: int | None = Field(default=None, ge=0)
    children: int | None = Field(default=None, ge=0)
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
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
    priority: int = Field(default=1, ge=1, le=5)
    status: ConversationQuestionStatus = "open"


class ConversationFieldMemory(BaseModel):
    field: TripFieldKey
    value: Any = None
    confidence: float = Field(default=0.0, ge=0, le=1)
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
    changed_fields: list[TripFieldKey] = Field(default_factory=list)
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
    confirmation_status: PlannerConfirmationStatus = "unconfirmed"
    finalized_at: datetime | None = None
    finalized_via: PlannerFinalizedVia | None = None
    open_questions: list[ConversationQuestion] = Field(default_factory=list)
    decision_cards: list[PlannerDecisionCard] = Field(default_factory=list)
    last_turn_summary: str | None = Field(default=None, max_length=400)
    active_goals: list[str] = Field(default_factory=list)
    suggestion_board: TripSuggestionBoardState = Field(
        default_factory=TripSuggestionBoardState
    )
    memory: TripConversationMemory = Field(default_factory=TripConversationMemory)


class CheckpointConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=4000)
    created_at: datetime | None = None
