from psycopg import OperationalError

from app.services.conversation_service import (
    _get_graph_state_with_retry,
    _invoke_graph_with_retry,
)


class _RetryGraph:
    def __init__(self, *, invoke_result=None, state_result=None):
        self.invoke_calls = 0
        self.state_calls = 0
        self._invoke_result = invoke_result
        self._state_result = state_result

    def invoke(self, payload, config=None):
        self.invoke_calls += 1
        if self.invoke_calls == 1:
            raise OperationalError("server closed the connection unexpectedly")
        return {
            "payload": payload,
            "config": config,
            "result": self._invoke_result,
        }

    def get_state(self, config):
        self.state_calls += 1
        if self.state_calls == 1:
            raise OperationalError("server closed the connection unexpectedly")
        return {"config": config, "result": self._state_result}


def test_invoke_graph_with_retry_retries_once_after_operational_error() -> None:
    graph = _RetryGraph(invoke_result="ok")

    result = _invoke_graph_with_retry(
        graph,
        payload={"trip_id": "trip_123"},
        config={"configurable": {"thread_id": "thread_123"}},
    )

    assert graph.invoke_calls == 2
    assert result["result"] == "ok"


def test_get_graph_state_with_retry_retries_once_after_operational_error() -> None:
    graph = _RetryGraph(state_result="ok")

    result = _get_graph_state_with_retry(
        graph,
        {"configurable": {"thread_id": "thread_123"}},
    )

    assert graph.state_calls == 2
    assert result["result"] == "ok"
