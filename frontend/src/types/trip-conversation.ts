export type ChatPlannerPhase =
  | "opening"
  | "collecting_requirements"
  | "shaping_trip"
  | "enriching_modules"
  | "reviewing"
  | "finalized";
export type PlannerConfirmationStatus = "unconfirmed" | "finalized";
export type PlannerFinalizedVia = "chat" | "board";
export type PlannerPlanningMode = "quick" | "advanced";
export type PlannerPlanningModeStatus =
  | "not_selected"
  | "selected"
  | "advanced_unavailable_fallback";
export type PlannerAdvancedStep =
  | "intake"
  | "resolve_dates"
  | "choose_anchor"
  | "anchor_flow"
  | "review";
export type PlannerAdvancedAnchor =
  | "flight"
  | "stay"
  | "trip_style"
  | "activities";
export type PlannerStaySelectionStatus =
  | "none"
  | "selected"
  | "needs_review";
export type PlannerStayCompatibilityStatus =
  | "fit"
  | "strained"
  | "conflicted";
export type PlannerHotelStyleTag =
  | "calm"
  | "central"
  | "design"
  | "luxury"
  | "food_access"
  | "practical"
  | "traditional"
  | "nightlife"
  | "walkable"
  | "value";
export type PlannerHotelSortOrder =
  | "best_fit"
  | "lowest_price"
  | "highest_price"
  | "best_area_fit";
export type PlannerHotelResultsStatus = "blocked" | "ready" | "empty";
export type PlannerDateResolutionStatus = "none" | "selected" | "confirmed";
export type PlannerStayStrategyType = "single_base" | "split_stay";
export type PlannerStayHotelSubstep =
  | "strategy_choice"
  | "hotel_shortlist"
  | "hotel_selected"
  | "hotel_review";
export type TripDetailsStepKey =
  | "modules"
  | "route"
  | "timing"
  | "travellers"
  | "vibe"
  | "budget";

export type TripFieldKey =
  | "from_location"
  | "from_location_flexible"
  | "to_location"
  | "start_date"
  | "end_date"
  | "travel_window"
  | "trip_length"
  | "weather_preference"
  | "budget_posture"
  | "budget_gbp"
  | "adults"
  | "children"
  | "travelers_flexible"
  | "activity_styles"
  | "custom_style"
  | "selected_modules";

export type ConversationFieldSource =
  | "user_explicit"
  | "user_inferred"
  | "profile_default"
  | "assistant_derived"
  | "board_action";
export type ConversationFieldConfidence = "low" | "medium" | "high";

export type ConversationOptionKind =
  | "destination"
  | "origin"
  | "timing_window"
  | "trip_length"
  | "activity_style"
  | "planning_module"
  | "budget_posture";

export type ConversationQuestionStatus = "open" | "answered" | "dismissed";
export type TripSuggestionBoardMode =
  | "idle"
  | "destination_suggestions"
  | "decision_cards"
  | "details_collection"
  | "planning_mode_choice"
  | "advanced_date_resolution"
  | "advanced_anchor_choice"
  | "advanced_next_step"
  | "advanced_stay_choice"
  | "advanced_stay_selected"
  | "advanced_stay_review"
  | "advanced_stay_hotel_choice"
  | "advanced_stay_hotel_selected"
  | "advanced_stay_hotel_review"
  | "helper";
export type DestinationSuggestionSelectionStatus =
  | "suggested"
  | "leading"
  | "confirmed";
export type PlannerChecklistStatus = "known" | "needed";
export type PlanningModeCardStatus = "available" | "in_development";
export type AdvancedAnchorCardStatus = "available" | "completed";
export type TripDetailsBoardActivityStyle =
  | "relaxed"
  | "adventure"
  | "luxury"
  | "family"
  | "culture"
  | "nightlife"
  | "romantic"
  | "food"
  | "outdoors";
export type TripDetailsBoardBudgetPosture =
  | "budget"
  | "mid_range"
  | "premium";
export type TripDetailsBoardModuleSelection = {
  flights: boolean;
  weather: boolean;
  activities: boolean;
  hotels: boolean;
};

export type PlannerDecisionCard = {
  title: string;
  description: string;
  options: string[];
};

export type DestinationSuggestionCard = {
  id: string;
  destination_name: string;
  country_or_region: string;
  image_url: string;
  short_reason: string;
  practicality_label: string;
  selection_status: DestinationSuggestionSelectionStatus;
};

export type PlanningModeChoiceCard = {
  id: PlannerPlanningMode;
  title: string;
  description: string;
  bullets: string[];
  status: PlanningModeCardStatus;
  badge?: string | null;
  cta_label?: string | null;
};

