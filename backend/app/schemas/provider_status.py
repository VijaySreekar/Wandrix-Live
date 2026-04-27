from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ProviderHealthStatus = Literal["ok", "error", "not_configured"]


class ProviderStatusItem(BaseModel):
    provider: str
    status: ProviderHealthStatus
    message: str
    checked_at: datetime


class ProviderStatusResponse(BaseModel):
    items: list[ProviderStatusItem]
