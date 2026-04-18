from sqlalchemy.orm import Session

from app.models.trip_draft import TripDraftModel


def create_trip_draft(
    db: Session,
    *,
    trip_id: str,
    thread_id: str,
    title: str,
    configuration: dict,
    timeline: list,
    module_outputs: dict,
    status: dict,
) -> TripDraftModel:
    draft = TripDraftModel(
        trip_id=trip_id,
        thread_id=thread_id,
        title=title,
        configuration=configuration,
        timeline=timeline,
        module_outputs=module_outputs,
        status=status,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def get_trip_draft(db: Session, trip_id: str) -> TripDraftModel | None:
    return db.get(TripDraftModel, trip_id)


def upsert_trip_draft(
    db: Session,
    *,
    trip_id: str,
    thread_id: str,
    title: str,
    configuration: dict,
    timeline: list,
    module_outputs: dict,
    status: dict,
) -> TripDraftModel:
    draft = get_trip_draft(db, trip_id)

    if draft is None:
        return create_trip_draft(
            db,
            trip_id=trip_id,
            thread_id=thread_id,
            title=title,
            configuration=configuration,
            timeline=timeline,
            module_outputs=module_outputs,
            status=status,
        )

    draft.thread_id = thread_id
    draft.title = title
    draft.configuration = configuration
    draft.timeline = timeline
    draft.module_outputs = module_outputs
    draft.status = status

    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
