from datetime import date, datetime, timezone

from app.graph.planner.board_action_merge import apply_board_action_updates
from app.graph.planner import conversation_state
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
from app.graph.planner.timing_intake import sanitize_timing_update
from app.graph.planner.trip_brief_board import (
    build_details_field_meta,
    get_suggested_details_step,
)
from app.graph.planner.turn_models import (
    DestinationSuggestionCandidate,
    ConversationOptionCandidate,
    RequestedActivityDecision,
    RequestedActivityScheduleEdit,
    RequestedFlightUpdate,
    RequestedReviewResolution,
    RequestedTripStyleDirectionUpdate,
    RequestedTripStylePaceUpdate,
    RequestedTripStyleTradeoffUpdate,
    TripFieldConfidenceUpdate,
    TripFieldSourceUpdate,
    TripOpenQuestionUpdate,
    TripTurnUpdate,
)
from app.schemas.trip_conversation import (
    ConversationDecisionEvent,
    PlannerDecisionCard,
    PlannerDecisionMemoryRecord,
    TripConversationState,
)
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services.providers.movement import MovementEstimate
from app.utils import destination_images


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


def test_budget_currency_only_merges_without_inventing_amount() -> None:
    configuration = merge_trip_configuration(
        TripConfiguration(),
        TripTurnUpdate(
            budget_currency="gbp",
            inferred_fields=["budget_currency"],
            field_confidences=[
                TripFieldConfidenceUpdate(
                    field="budget_currency",
                    confidence="high",
                )
            ],
            field_sources=[
                TripFieldSourceUpdate(
                    field="budget_currency",
                    source="user_explicit",
                )
            ],
        ),
    )

    assert configuration.budget_currency == "GBP"
    assert configuration.budget_amount is None
    assert configuration.budget_gbp is None


def test_legacy_budget_gbp_populates_currency_aware_fields() -> None:
    configuration = merge_trip_configuration(
        TripConfiguration(),
        TripTurnUpdate(
            budget_gbp=1800,
            confirmed_fields=["budget_gbp"],
        ),
    )

    assert configuration.budget_amount == 1800
    assert configuration.budget_currency == "GBP"
    assert configuration.budget_gbp == 1800


def test_trip_brief_field_meta_uses_memory_sources() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Lisbon",
        travel_window="around June 15th",
        trip_length="long weekend",
        budget_currency="GBP",
        activity_styles=["relaxed"],
    )
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            travel_window="around June 15th",
            trip_length="long weekend",
            budget_currency="GBP",
            activity_styles=["relaxed"],
            confirmed_fields=["to_location", "budget_currency"],
            inferred_fields=["travel_window", "trip_length", "activity_styles"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="high"),
                TripFieldConfidenceUpdate(field="budget_currency", confidence="high"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="medium"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="medium"),
                TripFieldConfidenceUpdate(field="activity_styles", confidence="medium"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_explicit"),
                TripFieldSourceUpdate(field="budget_currency", source="user_explicit"),
                TripFieldSourceUpdate(field="travel_window", source="user_inferred"),
                TripFieldSourceUpdate(field="trip_length", source="user_inferred"),
                TripFieldSourceUpdate(field="activity_styles", source="user_inferred"),
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Lisbon is the working direction.",
        turn_id="turn_1",
        user_message="Lisbon around June 15th, relaxed, in GBP.",
        now=now,
    )

    field_meta = build_details_field_meta(conversation.memory.field_memory)

    assert field_meta["budget_currency"].label == "You said"
    assert field_meta["activity_styles"].label == "Inferred"
    assert get_suggested_details_step(configuration) == "route"


def test_decision_memory_tracks_profile_defaults_as_working_not_confirmed() -> None:
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

    decision_memory = {
        record.key: record for record in conversation.memory.decision_memory
    }

    assert decision_memory["destination"].value_summary == "Barcelona"
    assert decision_memory["destination"].source == "user_explicit"
    assert decision_memory["destination"].status == "confirmed"
    assert decision_memory["origin"].value_summary == "London"
    assert decision_memory["origin"].source == "profile_default"
    assert decision_memory["origin"].confidence == "medium"
    assert decision_memory["origin"].status == "working"


def test_decision_memory_preserves_stronger_explicit_source_for_same_value() -> None:
    now = datetime.now(timezone.utc)
    current = TripConversationState.model_validate(
        {
            "memory": {
                "decision_memory": [
                    {
                        "key": "destination",
                        "value_summary": "Lisbon",
                        "source": "user_explicit",
                        "confidence": "high",
                        "status": "confirmed",
                        "rationale": "The user explicitly chose Lisbon.",
                        "updated_at": now.isoformat(),
                    }
                ]
            }
        }
    )
    configuration = TripConfiguration(to_location="Lisbon")

    conversation = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            to_location="Lisbon",
            inferred_fields=["to_location"],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="profile_default"),
            ],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="medium"),
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Lisbon is still the default destination.",
        turn_id="turn_2",
        user_message="Keep going.",
        now=now,
    )

    destination_memory = next(
        record
        for record in conversation.memory.decision_memory
        if record.key == "destination"
    )

    assert destination_memory.value_summary == "Lisbon"
    assert destination_memory.source == "user_explicit"
    assert destination_memory.confidence == "high"
    assert destination_memory.status == "confirmed"


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


def test_board_activity_schedule_action_is_merged_into_turn_update() -> None:
    update = apply_board_action_updates(
        TripTurnUpdate(),
        board_action={
            "action_id": "action_move_market",
            "type": "move_activity_candidate_to_day",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_kind": "activity",
            "activity_target_day_index": 2,
        },
    )

    assert len(update.requested_activity_schedule_edits) == 1
    edit = update.requested_activity_schedule_edits[0]
    assert edit.action == "move_to_day"
    assert edit.candidate_id == "activity_market"
    assert edit.candidate_title == "Nishiki Market tasting walk"
    assert edit.target_day_index == 2


def test_board_trip_style_direction_action_is_merged_into_turn_update() -> None:
    update = apply_board_action_updates(
        TripTurnUpdate(),
        board_action={
            "action_id": "action_trip_style_primary",
            "type": "select_trip_style_direction_primary",
            "trip_style_direction_primary": "food_led",
        },
    )

    assert len(update.requested_trip_style_direction_updates) == 1
    direction_update = update.requested_trip_style_direction_updates[0]
    assert direction_update.action == "select_primary"
    assert direction_update.primary == "food_led"


def test_board_trip_style_pace_action_is_merged_into_turn_update() -> None:
    update = apply_board_action_updates(
        TripTurnUpdate(),
        board_action={
            "action_id": "action_trip_style_pace",
            "type": "confirm_trip_style_pace",
            "trip_style_pace": "slow",
        },
    )

    assert len(update.requested_trip_style_pace_updates) == 1
    pace_update = update.requested_trip_style_pace_updates[0]
    assert pace_update.action == "confirm"
    assert pace_update.pace == "slow"


def test_board_trip_style_tradeoff_action_is_merged_into_turn_update() -> None:
    update = apply_board_action_updates(
        TripTurnUpdate(),
        board_action={
            "action_id": "action_trip_style_tradeoff",
            "type": "set_trip_style_tradeoff",
            "trip_style_tradeoff_axis": "must_sees_vs_wandering",
            "trip_style_tradeoff_value": "wandering",
        },
    )

    assert len(update.requested_trip_style_tradeoff_updates) == 1
    tradeoff_update = update.requested_trip_style_tradeoff_updates[0]
    assert tradeoff_update.action == "set_tradeoff"
    assert tradeoff_update.axis == "must_sees_vs_wandering"
    assert tradeoff_update.value == "wandering"


def test_decision_memory_records_completed_trip_style_from_chat_updates() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(to_location="Kyoto"),
        llm_update=TripTurnUpdate(
            requested_trip_style_direction_updates=[
                RequestedTripStyleDirectionUpdate(
                    action="confirm",
                    primary="culture_led",
                    accent="classic",
                )
            ],
            requested_trip_style_pace_updates=[
                RequestedTripStylePaceUpdate(action="confirm", pace="slow")
            ],
            requested_trip_style_tradeoff_updates=[
                RequestedTripStyleTradeoffUpdate(
                    action="confirm",
                    axis="must_sees_vs_wandering",
                    value="wandering",
                )
            ],
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="Trip character is set.",
        turn_id="turn_trip_style",
        user_message="Make it culture-led, classic, slow, and wandering.",
        now=now,
        planning_mode="advanced",
        advanced_step="anchor_flow",
        advanced_anchor="trip_style",
    )

    decision_memory = {
        record.key: record for record in conversation.memory.decision_memory
    }

    assert decision_memory["trip_style_direction"].source == "user_explicit"
    assert decision_memory["trip_style_direction"].status == "confirmed"
    assert "Culture-led" in decision_memory["trip_style_direction"].value_summary
    assert decision_memory["trip_style_pace"].value_summary == "Slow"
    assert decision_memory["trip_style_pace"].status == "confirmed"
    assert decision_memory["trip_style_tradeoffs"].status == "confirmed"


def test_decision_memory_records_confirmed_flights_from_board_action() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=date(2027, 4, 1),
        end_date=date(2027, 4, 6),
    )
    configuration.travelers.adults = 2
    board_action = {
        "action_id": "action_confirm_flights",
        "type": "confirm_flight_selection",
    }

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Flights are selected as working planning choices.",
        turn_id="turn_flights",
        user_message="",
        now=now,
        board_action=board_action,
        planning_mode="advanced",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )

    selected_flights = next(
        record
        for record in conversation.memory.decision_memory
        if record.key == "selected_flights"
    )

    assert conversation.flight_planning.selection_status == "completed"
    assert selected_flights.source == "board_action"
    assert selected_flights.status == "confirmed"
    assert selected_flights.confidence == "high"


def test_board_advanced_finalization_action_is_merged_into_turn_update() -> None:
    update = apply_board_action_updates(
        TripTurnUpdate(),
        board_action={
            "action_id": "action_finalize_advanced",
            "type": "finalize_advanced_plan",
        },
    )

    assert update.requested_advanced_finalization is True
    assert update.planner_intent == "none"


