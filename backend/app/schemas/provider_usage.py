from datetime import date, datetime

from pydantic import BaseModel


class ProviderUsageItem(BaseModel):
    provider: str
    label: str
    quota_limit: int | None
    request_count: int
    success_count: int
    error_count: int
    remaining_count: int | None
    usage_month: date
    last_status: str | None = None
    last_used_at: datetime | None = None
    message: str


class ProviderUsageResponse(BaseModel):
    items: list[ProviderUsageItem]
