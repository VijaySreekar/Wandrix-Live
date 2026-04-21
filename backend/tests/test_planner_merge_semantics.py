from datetime import datetime, timezone

from app.graph.planner.board_action_merge import apply_board_action_updates
from app.graph.planner.conversation_state import (
    build_conversation_state,
    build_status,
    detect_confirmed_field_corrections,
    is_trip_brief_confirmed,
    merge_decision_cards,
)
from app.graph.planner.draft_merge import merge_trip_configuration
from app.graph.planner.response_builder import build_assistant_response
from app.graph.planner.suggestion_board import build_default_decision_cards
from app.graph.planner.suggestion_board import build_suggestion_board_state
from app.graph.planner.turn_models import (
    DestinationSuggestionCandidate,
    ConversationOptionCandidate,
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripOpenQuestionUpdate,
    TripTurnUpdate,
)
from app.schemas.trip_conversation import (
    ConversationDecisionEvent,
    PlannerDecisionCard,
    TripConversationState,
)
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


def test_explicit_field_memory_stays_confirmed_when_later_turn_is_only_inferred() -> None:
    now = datetime.now(timezone.utc)
    initial_configuration = TripConfiguration(to_location="Lisbon")
    initial_conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=initial_configuration,
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            confirmed_fields=["to_location"],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Locked Lisbon as the trip direction.",
        turn_id="turn_1",
        user_message="Definitely Lisbon.",
        now=now,
    )

    follow_up_conversation = build_conversation_state(
        current=initial_conversation,
        previous_configuration=initial_configuration,
        next_configuration=initial_configuration,
        llm_update=TripTurnUpdate(
            to_location="Porto",
            inferred_fields=["to_location"],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Porto could work too, but Lisbon still looks strongest.",
        turn_id="turn_2",
        user_message="Maybe Porto too, but Lisbon still sounds right.",
        now=now,
    )
    status = build_status(
        current=TripDraftStatus(),
        configuration=initial_configuration,
        conversation=follow_up_conversation,
        module_outputs=TripModuleOutputs(),
        now=now,
    )

    field_memory = follow_up_conversation.memory.field_memory["to_location"]

    assert field_memory.value == "Lisbon"
    assert field_memory.source == "user_explicit"
    assert status.confirmed_fields == ["to_location"]
    assert status.inferred_fields == []


def test_field_memory_stores_structured_confidence_levels() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Barcelona",
    )
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            from_location="London",
            to_location="Barcelona",
            confirmed_fields=["to_location"],
            inferred_fields=["from_location"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="from_location", confidence="low"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="from_location", source="user_inferred"),
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Barcelona looks strongest, and London still feels provisional.",
        turn_id="turn_1",
        user_message="Probably Barcelona, leaving from London I think.",
        now=now,
    )

    destination_memory = conversation.memory.field_memory["to_location"]
    origin_memory = conversation.memory.field_memory["from_location"]

    assert destination_memory.confidence_level == "high"
    assert destination_memory.confidence is None
    assert destination_memory.source == "user_explicit"
    assert origin_memory.confidence_level == "low"
    assert origin_memory.confidence is None
    assert origin_memory.source == "user_inferred"


def test_field_memory_preserves_profile_default_source_as_inferred() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(from_location="London", to_location="Barcelona")
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            from_location="London",
            to_location="Barcelona",
            confirmed_fields=["to_location"],
            inferred_fields=["from_location"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="from_location", confidence="medium"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="from_location", source="profile_default"),
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Barcelona is locked, and London is just the current default origin.",
        turn_id="turn_1",
        user_message="Plan Barcelona next spring.",
        now=now,
    )
    status = build_status(
        current=TripDraftStatus(),
        configuration=configuration,
        conversation=conversation,
        module_outputs=TripModuleOutputs(),
        now=now,
    )

    origin_memory = conversation.memory.field_memory["from_location"]

    assert origin_memory.source == "profile_default"
    assert origin_memory.confidence_level == "medium"
    assert status.confirmed_fields == ["to_location"]
    assert status.inferred_fields == ["from_location"]