def test_trip_style_direction_reorders_activity_candidates() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 27, tzinfo=timezone.utc).date(),
        activity_styles=["culture"],
        custom_style="slow temple mornings and market-heavy afternoons",
        selected_modules={
            "flights": False,
            "weather": True,
            "activities": True,
            "hotels": False,
        },
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                location_label="Downtown Kyoto",
                category="catering.restaurant",
                notes=["Downtown Kyoto"],
            ),
            ActivityDetail(
                id="activity_temple",
                title="Higashiyama temple circuit",
                location_label="Higashiyama, Kyoto",
                category="entertainment.museum",
                notes=["Higashiyama, Kyoto"],
            ),
        ]
    )

    baseline = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert baseline.activity_planning.recommended_candidates[0].id == "activity_temple"

    direction_state = build_conversation_state(
        current=baseline,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_trip_style_direction_updates=[
                RequestedTripStyleDirectionUpdate(
                    action="select_primary",
                    primary="food_led",
                ),
                RequestedTripStyleDirectionUpdate(action="confirm"),
            ]
        ),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_2",
        user_message="Make this more food-led.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="trip_style",
    )

    reranked = build_conversation_state(
        current=direction_state,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_3",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert reranked.trip_style_planning.substep == "pace"
    assert reranked.trip_style_planning.selection_status == "selected"
    assert reranked.activity_planning.recommended_candidates[0].id == "activity_market"


def test_trip_style_pace_changes_activity_schedule_density() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
        selected_modules={
            "flights": False,
            "weather": True,
            "activities": True,
            "hotels": False,
        },
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id=f"activity_{index}",
                title=f"Kyoto experience {index}",
                location_label="Kyoto",
                category="entertainment.museum",
            )
            for index in range(1, 5)
        ]
    )

    def scheduled_stop_count_for_pace(pace: str) -> int:
        current = TripConversationState.model_validate(
            {
                "trip_style_planning": {
                    "substep": "completed",
                    "selected_primary_direction": "balanced",
                    "selection_status": "completed",
                    "selected_pace": pace,
                    "pace_status": "completed",
                }
            }
        )
        conversation = build_conversation_state(
            current=current,
            previous_configuration=configuration,
            next_configuration=configuration,
            llm_update=TripTurnUpdate(),
            module_outputs=module_outputs,
            assistant_response="",
            turn_id=f"turn_{pace}",
            user_message="",
            now=now,
            planning_mode="advanced",
            planning_mode_status="selected",
            brief_confirmed=True,
            advanced_step="anchor_flow",
            advanced_anchor="activities",
        )
        return sum(
            1
            for block in conversation.activity_planning.timeline_blocks
            if block.type in {"activity", "event"}
        )

    assert scheduled_stop_count_for_pace("slow") == 1
    assert scheduled_stop_count_for_pace("balanced") == 2
    assert scheduled_stop_count_for_pace("full") == 3


def test_trip_style_tradeoff_recommendations_are_adaptive() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        activity_styles=["culture"],
        selected_modules={
            "flights": False,
            "weather": True,
            "activities": True,
            "hotels": True,
        },
    )
    current = TripConversationState.model_validate(
        {
            "trip_style_planning": {
                "substep": "tradeoffs",
                "selected_primary_direction": "culture_led",
                "selected_accent": "local",
                "selection_status": "selected",
                "selected_pace": "full",
                "pace_status": "completed",
            },
            "stay_planning": {
                "selected_hotel_id": "hotel_gion_house",
                "selected_hotel_name": "Gion House Hotel",
                "selected_stay_direction": "Central base for Kyoto",
            },
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_tradeoffs",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="trip_style",
    )

    axes = {
        card.axis for card in conversation.trip_style_planning.recommended_tradeoff_cards
    }
    assert "must_sees_vs_wandering" in axes
    assert "convenience_vs_atmosphere" in axes
    assert "early_starts_vs_evening_energy" in axes or "polished_vs_hidden_gems" in axes
    assert len(axes) == 3


def test_trip_style_tradeoff_confirmation_completes_branch() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(to_location="Kyoto")
    current = TripConversationState.model_validate(
        {
            "trip_style_planning": {
                "substep": "tradeoffs",
                "selected_primary_direction": "culture_led",
                "selection_status": "selected",
                "selected_pace": "balanced",
                "pace_status": "completed",
                "recommended_tradeoff_cards": [],
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_trip_style_tradeoff_updates=[
                RequestedTripStyleTradeoffUpdate(
                    action="set_tradeoff",
                    axis="must_sees_vs_wandering",
                    value="must_sees",
                ),
                RequestedTripStyleTradeoffUpdate(action="confirm"),
            ]
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_tradeoff_confirm",
        user_message="Prioritize must-sees and lock these in.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="trip_style",
    )

    assert conversation.trip_style_planning.substep == "completed"
    assert conversation.trip_style_planning.selection_status == "completed"
    assert conversation.trip_style_planning.tradeoff_status == "completed"
    assert any(
        decision.axis == "must_sees_vs_wandering"
        and decision.selected_value == "must_sees"
        for decision in conversation.trip_style_planning.selected_tradeoffs
    )


def test_trip_style_tradeoffs_change_activity_ranking() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 24, tzinfo=timezone.utc).date(),
        selected_modules={
            "flights": False,
            "weather": True,
            "activities": True,
            "hotels": False,
        },
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_iconic_temple",
                title="Iconic heritage temple morning",
                location_label="Higashiyama, Kyoto",
                category="entertainment.museum",
            ),
            ActivityDetail(
                id="activity_local_walk",
                title="Local neighborhood market walk",
                location_label="Kyoto neighborhood lanes",
                category="commercial.marketplace",
            ),
        ]
    )

    def leading_candidate_for_tradeoff(value: str) -> str:
        current = TripConversationState.model_validate(
            {
                "trip_style_planning": {
                    "substep": "completed",
                    "selected_primary_direction": "balanced",
                    "selection_status": "completed",
                    "selected_pace": "balanced",
                    "pace_status": "completed",
                    "tradeoff_status": "completed",
                    "selected_tradeoffs": [
                        {
                            "axis": "must_sees_vs_wandering",
                            "selected_value": value,
                        }
                    ],
                }
            }
        )
        conversation = build_conversation_state(
            current=current,
            previous_configuration=configuration,
            next_configuration=configuration,
            llm_update=TripTurnUpdate(),
            module_outputs=module_outputs,
            assistant_response="",
            turn_id=f"turn_{value}",
            user_message="",
            now=now,
            planning_mode="advanced",
            planning_mode_status="selected",
            brief_confirmed=True,
            advanced_step="anchor_flow",
            advanced_anchor="activities",
        )
        return conversation.activity_planning.recommended_candidates[0].id

    assert leading_candidate_for_tradeoff("must_sees") == "activity_iconic_temple"
    assert leading_candidate_for_tradeoff("wandering") == "activity_local_walk"


def test_trip_style_pace_preserves_fixed_events_and_manual_activity_edits(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
        selected_modules={
            "flights": False,
            "weather": True,
            "activities": True,
            "hotels": False,
        },
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                location_label="Kyoto",
                category="catering.restaurant",
            ),
            ActivityDetail(
                id="activity_temple",
                title="Higashiyama temple circuit",
                location_label="Kyoto",
                category="entertainment.museum",
            ),
        ]
    )
    fixed_event_start = datetime(2027, 3, 22, 18, 0, tzinfo=timezone.utc)
    event_payload = {
        "id": "event_jazz",
        "title": "Kyoto Jazz Night",
        "location_label": "Kyoto",
        "start_at": fixed_event_start,
        "end_at": fixed_event_start.replace(hour=20),
    }
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [event_payload],
    )

    current = TripConversationState.model_validate(
        {
            "trip_style_planning": {
                "substep": "completed",
                "selected_primary_direction": "balanced",
                "selection_status": "completed",
                "selected_pace": "full",
                "pace_status": "completed",
            },
            "activity_planning": {
                "placement_preferences": [
                    {
                        "candidate_id": "activity_market",
                        "daypart": "morning",
                        "reserved": False,
                    }
                ]
            }
        }
    )
    full_plan = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_full",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    slowed_plan = build_conversation_state(
        current=full_plan,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_trip_style_pace_updates=[
                RequestedTripStylePaceUpdate(action="select_pace", pace="slow"),
                RequestedTripStylePaceUpdate(action="confirm"),
            ]
        ),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_slow",
        user_message="Slow it down.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        brief_confirmed=True,
        advanced_step="anchor_flow",
        advanced_anchor="trip_style",
    )

    fixed_event_blocks = [
        block
        for block in slowed_plan.activity_planning.timeline_blocks
        if block.candidate_id == "event_jazz"
    ]
    assert fixed_event_blocks
    assert fixed_event_blocks[0].fixed_time is True
    assert fixed_event_blocks[0].start_at == fixed_event_start
    manual_activity_blocks = [
        block
        for block in slowed_plan.activity_planning.timeline_blocks
        if block.candidate_id == "activity_market"
    ]
    assert manual_activity_blocks
    assert manual_activity_blocks[0].manual_override is True
    assert "activity_temple" in slowed_plan.activity_planning.unscheduled_candidate_ids


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


def test_timing_choice_board_appears_when_destination_has_no_timing() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(to_location="Lisbon"),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Lisbon sounds good.",
        turn_id="turn_1",
        user_message="Let's do Lisbon.",
        now=now,
    )

    board = conversation.suggestion_board

    assert board.mode == "timing_choice"
    assert board.details_form is not None
    assert board.details_form.to_location == "Lisbon"
    assert any(item.id == "timing" for item in board.need_details)
    assert any(item.id == "trip_length" for item in board.need_details)


def test_timing_choice_board_stays_when_trip_length_is_missing() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Lisbon",
            travel_window="early October",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Early October works.",
        turn_id="turn_1",
        user_message="Maybe Lisbon in early October.",
        now=now,
    )

    board = conversation.suggestion_board

    assert board.mode == "timing_choice"
    assert board.details_form is not None
    assert board.details_form.travel_window == "early October"
    assert any(item.id == "trip_length" for item in board.need_details)


def test_timing_placeholders_do_not_count_as_completed_timing() -> None:
    now = datetime.now(timezone.utc)
    llm_update = sanitize_timing_update(
        TripTurnUpdate(
            to_location="Athens",
            travel_window="late September",
            trip_length="length TBD",
            inferred_fields=["to_location", "travel_window", "trip_length"],
            field_confidences=[
                TripFieldConfidenceUpdate(field="to_location", confidence="medium"),
                TripFieldConfidenceUpdate(field="travel_window", confidence="medium"),
                TripFieldConfidenceUpdate(field="trip_length", confidence="medium"),
            ],
            field_sources=[
                TripFieldSourceUpdate(field="to_location", source="user_inferred"),
                TripFieldSourceUpdate(field="travel_window", source="user_inferred"),
                TripFieldSourceUpdate(field="trip_length", source="user_inferred"),
            ],
        )
    )
    next_configuration = merge_trip_configuration(TripConfiguration(), llm_update)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=next_configuration,
        llm_update=llm_update,
        module_outputs=TripModuleOutputs(),
        assistant_response="Athens in late September works.",
        turn_id="turn_1",
        user_message="Athens sounds right for late September; length TBD.",
        now=now,
    )

    assert next_configuration.trip_length is None
    assert "trip_length" not in llm_update.inferred_fields
    assert conversation.suggestion_board.mode == "timing_choice"
    assert any(
        item.id == "trip_length"
        for item in conversation.suggestion_board.need_details
    )


def test_timing_choice_board_skips_when_timing_is_understood() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Lisbon",
            travel_window="early October",
            trip_length="long weekend",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Early October for a long weekend works.",
        turn_id="turn_1",
        user_message="Lisbon in early October for a long weekend.",
        now=now,
    )

    assert conversation.suggestion_board.mode != "timing_choice"


