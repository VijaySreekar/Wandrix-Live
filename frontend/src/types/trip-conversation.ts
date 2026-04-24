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
export type PlannerActivityCandidateKind = "activity" | "event";
export type PlannerActivityDisposition = "essential" | "maybe" | "pass";
export type PlannerActivityDaypart = "morning" | "afternoon" | "evening";
export type PlannerReviewResolutionScope = "stay" | "hotel";
export type PlannerActivityScheduleStatus = "none" | "ready";
export type PlannerActivityCompletionStatus = "in_progress" | "completed";
export type PlannerActivityTimelineBlockType = "activity" | "event" | "transfer";
export type PlannerFlightStrategy =
  | "smoothest_route"
  | "best_timing"
  | "best_value"
  | "keep_flexible";
export type PlannerFlightSelectionStatus =
  | "none"
  | "selected"
  | "completed"
  | "kept_open";
export type PlannerFlightResultsStatus = "blocked" | "ready" | "placeholder";
export type PlannerFlightOptionSource = "provider" | "placeholder";
export type PlannerWeatherResultsStatus =
  | "ready"
  | "unavailable"
  | "not_requested";
export type PlannerAdvancedReviewReadinessStatus =
  | "ready"
  | "needs_review"
  | "flexible";
export type PlannerTripStyleSelectionStatus =
  | "none"
  | "selected"
  | "review"
  | "completed";
export type PlannerTripStyleSubstep =
  | "direction"
  | "pace"
  | "tradeoffs"
  | "completed";
export type PlannerTripPace = "slow" | "balanced" | "full";
export type PlannerTripStyleTradeoffAxis =
  | "must_sees_vs_wandering"
  | "convenience_vs_atmosphere"
  | "early_starts_vs_evening_energy"
  | "polished_vs_hidden_gems";
export type PlannerTripStyleTradeoffChoice =
  | "must_sees"
  | "wandering"
  | "convenience"
  | "atmosphere"
  | "early_starts"
  | "evening_energy"
  | "polished"
  | "hidden_gems"
  | "balanced";
export type PlannerTripDirectionPrimary =
  | "food_led"
  | "culture_led"
  | "nightlife_led"
  | "outdoors_led"
  | "balanced";
export type PlannerTripDirectionAccent =
  | "local"
  | "classic"
  | "polished"
  | "romantic"
  | "relaxed";
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
export type PlannerDecisionMemoryKey =
  | "destination"
  | "origin"
  | "date_window"
  | "travelers"
  | "budget"
  | "module_scope"
  | "trip_style_direction"
  | "trip_style_pace"
  | "trip_style_tradeoffs"
  | "selected_flights"
  | "selected_stay"
  | "selected_activities"
  | "weather_context"
  | "advanced_review";
export type PlannerDecisionSource =
  | "user_explicit"
  | "board_action"
  | "assistant_inferred"
  | "profile_default"
  | "provider"
  | "system";
export type PlannerDecisionConfidence = "low" | "medium" | "high";
export type PlannerDecisionStatus =
  | "working"
  | "confirmed"
  | "needs_review"
  | "superseded";
export type PlannerConflictSeverity = "info" | "warning" | "important";
export type PlannerConflictCategory =
  | "style_pace"
  | "logistics"
  | "stay_fit"
  | "weather"
  | "schedule_density"
  | "provider_confidence";
export type PlannerConflictRevisionTarget =
  | "flight"
  | "stay"
  | "trip_style"
  | "activities"
  | "review";

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
  | "advanced_flights_workspace"
  | "advanced_trip_style_direction"
  | "advanced_trip_style_pace"
  | "advanced_trip_style_tradeoffs"
  | "advanced_activities_workspace"
  | "advanced_stay_choice"
  | "advanced_stay_selected"
  | "advanced_stay_review"
  | "advanced_stay_hotel_choice"
  | "advanced_stay_hotel_selected"
  | "advanced_stay_hotel_review"
  | "advanced_review_workspace"
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

export type AdvancedFlightStrategyCard = {
  id: PlannerFlightStrategy;
  title: string;
  description: string;
  bullets: string[];
  recommended: boolean;
};

