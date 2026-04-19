from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.trip_draft_repository import (
    get_trip_draft as get_trip_draft_record,
    upsert_trip_draft as upsert_trip_draft_record,
)
from app.repositories.trip_repository import get_trip_for_user
from app.repositories.trip_repository import update_trip_title as update_trip_title_record
from app.schemas.conversation import (
    CheckpointConversationHistoryResponse,
    TripConversationMessageRequest,
    TripConversationMessageResponse,
)
from app.schemas.trip_draft import TripDraft, TripPlanningPhase


def send_trip_message(
    graph,
    db: Session,
    *,
    trip_id: str,
    user_id: str,
    payload: TripConversationMessageRequest,
) -> TripConversationMessageResponse:
    trip = get_trip_for_user(db, trip_id, user_id)

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip was not found.",
        )

    draft = get_trip_draft_record(db, trip.id)

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip draft was not found.",
        )

    graph_result = graph.invoke(
        {
            "browser_session_id": trip.browser_session_id,
            "trip_id": trip.id,
            "thread_id": trip.thread_id,
            "user_input": payload.message,
            "profile_context": payload.profile_context.model_dump(mode="json")
            if payload.profile_context
            else {},
            "current_location_context": payload.current_location_context.model_dump(
                mode="json"
            )
            if payload.current_location_context
            else {},
            "board_action": payload.board_action.model_dump(mode="json")
            if payload.board_action
            else {},
            "trip_draft": {
                "title": draft.title,
                "configuration": draft.configuration,
                "timeline": draft.timeline,
                "module_outputs": draft.module_outputs,
                "status": draft.status,
                "conversation": draft.conversation,
            },
            "metadata": {"user_id": user_id},
        },
        config={
            "configurable": {
                "thread_id": trip.thread_id,
            }
        },
    )
    updated_draft = graph_result.get("trip_draft")
    if not updated_draft:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph did not return an updated trip draft.",
        )

    persisted_draft = upsert_trip_draft_record(
        db,
        trip_id=trip.id,
        thread_id=trip.thread_id,
        title=updated_draft.get("title") or draft.title,
        configuration=updated_draft.get("configuration") or draft.configuration,
        timeline=updated_draft.get("timeline") or draft.timeline,
        module_outputs=updated_draft.get("module_outputs") or draft.module_outputs,
        status=updated_draft.get("status") or draft.status,
        conversation=updated_draft.get("conversation") or draft.conversation,
    )
    next_title = persisted_draft.title.strip()
    if next_title and next_title != trip.title:
        trip = update_trip_title_record(
            db,
            trip,
            title=next_title,
        )
    phase = cast(
        TripPlanningPhase,
        persisted_draft.status.get("phase") or "opening",
    )
    assistant_response = cast(
        str,
        graph_result.get("assistant_response")
        or "The planner processed your turn, but no assistant response was returned.",
    )

    return TripConversationMessageResponse(
        trip_id=trip.id,
        thread_id=trip.thread_id,
        draft_phase=phase,
        message=assistant_response,
        trip_draft=TripDraft.model_validate(
            {
                "trip_id": trip.id,
                "thread_id": trip.thread_id,
                "title": persisted_draft.title,
                "configuration": persisted_draft.configuration,
                "timeline": persisted_draft.timeline,
                "module_outputs": persisted_draft.module_outputs,
                "status": persisted_draft.status,
                "conversation": persisted_draft.conversation,
            }
        ),
    )


def get_trip_conversation_history(
    graph,
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> CheckpointConversationHistoryResponse:
    trip = get_trip_for_user(db, trip_id, user_id)

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip was not found.",
        )

    snapshot = graph.get_state(
        {
            "configurable": {
                "thread_id": trip.thread_id,
            }
        }
    )
    values = getattr(snapshot, "values", {}) or {}
    raw_messages = values.get("raw_messages", [])

    return CheckpointConversationHistoryResponse.model_validate(
        {
            "trip_id": trip.id,
            "thread_id": trip.thread_id,
            "messages": raw_messages,
        }
    )