def test_timing_decision_cards_clear_after_timing_is_understood() -> None:
    now = datetime.now(timezone.utc)
    previous_conversation = TripConversationState(
        decision_cards=[
            PlannerDecisionCard(
                title="Choose the timing shape for Lisbon",
                description="A rough travel window is the next useful choice.",
                options=[
                    "Spring city break",
                    "Early summer escape",
                    "Autumn weekend",
                    "I'm flexible",
                ],
            ),
            PlannerDecisionCard(
                title="Choose the feel for Lisbon",
                description="These are the strongest trip directions to decide between before I start shaping the itinerary.",
                options=[
                    "Food-led neighbourhood weekend",
                    "Classic highlights city break",
                ],
            ),
        ]
    )
    conversation = build_conversation_state(
        current=previous_conversation,
        previous_configuration=TripConfiguration(
            to_location="Lisbon",
            trip_length="long weekend",
        ),
        next_configuration=TripConfiguration(
            to_location="Lisbon",
            travel_window="around June 15",
            trip_length="long weekend",
        ),
        llm_update=TripTurnUpdate(travel_window="around June 15"),
        module_outputs=TripModuleOutputs(),
        assistant_response="Around June 15 works.",
        turn_id="turn_2",
        user_message="around june 15th please.",
        now=now,
    )

    decision_titles = [card.title for card in conversation.decision_cards]

    assert conversation.suggestion_board.mode == "details_collection"
    assert conversation.suggestion_board.title == "Build the trip brief"
    assert any(item.id == "route" for item in conversation.suggestion_board.need_details)
    assert "Choose the timing shape for Lisbon" not in decision_titles


def test_timing_choice_board_skips_when_exact_dates_are_known() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Lisbon",
            start_date=date(2027, 6, 3),
            end_date=date(2027, 6, 8),
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="June dates are set.",
        turn_id="turn_1",
        user_message="Lisbon June 3 to June 8, 2027.",
        now=now,
    )

    assert conversation.suggestion_board.mode != "timing_choice"


def test_advanced_intake_does_not_use_timing_choice_board() -> None:
    now = datetime.now(timezone.utc)
    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(to_location="Kyoto"),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="Advanced planning is selected.",
        turn_id="turn_1",
        user_message="Use advanced planning.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="intake",
    )

    assert conversation.suggestion_board.mode == "details_collection"


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

    assert "working direction" in response.lower()
    assert "next choice" in response.lower()
    assert "choose the feel for lisbon" in response.lower()


def test_details_collection_response_frames_next_gap_without_repetitive_checklist() -> None:
    configuration = TripConfiguration(
        to_location="Seville, Spain",
        travel_window="late September",
        trip_length="4 nights",
        weather_preference="warm",
        selected_modules={
            "flights": True,
            "weather": True,
            "activities": True,
            "hotels": True,
        },
    )
    conversation = TripConversationState.model_validate(
        {
            "suggestion_board": {
                "mode": "details_collection",
                "title": "Build the trip brief",
                "suggested_step": "route",
                "have_details": [
                    {
                        "id": "timing",
                        "label": "Timing",
                        "status": "known",
                        "value": "late September",
                    },
                    {
                        "id": "trip_length",
                        "label": "Trip length",
                        "status": "known",
                        "value": "4 nights",
                    },
                    {
                        "id": "weather",
                        "label": "Weather preference",
                        "status": "known",
                        "value": "warm",
                    },
                    {
                        "id": "modules",
                        "label": "Trip modules",
                        "status": "known",
                        "value": "flights, weather, activities, hotels",
                    },
                ],
                "need_details": [
                    {"id": "route", "label": "Route", "status": "needed"},
                    {"id": "travellers", "label": "Travellers", "status": "needed"},
                    {"id": "trip_style", "label": "Trip style", "status": "needed"},
                    {"id": "budget", "label": "Budget", "status": "needed"},
                ],
            },
        }
    )

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
    normalized_response = response.lower()

    assert "seville, spain" in normalized_response
    assert "late september" in normalized_response
    assert "4 nights" in normalized_response
    assert "warm weather" in normalized_response
    assert "full trip scope" in normalized_response
    assert "departure point" in normalized_response
    assert "brief on the right" in normalized_response
    assert "travellers, trip style, and budget" in normalized_response
    assert "here's what i have so far" not in normalized_response
    assert "to move this forward" not in normalized_response
    assert "tell me this in chat" not in normalized_response
    assert "right-hand checklist" not in normalized_response


def test_details_collection_response_prefers_clean_llm_copy() -> None:
    conversation = TripConversationState.model_validate(
        {
            "suggestion_board": {
                "mode": "details_collection",
                "suggested_step": "travellers",
                "need_details": [
                    {"id": "travellers", "label": "Travellers", "status": "needed"},
                ],
            },
        }
    )
    llm_copy = (
        "Seville in late September for 4 nights is taking shape. "
        "The next useful detail is who is travelling. "
        "You can type it here or use the brief on the right."
    )

    response = build_assistant_response(
        configuration=TripConfiguration(
            to_location="Seville",
            travel_window="late September",
            trip_length="4 nights",
        ),
        conversation=conversation,
        llm_update=TripTurnUpdate(assistant_response=llm_copy),
        brief_confirmed=False,
        fallback_text=llm_copy,
        profile_context={},
        board_action=None,
        confirmation_status="unconfirmed",
        finalized_via=None,
    )

    assert response == llm_copy


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


def test_completed_activities_response_can_carry_personalized_llm_copy() -> None:
    conversation = TripConversationState.model_validate(
        {
            "planning_mode": "advanced",
            "advanced_step": "anchor_flow",
            "advanced_anchor": "activities",
            "activity_planning": {
                "schedule_status": "ready",
                "completion_status": "completed",
                "completion_summary": "Kyoto Jazz Night is now acting as a real timed anchor, and the activities plan has enough structure to move on.",
                "completion_anchor_ids": ["ticketmaster_kyoto_jazz"],
            },
        }
    )

    response = build_assistant_response(
        configuration=TripConfiguration(
            to_location="Kyoto",
            selected_modules={
                "flights": True,
                "weather": True,
                "activities": True,
                "hotels": True,
            },
        ),
        conversation=conversation,
        llm_update=TripTurnUpdate(),
        brief_confirmed=True,
        fallback_text="That jazz-led version already feels like the trip's center of gravity.",
        profile_context={},
        board_action=None,
        confirmation_status="unconfirmed",
        finalized_via=None,
    )

    assert "kyoto jazz night" in response.lower()
    assert "center of gravity" in response.lower()
    assert "remaining planning choices" in response.lower()


def test_activity_change_response_mentions_top_proactive_conflict() -> None:
    conversation = TripConversationState.model_validate(
        {
            "planning_mode": "advanced",
            "advanced_step": "anchor_flow",
            "advanced_anchor": "activities",
            "trip_style_planning": {"selected_pace": "slow"},
            "activity_planning": {
                "schedule_status": "ready",
                "completion_status": "completed",
                "completion_summary": "The activities plan is drafted.",
                "day_plans": [
                    {
                        "id": "day_1",
                        "day_index": 1,
                        "day_label": "Day 1",
                        "blocks": [
                            {"id": "b1", "type": "activity", "title": "Temple", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b2", "type": "activity", "title": "Market", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b3", "type": "event", "title": "Dinner", "day_index": 1, "day_label": "Day 1"},
                        ],
                    }
                ],
            },
        }
    )
    conversation.planner_conflicts = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=conversation,
    )

    response = build_assistant_response(
        configuration=TripConfiguration(
            to_location="Kyoto",
            selected_modules={"activities": True},
        ),
        conversation=conversation,
        llm_update=TripTurnUpdate(),
        brief_confirmed=True,
        fallback_text=None,
        profile_context={},
        board_action={
            "action_id": "action_rebuild",
            "type": "rebuild_activity_day_plan",
        },
        confirmation_status="unconfirmed",
        finalized_via=None,
    )

    assert "worth resolving" in response.lower() or "resolve first" in response.lower()
    assert "recommended repair" in response.lower()
    assert "why it matters" in response.lower()


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


def test_destination_suggestions_use_backend_stable_images(monkeypatch) -> None:
    destination_images._resolve_wikimedia_destination_image.cache_clear()
    destination_images._search_wikipedia_titles.cache_clear()
    monkeypatch.setattr(
        destination_images,
        "_fetch_wikipedia_summary_image",
        lambda title: None,
    )
    monkeypatch.setattr(
        destination_images,
        "_search_wikipedia_titles",
        lambda query: (),
    )
    try:
        board = build_suggestion_board_state(
            current=TripConversationState(),
            configuration=TripConfiguration(),
            phase="opening",
            llm_update=TripTurnUpdate(
                destination_suggestions=[
                    DestinationSuggestionCandidate(
                        id="dest_lisbon",
                        destination_name="Lisbon",
                        country_or_region="Portugal",
                        image_url="https://source.unsplash.com/1200x900/?Lisbon+travel",
                        short_reason="Walkable food neighborhoods and mild weather.",
                        practicality_label="Short direct-flight fit",
                    ),
                ]
            ),
            resolved_location_context=None,
            board_action={},
            brief_confirmed=False,
        )
    finally:
        destination_images._resolve_wikimedia_destination_image.cache_clear()

    assert board.mode == "destination_suggestions"
    assert board.cards[0].image_url.startswith("https://images.unsplash.com/")
    assert "source.unsplash.com" not in board.cards[0].image_url


def test_destination_suggestions_use_wikimedia_for_uncurated_asian_destinations(
    monkeypatch,
) -> None:
    def fake_fetch(title: str) -> str | None:
        if title == "Bali":
            return "https://upload.wikimedia.org/wikipedia/commons/0/0a/Bali_Rice_Terrace.jpg"
        return None

    destination_images._resolve_wikimedia_destination_image.cache_clear()
    destination_images._search_wikipedia_titles.cache_clear()
    monkeypatch.setattr(
        destination_images,
        "_search_wikipedia_titles",
        lambda query: (),
    )
    monkeypatch.setattr(
        destination_images,
        "_fetch_wikipedia_summary_image",
        fake_fetch,
    )
    try:
        board = build_suggestion_board_state(
            current=TripConversationState(),
            configuration=TripConfiguration(),
            phase="opening",
            llm_update=TripTurnUpdate(
                destination_suggestions=[
                    DestinationSuggestionCandidate(
                        id="dest_bali",
                        destination_name="Bali",
                        country_or_region="Indonesia",
                        image_url=None,
                        short_reason="Warm weather, food, and slower days.",
                        practicality_label="Long-haul beach and culture option",
                    ),
                ]
            ),
            resolved_location_context=None,
            board_action={},
            brief_confirmed=False,
        )
    finally:
        destination_images._resolve_wikimedia_destination_image.cache_clear()

    assert board.mode == "destination_suggestions"
    assert board.cards[0].image_url.startswith("https://upload.wikimedia.org/")
    assert "Bali_Rice_Terrace" in board.cards[0].image_url


