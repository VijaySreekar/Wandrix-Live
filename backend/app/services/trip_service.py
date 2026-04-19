from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.browser_session_repository import get_browser_session
from app.repositories.trip_draft_repository import (
    get_trip_draft as get_trip_draft_record,
    upsert_trip_draft as upsert_trip_draft_record,
)
from app.repositories.trip_repository import (
    create_trip as create_trip_record,
    get_trip_for_user,
    list_trips_for_user,
)
from app.schemas.trip import (
    TripCreateRequest,
    TripCreateResponse,
    TripListItemResponse,
    TripListResponse,
)
from app.schemas.trip_draft import TripDraft, TripDraftStatus, TripDraftUpsertRequest


def create_trip(
    db: Session,
    payload: TripCreateRequest,
    *,
    user_id: str,
) -> TripCreateResponse:
    browser_session = get_browser_session(db, payload.browser_session_id)

    if browser_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Browser session was not found.",
        )

    if browser_session.user_id and browser_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to that browser session.",
        )

    trip_id = f"trip_{uuid4().hex}"
    thread_id = f"thread_{uuid4().hex}"
    title = payload.title or f"Trip {trip_id[-6:]}"
    trip = create_trip_record(
        db,
        trip_id=trip_id,
        browser_session_id=browser_session.id,
        user_id=user_id,
        thread_id=thread_id,
        title=title,
    )

    upsert_trip_draft_record(
        db,
        trip_id=trip.id,
        thread_id=trip.thread_id,
        title=trip.title,
        configuration={},
        timeline=[],
        module_outputs={},
        status=TripDraftStatus().model_dump(mode="json"),
    )

    return _build_trip_response(trip)


def get_trip(
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> TripCreateResponse:
    trip = _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    return _build_trip_response(trip)


def list_trips(
    db: Session,
    *,
    user_id: str,
    limit: int = 20,
) -> TripListResponse:
    trips = list_trips_for_user(db, user_id, limit=limit)
    return TripListResponse(
        items=[
            TripListItemResponse(
                **_build_trip_response(trip).model_dump(),
                updated_at=trip.updated_at,
                phase=_extract_trip_phase(trip),
                brochure_ready=_extract_brochure_ready(trip),
                from_location=_extract_configuration_value(trip, "from_location"),
                to_location=_extract_configuration_value(trip, "to_location"),
                start_date=_extract_configuration_value(trip, "start_date"),
                end_date=_extract_configuration_value(trip, "end_date"),
                selected_modules=_extract_selected_modules(trip),
                timeline_item_count=_extract_timeline_item_count(trip),
            )
            for trip in trips
        ]
    )


def get_trip_draft(
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> TripDraft:
    trip = _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    draft = get_trip_draft_record(db, trip.id)

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip draft was not found.",
        )

    return _build_trip_draft_response(trip.id, draft)


def save_trip_draft(
    db: Session,
    *,
    trip_id: str,
    user_id: str,
    payload: TripDraftUpsertRequest,
) -> TripDraft:
    trip = _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    draft = upsert_trip_draft_record(
        db,
        trip_id=trip.id,
        thread_id=trip.thread_id,
        title=payload.title,
        configuration=payload.configuration.model_dump(mode="json"),
        timeline=[item.model_dump(mode="json") for item in payload.timeline],
        module_outputs=payload.module_outputs.model_dump(mode="json"),
        status=payload.status.model_dump(mode="json"),
    )

    return _build_trip_draft_response(trip.id, draft)


def _get_owned_trip(db: Session, *, trip_id: str, user_id: str):
    trip = get_trip_for_user(db, trip_id, user_id)

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip was not found.",
        )

    return trip


def _build_trip_response(trip) -> TripCreateResponse:
    return TripCreateResponse(
        trip_id=trip.id,
        browser_session_id=trip.browser_session_id,
        thread_id=trip.thread_id,
        title=trip.title,
        trip_status=trip.trip_status,
        thread_status=trip.thread_status,
        created_at=trip.created_at,
    )


def _build_trip_draft_response(trip_id: str, draft) -> TripDraft:
    return TripDraft.model_validate(
        {
            "trip_id": trip_id,
            "thread_id": draft.thread_id,
            "title": draft.title,
            "configuration": draft.configuration,
            "timeline": draft.timeline,
            "module_outputs": draft.module_outputs,
            "status": draft.status,
        }
    )


def _extract_trip_phase(trip) -> str | None:
    if trip.draft and isinstance(trip.draft.status, dict):
        phase = trip.draft.status.get("phase")
        return phase if isinstance(phase, str) else None

    return None


def _extract_brochure_ready(trip) -> bool:
    if trip.draft and isinstance(trip.draft.status, dict):
        brochure_ready = trip.draft.status.get("brochure_ready")
        return brochure_ready is True

    return False


def _extract_configuration_value(trip, key: str) -> str | None:
    if trip.draft and isinstance(trip.draft.configuration, dict):
        value = trip.draft.configuration.get(key)
        return value if isinstance(value, str) else None

    return None


def _extract_selected_modules(trip) -> list[str]:
    if not trip.draft or not isinstance(trip.draft.configuration, dict):
        return []

    selected_modules = trip.draft.configuration.get("selected_modules")
    if not isinstance(selected_modules, dict):
        return []

    return [
        module_name
        for module_name, enabled in selected_modules.items()
        if isinstance(module_name, str) and enabled is True
    ]


def _extract_timeline_item_count(trip) -> int:
    if trip.draft and isinstance(trip.draft.timeline, list):
        return len(trip.draft.timeline)

    return 0
