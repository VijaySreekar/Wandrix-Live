import type {
  PlannerAdvancedAnchor,
  PlannerActivityCandidateKind,
  PlannerActivityDaypart,
  PlannerActivityDisposition,
  PlannerFlightStrategy,
  PlannerTripPace,
  PlannerTripStyleTradeoffAxis,
  PlannerTripStyleTradeoffChoice,
  PlannerTripDirectionAccent,
  PlannerTripDirectionPrimary,
  PlannerReviewResolutionScope,
  ChatPlannerPhase,
  CheckpointConversationMessage,
} from "@/types/trip-conversation";
import type {
  ActivityStyle,
  BudgetPosture,
  TripModuleSelection,
} from "@/types/trip-draft";
import type { TripDraft } from "@/types/trip-draft";

export type PlannerProfileContext = {
  display_name?: string | null;
  first_name?: string | null;
  home_airport?: string | null;
  preferred_currency?: string | null;
  home_city?: string | null;
  home_country?: string | null;
  trip_pace?: string | null;
  preferred_styles?: string[];
  location_summary?: string | null;
  location_assist_enabled?: boolean | null;
};

export type PlannerLocationContext = {
  source: string;
  city?: string | null;
  region?: string | null;
  country?: string | null;
  summary?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

export type ConversationBoardAction = {
  action_id: string;
  type:
    | "select_destination_suggestion"
    | "own_choice"
    | "confirm_trip_details"
    | "confirm_trip_brief"
    | "select_quick_plan"
    | "select_advanced_plan"
    | "select_advanced_anchor"
    | "select_date_option"
    | "pick_dates_for_me"
    | "confirm_working_dates"
    | "select_flight_strategy"
    | "select_outbound_flight"
    | "select_return_flight"
    | "confirm_flight_selection"
    | "keep_flights_open"
    | "select_stay_option"
    | "select_stay_hotel"
    | "keep_current_stay_choice"
    | "keep_current_hotel_choice"
    | "set_activity_candidate_disposition"
    | "rebuild_activity_day_plan"
    | "move_activity_candidate_to_day"
    | "move_activity_candidate_earlier"
    | "move_activity_candidate_later"
    | "pin_activity_candidate_daypart"
    | "send_activity_candidate_to_reserve"
    | "restore_activity_candidate_from_reserve"
    | "select_trip_style_direction_primary"
    | "select_trip_style_direction_accent"
    | "clear_trip_style_direction_accent"
    | "confirm_trip_style_direction"
    | "keep_current_trip_style_direction"
    | "select_trip_style_pace"
    | "confirm_trip_style_pace"
    | "keep_current_trip_style_pace"
    | "set_trip_style_tradeoff"
    | "confirm_trip_style_tradeoffs"
    | "keep_current_trip_style_tradeoffs"
    | "set_stay_hotel_filters"
    | "set_stay_hotel_sort"
    | "set_stay_hotel_page"
    | "reset_stay_hotel_filters"
    | "revise_advanced_review_section"
    | "finalize_advanced_plan"
    | "finalize_quick_plan"
    | "reopen_plan";
  advanced_anchor?: PlannerAdvancedAnchor | null;
  destination_name?: string | null;
  country_or_region?: string | null;
  suggestion_id?: string | null;
  date_option_id?: string | null;
  flight_strategy?: PlannerFlightStrategy | null;
  flight_option_id?: string | null;
  stay_option_id?: string | null;
  stay_segment_id?: string | null;
  stay_hotel_id?: string | null;
  stay_hotel_name?: string | null;
  activity_candidate_id?: string | null;
  activity_candidate_title?: string | null;
  activity_candidate_kind?: PlannerActivityCandidateKind | null;
  activity_candidate_disposition?: PlannerActivityDisposition | null;
  activity_target_day_index?: number | null;
  activity_target_daypart?: PlannerActivityDaypart | null;
  trip_style_direction_primary?: PlannerTripDirectionPrimary | null;
  trip_style_direction_accent?: PlannerTripDirectionAccent | null;
  trip_style_pace?: PlannerTripPace | null;
  trip_style_tradeoff_axis?: PlannerTripStyleTradeoffAxis | null;
  trip_style_tradeoff_value?: PlannerTripStyleTradeoffChoice | null;
  review_resolution_scope?: PlannerReviewResolutionScope | null;
  stay_hotel_max_nightly_rate?: number | null;
  stay_hotel_area_filter?: string | null;
  stay_hotel_style_filter?: string | null;
  stay_hotel_sort_order?: string | null;
  stay_hotel_page?: number | null;
  from_location?: string | null;
  from_location_flexible?: boolean | null;
  to_location?: string | null;
  selected_modules?: TripModuleSelection;
  travel_window?: string | null;
  trip_length?: string | null;
  weather_preference?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  adults?: number | null;
  children?: number | null;
  travelers_flexible?: boolean | null;
  activity_styles?: ActivityStyle[];
  custom_style?: string | null;
  budget_posture?: BudgetPosture | null;
  budget_gbp?: number | null;
};

export type TripConversationMessageRequest = {
  message: string;
  profile_context?: PlannerProfileContext;
  current_location_context?: PlannerLocationContext;
  board_action?: ConversationBoardAction;
};

export type OpeningTurnRequest = {
  message: string;
  profile_context?: PlannerProfileContext;
  current_location_context?: PlannerLocationContext;
};

export type OpeningTurnResponse = {
  should_start_trip: boolean;
  message: string;
};

export type TripConversationMessageResponse = {
  trip_id: string;
  thread_id: string;
  draft_phase: ChatPlannerPhase;
  message: string;
  trip_draft: TripDraft;
};

export type CheckpointConversationHistoryResponse = {
  trip_id: string;
  thread_id: string;
  messages: CheckpointConversationMessage[];
};
