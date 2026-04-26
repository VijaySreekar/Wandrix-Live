from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.brochure import BrochureHistoryResponse, BrochureSnapshot
from app.services.brochure_service import (
    get_latest_trip_brochure,
    get_trip_brochure,
    list_trip_brochures,
    render_trip_brochure_pdf,
)


router = APIRouter(prefix="/trips/{trip_id}/brochures", tags=["brochures"])


@router.get("", response_model=BrochureHistoryResponse)
def list_trip_brochures_route(
    trip_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrochureHistoryResponse:
    return list_trip_brochures(db, trip_id=trip_id, user_id=current_user.id)


@router.get("/latest", response_model=BrochureSnapshot)
def get_latest_trip_brochure_route(
    trip_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrochureSnapshot:
    return get_latest_trip_brochure(db, trip_id=trip_id, user_id=current_user.id)


@router.get("/{snapshot_id}", response_model=BrochureSnapshot)
def get_trip_brochure_route(
    trip_id: str,
    snapshot_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrochureSnapshot:
    return get_trip_brochure(
        db,
        trip_id=trip_id,
        snapshot_id=snapshot_id,
        user_id=current_user.id,
    )


@router.post("/{snapshot_id}/pdf")
def render_trip_brochure_pdf_route(
    trip_id: str,
    snapshot_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    pdf_bytes, file_name = render_trip_brochure_pdf(
        db,
        trip_id=trip_id,
        snapshot_id=snapshot_id,
        user_id=current_user.id,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