export type AdvancedAnchorChoiceCard = {
  id: PlannerAdvancedAnchor;
  title: string;
  description: string;
  bullets: string[];
  status: AdvancedAnchorCardStatus;
  recommended: boolean;
  badge?: string | null;
  cta_label?: string | null;
};

export type AdvancedDateOptionCard = {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  nights: number;
  reason: string;
  recommended: boolean;
  cta_label?: string | null;
};

export type AdvancedDateResolutionState = {
  source_timing_text?: string | null;
  source_trip_length_text?: string | null;
  recommended_date_options: AdvancedDateOptionCard[];
  selected_date_option_id?: string | null;
  selected_start_date?: string | null;
  selected_end_date?: string | null;
  selection_status: PlannerDateResolutionStatus;
  selection_rationale?: string | null;
  requires_confirmation: boolean;
};

export type AdvancedStayPlanningSegment = {
  id: string;
  title: string;
  destination_name?: string | null;
  summary?: string | null;
};

export type AdvancedStayOptionCard = {
  id: string;
  segment_id: string;
  strategy_type: PlannerStayStrategyType;
  title: string;
  summary: string;
  area_label?: string | null;
  areas: string[];
  best_for: string[];
  tradeoffs: string[];
  recommended: boolean;
  badge?: string | null;
  cta_label?: string | null;
};

export type AdvancedStayHotelOptionCard = {
  id: string;
  hotel_name: string;
  area?: string | null;
  image_url?: string | null;
  address?: string | null;
  source_url?: string | null;
  source_label?: string | null;
  summary: string;
  why_it_fits: string;
  tradeoffs: string[];
  style_tags: PlannerHotelStyleTag[];
  fit_score: number;
  outside_active_filters: boolean;
  price_signal?: string | null;
  nightly_rate_amount?: number | null;
  nightly_rate_currency?: string | null;
  nightly_tax_amount?: number | null;
  rate_provider_name?: string | null;
  rate_note?: string | null;
  check_in?: string | null;
  check_out?: string | null;
  recommended: boolean;
  cta_label?: string | null;
};

export type AdvancedStayHotelFilters = {
  max_nightly_rate?: number | null;
  area_filter?: string | null;
  style_filter?: PlannerHotelStyleTag | null;
};

export type AdvancedStayPlanningState = {
  active_segment_id?: string | null;
  segments: AdvancedStayPlanningSegment[];
  hotel_substep: PlannerStayHotelSubstep;
  recommended_stay_options: AdvancedStayOptionCard[];
  selected_stay_option_id?: string | null;
  selected_stay_direction?: string | null;
  selection_status: PlannerStaySelectionStatus;
  selection_rationale?: string | null;
  selection_assumptions: string[];
  compatibility_status: PlannerStayCompatibilityStatus;
  compatibility_notes: string[];
  recommended_hotels: AdvancedStayHotelOptionCard[];
  selected_hotel_id?: string | null;
  selected_hotel_name?: string | null;
  hotel_selection_status: PlannerStaySelectionStatus;
  hotel_selection_rationale?: string | null;
  hotel_selection_assumptions: string[];
  hotel_compatibility_status: PlannerStayCompatibilityStatus;
  hotel_compatibility_notes: string[];
  hotel_filters?: AdvancedStayHotelFilters;
  hotel_sort_order?: PlannerHotelSortOrder;
  hotel_results_status?: PlannerHotelResultsStatus;
  hotel_results_summary?: string | null;
  hotel_page?: number;
  hotel_page_size?: number;
  hotel_total_results?: number;
  hotel_total_pages?: number;
  available_hotel_areas?: string[];
  available_hotel_styles?: PlannerHotelStyleTag[];
  selected_hotel_card?: AdvancedStayHotelOptionCard | null;
};

export type PlannerChecklistItem = {
  id: string;
  label: string;
  status: PlannerChecklistStatus;
  value?: string | null;
};

export type TripDetailsCollectionFormState = {
  from_location?: string | null;
  from_location_flexible?: boolean | null;
  to_location?: string | null;
  selected_modules: TripDetailsBoardModuleSelection;
  travel_window?: string | null;
  trip_length?: string | null;
  weather_preference?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  adults?: number | null;
  children?: number | null;
  travelers_flexible?: boolean | null;
  activity_styles: TripDetailsBoardActivityStyle[];
  custom_style?: string | null;
  budget_posture?: TripDetailsBoardBudgetPosture | null;
  budget_gbp?: number | null;
};

