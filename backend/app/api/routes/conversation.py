from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.conversation import (
    TripConversationMessageRequest,
    TripConversationMessageResponse,
)
from app.services.conversation_service import send_trip_message


router = APIRouter(prefix="/trips", tags=["conversation"])


@router.post("/{trip_id}/conversation", response_model=TripConversationMessageResponse)
async def send_trip_message_route(
    request: Request,
    trip_id: str,
    payload: TripConversationMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripConversationMessageResponse:
    graph = getattr(request.app.state, "planning_graph", None)
    if graph is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Planning graph is not available.",
        )

    return send_trip_message(
        graph,
        db,
        trip_id=trip_id,
        user_id=current_user.id,
        payload=payload,
    )
