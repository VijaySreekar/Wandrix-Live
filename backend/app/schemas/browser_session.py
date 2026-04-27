from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BrowserSessionStatus = Literal["active"]


class BrowserSessionCreateRequest(BaseModel):
    timezone: str | None = Field(default=None, min_length=1, max_length=80)
    locale: str | None = Field(default=None, min_length=2, max_length=35)


class BrowserSessionCreateResponse(BaseModel):
    browser_session_id: str
    user_id: str | None
    timezone: str | None
    locale: str | None
    status: BrowserSessionStatus
    created_at: datetime
