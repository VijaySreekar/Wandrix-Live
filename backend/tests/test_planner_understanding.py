from app.graph.planner import understanding
from app.graph.planner.turn_models import TripTurnUpdate
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration


class _FakeStructuredModel:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def invoke(self, messages):
        self._captured["messages"] = messages
        return TripTurnUpdate()


class _FakeChatModel:
    def __init__(self, captured: dict) -> None:
        self._captured = captured

    def with_structured_output(self, schema, method):
        self._captured["schema"] = schema
        self._captured["method"] = method
        return _FakeStructuredModel(self._captured)


def test_understanding_prompt_teaches_ambiguity_preservation(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="Somewhere warm in Europe this autumn.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert captured["method"] == "json_schema"
    assert "Preserve ambiguity on purpose instead of collapsing it too early." in prompt
    assert (
        "If the user names a region, climate, or broad trip type without choosing one place, do not set to_location to a single guessed city or country."
        in prompt
    )
    assert (
        "If the user gives multiple possible destinations or origins, keep them as mentioned_options unless they clearly chose one."
        in prompt
    )
    assert "Prefer open_question_updates over the legacy open_questions string list." in prompt
    assert "Priority 1 means the highest-value next question." in prompt
    assert 'User: "Somewhere warm in Europe this autumn."' in prompt
    assert 'User: "Probably leaving from London, though Manchester could work too."' in prompt


def test_understanding_prompt_teaches_rough_timing_preservation(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="Maybe early October for five-ish days.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert (
        'If the user gives seasonal, holiday, relative-month, or soft timing language like "early October", "around Easter", "sometime in spring", or "late September", keep that in travel_window unless they gave exact calendar dates.'
        in prompt
    )
    assert (
        'If the user gives rough duration language like "long weekend", "five-ish days", "about a week", or "4 or 5 nights", keep that in trip_length unless they gave exact fixed dates.'
        in prompt
    )
    assert "Do not auto-convert rough timing into exact dates just to be helpful." in prompt
    assert 'User: "Maybe early October for five-ish days."' in prompt


def test_understanding_prompt_teaches_tentative_origin_preservation(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="I'd probably leave from London unless Manchester ends up much easier.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert (
        'If the user gives a likely or fallback origin, you may keep one working origin in from_location as an inferred field, but only when the wording supports "most likely" rather than "confirmed".'
        in prompt
    )
    assert (
        "If the user mentions an origin conditionally, preserve the fallback or comparison origin in mentioned_options instead of collapsing to one hard answer."
        in prompt
    )
    assert (
        'User: "I\'d probably leave from London unless Manchester ends up much easier."'
        in prompt
    )


def test_understanding_prompt_teaches_budget_nuance(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="I don't need luxury, but I don't want it to feel cheap either.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert "Budget language is often nuanced and mixed." in prompt
    assert (
        'If the user says things like "not too expensive", "keep hotels sensible", "happy to splurge on food", or "don\'t need luxury but don\'t want it cheap", interpret budget posture carefully and keep it inferred unless they made the posture explicit.'
        in prompt
    )
    assert (
        "If the budget signal is mixed or partial, prefer a soft budget_posture plus a clarifying open question instead of false certainty."
        in prompt
    )
    assert (
        'User: "I don\'t need luxury, but I don\'t want it to feel cheap either."'
        in prompt
    )


def test_understanding_prompt_teaches_traveller_composition_nuance(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="It's a family trip to Portugal.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert "Handle traveller composition carefully." in prompt
    assert (
        'If the user says they are a couple or says "the two of us", you may infer `adults=2` as an inferred field when the meaning is clear.'
        in prompt
    )
    assert (
        "If the user says family, travelling with kids, toddler, child, or similar family context without giving counts, do not invent exact adult or child numbers."
        in prompt
    )
    assert (
        "If child presence is implied but counts are missing, prefer an open question about the group makeup instead of false precision."
        in prompt
    )
    assert 'User: "It\'s a family trip to Portugal."' in prompt
    assert 'User: "It\'s just the two of us."' in prompt


def test_understanding_prompt_teaches_module_scope_narrowing(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="I already booked flights. Just help me with what to do in Kyoto.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert "Module scope is structured planner meaning, not just a side note." in prompt
    assert (
        "If the user says they only want one area like activities, hotels, flights, or weather, update `selected_modules` to reflect that focus."
        in prompt
    )
    assert (
        "If the user says something is already booked or they do not need help with it, turn that module off unless the same turn clearly re-enables it."
        in prompt
    )
    assert (
        "If the user says something like \"hotels later\" or \"we can sort flights ourselves\", keep the scope narrow for now rather than forcing every module back on."
        in prompt
    )
    assert 'User: "I already booked flights. Just help me with what to do in Kyoto."' in prompt


def test_understanding_prompt_teaches_profile_context_stays_soft(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="Somewhere sunny for a weekend.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={
            "home_city": "London",
            "preferred_styles": ["food"],
            "trip_pace": "relaxed",
        },
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert (
        "Saved profile context is there to personalize suggestions and wording, not to silently become trip facts."
        in prompt
    )
    assert (
        "Do not copy a saved home base, airport, preferred style, or trip pace into structured trip fields unless the user adopts it for this specific trip."
        in prompt
    )
    assert (
        "If profile context is helpful, mention it as an optional starting point in assistant_response rather than treating it as confirmed trip data."
        in prompt
    )


def test_understanding_prompt_teaches_planning_mode_is_explicit(monkeypatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        understanding,
        "create_chat_model",
        lambda temperature=0.1: _FakeChatModel(captured),
    )

    understanding.generate_llm_trip_update(
        user_input="Yes, go ahead.",
        configuration=TripConfiguration(),
        title="Trip planner",
        status=TripDraftStatus(),
        conversation=TripConversationState(),
        profile_context={},
        current_location_context={},
        board_action={},
        raw_messages=[],
    )

    prompt = captured["messages"][1][1]

    assert (
        "Treat planning mode as a separate explicit lifecycle decision from trip-brief confirmation."
        in prompt
    )
    assert (
        'Generic approval like "yes", "looks good", "proceed", or "go ahead" should usually confirm the brief first, not automatically choose a planning mode.'
        in prompt
    )
    assert (
        "Only set requested_planning_mode when the user is clearly asking to start that mode, not when they are just approving the trip brief in general."
        in prompt
    )
