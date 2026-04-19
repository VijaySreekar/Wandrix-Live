from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TripStatus = Literal["collecting_requirements"]
ThreadStatus = Literal["ready"]


class TripCreateRequest(BaseModel):
    browser_session_id: str = Field(..., min_length=1, max_length=80)
    title: str | None = Field(default=None, min_length=1, max_length=160)


class TripCreateResponse(BaseModel):
    trip_id: str
    browser_session_id: str
    thread_id: str
    title: str
    trip_status: TripStatus
    thread_status: ThreadStatus
    created_at: datetime


class TripListItemResponse(TripCreateResponse):
    updated_at: datetime
    phase: str | None = None
    brochure_ready: bool = False
    from_location: str | None = None
    to_location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    selected_modules: list[str] = Field(default_factory=list)
    timeline_item_count: int = 0


class TripListResponse(BaseModel):
    items: list[TripListItemResponse]