def test_explicit_correction_replaces_prior_inferred_field_memory() -> None:
    now = datetime.now(timezone.utc)
    previous_configuration = TripConfiguration(to_location="Rome")
    initial_conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=previous_configuration,
        llm_update=TripTurnUpdate(
            to_location="Rome",
            inferred_fields=["to_location"],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Rome looks like the leading option so far.",
        turn_id="turn_1",
        user_message="Maybe Rome in May.",
        now=now,
    )

    corrected_configuration = TripConfiguration(to_location="Florence")
    corrected_conversation = build_conversation_state(
        current=initial_conversation,
        previous_configuration=previous_configuration,
        next_configuration=corrected_configuration,
        llm_update=TripTurnUpdate(
            to_location="Florence",
            confirmed_fields=["to_location"],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Switching this over to Florence.",
        turn_id="turn_2",
        user_message="Actually make it Florence.",
        now=now,
    )

    field_memory = corrected_conversation.memory.field_memory["to_location"]

    assert field_memory.value == "Florence"
    assert field_memory.source == "user_explicit"
    assert corrected_conversation.memory.rejected_options[-1].kind == "destination"
    assert corrected_conversation.memory.rejected_options[-1].value == "Rome"


def test_board_confirmed_fields_get_high_confidence_memory() -> None:
    now = datetime.now(timezone.utc)
    board_action = {
        "action_id": "action_1",
        "type": "confirm_trip_details",
        "to_location": "Kyoto",
        "travel_window": "late March",
        "weather_preference": "mild",
    }
    llm_update = apply_board_action_updates(TripTurnUpdate(), board_action=board_action)
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="late March",
        weather_preference="mild",
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=llm_update,
        module_outputs=TripModuleOutputs(),
        assistant_response="Kyoto in late March is now the working brief.",
        turn_id="turn_1",
        user_message="",
        now=now,
        board_action=board_action,
        brief_confirmed=True,
    )
    status = build_status(
        current=TripDraftStatus(),
        configuration=configuration,
        conversation=conversation,
        module_outputs=TripModuleOutputs(),
        now=now,
    )

    destination_memory = conversation.memory.field_memory["to_location"]
    timing_memory = conversation.memory.field_memory["travel_window"]
    weather_memory = conversation.memory.field_memory["weather_preference"]

    assert destination_memory.source == "board_action"
    assert destination_memory.confidence_level == "high"
    assert timing_memory.source == "board_action"
    assert timing_memory.confidence_level == "high"
    assert weather_memory.source == "board_action"
    assert weather_memory.confidence_level == "high"
    assert status.confirmed_fields == [
        "to_location",
        "travel_window",
        "weather_preference",
    ]
    assert status.inferred_fields == []


def test_confirmed_correction_is_recorded_and_requires_reconfirmation() -> None:
    now = datetime.now(timezone.utc)
    previous_configuration = TripConfiguration(
        from_location="London",
        to_location="Rome",
        travel_window="May",
        trip_length="4 nights",
        budget_posture="mid_range",
    )
    current_conversation = TripConversationState.model_validate(
        {
            "memory": {
                "decision_history": [
                    {
                        "id": "decision_confirmed",
                        "title": "Trip details confirmed",
                        "description": "The user confirmed the current working trip details in chat.",
                        "options": [],
                        "selected_option": "confirm_trip_details",
                        "source_turn_id": "turn_1",
                        "resolved_at": now.isoformat(),
                    }
                ]
            }
        }
    )
    corrected_configuration = previous_configuration.model_copy(deep=True)
    corrected_configuration.to_location = "Florence"
    llm_update = TripTurnUpdate(
        to_location="Florence",
        confirmed_fields=["to_location"],
        field_sources=[
            TripFieldSourceUpdate(field="to_location", source="user_explicit"),
        ],
    )

    corrected_fields = detect_confirmed_field_corrections(
        previous_configuration=previous_configuration,
        next_configuration=corrected_configuration,
        llm_update=llm_update,
    )

    assert corrected_fields == ["to_location"]
    assert (
        is_trip_brief_confirmed(
            current_conversation,
            llm_update,
            corrected_fields=corrected_fields,
        )
        is False
    )

    next_conversation = build_conversation_state(
        current=current_conversation,
        previous_configuration=previous_configuration,
        next_configuration=corrected_configuration,
        llm_update=llm_update,
        module_outputs=TripModuleOutputs(),
        assistant_response="Switching this over to Florence.",
        turn_id="turn_2",
        user_message="Actually make it Florence.",
        now=now,
        brief_confirmed=False,
    )

    assert next_conversation.suggestion_board.mode == "details_collection"
    assert next_conversation.memory.decision_history[-1].title == "Trip details corrected"
    assert "Rome" in next_conversation.memory.decision_history[-1].description
    assert "Florence" in next_conversation.memory.decision_history[-1].description


