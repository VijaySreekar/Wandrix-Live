from datetime import date, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.provider_usage_metric import ProviderUsageMetricModel


def increment_provider_usage(
    db: Session,
    *,
    provider_key: str,
    usage_month: date,
    succeeded: bool,
    quota_limit: int | None,
    last_status: str,
    last_used_at: datetime,
) -> None:
    table = ProviderUsageMetricModel.__table__
    statement = insert(ProviderUsageMetricModel).values(
        provider_key=provider_key,
        usage_month=usage_month,
        request_count=1,
        success_count=1 if succeeded else 0,
        error_count=0 if succeeded else 1,
        quota_limit=quota_limit,
        last_status=last_status,
        last_used_at=last_used_at,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[
            ProviderUsageMetricModel.provider_key,
            ProviderUsageMetricModel.usage_month,
        ],
        set_={
            "request_count": table.c.request_count + 1,
            "success_count": table.c.success_count + (1 if succeeded else 0),
            "error_count": table.c.error_count + (0 if succeeded else 1),
            "quota_limit": quota_limit,
            "last_status": last_status,
            "last_used_at": last_used_at,
        },
    )
    db.execute(statement)
    db.commit()


def list_provider_usage_for_month(
    db: Session,
    *,
    usage_month: date,
) -> list[ProviderUsageMetricModel]:
    return (
        db.query(ProviderUsageMetricModel)
        .filter(ProviderUsageMetricModel.usage_month == usage_month)
        .order_by(ProviderUsageMetricModel.provider_key.asc())
        .all()
    )
