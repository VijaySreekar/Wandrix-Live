from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.brochure_snapshot import BrochureSnapshotModel


def create_brochure_snapshot(
    db: Session,
    *,
    snapshot_id: str,
    trip_id: str,
    version_number: int,
    finalized_at,
    payload: dict,
    warnings: list,
    hero_image: dict,
    summary: dict,
) -> BrochureSnapshotModel:
    db.execute(
        update(BrochureSnapshotModel)
        .where(BrochureSnapshotModel.trip_id == trip_id, BrochureSnapshotModel.is_latest.is_(True))
        .values(is_latest=False, status="historical")
    )

    snapshot = BrochureSnapshotModel(
        id=snapshot_id,
        trip_id=trip_id,
        version_number=version_number,
        status="latest",
        is_latest=True,
        finalized_at=finalized_at,
        payload=payload,
        warnings=warnings,
        hero_image=hero_image,
        summary=summary,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_brochure_snapshot(db: Session, trip_id: str) -> BrochureSnapshotModel | None:
    statement = (
        select(BrochureSnapshotModel)
        .where(BrochureSnapshotModel.trip_id == trip_id)
        .order_by(BrochureSnapshotModel.version_number.desc())
        .limit(1)
    )
    return db.scalar(statement)


def get_brochure_snapshot(db: Session, trip_id: str, snapshot_id: str) -> BrochureSnapshotModel | None:
    statement = select(BrochureSnapshotModel).where(
        BrochureSnapshotModel.trip_id == trip_id,
        BrochureSnapshotModel.id == snapshot_id,
    )
    return db.scalar(statement)


def list_brochure_snapshots(db: Session, trip_id: str) -> list[BrochureSnapshotModel]:
    statement = (
        select(BrochureSnapshotModel)
        .where(BrochureSnapshotModel.trip_id == trip_id)
        .order_by(BrochureSnapshotModel.version_number.desc())
    )
    return list(db.scalars(statement).all())


def get_next_brochure_version_number(db: Session, trip_id: str) -> int:
    statement = select(func.max(BrochureSnapshotModel.version_number)).where(
        BrochureSnapshotModel.trip_id == trip_id
    )
    max_version = db.scalar(statement)
    return int(max_version or 0) + 1
