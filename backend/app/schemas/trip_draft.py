from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.package import TravelerDetails


ActivityStyle = Literal[
    "relaxed",
    "adventure",
    "luxury",
    "family",
    "culture",
    "nightlife",
    "romantic",
    "food",
    "outdoors",
]

PlanningModuleKey = Literal["flights", "weather", "activities", "hotels"]
TimelineItemType = Literal["flight", "transfer", "hotel", "activity", "meal", "weather", "note"]
TimelineItemStatus = Literal["draft", "confirmed"]
TripFieldKey = Literal[
    "from_location",
    "to_location",
    "start_date",
    "end_date",
    "budget_gbp",
    "adults",
    "children",
    "activity_styles",
    "selected_modules",
]
TripPlanningPhase = Literal[
    "collecting_requirements",
    "planning",
    "ready_for_review",
    "finalized",
]


class TripModuleSelection(BaseModel):
    flights: bool = True
    weather: bool = True
    activities: bool = True
    hotels: bool = True


class TripConfiguration(BaseModel):
    from_location: str | None = Field(default=None, max_length=160)
    to_location: str | None = Field(default=None, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    travelers: TravelerDetails = Field(default_factory=TravelerDetails)
    budget_gbp: float | None = Field(default=None, gt=0)
    selected_modules: TripModuleSelection = Field(default_factory=TripModuleSelection)
    activity_styles: list[ActivityStyle] = Field(default_factory=list)


class FlightDetail(BaseModel):
    id: str
    direction: Literal["outbound", "return"]
    carrier: str
    flight_number: str | None = None
    departure_airport: str
    arrival_airport: str
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    duration_text: str | None = None
    notes: list[str] = Field(default_factory=list)


class HotelStayDetail(BaseModel):
    id: str
    hotel_name: str
    area: str | None = None
    check_in: datetime | None = None
    check_out: datetime | None = None
    notes: list[str] = Field(default_factory=list)


class WeatherDetail(BaseModel):
    id: str
    day_label: str
    summary: str
    high_c: int | None = None
    low_c: int | None = None
    notes: list[str] = Field(default_factory=list)


class ActivityDetail(BaseModel):
    id: str
    title: str
    category: str | None = None
    day_label: str | None = None
    time_label: str | None = None
    notes: list[str] = Field(default_factory=list)


class TripModuleOutputs(BaseModel):
    flights: list[FlightDetail] = Field(default_factory=list)
    hotels: list[HotelStayDetail] = Field(default_factory=list)
    weather: list[WeatherDetail] = Field(default_factory=list)
    activities: list[ActivityDetail] = Field(default_factory=list)


class TimelineItem(BaseModel):
    id: str
    type: TimelineItemType
    title: str
    day_label: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    location_label: str | None = None
    summary: str | None = None
    details: list[str] = Field(default_factory=list)
    source_module: PlanningModuleKey | None = None
    status: TimelineItemStatus = "draft"


class PlannerDecisionCard(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=240)
    options: list[str] = Field(default_factory=list, max_length=5)


class TripDraftStatus(BaseModel):
    phase: TripPlanningPhase = "collecting_requirements"
    missing_fields: list[str] = Field(default_factory=list)
    confirmed_fields: list[TripFieldKey] = Field(default_factory=list)
    inferred_fields: list[TripFieldKey] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    decision_cards: list[PlannerDecisionCard] = Field(default_factory=list)
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


class TripDraftUpsertRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    configuration: TripConfiguration = Field(default_factory=TripConfiguration)
    timeline: list[TimelineItem] = Field(default_factory=list)
    module_outputs: TripModuleOutputs = Field(default_factory=TripModuleOutputs)
    status: TripDraftStatus = Field(default_factory=TripDraftStatus)