def test_latest_trip_brief_event_controls_confirmation_state() -> None:
    now = datetime.now(timezone.utc)
    conversation = TripConversationState.model_validate(
        {
            "memory": {
                "decision_history": [
                    {
                        "id": "decision_confirmed",
                        "title": "Trip details confirmed",
                        "description": "The user confirmed the trip details.",
                        "options": [],
                        "selected_option": "confirm_trip_details",
                        "source_turn_id": "turn_1",
                        "resolved_at": now.isoformat(),
                    },
                    {
                        "id": "decision_corrected",
                        "title": "Trip details corrected",
                        "description": "The user corrected the destination.",
                        "options": ["to_location"],
                        "selected_option": "to_location",
                        "source_turn_id": "turn_2",
                        "resolved_at": now.isoformat(),
                    },
                ]
            }
        }
    )

    assert is_trip_brief_confirmed(conversation, TripTurnUpdate()) is False

    reconfirmed_conversation = conversation.model_copy(deep=True)
    reconfirmed_conversation.memory.decision_history.append(
        ConversationDecisionEvent(
            id="decision_reconfirmed",
            title="Trip details confirmed",
            description="The user confirmed the current working trip details in chat.",
            options=[],
            selected_option="confirm_trip_details",
            source_turn_id="turn_3",
            resolved_at=now,
        )
    )

    assert is_trip_brief_confirmed(reconfirmed_conversation, TripTurnUpdate()) is True


def test_open_questions_prioritize_destination_before_timing_when_trip_shape_is_broad() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(),
        llm_update=TripTurnUpdate(
            open_question_updates=[
                TripOpenQuestionUpdate(
                    question="What exact dates are you thinking about?",
                    field="start_date",
                    step="timing",
                    priority=1,
                    why="Timing would help.",
                ),
                TripOpenQuestionUpdate(
                    question="Which destination should I shape this trip around?",
                    field="to_location",
                    step="route",
                    priority=3,
                    why="Destination is still broad.",
                ),
            ]
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Keeping this broad for now.",
        turn_id="turn_1",
        user_message="Somewhere warm in Europe this autumn.",
        now=now,
    )

    open_questions = [
        question for question in conversation.open_questions if question.status == "open"
    ]

    assert open_questions[0].field == "to_location"
    assert open_questions[0].step == "route"
    assert open_questions[0].priority == 1
    assert open_questions[0].why is not None
    assert any(question.field == "travel_window" for question in open_questions)


def test_open_questions_mark_answered_when_field_is_no_longer_missing() -> None:
    now = datetime.now(timezone.utc)
    current_conversation = TripConversationState.model_validate(
        {
            "open_questions": [
                {
                    "id": "question_timing",
                    "question": "What month or travel window are you considering?",
                    "field": "travel_window",
                    "step": "timing",
                    "priority": 2,
                    "why": "Timing is still open.",
                    "status": "open",
                }
            ]
        }
    )
    next_configuration = TripConfiguration(
        to_location="Lisbon",
        travel_window="late September",
    )

    next_conversation = build_conversation_state(
        current=current_conversation,
        previous_configuration=TripConfiguration(to_location="Lisbon"),
        next_configuration=next_configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Late September works well.",
        turn_id="turn_2",
        user_message="Let's do late September.",
        now=now,
    )

    timing_question = next(
        question
        for question in next_conversation.open_questions
        if question.id == "question_timing"
    )

    assert timing_question.status == "answered"


def test_default_origin_question_stays_tentative() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Lisbon",
        travel_window="late September",
        trip_length="4 nights",
    )
    configuration.travelers.adults = 2
    configuration.selected_modules.activities = False

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Let's keep shaping this.",
        turn_id="turn_1",
        user_message="Plan Lisbon for late September.",
        now=now,
    )

    origin_question = next(
        question
        for question in conversation.open_questions
        if question.field == "from_location" and question.status == "open"
    )

    assert "most likely travelling from" in origin_question.question.lower()
    assert "likely departure point" in (origin_question.why or "").lower()


