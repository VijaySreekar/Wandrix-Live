import type {
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
    | "confirm_trip_brief";
  destination_name?: string | null;
  country_or_region?: string | null;
  suggestion_id?: string | null;
  from_location?: string | null;
  to_location?: string | null;
  selected_modules?: TripModuleSelection;
  travel_window?: string | null;
  trip_length?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  adults?: number | null;
  children?: number | null;
  activity_styles?: ActivityStyle[];
  budget_posture?: BudgetPosture | null;
  budget_gbp?: number | null;
};

export type TripConversationMessageRequest = {
  message: string;
  profile_context?: PlannerProfileContext;
  current_location_context?: PlannerLocationContext;
  board_action?: ConversationBoardAction;
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
