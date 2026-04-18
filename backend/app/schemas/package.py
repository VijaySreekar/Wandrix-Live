from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TravelerDetails(BaseModel):
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)


class TravelPackageRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=120)
    destination: str = Field(..., min_length=2, max_length=120)
    start_date: date
    end_date: date
    travelers: TravelerDetails = Field(default_factory=TravelerDetails)
    budget_gbp: float | None = Field(default=None, gt=0)
    interests: list[str] = Field(default_factory=list)
    pace: Literal["relaxed", "balanced", "packed"] = "balanced"
    include_flights: bool = True
    include_hotel: bool = True

    @model_validator(mode="after")
    def validate_dates(self) -> "TravelPackageRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class DailyPlan(BaseModel):
    day: int
    date: date
    morning: str
    afternoon: str
    evening: str


class TravelPackageResponse(BaseModel):
    title: str
    summary: str
    origin: str
    destination: str
    duration_nights: int
    travelers: TravelerDetails
    estimated_total_gbp: float | None
    inclusions: list[str]
    recommendations: list[str]
    itinerary: list[DailyPlan]