export type TripSuggestionBoardState = {
  mode: TripSuggestionBoardMode;
  source_context?: string | null;
  title?: string | null;
  subtitle?: string | null;
  cards: DestinationSuggestionCard[];
  planning_mode_cards: PlanningModeChoiceCard[];
  date_option_cards?: AdvancedDateOptionCard[];
  selected_date_option_id?: string | null;
  selected_start_date?: string | null;
  selected_end_date?: string | null;
  date_selection_status?: PlannerDateResolutionStatus | null;
  date_selection_rationale?: string | null;
  date_requires_confirmation?: boolean;
  source_timing_text?: string | null;
  source_trip_length_text?: string | null;
  advanced_anchor_cards?: AdvancedAnchorChoiceCard[];
  stay_cards?: AdvancedStayOptionCard[];
  hotel_cards?: AdvancedStayHotelOptionCard[];
  selected_stay_option_id?: string | null;
  stay_selection_status?: PlannerStaySelectionStatus | null;
  stay_selection_rationale?: string | null;
  stay_selection_assumptions?: string[];
  stay_compatibility_status?: PlannerStayCompatibilityStatus | null;
  stay_compatibility_notes?: string[];
  selected_hotel_id?: string | null;
  selected_hotel_name?: string | null;
  hotel_selection_status?: PlannerStaySelectionStatus | null;
  hotel_selection_rationale?: string | null;
  hotel_selection_assumptions?: string[];
  hotel_compatibility_status?: PlannerStayCompatibilityStatus | null;
  hotel_compatibility_notes?: string[];
  hotel_filters?: AdvancedStayHotelFilters;
  hotel_sort_order?: PlannerHotelSortOrder;
  hotel_results_status?: PlannerHotelResultsStatus | null;
  hotel_results_summary?: string | null;
  hotel_page?: number;
  hotel_page_size?: number;
  hotel_total_results?: number;
  hotel_total_pages?: number;
  available_hotel_areas?: string[];
  available_hotel_styles?: PlannerHotelStyleTag[];
  selected_hotel_card?: AdvancedStayHotelOptionCard | null;
  have_details: PlannerChecklistItem[];
  need_details: PlannerChecklistItem[];
  visible_steps: TripDetailsStepKey[];
  required_steps: TripDetailsStepKey[];
  details_form?: TripDetailsCollectionFormState | null;
  confirm_cta_label?: string | null;
  own_choice_prompt?: string | null;
};

export type ConversationQuestion = {
  id: string;
  question: string;
  field?: TripFieldKey | null;
  step?: TripDetailsStepKey | null;
  priority: number;
  why?: string | null;
  status: ConversationQuestionStatus;
};

export type ConversationFieldMemory = {
  field: TripFieldKey;
  value: unknown;
  confidence_level?: ConversationFieldConfidence | null;
  confidence?: number | null;
  source: ConversationFieldSource;
  source_turn_id?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
};

export type ConversationOptionMemory = {
  kind: ConversationOptionKind;
  value: string;
  source_turn_id?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
};

export type ConversationDecisionEvent = {
  id: string;
  title: string;
  description: string;
  options: string[];
  selected_option?: string | null;
  source_turn_id?: string | null;
  resolved_at?: string | null;
};

export type ConversationTurnSummary = {
  turn_id: string;
  user_message: string;
  assistant_message?: string | null;
  changed_fields: TripFieldKey[];
  resulting_phase: ChatPlannerPhase;
  created_at?: string | null;
};

export type TripConversationMemory = {
  field_memory: Partial<Record<TripFieldKey, ConversationFieldMemory>>;
  mentioned_options: ConversationOptionMemory[];
  rejected_options: ConversationOptionMemory[];
  decision_history: ConversationDecisionEvent[];
  turn_summaries: ConversationTurnSummary[];
};

export type TripConversationState = {
  phase: ChatPlannerPhase;
  planning_mode?: PlannerPlanningMode | null;
  planning_mode_status: PlannerPlanningModeStatus;
  advanced_step?: PlannerAdvancedStep | null;
  advanced_anchor?: PlannerAdvancedAnchor | null;
  confirmation_status: PlannerConfirmationStatus;
  finalized_at?: string | null;
  finalized_via?: PlannerFinalizedVia | null;
  open_questions: ConversationQuestion[];
  decision_cards: PlannerDecisionCard[];
  last_turn_summary?: string | null;
  active_goals: string[];
  advanced_date_resolution?: AdvancedDateResolutionState;
  stay_planning?: AdvancedStayPlanningState;
  suggestion_board: TripSuggestionBoardState;
  memory: TripConversationMemory;
};

export type CheckpointConversationMessage = {
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string | null;
};
