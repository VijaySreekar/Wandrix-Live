from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BrochureSnapshotModel(Base):
    __tablename__ = "brochure_snapshots"
    __table_args__ = (
        UniqueConstraint("trip_id", "version_number", name="uq_brochure_snapshots_trip_version"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    trip_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="latest")
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    finalized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    warnings: Mapped[list] = mapped_column(JSONB, nullable=False)
    hero_image: Mapped[dict] = mapped_column(JSONB, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    trip = relationship("TripModel", back_populates="brochure_snapshots")