export type AdvancedFlightLegCard = {
  carrier?: string | null;
  flight_number?: string | null;
  departure_airport: string;
  arrival_airport: string;
  departure_time?: string | null;
  arrival_time?: string | null;
  duration_text?: string | null;
};

export type AdvancedFlightOptionCard = {
  id: string;
  direction: "outbound" | "return";
  carrier: string;
  flight_number?: string | null;
  departure_airport: string;
  arrival_airport: string;
  departure_time?: string | null;
  arrival_time?: string | null;
  duration_text?: string | null;
  price_text?: string | null;
  stop_count?: number | null;
  layover_summary?: string | null;
  legs?: AdvancedFlightLegCard[];
  timing_quality?: string | null;
  inventory_notice?: string | null;
  summary: string;
  tradeoffs: string[];
  source_kind: PlannerFlightOptionSource;
  recommended: boolean;
};

export type AdvancedReviewSectionCard = {
  id: string;
  title: string;
  status: PlannerAdvancedReviewReadinessStatus;
  summary: string;
  notes: string[];
  revision_anchor?: PlannerAdvancedAnchor | null;
  cta_label?: string | null;
};

export type AdvancedReviewDecisionSignal = {
  id: string;
  title: string;
  value_summary: string;
  source: PlannerDecisionSource;
  source_label: string;
  confidence: PlannerDecisionConfidence;
  confidence_label: string;
  status: PlannerDecisionStatus;
  note?: string | null;
  related_anchor?: PlannerAdvancedAnchor | null;
};

