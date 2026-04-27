from datetime import date
from types import SimpleNamespace

from psycopg import OperationalError

from app.schemas.conversation import TripConversationMessageRequest
from app.schemas.trip_planning import (
    FlightDetail,
    HotelStayDetail,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services import conversation_service
from app.services.conversation_service import (
    get_trip_conversation_history,
    _get_graph_state_with_retry,
    _invoke_graph_with_retry,
    _should_create_brochure_snapshot,
    send_trip_message,
)
from app.schemas.trip_draft import TripDraft


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


def test_get_trip_conversation_history_normalizes_stage_one_checkpoint_response(
    monkeypatch,
) -> None:
    trip = SimpleNamespace(
        id="trip_1",
        thread_id="thread_1",
        browser_session_id="browser_1",
        title="Kyoto planner",
    )
    draft = SimpleNamespace(
        thread_id="thread_1",
        title="Kyoto planner",
        configuration={},
        timeline=[],
        module_outputs={
            "flights": [
                {
                    "id": "flight_out",
                    "direction": "outbound",
                    "carrier": "BA",
                    "departure_airport": "LHR",
                    "arrival_airport": "KIX",
                    "inventory_source": "live",
                }
            ],
            "weather": [
                {
                    "id": "weather_1",
                    "day_label": "Day 1",
                    "summary": "Sunny",
                }
            ],
            "hotels": [
                {
                    "id": "hotel_1",
                    "hotel_name": "Central Kyoto Stay",
                    "area": "Central Kyoto",
                    "notes": [],
                }
            ],
        },
        budget_estimate=None,
        status={"confirmation_status": "unconfirmed"},
        conversation={
            "planning_mode": "quick",
            "quick_plan_build": {
                "status": "complete",
                "completed_stages": ["brief", "flights", "weather", "hotels", "itinerary"],
            },
        },
    )

    class _Graph:
        def get_state(self, config):
            return SimpleNamespace(
                values={
                    "raw_messages": [
                        {
                            "role": "system",
                            "content": "Board action: select_quick_plan",
                            "created_at": "2027-04-01T10:00:00Z",
                        },
                        {
                            "role": "assistant",
                            "content": "Got it, I started a Quick Plan on the live board.",
                            "created_at": "2027-04-01T10:00:01Z",
                        },
                    ]
                }
            )

    monkeypatch.setattr(conversation_service, "get_trip_for_user", lambda *_: trip)
    monkeypatch.setattr(conversation_service, "get_trip_draft_record", lambda *_: draft)

    history = get_trip_conversation_history(
        _Graph(),
        db=SimpleNamespace(),
        trip_id="trip_1",
        user_id="user_1",
    )

    assert history.messages[0].role == "user"
    assert history.messages[0].content == (
        "Use Quick Plan and generate the first draft itinerary now."
    )
    assert history.messages[1].content == (
        "I've started the Quick Plan as a live board instead of waiting on a full itinerary. "
        "The confirmed brief, selected flight option, and flight budget are now saved. "
        "The weather for the selected dates is also on the board. "
        "I selected a working hotel based on budget fit, stay evidence, and area confidence. "
        "The board now includes a clocked day-by-day itinerary with transfers, meals, "
        "activities, hotel reset time, and return-flight timing."
    )


def test_brochure_snapshot_triggers_on_transition_to_finalized() -> None:
    previous = TripDraft(
        trip_id="trip_1",
        thread_id="thread_1",
        title="Kyoto planner",
    )
    next_draft = TripDraft.model_validate(
        {
            "trip_id": "trip_1",
            "thread_id": "thread_1",
            "title": "Kyoto planner",
            "status": {
                "confirmation_status": "finalized",
                "finalized_at": "2027-03-01T12:00:00Z",
                "finalized_via": "board",
                "brochure_ready": True,
            },
            "conversation": {
                "planning_mode": "advanced",
                "advanced_step": "review",
                "confirmation_status": "finalized",
            },
        }
    )

    assert _should_create_brochure_snapshot(previous, next_draft) is True


def test_quick_plan_snapshot_does_not_trigger_without_brochure_eligibility() -> None:
    previous = TripDraft(
        trip_id="trip_1",
        thread_id="thread_1",
        title="Kyoto planner",
    )
    next_draft = TripDraft.model_validate(
        {
            "trip_id": "trip_1",
            "thread_id": "thread_1",
            "title": "Kyoto planner",
            "status": {
                "confirmation_status": "finalized",
                "finalized_at": "2027-03-01T12:00:00Z",
                "finalized_via": "board",
                "brochure_ready": True,
            },
            "conversation": {
                "planning_mode": "quick",
                "confirmation_status": "finalized",
                "quick_plan_finalization": {
                    "accepted": True,
                    "review_status": "complete",
                    "quality_status": "repairable",
                    "brochure_eligible": False,
                },
            },
        }
    )

    assert _should_create_brochure_snapshot(previous, next_draft) is False


def test_send_trip_message_persists_budget_estimate_before_brochure_snapshot(
    monkeypatch,
) -> None:
    captured: dict = {}
    trip = SimpleNamespace(
        id="trip_1",
        thread_id="thread_1",
        browser_session_id="browser_1",
        title="Paris planner",
    )
    draft = SimpleNamespace(
        thread_id="thread_1",
        title="Paris planner",
        configuration={"to_location": "Paris"},
        timeline=[],
        module_outputs={},
        budget_estimate=None,
        status={"confirmation_status": "unconfirmed"},
        conversation={"planning_mode": "quick"},
    )
    budget_estimate = {
        "total_low_amount": 700,
        "total_high_amount": 920,
        "currency": "GBP",
        "categories": [],
        "caveat": "Directional estimate only.",
    }

    class _Graph:
        def invoke(self, payload, config=None):
            return {
                "assistant_response": "Locked in.",
                "trip_draft": {
                    "title": "Paris planner",
                    "configuration": draft.configuration,
                    "timeline": [],
                    "module_outputs": {},
                    "budget_estimate": budget_estimate,
                    "status": {
                        "confirmation_status": "finalized",
                        "finalized_at": "2027-05-01T12:00:00Z",
                        "finalized_via": "board",
                        "brochure_ready": True,
                    },
                    "conversation": {
                        "planning_mode": "quick",
                        "confirmation_status": "finalized",
                        "quick_plan_finalization": {
                            "accepted": True,
                            "review_status": "complete",
                            "quality_status": "pass",
                            "brochure_eligible": True,
                        },
                    },
                },
            }

    def _upsert_trip_draft(_db, **kwargs):
        captured["persisted_budget_estimate"] = kwargs["budget_estimate"]
        return SimpleNamespace(
            thread_id=kwargs["thread_id"],
            title=kwargs["title"],
            configuration=kwargs["configuration"],
            timeline=kwargs["timeline"],
            module_outputs=kwargs["module_outputs"],
            budget_estimate=kwargs["budget_estimate"],
            status=kwargs["status"],
            conversation=kwargs["conversation"],
        )

    def _create_snapshot(_db, *, trip, draft):
        captured["snapshot_budget_estimate"] = draft.budget_estimate.model_dump(
            mode="json"
        )

    monkeypatch.setattr(conversation_service, "get_trip_for_user", lambda *_: trip)
    monkeypatch.setattr(conversation_service, "get_trip_draft_record", lambda *_: draft)
    monkeypatch.setattr(conversation_service, "upsert_trip_draft_record", _upsert_trip_draft)
    monkeypatch.setattr(
        conversation_service,
        "create_brochure_snapshot_for_trip",
        _create_snapshot,
    )

    response = send_trip_message(
        _Graph(),
        db=SimpleNamespace(),
        trip_id="trip_1",
        user_id="user_1",
        payload=TripConversationMessageRequest(message="Confirm it."),
    )

    assert captured["persisted_budget_estimate"] == budget_estimate
    assert captured["snapshot_budget_estimate"] == budget_estimate
    assert response.trip_draft.budget_estimate is not None


def test_send_trip_message_quick_plan_stage_one_persists_brief_then_flights(
    monkeypatch,
) -> None:
    persisted_calls: list[dict] = []
    trip = SimpleNamespace(
        id="trip_1",
        thread_id="thread_1",
        browser_session_id="browser_1",
        title="Kyoto planner",
    )
    draft = SimpleNamespace(
        thread_id="thread_1",
        title="Kyoto planner",
        configuration={
            "from_location": "London",
            "to_location": "Kyoto",
            "start_date": "2027-04-10",
            "end_date": "2027-04-17",
            "travelers": {"adults": 2},
        },
        timeline=[{"id": "old", "type": "activity", "title": "Old itinerary"}],
        module_outputs={"weather": [{"id": "old_weather", "day_label": "Day 1", "summary": "Old", "high_c": None, "low_c": None, "notes": []}]},
        budget_estimate={"categories": [], "caveat": "Old"},
        status={"confirmation_status": "unconfirmed"},
        conversation={"planning_mode": "quick"},
    )

    class _Graph:
        updated_state: dict | None = None

        def invoke(self, payload, config=None):
            return {
                "assistant_response": "Starting quick plan.",
                "raw_messages": [
                    {
                        "role": "user",
                        "content": "Quick plan.",
                        "created_at": "2027-04-01T10:00:00Z",
                    },
                    {
                        "role": "assistant",
                        "content": "Starting quick plan.",
                        "created_at": "2027-04-01T10:00:01Z",
                    },
                ],
                "trip_draft": {
                    "title": "Kyoto planner",
                    "configuration": draft.configuration,
                    "timeline": draft.timeline,
                    "module_outputs": draft.module_outputs,
                    "budget_estimate": draft.budget_estimate,
                    "status": draft.status,
                    "conversation": {
                        "planning_mode": "quick",
                        "quick_plan_build": {
                            "status": "running",
                            "active_stage": "flights",
                            "completed_stages": ["brief"],
                            "failed_stage": None,
                            "message": "Brief saved.",
                        },
                    },
                },
            }

        def update_state(self, config, values, as_node=None):
            self.updated_state = {
                "config": config,
                "values": values,
                "as_node": as_node,
            }

    def _upsert_trip_draft(_db, **kwargs):
        persisted_calls.append(kwargs)
        return SimpleNamespace(
            thread_id=kwargs["thread_id"],
            title=kwargs["title"],
            configuration=kwargs["configuration"],
            timeline=kwargs["timeline"],
            module_outputs=kwargs["module_outputs"],
            budget_estimate=kwargs["budget_estimate"],
            status=kwargs["status"],
            conversation=kwargs["conversation"],
        )

    monkeypatch.setattr(conversation_service, "get_trip_for_user", lambda *_: trip)
    monkeypatch.setattr(conversation_service, "get_trip_draft_record", lambda *_: draft)
    monkeypatch.setattr(conversation_service, "upsert_trip_draft_record", _upsert_trip_draft)
    monkeypatch.setattr(conversation_service, "enrich_flights_from_travelpayouts", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(conversation_service, "enrich_flights_from_amadeus", lambda *_args, **_kwargs: [])
    def _build_stage_outputs(**kwargs):
        if kwargs["allowed_modules"] == {"weather"}:
            return TripModuleOutputs(
                flights=[
                    FlightDetail(
                        id="flight_out",
                        direction="outbound",
                        carrier="BA",
                        departure_airport="LHR",
                        arrival_airport="HND",
                        notes=[],
                    )
                ],
                weather=[
                    WeatherDetail(
                        id="weather_1",
                        day_label="Day 1",
                        summary="Clear skies expected.",
                        forecast_date=date(2027, 4, 10),
                    )
                ],
            )
        if kwargs["allowed_modules"] == {"hotels"}:
            return TripModuleOutputs(
                hotels=[
                    HotelStayDetail(
                        id="hotel_best",
                        hotel_name="Best Kyoto Stay",
                        area="Central Kyoto",
                        nightly_rate_amount=180,
                        nightly_rate_currency="GBP",
                        image_url="https://example.com/hotel.jpg",
                        source_url="https://example.com/hotel",
                        notes=["Central base with useful provider evidence."],
                    ),
                    HotelStayDetail(
                        id="hotel_alt",
                        hotel_name="Kyoto Alt Stay",
                        area="Gion",
                        nightly_rate_amount=220,
                        nightly_rate_currency="GBP",
                        notes=["Alternate stay area."],
                    ),
                ]
            )
        return TripModuleOutputs(
            flights=[
                FlightDetail(
                    id="flight_out",
                    direction="outbound",
                    carrier="BA",
                    departure_airport="LHR",
                    arrival_airport="HND",
                    notes=[],
                )
            ]
        )

    monkeypatch.setattr(
        conversation_service,
        "build_quick_plan_module_outputs",
        _build_stage_outputs,
    )

    graph = _Graph()

    response = send_trip_message(
        graph,
        db=SimpleNamespace(),
        trip_id="trip_1",
        user_id="user_1",
        payload=TripConversationMessageRequest(
            message="Quick plan.",
            board_action={"action_id": "action_1", "type": "select_quick_plan"},
        ),
    )

    assert len(persisted_calls) == 5
    assert persisted_calls[0]["timeline"] == []
    assert persisted_calls[0]["module_outputs"] == {
        "flights": [],
        "hotels": [],
        "weather": [],
        "activities": [],
    }
    assert persisted_calls[0]["conversation"]["quick_plan_build"]["active_stage"] == "flights"
    assert persisted_calls[1]["module_outputs"]["flights"][0]["id"] == "flight_out"
    assert persisted_calls[1]["module_outputs"]["weather"] == []
    assert persisted_calls[1]["conversation"]["quick_plan_build"]["active_stage"] == "weather"
    assert persisted_calls[2]["module_outputs"]["weather"][0]["id"] == "weather_live_1"
    assert persisted_calls[2]["conversation"]["quick_plan_build"]["active_stage"] == "hotels"
    assert persisted_calls[3]["module_outputs"]["hotels"][0]["id"] == "hotel_best"
    assert persisted_calls[3]["conversation"]["quick_plan_build"]["active_stage"] == "itinerary"
    assert persisted_calls[4]["module_outputs"]["flights"][0]["id"] == "flight_out"
    assert persisted_calls[4]["module_outputs"]["weather"][0]["id"] == "weather_live_1"
    assert persisted_calls[4]["module_outputs"]["weather"][1]["id"] == "weather_outlook_2"
    assert persisted_calls[4]["module_outputs"]["hotels"][0]["id"] == "hotel_best"
    assert persisted_calls[4]["conversation"]["quick_plan_build"]["status"] == "complete"
    assert "weather" in persisted_calls[4]["conversation"]["quick_plan_build"]["completed_stages"]
    assert "hotels" in persisted_calls[4]["conversation"]["quick_plan_build"]["completed_stages"]
    assert "itinerary" in persisted_calls[4]["conversation"]["quick_plan_build"]["completed_stages"]
    assert any(item["type"] == "transfer" for item in persisted_calls[4]["timeline"])
    assert any(item["type"] == "meal" for item in persisted_calls[4]["timeline"])
    assert persisted_calls[4]["conversation"]["stay_planning"]["selected_hotel_id"] == "hotel_best"
    assert persisted_calls[4]["conversation"]["quick_plan_finalization"]["brochure_eligible"] is False
    assert response.trip_draft.conversation.quick_plan_build.status == "complete"
    assert graph.updated_state is not None
    assert graph.updated_state["values"]["assistant_response"] == response.message
    assert graph.updated_state["values"]["raw_messages"][-1]["content"] == response.message


def test_send_trip_message_quick_plan_stage_one_uses_provider_dated_flights(
    monkeypatch,
) -> None:
    persisted_calls: list[dict] = []
    trip = SimpleNamespace(
        id="trip_1",
        thread_id="thread_1",
        browser_session_id="browser_1",
        title="Kyoto planner",
    )
    draft = SimpleNamespace(
        thread_id="thread_1",
        title="Kyoto planner",
        configuration={
            "from_location": "London",
            "to_location": "Kyoto",
            "start_date": "2027-04-10",
            "end_date": "2027-04-17",
            "travelers": {"adults": 2},
        },
        timeline=[],
        module_outputs={},
        budget_estimate=None,
        status={"confirmation_status": "unconfirmed"},
        conversation={"planning_mode": "quick"},
    )

    class _Graph:
        def invoke(self, payload, config=None):
            return {
                "assistant_response": "Starting quick plan.",
                "trip_draft": {
                    "title": "Kyoto planner",
                    "configuration": draft.configuration,
                    "timeline": [],
                    "module_outputs": {},
                    "budget_estimate": None,
                    "status": draft.status,
                    "conversation": {
                        "planning_mode": "quick",
                        "quick_plan_build": {
                            "status": "running",
                            "active_stage": "flights",
                            "completed_stages": ["brief"],
                            "failed_stage": None,
                            "message": "Brief saved.",
                        },
                    },
                },
            }

    def _upsert_trip_draft(_db, **kwargs):
        persisted_calls.append(kwargs)
        return SimpleNamespace(
            thread_id=kwargs["thread_id"],
            title=kwargs["title"],
            configuration=kwargs["configuration"],
            timeline=kwargs["timeline"],
            module_outputs=kwargs["module_outputs"],
            budget_estimate=kwargs["budget_estimate"],
            status=kwargs["status"],
            conversation=kwargs["conversation"],
        )

    def _build_weather_only(**kwargs):
        if kwargs["allowed_modules"] == {"hotels"}:
            return TripModuleOutputs(
                hotels=[
                    HotelStayDetail(
                        id="hotel_best",
                        hotel_name="Barcelona Best Stay",
                        area="Eixample",
                        nightly_rate_amount=160,
                        nightly_rate_currency="GBP",
                        image_url="https://example.com/barcelona.jpg",
                        source_url="https://example.com/barcelona",
                        notes=["Central and budget-fit hotel."],
                    )
                ]
            )
        if kwargs["allowed_modules"] != {"weather"}:
            raise AssertionError("Stage 1 exact-date flights should use provider flight options first.")
        return TripModuleOutputs(
            weather=[
                WeatherDetail(
                    id="weather_1",
                    day_label="Day 1",
                    summary="Mostly clear conditions.",
                    forecast_date=date(2027, 4, 10),
                )
            ]
        )

    def _raise_if_amadeus_used(*_args, **_kwargs):
        raise AssertionError("Stage 1 should use the demo provider before Amadeus.")

    monkeypatch.setattr(conversation_service, "get_trip_for_user", lambda *_: trip)
    monkeypatch.setattr(conversation_service, "get_trip_draft_record", lambda *_: draft)
    monkeypatch.setattr(conversation_service, "upsert_trip_draft_record", _upsert_trip_draft)
    monkeypatch.setattr(conversation_service, "build_quick_plan_module_outputs", _build_weather_only)
    monkeypatch.setattr(conversation_service, "enrich_flights_from_amadeus", _raise_if_amadeus_used)
    monkeypatch.setattr(
        conversation_service,
        "enrich_flights_from_travelpayouts",
        lambda *_args, **_kwargs: [
            FlightDetail(
                id="provider_out_slow",
                direction="outbound",
                carrier="Slow Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                price_text="GBP 900",
                fare_amount=900,
                fare_currency="GBP",
                stop_count=2,
                inventory_source="cached",
            ),
            FlightDetail(
                id="provider_return_slow",
                direction="return",
                carrier="Slow Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                price_text="GBP 900",
                fare_amount=900,
                fare_currency="GBP",
                stop_count=2,
                inventory_source="cached",
            ),
            FlightDetail(
                id="provider_out_best",
                direction="outbound",
                carrier="Best Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                price_text="GBP 700",
                fare_amount=700,
                fare_currency="GBP",
                stop_count=0,
                inventory_source="cached",
            ),
            FlightDetail(
                id="provider_return_best",
                direction="return",
                carrier="Best Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                price_text="GBP 700",
                fare_amount=700,
                fare_currency="GBP",
                stop_count=0,
                inventory_source="cached",
            ),
        ],
    )

    send_trip_message(
        _Graph(),
        db=SimpleNamespace(),
        trip_id="trip_1",
        user_id="user_1",
        payload=TripConversationMessageRequest(
            message="Quick plan.",
            board_action={"action_id": "action_1", "type": "select_quick_plan"},
        ),
    )

    final_call = persisted_calls[-1]
    flights = final_call["module_outputs"]["flights"]
    assert [flight["id"] for flight in flights] == ["provider_out_best", "provider_return_best"]
    assert final_call["module_outputs"]["weather"][0]["id"] == "weather_live_1"
    assert final_call["module_outputs"]["weather"][1]["id"] == "weather_outlook_2"
    assert final_call["module_outputs"]["hotels"][0]["id"] == "hotel_best"
    assert final_call["conversation"]["stay_planning"]["selected_hotel_id"] == "hotel_best"
    assert "itinerary" in final_call["conversation"]["quick_plan_build"]["completed_stages"]
    assert any(item["type"] == "flight" for item in final_call["timeline"])
    assert any(item["type"] == "transfer" for item in final_call["timeline"])
    assert all(flight["inventory_source"] == "live" for flight in flights)
    assert final_call["budget_estimate"]["categories"][0]["source"] == "provider_price"
    assert final_call["budget_estimate"]["categories"][0]["low_amount"] == 700
    assert final_call["budget_estimate"]["categories"][1]["category"] == "stay"


def test_send_trip_message_quick_plan_stage_one_uses_placeholder_without_provider_flights(
    monkeypatch,
) -> None:
    persisted_calls: list[dict] = []
    trip = SimpleNamespace(
        id="trip_1",
        thread_id="thread_1",
        browser_session_id="browser_1",
        title="Kyoto planner",
    )
    draft = SimpleNamespace(
        thread_id="thread_1",
        title="Kyoto planner",
        configuration={
            "from_location": "London",
            "to_location": "Kyoto",
            "start_date": "2027-04-10",
            "end_date": "2027-04-17",
            "travelers": {"adults": 2},
        },
        timeline=[],
        module_outputs={},
        budget_estimate=None,
        status={"confirmation_status": "unconfirmed"},
        conversation={"planning_mode": "quick"},
    )

    class _Graph:
        def invoke(self, payload, config=None):
            return {
                "assistant_response": "Starting quick plan.",
                "trip_draft": {
                    "title": "Kyoto planner",
                    "configuration": draft.configuration,
                    "timeline": [],
                    "module_outputs": {},
                    "budget_estimate": None,
                    "status": draft.status,
                    "conversation": {
                        "planning_mode": "quick",
                        "quick_plan_build": {
                            "status": "running",
                            "active_stage": "flights",
                            "completed_stages": ["brief"],
                            "failed_stage": None,
                            "message": "Brief saved.",
                        },
                    },
                },
            }

    def _upsert_trip_draft(_db, **kwargs):
        persisted_calls.append(kwargs)
        return SimpleNamespace(
            thread_id=kwargs["thread_id"],
            title=kwargs["title"],
            configuration=kwargs["configuration"],
            timeline=kwargs["timeline"],
            module_outputs=kwargs["module_outputs"],
            budget_estimate=kwargs["budget_estimate"],
            status=kwargs["status"],
            conversation=kwargs["conversation"],
        )

    monkeypatch.setattr(conversation_service, "get_trip_for_user", lambda *_: trip)
    monkeypatch.setattr(conversation_service, "get_trip_draft_record", lambda *_: draft)
    monkeypatch.setattr(conversation_service, "upsert_trip_draft_record", _upsert_trip_draft)
    monkeypatch.setattr(conversation_service, "enrich_flights_from_travelpayouts", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(conversation_service, "enrich_flights_from_amadeus", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        conversation_service,
        "build_quick_plan_module_outputs",
        lambda **_: TripModuleOutputs(),
    )

    response = send_trip_message(
        _Graph(),
        db=SimpleNamespace(),
        trip_id="trip_1",
        user_id="user_1",
        payload=TripConversationMessageRequest(
            message="Quick plan.",
            board_action={"action_id": "action_1", "type": "select_quick_plan"},
        ),
    )

    final_call = persisted_calls[-1]
    final_build = final_call["conversation"]["quick_plan_build"]
    assert final_build["status"] == "complete"
    assert final_build["failed_stage"] == "hotels"
    assert "placeholder" not in final_build["message"].lower()
    assert final_call["module_outputs"]["flights"][0]["inventory_source"] == "placeholder"
    assert final_call["module_outputs"]["flights"][0]["carrier"] == "Best-fit route estimate"
    assert final_call["module_outputs"]["flights"][0]["duration_text"] == "Best-fit route"
    assert final_call["module_outputs"]["flights"][0]["price_text"].startswith("Flight budget GBP")
    assert final_call["module_outputs"]["flights"][0]["arrival_airport"] == "OSA"
    assert final_call["module_outputs"]["weather"][0]["id"] == "weather_outlook_1"
    assert "weather" in final_call["conversation"]["quick_plan_build"]["completed_stages"]
    assert "itinerary" in final_call["conversation"]["quick_plan_build"]["completed_stages"]
    assert any(
        "Kyoto is reached" in note
        for note in final_call["module_outputs"]["flights"][0]["notes"]
    )
    assert final_call["module_outputs"]["flights"][1]["direction"] == "return"
    assert final_call["budget_estimate"]["categories"][0]["category"] == "flights"
    assert final_call["budget_estimate"]["categories"][0]["source"] == "planner_estimate"
    assert response.trip_draft.conversation.quick_plan_finalization.brochure_eligible is False


def test_send_trip_message_sanitizes_existing_overlong_last_turn_summary(
    monkeypatch,
) -> None:
    captured: dict = {}
    trip = SimpleNamespace(
        id="trip_1",
        thread_id="thread_1",
        browser_session_id="browser_1",
        title="Kyoto planner",
    )
    draft = SimpleNamespace(
        thread_id="thread_1",
        title="Kyoto planner",
        configuration={"to_location": "Kyoto"},
        timeline=[],
        module_outputs={},
        budget_estimate=None,
        status={"confirmation_status": "unconfirmed"},
        conversation={
            "planning_mode": "quick",
            "last_turn_summary": " ".join(["Overlong previous summary."] * 30),
        },
    )

    class _Graph:
        def invoke(self, payload, config=None):
            captured["payload_summary"] = payload["trip_draft"]["conversation"][
                "last_turn_summary"
            ]
            return {
                "assistant_response": "Still working.",
                "trip_draft": {
                    "title": "Kyoto planner",
                    "configuration": draft.configuration,
                    "timeline": [],
                    "module_outputs": {},
                    "budget_estimate": None,
                    "status": draft.status,
                    "conversation": payload["trip_draft"]["conversation"],
                },
            }

    def _upsert_trip_draft(_db, **kwargs):
        captured["persisted_summary"] = kwargs["conversation"]["last_turn_summary"]
        return SimpleNamespace(
            thread_id=kwargs["thread_id"],
            title=kwargs["title"],
            configuration=kwargs["configuration"],
            timeline=kwargs["timeline"],
            module_outputs=kwargs["module_outputs"],
            budget_estimate=kwargs["budget_estimate"],
            status=kwargs["status"],
            conversation=kwargs["conversation"],
        )

    monkeypatch.setattr(conversation_service, "get_trip_for_user", lambda *_: trip)
    monkeypatch.setattr(conversation_service, "get_trip_draft_record", lambda *_: draft)
    monkeypatch.setattr(conversation_service, "upsert_trip_draft_record", _upsert_trip_draft)

    response = send_trip_message(
        _Graph(),
        db=SimpleNamespace(),
        trip_id="trip_1",
        user_id="user_1",
        payload=TripConversationMessageRequest(message="Retry."),
    )

    assert len(captured["payload_summary"]) <= 400
    assert len(captured["persisted_summary"]) <= 400
    assert response.trip_draft.conversation.last_turn_summary is not None
    assert len(response.trip_draft.conversation.last_turn_summary) <= 400
