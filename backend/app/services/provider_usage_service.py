from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.provider_usage_repository import (
    increment_provider_usage,
    list_provider_usage_for_month,
)
from app.schemas.provider_usage import ProviderUsageItem, ProviderUsageResponse


@dataclass(frozen=True)
class ProviderUsageDefinition:
    key: str
    label: str
    quota_limit: int | None
    message: str


PROVIDER_USAGE_DEFINITIONS: tuple[ProviderUsageDefinition, ...] = (
    ProviderUsageDefinition(
        key="xotelo",
        label="Xotelo hotel search",
        quota_limit=1000,
        message="RapidAPI destination hotel search used for cached hotel discovery.",
    ),
    ProviderUsageDefinition(
        key="agoda",
        label="Agoda overnight search",
        quota_limit=500,
        message="RapidAPI Agoda endpoint is wired for future property-level enrichment.",
    ),
    ProviderUsageDefinition(
        key="hotels_com",
        label="Hotels.com reviews",
        quota_limit=500,
        message="RapidAPI Hotels.com endpoint is wired for future property review enrichment.",
    ),
    ProviderUsageDefinition(
        key="travel_advisor",
        label="Travel Advisor Q&A",
        quota_limit=500,
        message="RapidAPI Travel Advisor endpoint is wired for future TripAdvisor Q&A enrichment.",
    ),
)


def record_provider_usage(
    *,
    provider_key: str,
    succeeded: bool,
    quota_limit: int | None = None,
    last_status: str = "ok",
) -> None:
    usage_month = date.today().replace(day=1)
    last_used_at = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        increment_provider_usage(
            db,
            provider_key=provider_key,
            usage_month=usage_month,
            succeeded=succeeded,
            quota_limit=quota_limit,
            last_status=last_status,
            last_used_at=last_used_at,
        )
    finally:
        db.close()


def get_provider_usage_summary(*, db: Session | None = None) -> ProviderUsageResponse:
    usage_month = date.today().replace(day=1)
    owns_session = db is None
    active_db = db or SessionLocal()

    try:
        persisted_items = {
            item.provider_key: item
            for item in list_provider_usage_for_month(active_db, usage_month=usage_month)
        }

        items = []
        for definition in PROVIDER_USAGE_DEFINITIONS:
            persisted = persisted_items.get(definition.key)
            request_count = persisted.request_count if persisted else 0
            success_count = persisted.success_count if persisted else 0
            error_count = persisted.error_count if persisted else 0
            quota_limit = (
                persisted.quota_limit
                if persisted and persisted.quota_limit is not None
                else definition.quota_limit
            )
            remaining_count = (
                max(quota_limit - request_count, 0) if quota_limit is not None else None
            )

            items.append(
                ProviderUsageItem(
                    provider=definition.key,
                    label=definition.label,
                    quota_limit=quota_limit,
                    request_count=request_count,
                    success_count=success_count,
                    error_count=error_count,
                    remaining_count=remaining_count,
                    usage_month=usage_month,
                    last_status=persisted.last_status if persisted else None,
                    last_used_at=persisted.last_used_at if persisted else None,
                    message=definition.message,
                )
            )

        return ProviderUsageResponse(items=items)
    finally:
        if owns_session:
            active_db.close()
