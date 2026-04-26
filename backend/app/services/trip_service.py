from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.browser_session_repository import get_browser_session
from app.repositories.trip_draft_repository import (
    get_trip_draft as get_trip_draft_record,
    upsert_trip_draft as upsert_trip_draft_record,
)
from app.repositories.trip_repository import (
    create_trip as create_trip_record,
    delete_trip as delete_trip_record,
    get_trip_for_user,
    list_trips_for_user,
)
from app.schemas.trip import (
    TripDeleteResponse,
    TripCreateRequest,
    TripCreateResponse,
    TripListItemResponse,
    TripListResponse,
)
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraft, TripDraftStatus, TripDraftUpsertRequest


DEFAULT_TRIP_TITLE = "New chat"


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
    title = payload.title or DEFAULT_TRIP_TITLE
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
        budget_estimate=None,
        status=TripDraftStatus().model_dump(mode="json"),
        conversation=TripConversationState().model_dump(mode="json"),
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


def delete_trip(
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> TripDeleteResponse:
    trip = _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    delete_trip_record(db, trip)
    return TripDeleteResponse(trip_id=trip_id, deleted=True)


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
                updated_at=_effective_trip_updated_at(trip),
                phase=_extract_trip_phase(trip),
                brochure_ready=_extract_brochure_ready(trip),
                latest_brochure_snapshot_id=_extract_latest_brochure_snapshot_id(trip),
                latest_brochure_version=_extract_latest_brochure_version(trip),
                brochure_versions_count=_extract_brochure_versions_count(trip),
                from_location=_extract_configuration_value(trip, "from_location"),
                to_location=_extract_configuration_value(trip, "to_location"),
                start_date=_extract_configuration_value(trip, "start_date"),
                end_date=_extract_configuration_value(trip, "end_date"),
                travel_window=_extract_configuration_value(trip, "travel_window"),
                trip_length=_extract_configuration_value(trip, "trip_length"),
                selected_modules=_extract_selected_modules(trip),
                timeline_item_count=_extract_timeline_item_count(trip),
            )
            for trip in trips
        ]
    )


def _effective_trip_updated_at(trip) -> datetime:
    timestamps = [trip.updated_at]
    draft_updated_at = getattr(getattr(trip, "draft", None), "updated_at", None)
    if isinstance(draft_updated_at, datetime):
        timestamps.append(draft_updated_at)
    if trip.draft and isinstance(trip.draft.status, dict):
        status_updated_at = trip.draft.status.get("last_updated_at")
        if isinstance(status_updated_at, str):
            try:
                timestamps.append(datetime.fromisoformat(status_updated_at))
            except ValueError:
                pass
        elif isinstance(status_updated_at, datetime):
            timestamps.append(status_updated_at)
    return max(timestamps, key=_datetime_sort_value)


def _datetime_sort_value(value: datetime) -> float:
    try:
        return value.timestamp()
    except (OSError, ValueError):
        return 0


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
        budget_estimate=payload.budget_estimate.model_dump(mode="json")
        if payload.budget_estimate
        else None,
        status=payload.status.model_dump(mode="json"),
        conversation=payload.conversation.model_dump(mode="json"),
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
            "budget_estimate": draft.budget_estimate,
            "status": draft.status,
            "conversation": draft.conversation,
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


def _extract_latest_brochure_snapshot_id(trip) -> str | None:
    latest_snapshot = _get_latest_brochure_snapshot(trip)
    return latest_snapshot.id if latest_snapshot is not None else None


def _extract_latest_brochure_version(trip) -> int | None:
    latest_snapshot = _get_latest_brochure_snapshot(trip)
    return latest_snapshot.version_number if latest_snapshot is not None else None


def _extract_brochure_versions_count(trip) -> int:
    snapshots = getattr(trip, "brochure_snapshots", None)
    if isinstance(snapshots, list):
        return len(snapshots)
    return 0


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


def _get_latest_brochure_snapshot(trip):
    snapshots = getattr(trip, "brochure_snapshots", None)
    if not isinstance(snapshots, list) or not snapshots:
        return None

    return snapshots[0]
