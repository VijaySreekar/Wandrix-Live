from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.trip_conversation import (
    CheckpointConversationMessage,
    ChatPlannerPhase,
    PlannerAdvancedAnchor,
    PlannerFlightStrategy,
    PlannerActivityCandidateKind,
    PlannerActivityDaypart,
    PlannerActivityDisposition,
    PlannerTripPace,
    PlannerTripStyleTradeoffAxis,
    PlannerTripStyleTradeoffChoice,
    PlannerTripDirectionAccent,
    PlannerTripDirectionPrimary,
    PlannerReviewResolutionScope,
    PlannerConflictSafeEdit,
)
from app.schemas.trip_planning import ActivityStyle, BudgetPosture, TripModuleSelection
from app.schemas.trip_draft import TripDraft


class PlannerProfileContext(BaseModel):
    display_name: str | None = None
    first_name: str | None = None
    home_airport: str | None = None
    preferred_currency: str | None = None
    home_city: str | None = None
    home_country: str | None = None
    trip_pace: str | None = None
    preferred_styles: list[str] = Field(default_factory=list)
    location_summary: str | None = None
    location_assist_enabled: bool | None = None


class PlannerLocationContext(BaseModel):
    source: str = Field(..., min_length=1, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    summary: str | None = Field(default=None, max_length=240)
    latitude: float | None = None
    longitude: float | None = None


class ConversationBoardAction(BaseModel):
    action_id: str = Field(..., min_length=1, max_length=80)
    type: Literal[
        "select_destination_suggestion",
        "own_choice",
        "confirm_trip_details",
        "confirm_trip_brief",
        "select_quick_plan",
        "select_advanced_plan",
        "select_advanced_anchor",
        "select_date_option",
        "pick_dates_for_me",
        "confirm_working_dates",
        "select_flight_strategy",
        "select_outbound_flight",
        "select_return_flight",
        "confirm_flight_selection",
        "keep_flights_open",
        "select_stay_option",
        "select_stay_hotel",
        "keep_current_stay_choice",
        "keep_current_hotel_choice",
        "set_activity_candidate_disposition",
        "rebuild_activity_day_plan",
        "move_activity_candidate_to_day",
        "move_activity_candidate_earlier",
        "move_activity_candidate_later",
        "pin_activity_candidate_daypart",
        "send_activity_candidate_to_reserve",
        "restore_activity_candidate_from_reserve",
        "select_trip_style_direction_primary",
        "select_trip_style_direction_accent",
        "clear_trip_style_direction_accent",
        "confirm_trip_style_direction",
        "keep_current_trip_style_direction",
        "select_trip_style_pace",
        "confirm_trip_style_pace",
        "keep_current_trip_style_pace",
        "set_trip_style_tradeoff",
        "confirm_trip_style_tradeoffs",
        "keep_current_trip_style_tradeoffs",
        "set_stay_hotel_filters",
        "set_stay_hotel_sort",
        "set_stay_hotel_page",
        "reset_stay_hotel_filters",
        "revise_advanced_review_section",
        "resolve_planner_conflict",
        "defer_planner_conflict",
        "apply_planner_conflict_safe_edit",
        "finalize_advanced_plan",
        "finalize_quick_plan",
        "reopen_plan",
    ]
    advanced_anchor: PlannerAdvancedAnchor | None = None
    destination_name: str | None = Field(default=None, max_length=120)
    country_or_region: str | None = Field(default=None, max_length=120)
    suggestion_id: str | None = Field(default=None, max_length=80)
    date_option_id: str | None = Field(default=None, max_length=80)
    flight_strategy: PlannerFlightStrategy | None = None
    flight_option_id: str | None = Field(default=None, max_length=120)
    stay_option_id: str | None = Field(default=None, max_length=80)
    stay_segment_id: str | None = Field(default=None, max_length=80)
    stay_hotel_id: str | None = Field(default=None, max_length=120)
    stay_hotel_name: str | None = Field(default=None, max_length=160)
    activity_candidate_id: str | None = Field(default=None, max_length=160)
    activity_candidate_title: str | None = Field(default=None, max_length=160)
    activity_candidate_kind: PlannerActivityCandidateKind | None = None
    activity_candidate_disposition: PlannerActivityDisposition | None = None
    activity_target_day_index: int | None = Field(default=None, ge=1, le=30)
    activity_target_daypart: PlannerActivityDaypart | None = None
    trip_style_direction_primary: PlannerTripDirectionPrimary | None = None
    trip_style_direction_accent: PlannerTripDirectionAccent | None = None
    trip_style_pace: PlannerTripPace | None = None
    trip_style_tradeoff_axis: PlannerTripStyleTradeoffAxis | None = None
    trip_style_tradeoff_value: PlannerTripStyleTradeoffChoice | None = None
    review_resolution_scope: PlannerReviewResolutionScope | None = None
    planner_conflict_id: str | None = Field(default=None, max_length=120)
    planner_conflict_safe_edit: PlannerConflictSafeEdit | None = None
    planner_conflict_resolution_summary: str | None = Field(default=None, max_length=280)
    stay_hotel_max_nightly_rate: float | None = Field(default=None, ge=0)
    stay_hotel_area_filter: str | None = Field(default=None, max_length=160)
    stay_hotel_style_filter: str | None = Field(default=None, max_length=40)
    stay_hotel_sort_order: str | None = Field(default=None, max_length=40)
    stay_hotel_page: int | None = Field(default=None, ge=1, le=99)
    from_location: str | None = Field(default=None, max_length=160)
    from_location_flexible: bool | None = None
    to_location: str | None = Field(default=None, max_length=160)
    selected_modules: TripModuleSelection | None = None
    travel_window: str | None = Field(default=None, max_length=120)
    trip_length: str | None = Field(default=None, max_length=120)
    weather_preference: str | None = Field(default=None, max_length=80)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    adults: int | None = Field(default=None, ge=0)
    children: int | None = Field(default=None, ge=0)
    travelers_flexible: bool | None = None
    activity_styles: list[ActivityStyle] = Field(default_factory=list)
    custom_style: str | None = Field(default=None, max_length=160)
    budget_posture: BudgetPosture | None = None
    budget_gbp: float | None = Field(default=None, gt=0)


class TripConversationMessageRequest(BaseModel):
    message: str = Field(default="", max_length=4000)
    profile_context: PlannerProfileContext | None = None
    current_location_context: PlannerLocationContext | None = None
    board_action: ConversationBoardAction | None = None

    @model_validator(mode="after")
    def validate_turn_has_message_or_board_action(self):
        if self.message.strip() or self.board_action is not None:
            return self
        raise ValueError("A conversation turn needs either a message or a board action.")


class OpeningTurnRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    profile_context: PlannerProfileContext | None = None
    current_location_context: PlannerLocationContext | None = None


class OpeningTurnResponse(BaseModel):
    should_start_trip: bool
    message: str = Field(..., min_length=1, max_length=4000)


class TripConversationMessageResponse(BaseModel):
    trip_id: str
    thread_id: str
    draft_phase: ChatPlannerPhase
    message: str
    trip_draft: TripDraft


class CheckpointConversationHistoryResponse(BaseModel):
    trip_id: str
    thread_id: str
    messages: list[CheckpointConversationMessage] = Field(default_factory=list)
