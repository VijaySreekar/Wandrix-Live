from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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
BudgetPosture = Literal["budget", "mid_range", "premium"]
BudgetEstimateCategoryKey = Literal[
    "flights",
    "stay",
    "activities",
    "food",
    "local_transport",
]
BudgetEstimateSource = Literal["provider_price", "planner_estimate", "unavailable"]

PlanningModuleKey = Literal["flights", "weather", "activities", "hotels"]
TimelineItemType = Literal[
    "flight",
    "transfer",
    "hotel",
    "activity",
    "event",
    "meal",
    "weather",
    "note",
]
TimelineItemStatus = Literal["draft", "confirmed"]
TimelineTimingSource = Literal["provider_exact", "planner_estimate", "user_confirmed"]


class PlannerTravelerDetails(BaseModel):
    adults: int | None = Field(default=None, ge=0)
    children: int | None = Field(default=None, ge=0)


class TripModuleSelection(BaseModel):
    flights: bool = True
    weather: bool = True
    activities: bool = True
    hotels: bool = True


class TripConfiguration(BaseModel):
    from_location: str | None = Field(default=None, max_length=160)
    from_location_flexible: bool | None = None
    to_location: str | None = Field(default=None, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    weather_preference: str | None = Field(default=None, max_length=80)
    travelers: PlannerTravelerDetails = Field(default_factory=PlannerTravelerDetails)
    travelers_flexible: bool | None = None
    budget_posture: BudgetPosture | None = None
    budget_amount: float | None = Field(default=None, gt=0)
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3)
    budget_gbp: float | None = Field(default=None, gt=0)
    selected_modules: TripModuleSelection = Field(default_factory=TripModuleSelection)
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    custom_style: str | None = Field(default=None, max_length=160)

    @field_validator("budget_currency", mode="before")
    @classmethod
    def normalize_budget_currency(cls, value):
        if value in (None, ""):
            return None
        normalized = str(value).strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("budget_currency must be a 3-letter ISO currency code")
        return normalized

    @model_validator(mode="after")
    def sync_legacy_budget_gbp(self):
        if (
            self.budget_amount is None
            and self.budget_gbp is not None
            and self.budget_currency in (None, "GBP")
        ):
            self.budget_amount = self.budget_gbp
            self.budget_currency = self.budget_currency or "GBP"
        if self.budget_currency == "GBP" and self.budget_gbp is None:
            self.budget_gbp = self.budget_amount
        if self.budget_currency != "GBP":
            self.budget_gbp = None
        return self


class FlightLegDetail(BaseModel):
    carrier: str | None = Field(default=None, max_length=120)
    flight_number: str | None = Field(default=None, max_length=80)
    departure_airport: str = Field(..., min_length=1, max_length=40)
    arrival_airport: str = Field(..., min_length=1, max_length=40)
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    duration_text: str | None = Field(default=None, max_length=80)


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
    notes: list[str] = Field(default_factory=list)


class HotelStayDetail(BaseModel):
    id: str
    hotel_name: str
    hotel_key: str | None = Field(default=None, max_length=160)
    area: str | None = None
    address: str | None = Field(default=None, max_length=240)
    image_url: str | None = Field(default=None, max_length=1000)
    source_url: str | None = Field(default=None, max_length=1000)
    source_label: str | None = Field(default=None, max_length=80)
    nightly_rate_amount: float | None = Field(default=None, ge=0)
    nightly_rate_currency: str | None = Field(default=None, max_length=8)
    nightly_tax_amount: float | None = Field(default=None, ge=0)
    rate_provider_name: str | None = Field(default=None, max_length=120)
    check_in: datetime | None = None
    check_out: datetime | None = None
    notes: list[str] = Field(default_factory=list)


class WeatherDetail(BaseModel):
    id: str
    day_label: str
    summary: str
    forecast_date: date | None = None
    weather_code: int | None = None
    condition_tags: list[str] = Field(default_factory=list, max_length=8)
    temperature_band: str | None = Field(default=None, max_length=40)
    weather_risk_level: Literal["low", "medium", "high"] | None = None
    high_c: int | None = None
    low_c: int | None = None
    notes: list[str] = Field(default_factory=list)


class ActivityDetail(BaseModel):
    id: str
    title: str
    category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    venue_name: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=240)
    source_label: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=1000)
    availability_text: str | None = Field(default=None, max_length=120)
    price_text: str | None = Field(default=None, max_length=120)
    status_text: str | None = Field(default=None, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, ge=15, le=480)
    start_at: datetime | None = None
    end_at: datetime | None = None
    day_label: str | None = None
    time_label: str | None = None
    notes: list[str] = Field(default_factory=list)


class TripModuleOutputs(BaseModel):
    flights: list[FlightDetail] = Field(default_factory=list)
    hotels: list[HotelStayDetail] = Field(default_factory=list)
    weather: list[WeatherDetail] = Field(default_factory=list)
    activities: list[ActivityDetail] = Field(default_factory=list)


class TripBudgetEstimateCategory(BaseModel):
    category: BudgetEstimateCategoryKey
    label: str
    low_amount: float | None = Field(default=None, ge=0)
    high_amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source: BudgetEstimateSource = "unavailable"
    notes: list[str] = Field(default_factory=list, max_length=4)


class TripBudgetEstimate(BaseModel):
    total_low_amount: float | None = Field(default=None, ge=0)
    total_high_amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    categories: list[TripBudgetEstimateCategory] = Field(default_factory=list)
    caveat: str = (
        "Directional estimate only; prices are not booking-confirmed and may change."
    )


class TimelineItem(BaseModel):
    id: str
    type: TimelineItemType
    title: str
    day_label: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    timing_source: TimelineTimingSource | None = None
    timing_note: str | None = Field(default=None, max_length=160)
    venue_name: str | None = Field(default=None, max_length=160)
    location_label: str | None = None
    summary: str | None = None
    details: list[str] = Field(default_factory=list)
    source_label: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=1000)
    availability_text: str | None = Field(default=None, max_length=120)
    price_text: str | None = Field(default=None, max_length=120)
    status_text: str | None = Field(default=None, max_length=120)
    source_module: PlanningModuleKey | None = None
    status: TimelineItemStatus = "draft"
