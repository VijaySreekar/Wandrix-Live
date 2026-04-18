from typing import Any

from typing_extensions import TypedDict


class PlanningGraphState(TypedDict, total=False):
    browser_session_id: str
    trip_id: str
    thread_id: str
    user_input: str
    trip_draft: dict[str, Any]
    assistant_response: str
    metadata: dict[str, Any]
