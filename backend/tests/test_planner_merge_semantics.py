from datetime import datetime, timezone

from app.graph.planner.board_action_merge import apply_board_action_updates
from app.graph.planner.conversation_state import build_conversation_state, build_status
from app.graph.planner.turn_models import TripFieldConfidenceUpdate, TripTurnUpdate
from app.schemas.trip_conversation import TripConversationState
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
    assert origin_memory.confidence_level == "low"
    assert origin_memory.confidence is None


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
    }
    llm_update = apply_board_action_updates(TripTurnUpdate(), board_action=board_action)
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="late March",
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

    destination_memory = conversation.memory.field_memory["to_location"]
    timing_memory = conversation.memory.field_memory["travel_window"]

    assert destination_memory.source == "user_explicit"
    assert destination_memory.confidence_level == "high"
    assert timing_memory.source == "user_explicit"
    assert timing_memory.confidence_level == "high"
