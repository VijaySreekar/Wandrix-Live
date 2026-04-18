from uuid import uuid4

from sqlalchemy.orm import Session

from app.repositories.browser_session_repository import (
    create_browser_session as create_browser_session_record,
)
from app.schemas.browser_session import (
    BrowserSessionCreateRequest,
    BrowserSessionCreateResponse,
)


def create_browser_session(
    db: Session,
    payload: BrowserSessionCreateRequest,
    *,
    user_id: str | None,
) -> BrowserSessionCreateResponse:
    browser_session = create_browser_session_record(
        db,
        browser_session_id=f"bs_{uuid4().hex}",
        user_id=user_id,
        timezone=payload.timezone,
        locale=payload.locale,
    )

    return BrowserSessionCreateResponse(
        browser_session_id=browser_session.id,
        user_id=browser_session.user_id,
        timezone=browser_session.timezone,
        locale=browser_session.locale,
        status=browser_session.status,
        created_at=browser_session.created_at,
    )
