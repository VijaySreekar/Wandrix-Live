from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, Field
from sqlalchemy import select, text

from app.db.session import SessionLocal
from app.graph.checkpointer import (
    compile_planning_graph_with_pool,
    create_postgres_checkpointer_pool,
)
from app.graph.planner.draft_merge import derive_trip_title
from app.integrations.llm.client import create_chat_model
from app.models.trip import TripModel
from app.models.trip_draft import TripDraftModel
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


class ExistingTripTitle(BaseModel):
    title: str | None = Field(default=None, max_length=80)


def main() -> None:
    pool = create_postgres_checkpointer_pool()
    if pool is not None:
        pool.open(wait=True)

    graph = compile_planning_graph_with_pool(pool)
    session = SessionLocal()

    retitled_count = 0
    deleted_count = 0

    try:
        trips = session.execute(select(TripModel).order_by(TripModel.updated_at.desc())).scalars().all()

        for trip in trips:
            draft = trip.draft
            raw_messages = _get_raw_messages(graph, trip.thread_id)

            if _is_empty_trip(draft, raw_messages):
                _delete_trip(session, trip)
                _delete_checkpoint_rows(session, trip.thread_id)
                deleted_count += 1
                continue

            if not _has_generic_title(trip.title):
                continue

            next_title = _build_trip_title(draft, raw_messages)
            if not next_title or next_title == trip.title:
                continue

            trip.title = next_title
            if draft is not None:
                draft.title = next_title
                session.add(draft)
            session.add(trip)
            retitled_count += 1

        session.commit()
    finally:
        session.close()
        if pool is not None:
            pool.close()

    print(f"Retitled {retitled_count} trips.")
    print(f"Deleted {deleted_count} empty trips.")


def _get_raw_messages(graph, thread_id: str) -> list[dict]:
    try:
        snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    except Exception:
        return []

    values = getattr(snapshot, "values", {}) or {}
    messages = values.get("raw_messages", [])
    return [message for message in messages if isinstance(message, dict)]


def _is_empty_trip(draft: TripDraftModel | None, raw_messages: list[dict]) -> bool:
    if raw_messages:
        return False

    if draft is None:
        return True

    configuration = TripConfiguration.model_validate(draft.configuration or {})
    module_outputs = TripModuleOutputs.model_validate(draft.module_outputs or {})
    conversation = TripConversationState.model_validate(draft.conversation or {})
    status = draft.status or {}

    has_configuration = any(
        [
            configuration.from_location,
            configuration.to_location,
            configuration.start_date,
            configuration.end_date,
            configuration.travel_window,
            configuration.trip_length,
            configuration.travelers.adults is not None,
            configuration.travelers.children is not None,
            configuration.budget_gbp is not None,
            bool(configuration.activity_styles),
        ]
    )
    has_module_outputs = any(
        [
            bool(module_outputs.flights),
            bool(module_outputs.hotels),
            bool(module_outputs.weather),
            bool(module_outputs.activities),
        ]
    )
    has_conversation = any(
        [
            bool(conversation.open_questions),
            bool(conversation.decision_cards),
            bool(conversation.active_goals),
            bool(conversation.last_turn_summary),
            bool(conversation.memory.field_memory),
            bool(conversation.memory.mentioned_options),
            bool(conversation.memory.rejected_options),
            bool(conversation.memory.decision_history),
            bool(conversation.memory.turn_summaries),
            bool(conversation.suggestion_board.cards),
            bool(conversation.suggestion_board.title),
            bool(conversation.suggestion_board.subtitle),
        ]
    )
    has_status_activity = bool(status.get("last_updated_at"))
    has_timeline = bool(draft.timeline)

    return not any(
        [
            has_configuration,
            has_module_outputs,
            has_conversation,
            has_status_activity,
            has_timeline,
        ]
    )


def _has_generic_title(title: str | None) -> bool:
    if not title:
        return True

    normalized = title.strip().lower()
    return normalized == "trip planner" or normalized.startswith("trip ")


def _build_trip_title(draft: TripDraftModel | None, raw_messages: list[dict]) -> str:
    if draft is None:
        return "Trip planner"

    configuration = TripConfiguration.model_validate(draft.configuration or {})
    conversation = TripConversationState.model_validate(draft.conversation or {})
    user_messages = [
        str(message.get("content", "")).strip()
        for message in raw_messages
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]
    recent_user_messages = user_messages[-3:]

    fallback_title = derive_trip_title(configuration).strip()
    if fallback_title == "Trip planner" and configuration.from_location and configuration.to_location:
        fallback_title = f"{configuration.from_location} to {configuration.to_location}"

    prompt = f"""
Create a concise 2 to 6 word title for a saved Wandrix trip chat.

Rules:
- The title should feel like a human sidebar label for the trip.
- Use the destination, travel style, timing, or route when helpful.
- Do not use generic labels like "Trip planner", "Travel plan", or "Trip".
- Keep it short, specific, and natural.
- If the trip is still broad, use the best available grounded summary from the user messages and configuration.

Current trip configuration:
{configuration.model_dump(mode="json")}

Current conversation summary:
{conversation.last_turn_summary or ""}

Recent user messages:
{recent_user_messages}
""".strip()

    try:
        model = create_chat_model(temperature=0.1)
        structured_model = model.with_structured_output(
            ExistingTripTitle,
            method="json_schema",
        )
        result = structured_model.invoke(
            [
                ("system", "Generate a short saved-trip title for Wandrix."),
                ("human", prompt),
            ]
        )
        candidate = (result.title or "").strip()
        if candidate and not _has_generic_title(candidate):
            return candidate
    except Exception:
        pass

    if fallback_title and fallback_title != "Trip planner":
        return fallback_title

    return _fallback_from_user_messages(recent_user_messages) or "Saved trip"


def _fallback_from_user_messages(messages: Iterable[str]) -> str | None:
    for message in reversed(list(messages)):
        cleaned = " ".join(message.split())
        if cleaned:
            return cleaned[:60]
    return None


def _delete_trip(session, trip: TripModel) -> None:
    draft = trip.draft
    if draft is not None:
        session.delete(draft)
    session.delete(trip)
    session.flush()


def _delete_checkpoint_rows(session, thread_id: str) -> None:
    for table_name in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
        session.execute(
            text(f"delete from {table_name} where thread_id = :thread_id"),
            {"thread_id": thread_id},
        )


if __name__ == "__main__":
    main()