def test_default_budget_question_supports_mixed_tradeoffs() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Lisbon",
        travel_window="late September",
        trip_length="4 nights",
    )
    configuration.travelers.adults = 2
    configuration.selected_modules.activities = False

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Let's keep shaping this.",
        turn_id="turn_1",
        user_message="Plan Lisbon for late September.",
        now=now,
    )

    budget_question = next(
        question
        for question in conversation.open_questions
        if question.field == "budget_posture" and question.status == "open"
    )

    assert "splurge" in budget_question.question.lower()
    assert "keep sensible" in budget_question.question.lower()
    assert "mixed" in (budget_question.why or "").lower()


def test_default_traveller_question_handles_group_makeup() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="late March",
        trip_length="5 nights",
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Let's keep shaping this.",
        turn_id="turn_1",
        user_message="Plan Kyoto in late March.",
        now=now,
    )

    traveller_question = next(
        question
        for question in conversation.open_questions
        if question.field == "adults" and question.status == "open"
    )

    assert "children" in traveller_question.question.lower()
    assert "group makeup" in (traveller_question.why or "").lower()


def test_default_module_scope_question_supports_booked_items() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        travel_window="late March",
        trip_length="5 nights",
        budget_posture="mid_range",
    )
    configuration.travelers.adults = 2
    configuration.activity_styles = ["culture"]

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Let's figure out the scope first.",
        turn_id="turn_1",
        user_message="Help me plan Kyoto.",
        now=now,
    )

    module_question = next(
        question
        for question in conversation.open_questions
        if question.field == "selected_modules" and question.status == "open"
    )

    assert "already booked" in module_question.question.lower()
    assert "providers" in (module_question.why or "").lower()


def test_inferred_module_scope_can_narrow_default_modules() -> None:
    narrowed = merge_trip_configuration(
        TripConfiguration(),
        TripTurnUpdate(
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
            inferred_fields=["selected_modules"],
        ),
    )

    assert narrowed.selected_modules.activities is True
    assert narrowed.selected_modules.flights is False
    assert narrowed.selected_modules.hotels is False
    assert narrowed.selected_modules.weather is False


def test_own_choice_clears_destination_suggestions() -> None:
    now = datetime.now(timezone.utc)
    current = TripConversationState.model_validate(
        {
            "suggestion_board": {
                "mode": "destination_suggestions",
                "cards": [
                    {
                        "id": "dest_1",
                        "destination_name": "Valencia",
                        "country_or_region": "Spain",
                        "image_url": "https://example.com/valencia.jpg",
                        "short_reason": "Sunny and easy.",
                        "practicality_label": "Shorthaul",
                        "selection_status": "suggested",
                    }
                ],
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Tell me the destination you already have in mind.",
        turn_id="turn_1",
        user_message="",
        now=now,
        board_action={
            "action_id": "action_1",
            "type": "own_choice",
            "prompt_text": "Tell me the destination you already have in mind.",
        },
    )

    assert conversation.suggestion_board.mode == "helper"
    assert conversation.suggestion_board.cards == []
    assert "destination you already have in mind" in (
        conversation.suggestion_board.title or ""
    ).lower()


def test_default_decision_cards_are_contextual() -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="late March",
        trip_length="5 nights",
    )

    cards = build_default_decision_cards(configuration)

    assert cards[0].title == "Set the departure point"
    assert any("usual airport" in option.lower() for option in cards[0].options)
    assert cards[1].title == "Choose the feel for Kyoto"
    assert any("food-led" in option.lower() for option in cards[1].options)


def test_generic_decision_cards_are_filtered_out() -> None:
    cards = merge_decision_cards(
        [],
        [
            PlannerDecisionCard(
                title="Next trip decisions",
                description="These cards can help shape the trip.",
                options=["Option 1", "Option 2"],
            ),
            PlannerDecisionCard(
                title="Choose the feel for Lisbon",
                description="These are the strongest trip directions to decide between before I start shaping the itinerary.",
                options=[
                    "Food-led neighbourhood weekend",
                    "Classic highlights city break",
                ],
            ),
        ],
        "shaping_trip",
    )

    assert len(cards) == 1
    assert cards[0].title == "Choose the feel for Lisbon"


def test_decision_card_response_mentions_real_choices() -> None:
    conversation = TripConversationState.model_validate(
        {
            "suggestion_board": {
                "mode": "decision_cards",
            },
            "decision_cards": [
                {
                    "title": "Choose the feel for Lisbon",
                    "description": "These are the strongest trip directions to decide between before I start shaping the itinerary.",
                    "options": [
                        "Food-led neighbourhood weekend",
                        "Classic highlights city break",
                    ],
                }
            ],
        }
    )

    response = build_assistant_response(
        configuration=TripConfiguration(to_location="Lisbon"),
        conversation=conversation,
        llm_update=TripTurnUpdate(),
        brief_confirmed=False,
        fallback_text=None,
        profile_context={},
        board_action=None,
        confirmation_status="unconfirmed",
        finalized_via=None,
    )

    assert "stop asking filler questions" in response.lower()
    assert "choose the feel for lisbon" in response.lower()


def test_shaping_response_frames_working_shape_and_next_move() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Lisbon",
        travel_window="early October",
        trip_length="five-ish days",
    )
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            from_location="London",
            to_location="Lisbon",
            travel_window="early October",
            trip_length="five-ish days",
            confirmed_fields=["to_location"],
            inferred_fields=["from_location", "travel_window", "trip_length"],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="from_location", source="user_inferred"),
                TripFieldSourceUpdate(field="travel_window", source="user_inferred"),
                TripFieldSourceUpdate(field="trip_length", source="user_inferred"),
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_1",
        user_message="Lisbon in early October for five-ish days, probably from London.",
        now=now,
    )
    conversation = conversation.model_copy(deep=True)
    conversation.suggestion_board.mode = "helper"

    response = build_assistant_response(
        configuration=configuration,
        conversation=conversation,
        llm_update=TripTurnUpdate(),
        brief_confirmed=False,
        fallback_text=None,
        profile_context={},
        board_action=None,
        confirmation_status="unconfirmed",
        finalized_via=None,
    )

    assert "i now have lisbon" in response.lower()
    assert "early october" in response.lower()
    assert "five-ish days" in response.lower()
    assert "departure point" in response.lower()
    assert "provisional" in response.lower()
    assert "main thing i'd confirm next" in response.lower()


