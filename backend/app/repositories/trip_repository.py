from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.models.trip import TripModel


def create_trip(
    db: Session,
    *,
    trip_id: str,
    browser_session_id: str,
    user_id: str | None,
    thread_id: str,
    title: str,
) -> TripModel:
    trip = TripModel(
        id=trip_id,
        browser_session_id=browser_session_id,
        user_id=user_id,
        thread_id=thread_id,
        title=title,
        trip_status="collecting_requirements",
        thread_status="ready",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip_title(
    db: Session,
    trip: TripModel,
    *,
    title: str,
) -> TripModel:
    trip.title = title
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def get_trip_for_user(db: Session, trip_id: str, user_id: str) -> TripModel | None:
    statement = select(TripModel).where(
        TripModel.id == trip_id,
        TripModel.user_id == user_id,
    )
    return db.scalar(statement)


def list_trips_for_user(
    db: Session,
    user_id: str,
    *,
    limit: int = 20,
) -> list[TripModel]:
    statement = (
        select(TripModel)
        .options(selectinload(TripModel.draft))
        .where(TripModel.user_id == user_id)
        .order_by(TripModel.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())