def test_destination_suggestions_resolve_parenthetical_destination_names(
    monkeypatch,
) -> None:
    destination_images._resolve_wikimedia_destination_image.cache_clear()
    destination_images._search_wikipedia_titles.cache_clear()
    monkeypatch.setattr(
        destination_images,
        "_search_wikipedia_titles",
        lambda query: (),
    )
    monkeypatch.setattr(
        destination_images,
        "_fetch_wikipedia_summary_image",
        lambda title: "https://upload.wikimedia.org/wikipedia/commons/4/4d/Visakhapatnam_beach_road.jpg"
        if title == "Visakhapatnam"
        else None,
    )
    try:
        board = build_suggestion_board_state(
            current=TripConversationState(),
            configuration=TripConfiguration(),
            phase="opening",
            llm_update=TripTurnUpdate(
                destination_suggestions=[
                    DestinationSuggestionCandidate(
                        id="dest_vizag",
                        destination_name="Visakhapatnam (Vizag)",
                        country_or_region="India",
                        image_url=None,
                        short_reason="Coastal, warm, and easier-paced.",
                        practicality_label="Relaxed coast fit",
                    ),
                ]
            ),
            resolved_location_context=None,
            board_action={},
            brief_confirmed=False,
        )
    finally:
        destination_images._resolve_wikimedia_destination_image.cache_clear()

    assert board.mode == "destination_suggestions"
    assert "Visakhapatnam_beach_road" in board.cards[0].image_url


def test_destination_suggestions_reject_unconfigured_image_hosts(monkeypatch) -> None:
    destination_images._resolve_wikimedia_destination_image.cache_clear()
    destination_images._search_wikipedia_titles.cache_clear()
    monkeypatch.setattr(
        destination_images,
        "_fetch_wikipedia_summary_image",
        lambda title: None,
    )
    monkeypatch.setattr(
        destination_images,
        "_search_wikipedia_titles",
        lambda query: (),
    )
    board = build_suggestion_board_state(
        current=TripConversationState(),
        configuration=TripConfiguration(),
        phase="opening",
        llm_update=TripTurnUpdate(
            destination_suggestions=[
                DestinationSuggestionCandidate(
                    id="dest_zadar",
                    destination_name="Zadar",
                    country_or_region="Croatia",
                    image_url="https://example.com/zadar.jpg",
                    short_reason="Coastal old-town energy with a slower pace.",
                    practicality_label="Good shoulder-season option",
                ),
            ]
        ),
        resolved_location_context=None,
        board_action={},
        brief_confirmed=False,
    )
    destination_images._resolve_wikimedia_destination_image.cache_clear()

    assert board.mode == "destination_suggestions"
    assert board.cards[0].image_url.startswith("https://images.unsplash.com/")
    assert "example.com" not in board.cards[0].image_url


def test_destination_suggestions_prefer_dynamic_wikimedia_over_provider_url(
    monkeypatch,
) -> None:
    destination_images._resolve_wikimedia_destination_image.cache_clear()
    destination_images._search_wikipedia_titles.cache_clear()
    monkeypatch.setattr(
        destination_images,
        "_fetch_wikipedia_summary_image",
        lambda title: "https://upload.wikimedia.org/wikipedia/commons/3/3a/Mumbai_03-2016_30_Gateway_of_India.jpg"
        if title == "Mumbai"
        else None,
    )
    monkeypatch.setattr(
        destination_images,
        "_search_wikipedia_titles",
        lambda query: (),
    )
    try:
        board = build_suggestion_board_state(
            current=TripConversationState(),
            configuration=TripConfiguration(),
            phase="opening",
            llm_update=TripTurnUpdate(
                destination_suggestions=[
                    DestinationSuggestionCandidate(
                        id="dest_mumbai",
                        destination_name="Mumbai",
                        country_or_region="India",
                        image_url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/28/random-hotel.jpg",
                        short_reason="Warm, vivid, and food-led.",
                        practicality_label="Vibrant city break",
                    ),
                ]
            ),
            resolved_location_context=None,
            board_action={},
            brief_confirmed=False,
        )
    finally:
        destination_images._resolve_wikimedia_destination_image.cache_clear()

    assert board.mode == "destination_suggestions"
    assert "Gateway_of_India" in board.cards[0].image_url
    assert "tripadvisor" not in board.cards[0].image_url


def test_destination_suggestions_use_dynamic_wikimedia_before_generic_fallback(
    monkeypatch,
) -> None:
    destination_images._resolve_wikimedia_destination_image.cache_clear()
    destination_images._search_wikipedia_titles.cache_clear()
    monkeypatch.setattr(
        destination_images,
        "_fetch_wikipedia_summary_image",
        lambda title: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Plaza_de_Espa%C3%B1a_%28Sevilla%29_-_01.jpg/3840px-Plaza_de_Espa%C3%B1a_%28Sevilla%29_-_01.jpg"
        if title == "Seville"
        else None,
    )
    monkeypatch.setattr(
        destination_images,
        "_search_wikipedia_titles",
        lambda query: (),
    )
    try:
        board = build_suggestion_board_state(
            current=TripConversationState(),
            configuration=TripConfiguration(),
            phase="opening",
            llm_update=TripTurnUpdate(
                destination_suggestions=[
                    DestinationSuggestionCandidate(
                        id="dest_seville",
                        destination_name="Seville",
                        country_or_region="Spain",
                        image_url=None,
                        short_reason="Sunny, atmospheric, and compact.",
                        practicality_label="Best atmosphere fit",
                    ),
                ]
            ),
            resolved_location_context=None,
            board_action={},
            brief_confirmed=False,
        )
    finally:
        destination_images._resolve_wikimedia_destination_image.cache_clear()

    assert board.mode == "destination_suggestions"
    assert "Plaza_de_Espa" in board.cards[0].image_url
    assert "photo-1562883676-8c7feb1c4d73" not in board.cards[0].image_url


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


def test_activity_workspace_board_action_updates_disposition(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Music | Jazz | Blue Note Kyoto, Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "price_text": "GBP 35-85",
                "status_text": "On Sale",
                "start_at": datetime(2027, 3, 24, 19, 30, tzinfo=timezone.utc),
                "end_at": None,
            }
        ],
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
            activity_styles=["food", "culture"],
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            activities=[
                {
                    "id": "activity_walk",
                    "title": "Gion evening walk",
                    "category": "tourism.sights",
                    "time_label": "Evening",
                    "notes": ["Gion, Kyoto"],
                }
            ]
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_activity_essential",
            "type": "set_activity_candidate_disposition",
            "activity_candidate_id": "activity_walk",
            "activity_candidate_title": "Gion evening walk",
            "activity_candidate_disposition": "essential",
        },
    )

    candidate = next(
        item
        for item in conversation.activity_planning.recommended_candidates
        if item.id == "activity_walk"
    )
    event_candidate = next(
        item
        for item in conversation.activity_planning.recommended_candidates
        if item.kind == "event"
    )

    assert conversation.activity_planning.essential_ids == ["activity_walk"]
    assert candidate.disposition == "essential"
    assert event_candidate.venue_name == "Blue Note Kyoto"
    assert event_candidate.price_text == "GBP 35-85"
    assert conversation.activity_planning.workspace_touched is True
    assert conversation.activity_planning.completion_status == "in_progress"
    assert conversation.suggestion_board.mode == "advanced_activities_workspace"


def test_activity_workspace_chat_decision_ignores_ambiguous_titles(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
        ),
        llm_update=TripTurnUpdate(
            requested_activity_decisions=[
                RequestedActivityDecision(
                    candidate_title="Temple Walk",
                    disposition="pass",
                )
            ]
        ),
        module_outputs=TripModuleOutputs(
            activities=[
                {
                    "id": "activity_walk_1",
                    "title": "Temple Walk",
                    "notes": ["Higashiyama, Kyoto"],
                },
                {
                    "id": "activity_walk_2",
                    "title": "Temple Walk",
                    "notes": ["North Kyoto"],
                },
            ]
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="Pass on Temple Walk.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.activity_planning.passed_ids == []
    assert all(
        candidate.disposition == "maybe"
        for candidate in conversation.activity_planning.recommended_candidates
    )


def test_activity_workspace_disposition_changes_are_reversible(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )
    base_configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="late March",
        trip_length="5 nights",
    )
    base_outputs = TripModuleOutputs(
        activities=[
            {
                "id": "activity_market",
                "title": "Nishiki Market tasting walk",
                "notes": ["Nishiki Market, Kyoto"],
            }
        ]
    )

    first_pass = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=base_configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=base_outputs,
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_pass_market",
            "type": "set_activity_candidate_disposition",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_disposition": "pass",
        },
    )
    second_pass = build_conversation_state(
        current=first_pass,
        previous_configuration=base_configuration,
        next_configuration=base_configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=base_outputs,
        assistant_response="",
        turn_id="turn_2",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_maybe_market",
            "type": "set_activity_candidate_disposition",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_disposition": "maybe",
        },
    )

    assert first_pass.activity_planning.passed_ids == ["activity_market"]
    assert second_pass.activity_planning.passed_ids == []
    assert second_pass.activity_planning.maybe_ids == ["activity_market"]


def test_activity_workspace_board_and_chat_schedule_moves_converge(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 24, tzinfo=timezone.utc).date(),
        travel_window="late March",
        trip_length="2 nights",
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                category="commercial.marketplace",
                location_label="Nishiki Market, Kyoto",
                estimated_duration_minutes=90,
                time_label="Afternoon",
                notes=["Nishiki Market, Kyoto"],
            ),
            ActivityDetail(
                id="activity_walk",
                title="Gion evening walk",
                category="tourism.sights",
                location_label="Gion, Kyoto",
                estimated_duration_minutes=90,
                time_label="Evening",
                notes=["Gion, Kyoto"],
            ),
        ]
    )

    seeded = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_seed",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    board_version = build_conversation_state(
        current=seeded,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_board_move",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_move_market",
            "type": "move_activity_candidate_to_day",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_kind": "activity",
            "activity_target_day_index": 2,
        },
    )
    chat_version = build_conversation_state(
        current=seeded,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_activity_schedule_edits=[
                RequestedActivityScheduleEdit(
                    action="move_to_day",
                    candidate_title="Nishiki Market tasting walk",
                    candidate_kind="activity",
                    target_day_index=2,
                )
            ]
        ),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_chat_move",
        user_message="Move Nishiki Market to day 2.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    board_block = next(
        block
        for block in board_version.activity_planning.timeline_blocks
        if block.candidate_id == "activity_market"
    )
    chat_block = next(
        block
        for block in chat_version.activity_planning.timeline_blocks
        if block.candidate_id == "activity_market"
    )

    assert board_block.day_index == 2
    assert chat_block.day_index == 2
    assert board_block.daypart == chat_block.daypart
    assert board_version.activity_planning.placement_preferences[0].candidate_id == "activity_market"
    assert chat_version.activity_planning.placement_preferences[0].candidate_id == "activity_market"


def test_activity_workspace_can_reserve_and_restore_candidate(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        travel_window="late March",
        trip_length="1 night",
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                category="commercial.marketplace",
                location_label="Nishiki Market, Kyoto",
                estimated_duration_minutes=90,
                time_label="Afternoon",
                notes=["Nishiki Market, Kyoto"],
            )
        ]
    )
    seeded = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_seed",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )
    reserved = build_conversation_state(
        current=seeded,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_reserve",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_reserve_market",
            "type": "send_activity_candidate_to_reserve",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_kind": "activity",
        },
    )
    restored = build_conversation_state(
        current=reserved,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_restore",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_restore_market",
            "type": "restore_activity_candidate_from_reserve",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_kind": "activity",
        },
    )

    assert reserved.activity_planning.reserved_candidate_ids == ["activity_market"]
    assert "activity_market" in reserved.activity_planning.unscheduled_candidate_ids
    assert all(
        block.candidate_id != "activity_market"
        for block in reserved.activity_planning.timeline_blocks
    )
    assert restored.activity_planning.reserved_candidate_ids == []
    assert any(
        block.candidate_id == "activity_market"
        for block in restored.activity_planning.timeline_blocks
    )