def test_rejected_destination_is_filtered_from_future_suggestions() -> None:
    current = TripConversationState.model_validate(
        {
            "memory": {
                "rejected_options": [
                    {
                        "kind": "destination",
                        "value": "Prague",
                    }
                ]
            }
        }
    )

    board = build_suggestion_board_state(
        current=current,
        configuration=TripConfiguration(),
        phase="opening",
        llm_update=TripTurnUpdate(
            destination_suggestions=[
                DestinationSuggestionCandidate(
                    id="dest_prague",
                    destination_name="Prague",
                    country_or_region="Czech Republic",
                    image_url="https://example.com/prague.jpg",
                    short_reason="Historic and compact.",
                    practicality_label="Weekend-friendly",
                ),
                DestinationSuggestionCandidate(
                    id="dest_valencia",
                    destination_name="Valencia",
                    country_or_region="Spain",
                    image_url="https://example.com/valencia.jpg",
                    short_reason="Sunny and food-led.",
                    practicality_label="Easy short-haul",
                ),
            ]
        ),
        resolved_location_context=None,
        board_action={},
        brief_confirmed=False,
    )

    assert board.mode == "destination_suggestions"
    assert [card.destination_name for card in board.cards] == ["Valencia"]


def test_reintroduced_destination_leaves_rejected_memory() -> None:
    now = datetime.now(timezone.utc)
    current = TripConversationState.model_validate(
        {
            "memory": {
                "rejected_options": [
                    {
                        "kind": "destination",
                        "value": "Prague",
                        "source_turn_id": "turn_1",
                        "first_seen_at": now.isoformat(),
                        "last_seen_at": now.isoformat(),
                    }
                ]
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(to_location="Prague"),
        llm_update=TripTurnUpdate(
            to_location="Prague",
            confirmed_fields=["to_location"],
            mentioned_options=[
                ConversationOptionCandidate(kind="destination", value="Prague")
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Okay, let's switch this back to Prague.",
        turn_id="turn_2",
        user_message="Actually, let's do Prague after all.",
        now=now,
    )

    assert [option.value for option in conversation.memory.rejected_options] == []
    assert any(
        option.value == "Prague"
        for option in conversation.memory.mentioned_options
    )
