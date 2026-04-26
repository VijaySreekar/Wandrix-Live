from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderUsageMetricModel(Base):
    __tablename__ = "provider_usage_metrics"

    provider_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    usage_month: Mapped[date] = mapped_column(Date(), primary_key=True)
    request_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    quota_limit: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