def test_fixed_time_event_keeps_locked_slot_when_chat_requests_move(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": datetime(2027, 3, 23, 20, 0, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 24, tzinfo=timezone.utc).date(),
        travel_window="late March",
        trip_length="2 nights",
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_activity_schedule_edits=[
                RequestedActivityScheduleEdit(
                    action="move_to_day",
                    candidate_title="Kyoto Jazz Night",
                    candidate_kind="event",
                    target_day_index=2,
                )
            ]
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_fixed_event",
        user_message="Move Kyoto Jazz Night to day 2.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    event_block = next(
        block
        for block in conversation.activity_planning.timeline_blocks
        if block.candidate_id == "ticketmaster_kyoto_jazz"
    )

    assert event_block.day_index == 1
    assert event_block.fixed_time is True
    assert any(
        "fixed event time" in note.lower()
        for note in conversation.activity_planning.schedule_notes
    )


def test_advanced_flight_workspace_uses_provider_cards_and_board_actions() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 29, tzinfo=timezone.utc).date(),
        trip_length="6 nights",
    )
    configuration.travelers.adults = 2
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="tp_outbound",
                direction="outbound",
                carrier="Working Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                departure_time=datetime(2027, 3, 23, 9, 10, tzinfo=timezone.utc),
                arrival_time=datetime(2027, 3, 24, 7, 30, tzinfo=timezone.utc),
                duration_text="13h 20m",
            ),
            FlightDetail(
                id="tp_return",
                direction="return",
                carrier="Working Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                departure_time=datetime(2027, 3, 29, 12, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2027, 3, 29, 18, 5, tzinfo=timezone.utc),
                duration_text="14h 5m",
            ),
        ]
    )

    seeded = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_seed_flights",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )
    selected = build_conversation_state(
        current=seeded,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_select_flights",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
        board_action={
            "action_id": "action_select_outbound",
            "type": "select_outbound_flight",
            "flight_option_id": "tp_outbound",
        },
    )
    completed = build_conversation_state(
        current=selected,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_flight_updates=[
                RequestedFlightUpdate(
                    action="select_return",
                    flight_option_id="tp_return",
                ),
                RequestedFlightUpdate(action="confirm"),
            ]
        ),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_confirm_flights",
        user_message="Use that return and lock these flights in.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )

    assert seeded.flight_planning.results_status == "ready"
    assert seeded.flight_planning.outbound_options[0].source_kind == "provider"
    assert selected.flight_planning.selected_outbound_flight_id == "tp_outbound"
    assert completed.flight_planning.selected_return_flight_id == "tp_return"
    assert completed.flight_planning.selection_status == "completed"
    assert completed.suggestion_board.mode == "advanced_anchor_choice"
    assert "flight" in {
        card.id for card in completed.suggestion_board.advanced_anchor_cards if card.status == "completed"
    }


def test_advanced_flight_strategy_ranks_richer_inventory_details() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 29, tzinfo=timezone.utc).date(),
        trip_length="6 nights",
    )
    configuration.travelers.adults = 2
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="outbound_direct_expensive",
                direction="outbound",
                carrier="Direct Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                departure_time=datetime(2027, 3, 23, 8, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2027, 3, 23, 16, 0, tzinfo=timezone.utc),
                duration_text="12h",
                price_text="GBP 900",
                stop_count=0,
            ),
            FlightDetail(
                id="outbound_value",
                direction="outbound",
                carrier="Value Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                departure_time=datetime(2027, 3, 23, 7, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
                duration_text="16h",
                price_text="GBP 520",
                stop_count=1,
            ),
            FlightDetail(
                id="return_direct",
                direction="return",
                carrier="Direct Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                departure_time=datetime(2027, 3, 29, 14, 0, tzinfo=timezone.utc),
                duration_text="13h",
                price_text="GBP 900",
                stop_count=0,
            ),
            FlightDetail(
                id="return_value",
                direction="return",
                carrier="Value Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                departure_time=datetime(2027, 3, 29, 7, 0, tzinfo=timezone.utc),
                duration_text="17h",
                price_text="GBP 520",
                stop_count=1,
            ),
        ]
    )

    smooth = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_flight_updates=[
                RequestedFlightUpdate(action="select_strategy", strategy="smoothest_route"),
                RequestedFlightUpdate(action="confirm"),
            ]
        ),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_smooth_flights",
        user_message="Use the smoothest flights.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )
    value = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_flight_updates=[
                RequestedFlightUpdate(action="select_strategy", strategy="best_value"),
                RequestedFlightUpdate(action="confirm"),
            ]
        ),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_value_flights",
        user_message="Use the better value flights.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )

    assert smooth.flight_planning.selected_outbound_flight_id == "outbound_direct_expensive"
    assert smooth.flight_planning.selected_return_flight_id == "return_direct"
    assert value.flight_planning.selected_outbound_flight_id == "outbound_value"
    assert value.flight_planning.selected_return_flight_id == "return_value"
    assert value.flight_planning.selected_outbound_flight.price_text == "GBP 520"


def test_advanced_flight_workspace_blocks_missing_route_details() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 29, tzinfo=timezone.utc).date(),
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_blocked_flights",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )

    assert conversation.flight_planning.results_status == "blocked"
    assert "departure point" in conversation.flight_planning.missing_requirements
    assert "traveler count" in conversation.flight_planning.missing_requirements
    assert conversation.suggestion_board.mode == "advanced_flights_workspace"


def test_advanced_flight_workspace_uses_placeholders_when_inventory_is_empty() -> None:
    now = datetime.now(timezone.utc)
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 29, tzinfo=timezone.utc).date(),
    )
    configuration.travelers.adults = 2

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(
            requested_flight_updates=[
                RequestedFlightUpdate(action="keep_open"),
            ]
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_placeholder_flights",
        user_message="Keep flights flexible.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="flight",
    )

    assert conversation.flight_planning.results_status == "placeholder"
    assert conversation.flight_planning.outbound_options
    assert conversation.flight_planning.return_options
    assert all(
        option.source_kind == "placeholder"
        for option in [
            *conversation.flight_planning.outbound_options,
            *conversation.flight_planning.return_options,
        ]
    )
    assert conversation.flight_planning.selection_status == "kept_open"
    assert conversation.suggestion_board.mode == "advanced_anchor_choice"


