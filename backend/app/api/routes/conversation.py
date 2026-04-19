from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.conversation import (
    CheckpointConversationHistoryResponse,
    TripConversationMessageRequest,
    TripConversationMessageResponse,
)
from app.services.conversation_service import (
    get_trip_conversation_history,
    send_trip_message,
)


router = APIRouter(prefix="/trips", tags=["conversation"])


@router.post("/{trip_id}/conversation", response_model=TripConversationMessageResponse)
def send_trip_message_route(
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


@router.get(
    "/{trip_id}/conversation/history",
    response_model=CheckpointConversationHistoryResponse,
)
def get_trip_conversation_history_route(
    request: Request,
    trip_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckpointConversationHistoryResponse:
    graph = getattr(request.app.state, "planning_graph", None)
    if graph is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Planning graph is not available.",
        )

    return get_trip_conversation_history(
        graph,
        db,
        trip_id=trip_id,
        user_id=current_user.id,
    )
