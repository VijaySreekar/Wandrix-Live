from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ChatPlannerPhase = Literal[
    "opening",
    "collecting_requirements",
    "shaping_trip",
    "enriching_modules",
    "reviewing",
]

TripFieldKey = Literal[
    "from_location",
    "to_location",
    "start_date",
    "end_date",
    "travel_window",
    "trip_length",
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


class PlannerDecisionCard(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=240)
    options: list[str] = Field(default_factory=list, max_length=5)


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
    open_questions: list[ConversationQuestion] = Field(default_factory=list)
    decision_cards: list[PlannerDecisionCard] = Field(default_factory=list)
    last_turn_summary: str | None = Field(default=None, max_length=400)
    active_goals: list[str] = Field(default_factory=list)
    memory: TripConversationMemory = Field(default_factory=TripConversationMemory)


class CheckpointConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=4000)
    created_at: datetime | None = None
