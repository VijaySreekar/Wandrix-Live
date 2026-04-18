from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TripModel(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    browser_session_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("browser_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    trip_status: Mapped[str] = mapped_column(
        String(40),
        default="collecting_requirements",
        nullable=False,
    )
    thread_status: Mapped[str] = mapped_column(
        String(40),
        default="ready",
        nullable=False,
    )
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

    browser_session = relationship("BrowserSessionModel", back_populates="trips")
    draft = relationship(
        "TripDraftModel",
        back_populates="trip",
        cascade="all, delete-orphan",
        uselist=False,
    )
