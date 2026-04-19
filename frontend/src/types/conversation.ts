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

export type TripConversationMessageRequest = {
  message: string;
  profile_context?: PlannerProfileContext;
};

export type TripConversationMessageResponse = {
  trip_id: string;
  thread_id: string;
  draft_phase:
    | "collecting_requirements"
    | "planning"
    | "ready_for_review"
    | "finalized";
  message: string;
};
