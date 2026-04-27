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
    latest_brochure_snapshot_id: str | None = None
    latest_brochure_version: int | None = None
    brochure_versions_count: int = 0
    from_location: str | None = None
    to_location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    travel_window: str | None = None
    trip_length: str | None = None
    selected_modules: list[str] = Field(default_factory=list)
    timeline_item_count: int = 0


class TripListResponse(BaseModel):
    items: list[TripListItemResponse]


class TripDeleteResponse(BaseModel):
    trip_id: str
    deleted: bool = True
