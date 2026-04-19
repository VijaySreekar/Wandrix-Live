from typing import Any

from typing_extensions import TypedDict


class PlanningGraphState(TypedDict, total=False):
    browser_session_id: str
    trip_id: str
    thread_id: str
    user_input: str
    profile_context: dict[str, Any]
    trip_draft: dict[str, Any]
    raw_messages: list[dict[str, Any]]
    assistant_response: str
    metadata: dict[str, Any]
