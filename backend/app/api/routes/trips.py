from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.trip import TripCreateRequest, TripCreateResponse, TripListResponse
from app.schemas.trip_draft import TripDraft, TripDraftUpsertRequest
from app.services.trip_service import (
    create_trip,
    get_trip,
    get_trip_draft,
    list_trips,
    save_trip_draft,
)


router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripCreateResponse)
async def create_trip_route(
    payload: TripCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripCreateResponse:
    return create_trip(db, payload, user_id=current_user.id)


@router.get("", response_model=TripListResponse)
async def list_trips_route(
    limit: int = Query(default=12, ge=1, le=50),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripListResponse:
    return list_trips(db, user_id=current_user.id, limit=limit)


@router.get("/{trip_id}", response_model=TripCreateResponse)
async def get_trip_route(
    trip_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripCreateResponse:
    return get_trip(db, trip_id=trip_id, user_id=current_user.id)


@router.get("/{trip_id}/draft", response_model=TripDraft)
async def get_trip_draft_route(
    trip_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripDraft:
    return get_trip_draft(db, trip_id=trip_id, user_id=current_user.id)


@router.put("/{trip_id}/draft", response_model=TripDraft)
async def save_trip_draft_route(
    trip_id: str,
    payload: TripDraftUpsertRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripDraft:
    return save_trip_draft(db, trip_id=trip_id, user_id=current_user.id, payload=payload)
