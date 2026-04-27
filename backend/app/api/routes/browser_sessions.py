from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.browser_session import (
    BrowserSessionCreateRequest,
    BrowserSessionCreateResponse,
)
from app.services.browser_session_service import create_browser_session


router = APIRouter(prefix="/browser-sessions", tags=["browser-sessions"])


@router.post("", response_model=BrowserSessionCreateResponse)
def create_browser_session_route(
    payload: BrowserSessionCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrowserSessionCreateResponse:
    return create_browser_session(db, payload, user_id=current_user.id)
