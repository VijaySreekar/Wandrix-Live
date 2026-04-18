from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TripDraftModel(Base):
    __tablename__ = "trip_drafts"

    trip_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("trips.id", ondelete="CASCADE"),
        primary_key=True,
    )
    thread_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False)
    timeline: Mapped[list] = mapped_column(JSONB, nullable=False)
    module_outputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[dict] = mapped_column(JSONB, nullable=False)
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

    trip = relationship("TripModel", back_populates="draft")