export type PlannerConflictRecord = {
  id: string;
  severity: PlannerConflictSeverity;
  category: PlannerConflictCategory;
  affected_areas: string[];
  summary: string;
  evidence: string[];
  source_decision_ids: string[];
  suggested_repair: string;
  revision_target?: PlannerConflictRevisionTarget | null;
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

export type AdvancedActivityCandidateCard = {
  id: string;
  kind: PlannerActivityCandidateKind;
  title: string;
  latitude?: number | null;
  longitude?: number | null;
  venue_name?: string | null;
  location_label?: string | null;
  summary?: string | null;
  source_label?: string | null;
  source_url?: string | null;
  image_url?: string | null;
  availability_text?: string | null;
  price_text?: string | null;
  status_text?: string | null;
  estimated_duration_minutes?: number | null;
  time_label?: string | null;
  start_at?: string | null;
  end_at?: string | null;
  recommended: boolean;
  disposition: PlannerActivityDisposition;
  ranking_reasons: string[];
};

export type AdvancedActivityPlacementPreference = {
  candidate_id: string;
  day_index?: number | null;
  daypart?: PlannerActivityDaypart | null;
  reserved: boolean;
};

export type AdvancedActivityTimelineBlock = {
  id: string;
  type: PlannerActivityTimelineBlockType;
  candidate_id?: string | null;
  title: string;
  day_index: number;
  day_label: string;
  daypart?: PlannerActivityDaypart | null;
  venue_name?: string | null;
  location_label?: string | null;
  start_at?: string | null;
  end_at?: string | null;
  summary?: string | null;
  details: string[];
  source_label?: string | null;
  source_url?: string | null;
  image_url?: string | null;
  availability_text?: string | null;
  price_text?: string | null;
  status_text?: string | null;
  fixed_time: boolean;
  manual_override: boolean;
};

export type AdvancedActivityDayPlan = {
  id: string;
  day_index: number;
  day_label: string;
  date?: string | null;
  blocks: AdvancedActivityTimelineBlock[];
};

export type AdvancedActivityPlanningState = {
  recommended_candidates: AdvancedActivityCandidateCard[];
  visible_candidates: AdvancedActivityCandidateCard[];
  placement_preferences: AdvancedActivityPlacementPreference[];
  essential_ids: string[];
  maybe_ids: string[];
  passed_ids: string[];
  selected_event_ids: string[];
  reserved_candidate_ids: string[];
  workspace_summary?: string | null;
  day_plans: AdvancedActivityDayPlan[];
  timeline_blocks: AdvancedActivityTimelineBlock[];
  unscheduled_candidate_ids: string[];
  schedule_summary?: string | null;
  schedule_notes: string[];
  schedule_status: PlannerActivityScheduleStatus;
  workspace_touched: boolean;
  completion_status: PlannerActivityCompletionStatus;
  completion_summary?: string | null;
  completion_anchor_ids: string[];
};

export type TripStyleTradeoffOption = {
  value: PlannerTripStyleTradeoffChoice;
  label: string;
  description: string;
  recommended: boolean;
};

export type TripStyleTradeoffCard = {
  axis: PlannerTripStyleTradeoffAxis;
  title: string;
  description: string;
  options: TripStyleTradeoffOption[];
};

export type TripStyleTradeoffDecision = {
  axis: PlannerTripStyleTradeoffAxis;
  selected_value: PlannerTripStyleTradeoffChoice;
};

export type TripStylePlanningState = {
  substep: PlannerTripStyleSubstep;
  recommended_primary_directions: PlannerTripDirectionPrimary[];
  recommended_accents: PlannerTripDirectionAccent[];
  selected_primary_direction?: PlannerTripDirectionPrimary | null;
  selected_accent?: PlannerTripDirectionAccent | null;
  selection_status: PlannerTripStyleSelectionStatus;
  workspace_summary?: string | null;
  selection_rationale?: string | null;
  downstream_influence_summary?: string | null;
  recommended_paces: PlannerTripPace[];
  selected_pace?: PlannerTripPace | null;
  pace_status: PlannerTripStyleSelectionStatus;
  pace_rationale?: string | null;
  pace_downstream_influence_summary?: string | null;
  recommended_tradeoff_cards: TripStyleTradeoffCard[];
  selected_tradeoffs: TripStyleTradeoffDecision[];
  tradeoff_status: PlannerTripStyleSelectionStatus;
  tradeoff_rationale?: string | null;
  tradeoff_downstream_influence_summary?: string | null;
  workspace_touched: boolean;
  completion_summary?: string | null;
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
  flight_strategy_cards?: AdvancedFlightStrategyCard[];
  outbound_flight_options?: AdvancedFlightOptionCard[];
  return_flight_options?: AdvancedFlightOptionCard[];
  selected_flight_strategy?: PlannerFlightStrategy | null;
  selected_outbound_flight_id?: string | null;
  selected_return_flight_id?: string | null;
  selected_outbound_flight?: AdvancedFlightOptionCard | null;
  selected_return_flight?: AdvancedFlightOptionCard | null;
  flight_selection_status?: PlannerFlightSelectionStatus | null;
  flight_results_status?: PlannerFlightResultsStatus | null;
  flight_missing_requirements?: string[];
  flight_workspace_summary?: string | null;
  flight_selection_summary?: string | null;
  flight_downstream_notes?: string[];
  flight_arrival_day_impact_summary?: string | null;
  flight_departure_day_impact_summary?: string | null;
  flight_timing_review_notes?: string[];
  flight_completion_summary?: string | null;
  weather_results_status?: PlannerWeatherResultsStatus | null;
  weather_workspace_summary?: string | null;
  weather_day_impact_summaries?: string[];
  weather_activity_influence_notes?: string[];
  advanced_review_readiness_status?: PlannerAdvancedReviewReadinessStatus | null;
  advanced_review_summary?: string | null;
  advanced_review_completed_summary?: string | null;
  advanced_review_open_summary?: string | null;
  advanced_review_section_cards?: AdvancedReviewSectionCard[];
  advanced_review_notes?: string[];
  advanced_review_decision_signals?: AdvancedReviewDecisionSignal[];
  planner_conflicts?: PlannerConflictRecord[];
  stay_cards?: AdvancedStayOptionCard[];
  hotel_cards?: AdvancedStayHotelOptionCard[];
  activity_candidates?: AdvancedActivityCandidateCard[];
  essential_ids?: string[];
  maybe_ids?: string[];
  passed_ids?: string[];
  selected_event_ids?: string[];
  reserved_candidate_ids?: string[];
  activity_workspace_summary?: string | null;
  trip_style_recommended_primaries?: PlannerTripDirectionPrimary[];
  trip_style_recommended_accents?: PlannerTripDirectionAccent[];
  selected_trip_style_primary?: PlannerTripDirectionPrimary | null;
  selected_trip_style_accent?: PlannerTripDirectionAccent | null;
  trip_style_selection_status?: PlannerTripStyleSelectionStatus | null;
  trip_style_substep?: PlannerTripStyleSubstep | null;
  trip_style_workspace_summary?: string | null;
  trip_style_selection_rationale?: string | null;
  trip_style_downstream_influence_summary?: string | null;
  trip_style_recommended_paces?: PlannerTripPace[];
  selected_trip_style_pace?: PlannerTripPace | null;
  trip_style_pace_status?: PlannerTripStyleSelectionStatus | null;
  trip_style_pace_rationale?: string | null;
  trip_style_pace_downstream_influence_summary?: string | null;
  trip_style_recommended_tradeoff_cards?: TripStyleTradeoffCard[];
  selected_trip_style_tradeoffs?: TripStyleTradeoffDecision[];
  trip_style_tradeoff_status?: PlannerTripStyleSelectionStatus | null;
  trip_style_tradeoff_rationale?: string | null;
  trip_style_tradeoff_downstream_influence_summary?: string | null;
  trip_style_completion_summary?: string | null;
  activity_day_plans?: AdvancedActivityDayPlan[];
  unscheduled_activity_candidate_ids?: string[];
  activity_schedule_summary?: string | null;
  activity_schedule_notes?: string[];
  activity_schedule_status?: PlannerActivityScheduleStatus;
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

export type PlannerDecisionMemoryRecord = {
  key: PlannerDecisionMemoryKey;
  value_summary: string;
  source: PlannerDecisionSource;
  confidence: PlannerDecisionConfidence;
  status: PlannerDecisionStatus;
  rationale?: string | null;
  related_anchor?: PlannerAdvancedAnchor | null;
  updated_at?: string | null;
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
  decision_memory: PlannerDecisionMemoryRecord[];
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
  planner_conflicts: PlannerConflictRecord[];
  advanced_date_resolution?: AdvancedDateResolutionState;
  flight_planning?: AdvancedFlightPlanningState;
  weather_planning?: AdvancedWeatherPlanningState;
  advanced_review_planning?: AdvancedReviewPlanningState;
  trip_style_planning?: TripStylePlanningState;
  activity_planning?: AdvancedActivityPlanningState;
  stay_planning?: AdvancedStayPlanningState;
  suggestion_board: TripSuggestionBoardState;
  memory: TripConversationMemory;
};

export type AdvancedFlightPlanningState = {
  strategy_cards: AdvancedFlightStrategyCard[];
  outbound_options: AdvancedFlightOptionCard[];
  return_options: AdvancedFlightOptionCard[];
  selected_strategy?: PlannerFlightStrategy | null;
  selected_outbound_flight_id?: string | null;
  selected_return_flight_id?: string | null;
  selected_outbound_flight?: AdvancedFlightOptionCard | null;
  selected_return_flight?: AdvancedFlightOptionCard | null;
  selection_status: PlannerFlightSelectionStatus;
  results_status: PlannerFlightResultsStatus;
  missing_requirements: string[];
  workspace_summary?: string | null;
  selection_summary?: string | null;
  downstream_notes: string[];
  arrival_day_impact_summary?: string | null;
  departure_day_impact_summary?: string | null;
  timing_review_notes: string[];
  workspace_touched: boolean;
  completion_summary?: string | null;
};

export type AdvancedWeatherPlanningState = {
  results_status: PlannerWeatherResultsStatus;
  workspace_summary?: string | null;
  day_impact_summaries: string[];
  activity_influence_notes: string[];
};

export type AdvancedReviewPlanningState = {
  readiness_status: PlannerAdvancedReviewReadinessStatus;
  workspace_summary?: string | null;
  completed_summary?: string | null;
  open_summary?: string | null;
  section_cards: AdvancedReviewSectionCard[];
  review_notes: string[];
};

export type CheckpointConversationMessage = {
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string | null;
};
