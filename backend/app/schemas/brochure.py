from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    PlanningModuleKey,
    TimelineItem,
    TripBudgetEstimate,
    WeatherDetail,
)


BrochureWarningCategory = Literal[
    "timing",
    "logistics",
    "budget",
    "weather",
    "selection_pending",
    "review",
]
BrochureSnapshotStatus = Literal["latest", "historical"]
BrochureAdvancedReviewStatus = Literal["ready", "needs_review", "flexible"]


class BrochureHeroImage(BaseModel):
    url: str = Field(..., min_length=1, max_length=600)
    alt_text: str = Field(..., min_length=1, max_length=200)
    attribution: str | None = Field(default=None, max_length=160)


class BrochureMetric(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    value: str = Field(..., min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=240)


class BrochureWarning(BaseModel):
    id: str
    category: BrochureWarningCategory
    title: str = Field(..., min_length=1, max_length=120)
    message: str = Field(..., min_length=1, max_length=320)
    related_timeline_ids: list[str] = Field(default_factory=list)


class BrochureSection(BaseModel):
    id: str
    title: str = Field(..., min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=320)


class BrochureAdvancedSectionSummary(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    status: BrochureAdvancedReviewStatus = "flexible"
    summary: str = Field(..., min_length=1, max_length=320)
    notes: list[str] = Field(default_factory=list, max_length=4)


class BrochureResourceLink(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    url: str = Field(..., min_length=1, max_length=600)


class BrochureItineraryDay(BaseModel):
    id: str
    label: str = Field(..., min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=320)
    items: list[TimelineItem] = Field(default_factory=list)


class BrochureBudgetSummary(BaseModel):
    headline: str = Field(..., min_length=1, max_length=160)
    detail: str = Field(..., min_length=1, max_length=320)


class BrochureTravelSummary(BaseModel):
    headline: str = Field(..., min_length=1, max_length=160)
    detail: str = Field(..., min_length=1, max_length=320)


class BrochureSnapshotPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    route_text: str = Field(..., min_length=1, max_length=320)
    origin_label: str | None = Field(default=None, max_length=160)
    destination_label: str | None = Field(default=None, max_length=160)
    travel_window_text: str = Field(..., min_length=1, max_length=200)
    party_text: str = Field(..., min_length=1, max_length=120)
    budget_text: str = Field(..., min_length=1, max_length=120)
    style_tags: list[str] = Field(default_factory=list)
    module_tags: list[str] = Field(default_factory=list)
    planning_mode: Literal["quick", "advanced"] | None = None
    quick_plan_module_scope: list[PlanningModuleKey] = Field(default_factory=list)
    quick_plan_assumptions: list[dict] = Field(default_factory=list)
    quick_plan_review_status: str | None = None
    quick_plan_quality_status: str | None = None
    quick_plan_intelligence_summary: dict[str, Any] = Field(default_factory=dict)
    quick_plan_excluded_modules: list[dict[str, Any]] = Field(default_factory=list)
    quick_plan_provider_confidence_notes: list[str] = Field(default_factory=list)
    executive_summary: str = Field(..., min_length=1, max_length=500)
    hero_image: BrochureHeroImage
    metrics: list[BrochureMetric] = Field(default_factory=list)
    sections: list[BrochureSection] = Field(default_factory=list)
    advanced_review_status: BrochureAdvancedReviewStatus | None = None
    advanced_review_summary: str | None = Field(default=None, max_length=400)
    advanced_section_summaries: list[BrochureAdvancedSectionSummary] = Field(
        default_factory=list
    )
    trip_character_summary: str | None = Field(default=None, max_length=400)
    planned_experience_summary: str | None = Field(default=None, max_length=400)
    flexible_items: list[str] = Field(default_factory=list)
    worth_reviewing_notes: list[str] = Field(default_factory=list)
    warnings: list[BrochureWarning] = Field(default_factory=list)
    itinerary_days: list[BrochureItineraryDay] = Field(default_factory=list)
    flights: list[FlightDetail] = Field(default_factory=list)
    stays: list[HotelStayDetail] = Field(default_factory=list)
    weather: list[WeatherDetail] = Field(default_factory=list)
    highlights: list[ActivityDetail] = Field(default_factory=list)
    planning_notes: list[str] = Field(default_factory=list)
    budget_estimate: TripBudgetEstimate | None = None
    budget_summary: BrochureBudgetSummary
    travel_summary: BrochureTravelSummary
    resources: list[BrochureResourceLink] = Field(default_factory=list)


class BrochureSnapshotSummary(BaseModel):
    snapshot_id: str
    trip_id: str
    version_number: int
    status: BrochureSnapshotStatus
    finalized_at: datetime
    created_at: datetime
    pdf_file_name: str


class BrochureHistoryItem(BrochureSnapshotSummary):
    is_latest: bool = False


class BrochureSnapshot(BaseModel):
    snapshot_id: str
    trip_id: str
    version_number: int
    status: BrochureSnapshotStatus
    finalized_at: datetime
    created_at: datetime
    pdf_file_name: str
    payload: BrochureSnapshotPayload


class BrochureHistoryResponse(BaseModel):
    items: list[BrochureHistoryItem] = Field(default_factory=list)
