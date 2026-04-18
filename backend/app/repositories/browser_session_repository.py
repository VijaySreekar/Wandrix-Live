from sqlalchemy.orm import Session

from app.models.browser_session import BrowserSessionModel


def create_browser_session(
    db: Session,
    *,
    browser_session_id: str,
    user_id: str | None,
    timezone: str | None,
    locale: str | None,
) -> BrowserSessionModel:
    browser_session = BrowserSessionModel(
        id=browser_session_id,
        user_id=user_id,
        timezone=timezone,
        locale=locale,
        status="active",
    )
    db.add(browser_session)
    db.commit()
    db.refresh(browser_session)
    return browser_session


def get_browser_session(db: Session, browser_session_id: str) -> BrowserSessionModel | None:
    return db.get(BrowserSessionModel, browser_session_id)
