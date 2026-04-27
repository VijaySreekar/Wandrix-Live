from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.graph.checkpointer import compile_planning_graph_with_pool
from app.schemas.auth import AuthenticatedUser
from app.schemas.conversation import (
    CheckpointConversationHistoryResponse,
    OpeningTurnRequest,
    OpeningTurnResponse,
    TripConversationMessageRequest,
    TripConversationMessageResponse,
)
from app.services.conversation_service import (
    get_trip_conversation_history,
    respond_to_opening_turn,
    send_trip_message,
)


router = APIRouter(prefix="/trips", tags=["conversation"])
chat_router = APIRouter(prefix="/chat", tags=["conversation"])


@chat_router.post("/opening-turn", response_model=OpeningTurnResponse)
def opening_turn_route(
    payload: OpeningTurnRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OpeningTurnResponse:
    del current_user
    return respond_to_opening_turn(payload=payload)


@router.post("/{trip_id}/conversation", response_model=TripConversationMessageResponse)
def send_trip_message_route(
    request: Request,
    trip_id: str,
    payload: TripConversationMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripConversationMessageResponse:
    graph = _resolve_request_graph(request)

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
    graph = _resolve_request_graph(request)

    return get_trip_conversation_history(
        graph,
        db,
        trip_id=trip_id,
        user_id=current_user.id,
    )


def _resolve_request_graph(request: Request):
    pool = getattr(request.app.state, "checkpointer_pool", None)
    try:
        return compile_planning_graph_with_pool(pool)
    except Exception as exc:  # pragma: no cover - defensive route fallback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Planning graph is not available.",
        ) from exc