def test_late_selected_arrival_softens_day_one_activity_schedule(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "event_late_jazz",
                "kind": "event",
                "title": "Late jazz set",
                "location_label": "Kyoto",
                "summary": "Fixed evening event",
                "start_at": datetime(2027, 3, 23, 20, 0, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 25, tzinfo=timezone.utc).date(),
    )
    configuration.travelers.adults = 2
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="late_outbound",
                direction="outbound",
                carrier="Working Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                departure_time=datetime(2027, 3, 23, 8, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2027, 3, 23, 22, 30, tzinfo=timezone.utc),
                duration_text="14h 30m",
            ),
            FlightDetail(
                id="normal_return",
                direction="return",
                carrier="Working Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                departure_time=datetime(2027, 3, 25, 18, 0, tzinfo=timezone.utc),
            ),
        ],
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                category="commercial.marketplace",
                time_label="Morning",
            ),
            ActivityDetail(
                id="activity_garden",
                title="Philosopher's Path garden walk",
                category="leisure.park",
                time_label="Afternoon",
            ),
        ],
    )
    current = TripConversationState.model_validate(
        {
            "planning_mode": "advanced",
            "planning_mode_status": "selected",
            "advanced_step": "anchor_flow",
            "advanced_anchor": "activities",
            "flight_planning": {
                "strategy_cards": [],
                "outbound_options": [],
                "return_options": [],
                "selected_strategy": "best_timing",
                "selected_outbound_flight_id": "late_outbound",
                "selected_return_flight_id": "normal_return",
                "selection_status": "completed",
                "results_status": "ready",
                "missing_requirements": [],
                "workspace_touched": True,
            },
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_late_arrival_activities",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    day_one_auto_blocks = [
        block
        for block in conversation.activity_planning.timeline_blocks
        if block.day_index == 1 and block.type == "activity" and not block.manual_override
    ]

    assert day_one_auto_blocks == []
    assert any(
        block.candidate_id == "event_late_jazz" and block.fixed_time
        for block in conversation.activity_planning.timeline_blocks
    )
    assert conversation.flight_planning.arrival_day_impact_summary is not None
    assert any(
        "very late arrival" in note.lower()
        for note in conversation.activity_planning.schedule_notes
    )
    assert any(
        "selected flight timing" in note.lower()
        for note in conversation.activity_planning.schedule_notes
    )


def test_early_selected_return_softens_final_day_activity_schedule(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(conversation_state, "enrich_events_from_ticketmaster", lambda configuration: [])
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 25, tzinfo=timezone.utc).date(),
    )
    configuration.travelers.adults = 2
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="normal_outbound",
                direction="outbound",
                carrier="Working Air",
                departure_airport="LHR",
                arrival_airport="KIX",
                departure_time=datetime(2027, 3, 23, 8, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2027, 3, 23, 10, 30, tzinfo=timezone.utc),
            ),
            FlightDetail(
                id="early_return",
                direction="return",
                carrier="Working Air",
                departure_airport="KIX",
                arrival_airport="LHR",
                departure_time=datetime(2027, 3, 25, 9, 0, tzinfo=timezone.utc),
            ),
        ],
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                category="commercial.marketplace",
                time_label="Morning",
            ),
            ActivityDetail(
                id="activity_garden",
                title="Philosopher's Path garden walk",
                category="leisure.park",
                time_label="Afternoon",
            ),
            ActivityDetail(
                id="activity_gallery",
                title="Small gallery wander",
                category="entertainment.culture",
                time_label="Afternoon",
            ),
        ],
    )
    current = TripConversationState.model_validate(
        {
            "planning_mode": "advanced",
            "planning_mode_status": "selected",
            "advanced_step": "anchor_flow",
            "advanced_anchor": "activities",
            "flight_planning": {
                "strategy_cards": [],
                "outbound_options": [],
                "return_options": [],
                "selected_strategy": "best_timing",
                "selected_outbound_flight_id": "normal_outbound",
                "selected_return_flight_id": "early_return",
                "selection_status": "completed",
                "results_status": "ready",
                "missing_requirements": [],
                "workspace_touched": True,
            },
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_early_return_activities",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    final_day_auto_blocks = [
        block
        for block in conversation.activity_planning.timeline_blocks
        if block.day_index == 3 and block.type == "activity" and not block.manual_override
    ]

    assert final_day_auto_blocks == []
    assert conversation.flight_planning.departure_day_impact_summary is not None
    assert any(
        "early return" in note.lower()
        for note in conversation.activity_planning.schedule_notes
    )


def test_keep_flexible_flights_do_not_constrain_activity_schedule(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(conversation_state, "enrich_events_from_ticketmaster", lambda configuration: [])
    configuration = TripConfiguration(
        from_location="London",
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 24, tzinfo=timezone.utc).date(),
    )
    configuration.travelers.adults = 2
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                category="commercial.marketplace",
                time_label="Morning",
            )
        ]
    )
    current = TripConversationState.model_validate(
        {
            "planning_mode": "advanced",
            "planning_mode_status": "selected",
            "advanced_step": "anchor_flow",
            "advanced_anchor": "activities",
            "flight_planning": {
                "strategy_cards": [],
                "outbound_options": [],
                "return_options": [],
                "selected_strategy": "keep_flexible",
                "selection_status": "kept_open",
                "results_status": "placeholder",
                "missing_requirements": [],
                "workspace_touched": True,
            },
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=configuration,
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_flexible_flights_activities",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert any(
        block.candidate_id == "activity_market" and block.day_index == 1
        for block in conversation.activity_planning.timeline_blocks
    )
    assert conversation.flight_planning.arrival_day_impact_summary is None
    assert not any("arrival" in note.lower() for note in conversation.activity_planning.schedule_notes)


def test_activity_workspace_builds_timed_day_plan_with_transfers(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Music | Jazz | Blue Note Kyoto, Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "price_text": "GBP 35-85",
                "status_text": "On Sale",
                "latitude": 35.0036,
                "longitude": 135.7694,
                "estimated_duration_minutes": 120,
                "start_at": datetime(2027, 3, 23, 19, 30, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 21, 30, tzinfo=timezone.utc),
            }
        ],
    )
    monkeypatch.setattr(
        conversation_state,
        "estimate_travel_duration_minutes",
        lambda **kwargs: MovementEstimate(
            minutes=24,
            distance_meters=1800,
            source="heuristic",
        ),
    )

    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
        travel_window="late March",
        trip_length="1 night",
    )
    module_outputs = TripModuleOutputs(
        activities=[
            ActivityDetail(
                id="activity_market",
                title="Nishiki Market tasting walk",
                category="catering.restaurant",
                latitude=35.0051,
                longitude=135.7649,
                location_label="Nishiki Market, Kyoto",
                source_label="Geoapify",
                estimated_duration_minutes=90,
                time_label="Afternoon",
                notes=["Nishiki Market, Kyoto"],
            ),
            ActivityDetail(
                id="activity_shrine",
                title="Fushimi Inari morning walk",
                category="tourism.sights",
                latitude=34.9671,
                longitude=135.7727,
                location_label="Fushimi Inari, Kyoto",
                source_label="Geoapify",
                estimated_duration_minutes=120,
                time_label="Morning",
                notes=["Fushimi Inari, Kyoto"],
            ),
        ]
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=module_outputs,
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.activity_planning.schedule_status == "ready"
    assert conversation.activity_planning.day_plans
    assert any(
        block.type == "event" for block in conversation.activity_planning.timeline_blocks
    )
    assert any(
        block.type == "transfer"
        for block in conversation.activity_planning.timeline_blocks
    )
    assert conversation.activity_planning.schedule_summary is not None
    assert "Kyoto Jazz Night" in conversation.activity_planning.schedule_summary
    assert conversation.stay_planning.compatibility_status == "fit"


def test_activity_workspace_can_put_selected_stay_under_review(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": datetime(2027, 3, 23, 20, 0, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )

    current = TripConversationState.model_validate(
        {
            "stay_planning": {
                "recommended_stay_options": [
                    {
                        "id": "stay_quiet_local",
                        "segment_id": "segment_primary",
                        "strategy_type": "single_base",
                        "title": "Quieter local base",
                        "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                        "area_label": "Calmer residential pockets",
                        "areas": [],
                        "best_for": ["Relaxed pacing and easier mornings"],
                        "tradeoffs": ["Daily travel can need more planning"],
                        "recommended": True,
                    }
                ],
                "selected_stay_option_id": "stay_quiet_local",
                "selected_stay_direction": "Quieter local base",
                "selection_status": "selected",
                "compatibility_status": "fit",
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.stay_planning.selection_status == "needs_review"
    assert conversation.stay_planning.compatibility_status == "conflicted"
    assert "Kyoto Jazz Night" in conversation.stay_planning.compatibility_notes[0]
    assert "later nights" in conversation.stay_planning.compatibility_notes[0]
    assert conversation.stay_planning.recommended_stay_options[0].id == "stay_food_forward"
    assert conversation.stay_planning.recommended_stay_options[0].recommended is True
    assert conversation.stay_planning.recommended_stay_options[0].badge == "Better fit now"


def test_activity_workspace_can_put_selected_hotel_under_review_without_straining_stay(
    monkeypatch,
) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )

    current = TripConversationState.model_validate(
        {
            "stay_planning": {
                "recommended_stay_options": [
                    {
                        "id": "stay_food_forward",
                        "segment_id": "segment_primary",
                        "strategy_type": "single_base",
                        "title": "Food-forward neighbourhood base",
                        "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                        "area_label": "Dining-led Kyoto pockets",
                        "areas": [],
                        "best_for": ["Food and evening structure"],
                        "tradeoffs": ["Less purely practical than a station-led base"],
                        "recommended": True,
                    }
                ],
                "selected_stay_option_id": "stay_food_forward",
                "selected_stay_direction": "Food-forward neighbourhood base",
                "selection_status": "selected",
                "compatibility_status": "fit",
                "selected_hotel_id": "hotel_station_stay",
                "selected_hotel_name": "Kyoto Station Stay",
                "hotel_selection_status": "selected",
                "hotel_compatibility_status": "fit",
                "selected_hotel_card": {
                    "id": "hotel_station_stay",
                    "hotel_name": "Kyoto Station Stay",
                    "area": "Central Kyoto Station",
                    "summary": "A practical station hotel.",
                    "why_it_fits": "Easy for transport-heavy movement.",
                },
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            hotels=[
                HotelStayDetail(
                    id="hotel_station_stay",
                    hotel_name="Kyoto Station Stay",
                    area="Central Kyoto Station",
                    notes=["Area fit: connected hub"],
                ),
                HotelStayDetail(
                    id="hotel_gion_house",
                    hotel_name="Gion House Hotel",
                    area="Gion",
                    notes=["Area fit: food and evening walking"],
                ),
            ],
            activities=[
                ActivityDetail(
                    id="activity_market",
                    title="Nishiki Market tasting walk",
                    category="catering.restaurant",
                    location_label="Nishiki Market, Kyoto",
                    time_label="Evening",
                )
            ]
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_market_essential",
            "type": "set_activity_candidate_disposition",
            "activity_candidate_id": "activity_market",
            "activity_candidate_title": "Nishiki Market tasting walk",
            "activity_candidate_disposition": "essential",
        },
    )

    assert conversation.stay_planning.selection_status == "selected"
    assert conversation.stay_planning.compatibility_status == "fit"
    assert conversation.stay_planning.hotel_selection_status == "needs_review"
    assert conversation.stay_planning.hotel_compatibility_status == "strained"
    assert "Kyoto Station Stay" in conversation.stay_planning.hotel_compatibility_notes[0]
    assert "Nishiki Market tasting walk" in conversation.stay_planning.hotel_compatibility_notes[0]
    assert conversation.stay_planning.recommended_hotels[0].hotel_name != "Kyoto Station Stay"
    assert conversation.stay_planning.recommended_hotels[0].recommended is True
    assert "re-ranked around Nishiki Market tasting walk" in (
        conversation.stay_planning.hotel_results_summary or ""
    )


def test_activity_workspace_keeps_stay_fit_when_signals_are_weak(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )

    current = TripConversationState.model_validate(
        {
            "stay_planning": {
                "selected_stay_option_id": "stay_quiet_local",
                "selected_stay_direction": "Quieter local base",
                "selection_status": "selected",
                "compatibility_status": "fit",
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            activities=[
                ActivityDetail(
                    id="activity_temple",
                    title="Temple garden walk",
                    category="tourism.sights",
                    location_label="Higashiyama, Kyoto",
                    time_label="Morning",
                )
            ]
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.stay_planning.selection_status == "selected"
    assert conversation.stay_planning.compatibility_status == "fit"
    assert conversation.stay_planning.compatibility_notes == []
    assert conversation.activity_planning.completion_status == "in_progress"
    assert conversation.activity_planning.completion_summary is None


def test_board_keep_current_stay_choice_resolves_review_without_dropping_activity_plan(
    monkeypatch,
) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": datetime(2027, 3, 23, 20, 0, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )

    conversation = build_conversation_state(
        current=TripConversationState.model_validate(
            {
                "stay_planning": {
                    "recommended_stay_options": [
                        {
                            "id": "stay_quiet_local",
                            "segment_id": "segment_primary",
                            "strategy_type": "single_base",
                            "title": "Quieter local base",
                            "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                            "area_label": "Calmer residential pockets",
                            "areas": [],
                            "best_for": ["Relaxed pacing and easier mornings"],
                            "tradeoffs": ["Daily travel can need more planning"],
                            "recommended": True,
                        }
                    ],
                    "selected_stay_option_id": "stay_quiet_local",
                    "selected_stay_direction": "Quieter local base",
                    "selection_status": "selected",
                    "compatibility_status": "fit",
                }
            }
        ),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
        board_action={
            "action_id": "action_keep_stay",
            "type": "keep_current_stay_choice",
        },
    )

    assert conversation.stay_planning.selection_status == "selected"
    assert conversation.stay_planning.compatibility_status == "fit"
    assert conversation.stay_planning.accepted_stay_review_signature is not None
    assert conversation.stay_planning.accepted_stay_review_summary is not None
    assert conversation.activity_planning.schedule_status == "ready"
    assert conversation.activity_planning.timeline_blocks
    assert conversation.activity_planning.completion_status == "completed"


def test_chat_keep_current_hotel_choice_resolves_review(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [],
    )

    conversation = build_conversation_state(
        current=TripConversationState.model_validate(
            {
                "stay_planning": {
                    "recommended_stay_options": [
                        {
                            "id": "stay_food_forward",
                            "segment_id": "segment_primary",
                            "strategy_type": "single_base",
                            "title": "Food-forward neighbourhood base",
                            "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                            "area_label": "Dining-led Kyoto pockets",
                            "areas": [],
                            "best_for": ["Food and evening structure"],
                            "tradeoffs": ["Less purely practical than a station-led base"],
                            "recommended": True,
                        }
                    ],
                    "selected_stay_option_id": "stay_food_forward",
                    "selected_stay_direction": "Food-forward neighbourhood base",
                    "selection_status": "selected",
                    "compatibility_status": "fit",
                    "selected_hotel_id": "hotel_station_stay",
                    "selected_hotel_name": "Kyoto Station Stay",
                    "hotel_selection_status": "selected",
                    "hotel_compatibility_status": "fit",
                    "selected_hotel_card": {
                        "id": "hotel_station_stay",
                        "hotel_name": "Kyoto Station Stay",
                        "area": "Central Kyoto Station",
                        "summary": "A practical station hotel.",
                        "why_it_fits": "Easy for transport-heavy movement.",
                    },
                }
            }
        ),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
        ),
        llm_update=TripTurnUpdate(
            requested_activity_decisions=[
                RequestedActivityDecision(
                    candidate_title="Nishiki Market tasting walk",
                    disposition="essential",
                )
            ],
            requested_review_resolutions=[RequestedReviewResolution(scope="hotel")],
        ),
        module_outputs=TripModuleOutputs(
            hotels=[
                HotelStayDetail(
                    id="hotel_station_stay",
                    hotel_name="Kyoto Station Stay",
                    area="Central Kyoto Station",
                    notes=["Area fit: connected hub"],
                ),
                HotelStayDetail(
                    id="hotel_gion_house",
                    hotel_name="Gion House Hotel",
                    area="Gion",
                    notes=["Area fit: food and evening walking"],
                ),
            ],
            activities=[
                ActivityDetail(
                    id="activity_market",
                    title="Nishiki Market tasting walk",
                    category="catering.restaurant",
                    location_label="Nishiki Market, Kyoto",
                    time_label="Evening",
                )
            ],
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="Keep the current hotel.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.stay_planning.hotel_selection_status == "selected"
    assert conversation.stay_planning.hotel_compatibility_status == "fit"
    assert conversation.stay_planning.accepted_hotel_review_signature is not None
    assert conversation.activity_planning.timeline_blocks


def test_chat_switch_to_named_stay_direction_can_clear_review(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": datetime(2027, 3, 23, 20, 0, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )

    current = TripConversationState.model_validate(
        {
            "stay_planning": {
                "recommended_stay_options": [
                    {
                        "id": "stay_quiet_local",
                        "segment_id": "segment_primary",
                        "strategy_type": "single_base",
                        "title": "Quieter local base",
                        "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                        "area_label": "Calmer residential pockets",
                        "areas": [],
                        "best_for": ["Relaxed pacing and easier mornings"],
                        "tradeoffs": ["Daily travel can need more planning"],
                        "recommended": False,
                    },
                    {
                        "id": "stay_food_forward",
                        "segment_id": "segment_primary",
                        "strategy_type": "single_base",
                        "title": "Food-forward neighbourhood base",
                        "summary": "Choose a neighbourhood-led base built around food and evening walks.",
                        "area_label": "Dining-led Kyoto pockets",
                        "areas": [],
                        "best_for": ["Food and evening structure"],
                        "tradeoffs": ["Less purely practical than a station-led base"],
                        "recommended": True,
                    },
                ],
                "selected_stay_option_id": "stay_quiet_local",
                "selected_stay_direction": "Quieter local base",
                "selection_status": "selected",
                "compatibility_status": "fit",
            }
        }
    )

    conversation = build_conversation_state(
        current=current,
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        llm_update=TripTurnUpdate(
            requested_stay_option_title="Food-forward neighbourhood base"
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_1",
        user_message="Switch to Food-forward neighbourhood base.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.stay_planning.selected_stay_option_id == "stay_food_forward"
    assert conversation.stay_planning.selection_status == "selected"
    assert conversation.stay_planning.compatibility_status == "fit"
    assert conversation.activity_planning.schedule_status == "ready"


def test_accepted_stay_review_does_not_reopen_until_evidence_changes(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Late jazz set in Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "start_at": datetime(2027, 3, 23, 20, 0, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 23, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )

    accepted = build_conversation_state(
        current=TripConversationState.model_validate(
            {
                "stay_planning": {
                    "recommended_stay_options": [
                        {
                            "id": "stay_quiet_local",
                            "segment_id": "segment_primary",
                            "strategy_type": "single_base",
                            "title": "Quieter local base",
                            "summary": "Choose a calmer local area so the trip starts and ends more gently.",
                            "area_label": "Calmer residential pockets",
                            "areas": [],
                            "best_for": ["Relaxed pacing and easier mornings"],
                            "tradeoffs": ["Daily travel can need more planning"],
                            "recommended": True,
                        }
                    ],
                    "selected_stay_option_id": "stay_quiet_local",
                    "selected_stay_direction": "Quieter local base",
                    "selection_status": "selected",
                    "compatibility_status": "fit",
                }
            }
        ),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        llm_update=TripTurnUpdate(
            requested_review_resolutions=[RequestedReviewResolution(scope="stay")]
        ),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_1",
        user_message="Keep this base anyway.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    unchanged = build_conversation_state(
        current=accepted,
        previous_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_2",
        user_message="Keep going.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert unchanged.stay_planning.selection_status == "selected"
    assert unchanged.stay_planning.compatibility_status == "fit"

    reopened = build_conversation_state(
        current=accepted,
        previous_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 23, tzinfo=timezone.utc).date(),
            travel_window="late March",
            trip_length="1 night",
        ),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            travel_window="late March",
            trip_length="5 nights",
            activity_styles=["nightlife"],
            custom_style="late-night bars and food alleys",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            activities=[
                ActivityDetail(id="activity_1", title="Late izakaya crawl"),
                ActivityDetail(id="activity_2", title="Cocktail bar hop"),
                ActivityDetail(id="activity_3", title="Night market tasting route"),
                ActivityDetail(id="activity_4", title="Evening jazz set"),
                ActivityDetail(id="activity_5", title="After-dark food alley walk"),
            ]
        ),
        assistant_response="",
        turn_id="turn_3",
        user_message="Now make it more nightlife-heavy.",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert reopened.stay_planning.selection_status == "needs_review"
    assert reopened.stay_planning.compatibility_status == "conflicted"
    assert reopened.stay_planning.accepted_stay_review_summary is not None


def test_event_candidate_can_lead_the_ranked_workspace(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda configuration: [
            {
                "id": "ticketmaster_kyoto_jazz",
                "kind": "event",
                "title": "Kyoto Jazz Night",
                "venue_name": "Blue Note Kyoto",
                "location_label": "Blue Note Kyoto, Kyoto",
                "summary": "Music | Jazz | Blue Note Kyoto, Kyoto",
                "source_label": "Ticketmaster",
                "source_url": "https://example.com/jazz",
                "status_text": "On Sale",
                "price_text": "GBP 35-85",
                "start_at": datetime(2027, 3, 24, 19, 30, tzinfo=timezone.utc),
                "end_at": datetime(2027, 3, 24, 22, 0, tzinfo=timezone.utc),
            }
        ],
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=TripConfiguration(
            to_location="Kyoto",
            start_date=datetime(2027, 3, 22, tzinfo=timezone.utc).date(),
            end_date=datetime(2027, 3, 27, tzinfo=timezone.utc).date(),
            activity_styles=["nightlife", "culture"],
            custom_style="live jazz and late dinners",
        ),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            activities=[
                {
                    "id": "activity_walk",
                    "title": "Temple walk",
                    "category": "tourism.sights",
                    "notes": ["Higashiyama, Kyoto"],
                }
            ]
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.activity_planning.visible_candidates[0].kind == "event"
    assert "Event-led around Kyoto Jazz Night" in (
        conversation.activity_planning.workspace_summary or ""
    )
    assert conversation.activity_planning.completion_status == "in_progress"
    assert conversation.activity_planning.completion_summary is None


def test_weather_pass_marks_unavailable_forecast_honestly(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda _configuration: [],
    )
    configuration = TripConfiguration(
        to_location="Lisbon",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 3),
        weather_preference="warm",
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            activities=[ActivityDetail(id="activity_1", title="Riverside garden walk")]
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.weather_planning.results_status == "unavailable"
    assert "not available" in (conversation.weather_planning.workspace_summary or "")
    assert conversation.weather_planning.activity_influence_notes == [
        "Using the warm weather preference softly until live forecast data appears."
    ]


def test_rainy_weather_nudges_indoor_activity_above_outdoor(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        conversation_state,
        "enrich_events_from_ticketmaster",
        lambda _configuration: [],
    )
    configuration = TripConfiguration(
        to_location="Lisbon",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 2),
    )

    conversation = build_conversation_state(
        current=TripConversationState(),
        previous_configuration=TripConfiguration(),
        next_configuration=configuration,
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(
            weather=[
                WeatherDetail(
                    id="weather_1",
                    day_label="Day 1",
                    forecast_date=date(2026, 5, 1),
                    summary="Rain likely during part of the day.",
                    condition_tags=["rain"],
                    temperature_band="mild",
                    weather_risk_level="medium",
                    high_c=18,
                    low_c=12,
                )
            ],
            activities=[
                ActivityDetail(
                    id="outdoor_garden",
                    title="Open-air garden viewpoint",
                    notes=["Outdoor garden walk with viewpoints."],
                ),
                ActivityDetail(
                    id="indoor_museum",
                    title="Museum and food market afternoon",
                    notes=["Covered museum galleries and indoor food market."],
                ),
            ],
        ),
        assistant_response="",
        turn_id="turn_1",
        user_message="",
        now=now,
        planning_mode="advanced",
        planning_mode_status="selected",
        advanced_step="anchor_flow",
        advanced_anchor="activities",
    )

    assert conversation.weather_planning.results_status == "ready"
    assert conversation.activity_planning.visible_candidates[0].id == "indoor_museum"
    assert any(
        "rain risk" in note.lower()
        for note in conversation.activity_planning.schedule_notes
    )


def test_advanced_review_state_summarizes_selected_and_flexible_planning() -> None:
    configuration = TripConfiguration.model_validate(
        {
            "to_location": "Kyoto",
            "selected_modules": {
                "flights": True,
                "hotels": True,
                "activities": True,
                "weather": True,
            },
        }
    )
    review = conversation_state.merge_advanced_review_planning_state(
        configuration=configuration,
        flight_planning=TripConversationState.model_validate(
            {
                "flight_planning": {
                    "selection_status": "completed",
                    "completion_summary": "Working flights arrive late on Day 1 and leave before lunch.",
                    "arrival_day_impact_summary": "Late arrival is softening Day 1.",
                    "timing_review_notes": ["Early return keeps the final morning light."],
                }
            }
        ).flight_planning,
        stay_planning=TripConversationState.model_validate(
            {
                "stay_planning": {
                    "selected_hotel_id": "hotel_gion",
                    "selected_hotel_name": "Gion House",
                    "hotel_selection_status": "selected",
                    "hotel_selection_rationale": "Gion House keeps evenings walkable.",
                    "hotel_compatibility_status": "strained",
                    "hotel_compatibility_notes": [
                        "The stay is a little far from the morning market route."
                    ],
                }
            }
        ).stay_planning,
        trip_style_planning=TripConversationState.model_validate(
            {
                "trip_style_planning": {
                    "substep": "completed",
                    "selection_status": "completed",
                    "selected_primary_direction": "culture_led",
                    "selected_pace": "slow",
                    "completion_summary": "Culture-led, slower days are the current trip character.",
                }
            }
        ).trip_style_planning,
        activity_planning=TripConversationState.model_validate(
            {
                "activity_planning": {
                    "completion_status": "completed",
                    "completion_summary": "Temples, markets, and one evening performance are planned.",
                    "reserved_candidate_ids": ["activity_extra_market"],
                    "schedule_notes": [
                        "Slow pace is keeping extra ideas in reserve instead of filling every daypart."
                    ],
                }
            }
        ).activity_planning,
        weather_planning=TripConversationState.model_validate(
            {
                "weather_planning": {
                    "results_status": "ready",
                    "workspace_summary": "Live forecast is available for the travel dates.",
                    "day_impact_summaries": ["Day 2 has rain risk, so indoor ideas are stronger."],
                    "activity_influence_notes": ["Rain risk is lifting museums and covered markets."],
                }
            }
        ).weather_planning,
    )

    sections = {section.id: section for section in review.section_cards}

    assert review.readiness_status == "needs_review"
    assert sections["flight"].title == "Working flights"
    assert sections["stay"].status == "needs_review"
    assert sections["trip_style"].summary.startswith("Culture-led")
    assert sections["activities"].notes[-1] == "1 idea saved for later."
    assert sections["weather"].revision_anchor is None
    assert any("Rain risk" in note for note in review.review_notes)


def test_advanced_review_uses_decision_memory_for_source_confidence_notes() -> None:
    base = TripConversationState.model_validate(
        {
            "flight_planning": {
                "selection_status": "completed",
                "completion_summary": "Evening outbound and morning return selected.",
            }
        }
    )
    review = conversation_state.merge_advanced_review_planning_state(
        configuration=TripConfiguration(
            to_location="Kyoto",
            selected_modules={
                "flights": True,
                "weather": False,
                "activities": False,
                "hotels": False,
            },
        ),
        stay_planning=base.stay_planning,
        trip_style_planning=base.trip_style_planning,
        activity_planning=base.activity_planning,
        flight_planning=base.flight_planning,
        weather_planning=base.weather_planning,
        decision_memory=[
            PlannerDecisionMemoryRecord(
                key="selected_flights",
                value_summary="Evening outbound and morning return selected.",
                source="assistant_inferred",
                confidence="low",
                status="confirmed",
                related_anchor="flight",
            )
        ],
    )

    sections = {section.id: section for section in review.section_cards}

    assert review.readiness_status == "needs_review"
    assert review.decision_signals[0].source_label == "Inferred from context"
    assert review.decision_signals[0].confidence_label == "Low confidence"
    assert sections["flight"].status == "needs_review"
    assert any("limited signal" in note for note in review.review_notes)


def test_planner_conflicts_detect_slow_pace_dense_activity_days() -> None:
    conversation = TripConversationState.model_validate(
        {
            "trip_style_planning": {
                "selected_pace": "slow",
            },
            "activity_planning": {
                "completion_status": "completed",
                "day_plans": [
                    {
                        "id": "day_1",
                        "day_index": 1,
                        "day_label": "Day 1",
                        "blocks": [
                            {"id": "b1", "type": "activity", "title": "Temple", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b2", "type": "activity", "title": "Market", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b3", "type": "event", "title": "Dinner", "day_index": 1, "day_label": "Day 1"},
                        ],
                    }
                ],
            },
        }
    )

    conflicts = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=conversation,
    )

    assert conflicts[0].category == "schedule_density"
    assert conflicts[0].revision_target == "activities"
    assert conflicts[0].status == "open"
    assert any(option.action == "safe_edit" for option in conflicts[0].resolution_options)
    assert conflicts[0].priority_label in {"worth_resolving", "resolve_first"}
    assert conflicts[0].recommended_repair
    assert "pace" in (conflicts[0].why_it_matters or "")
    assert "Recommended repair" in (conflicts[0].proactive_summary or "")
    assert "slow pace" in conflicts[0].summary


def test_planner_conflicts_detect_food_led_trip_without_food_anchor() -> None:
    conversation = TripConversationState.model_validate(
        {
            "trip_style_planning": {
                "selected_primary_direction": "food_led",
            },
            "activity_planning": {
                "completion_status": "completed",
                "visible_candidates": [
                    {
                        "id": "temple",
                        "title": "Temple morning",
                        "summary": "A heritage temple visit.",
                        "disposition": "essential",
                    }
                ],
            },
        }
    )

    conflicts = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=conversation,
    )

    assert conflicts[0].category == "style_pace"
    assert conflicts[0].revision_target == "activities"
    assert "food-led" in conflicts[0].summary


def test_advanced_review_includes_planner_conflict_notes() -> None:
    base = TripConversationState.model_validate(
        {
            "trip_style_planning": {
                "selected_pace": "slow",
                "substep": "completed",
            },
            "activity_planning": {
                "completion_status": "completed",
                "completion_summary": "A full first day is planned.",
                "day_plans": [
                    {
                        "id": "day_1",
                        "day_index": 1,
                        "day_label": "Day 1",
                        "blocks": [
                            {"id": "b1", "type": "activity", "title": "Temple", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b2", "type": "activity", "title": "Market", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b3", "type": "event", "title": "Dinner", "day_index": 1, "day_label": "Day 1"},
                        ],
                    }
                ],
            },
        }
    )
    conflicts = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=base,
    )

    review = conversation_state.merge_advanced_review_planning_state(
        configuration=TripConfiguration(
            to_location="Kyoto",
            selected_modules={
                "flights": False,
                "weather": False,
                "activities": True,
                "hotels": False,
            },
        ),
        stay_planning=base.stay_planning,
        trip_style_planning=base.trip_style_planning,
        activity_planning=base.activity_planning,
        flight_planning=base.flight_planning,
        weather_planning=base.weather_planning,
        planner_conflicts=conflicts,
    )

    assert review.readiness_status == "needs_review"
    assert any("slow pace" in note for note in review.review_notes)


def test_planner_conflict_resolution_status_persists_until_evidence_changes() -> None:
    conversation = TripConversationState.model_validate(
        {
            "trip_style_planning": {"selected_pace": "slow"},
            "activity_planning": {
                "completion_status": "completed",
                "day_plans": [
                    {
                        "id": "day_1",
                        "day_index": 1,
                        "day_label": "Day 1",
                        "blocks": [
                            {"id": "b1", "type": "activity", "title": "Temple", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b2", "type": "activity", "title": "Market", "day_index": 1, "day_label": "Day 1"},
                            {"id": "b3", "type": "event", "title": "Dinner", "day_index": 1, "day_label": "Day 1"},
                        ],
                    }
                ],
            },
        }
    )
    conflicts = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=conversation,
    )
    resolved = conflicts[0].model_copy(
        update={
            "status": "resolved",
            "resolution_summary": "Accepted the fuller first day.",
            "resolution_action": "resolve",
        }
    )

    persisted = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=conversation,
        previous_conflicts=[resolved],
    )

    assert persisted[0].status == "resolved"
    assert persisted[0].resolution_summary == "Accepted the fuller first day."

    conversation.memory.decision_memory = [
        PlannerDecisionMemoryRecord(
            key="conflict_resolution",
            value_summary="Accepted as tradeoff: Accepted the fuller first day.",
            source="board_action",
            confidence="high",
            status="confirmed",
            rationale="The traveler accepted this tradeoff.",
        )
    ]
    persisted_with_memory = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=conversation,
        previous_conflicts=[resolved],
    )

    assert persisted_with_memory[0].status == "resolved"
    assert "unless the plan changes materially" in (
        persisted_with_memory[0].resolution_summary or ""
    )

    changed = conversation.model_copy(deep=True)
    changed.activity_planning.day_plans[0].day_label = "Arrival day"
    changed.activity_planning.day_plans[0].blocks[0].day_label = "Arrival day"
    reopened = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=changed,
        previous_conflicts=[resolved],
    )

    assert reopened[0].status == "open"
    assert reopened[0].resolution_summary is None


def test_conflict_safe_edit_reserves_maybe_items_without_touching_essentials_or_fixed_events() -> None:
    base = TripConversationState.model_validate(
        {
            "planning_mode": "advanced",
            "advanced_step": "review",
            "trip_style_planning": {"selected_pace": "slow"},
            "activity_planning": {
                "completion_status": "completed",
                "essential_ids": ["temple"],
                "maybe_ids": ["market"],
                "visible_candidates": [
                    {"id": "temple", "title": "Temple", "disposition": "essential"},
                    {"id": "market", "title": "Market", "disposition": "maybe"},
                ],
                "day_plans": [
                    {
                        "id": "day_1",
                        "day_index": 1,
                        "day_label": "Day 1",
                        "blocks": [
                            {"id": "temple_block", "type": "activity", "candidate_id": "temple", "title": "Temple", "day_index": 1, "day_label": "Day 1"},
                            {"id": "market_block", "type": "activity", "candidate_id": "market", "title": "Market", "day_index": 1, "day_label": "Day 1"},
                            {"id": "dinner_block", "type": "event", "candidate_id": "dinner", "title": "Dinner", "day_index": 1, "day_label": "Day 1", "fixed_time": True},
                        ],
                    }
                ],
                "timeline_blocks": [
                    {"id": "temple_block", "type": "activity", "candidate_id": "temple", "title": "Temple", "day_index": 1, "day_label": "Day 1"},
                    {"id": "market_block", "type": "activity", "candidate_id": "market", "title": "Market", "day_index": 1, "day_label": "Day 1"},
                    {"id": "dinner_block", "type": "event", "candidate_id": "dinner", "title": "Dinner", "day_index": 1, "day_label": "Day 1", "fixed_time": True},
                ],
            },
        }
    )
    conflicts = conversation_state.build_planner_conflicts(
        configuration=TripConfiguration(to_location="Kyoto"),
        conversation=base,
    )
    base.planner_conflicts = conflicts

    updated = build_conversation_state(
        current=base,
        previous_configuration=TripConfiguration(to_location="Kyoto"),
        next_configuration=TripConfiguration(to_location="Kyoto"),
        llm_update=TripTurnUpdate(),
        module_outputs=TripModuleOutputs(),
        assistant_response="",
        turn_id="turn_conflict_safe_edit",
        user_message="",
        now=datetime(2026, 4, 24, tzinfo=timezone.utc),
        planning_mode="advanced",
        advanced_step="review",
        board_action={
            "action_id": "action_safe_edit",
            "type": "apply_planner_conflict_safe_edit",
            "planner_conflict_id": "conflict_slow_pace_dense_days",
            "planner_conflict_safe_edit": "reserve_maybe_activity_extras",
        },
    )

    assert "market" in updated.activity_planning.reserved_candidate_ids
    assert "temple" not in updated.activity_planning.reserved_candidate_ids
    assert any(block.id == "dinner_block" for block in updated.activity_planning.timeline_blocks)
    resolved = next(
        conflict
        for conflict in updated.planner_conflicts
        if conflict.id == "conflict_slow_pace_dense_days"
    )
    assert resolved.status == "resolved"
    assert "Resolved by moving lower-priority flexible activities" in (
        resolved.resolution_summary or ""
    )
    memory_record = next(
        record
        for record in updated.memory.decision_memory
        if record.key == "conflict_resolution"
    )
    assert memory_record.status == "confirmed"
    assert memory_record.source == "board_action"
    assert "Resolved by safe edit" in memory_record.value_summary
    assert "future advice" in (memory_record.rationale or "")
