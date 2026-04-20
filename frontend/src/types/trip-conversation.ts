export type ChatPlannerPhase =
  | "opening"
  | "collecting_requirements"
  | "shaping_trip"
  | "enriching_modules"
  | "reviewing";
export type PlannerPlanningMode = "quick" | "advanced";
export type PlannerPlanningModeStatus =
  | "not_selected"
  | "selected"
  | "advanced_unavailable_fallback";
export type TripDetailsStepKey =
  | "modules"
  | "route"
  | "timing"
  | "travellers"
  | "vibe"
  | "budget";

export type TripFieldKey =
  | "from_location"
  | "to_location"
  | "start_date"
  | "end_date"
  | "travel_window"
  | "trip_length"
  | "budget_posture"
  | "budget_gbp"
  | "adults"
  | "children"
  | "activity_styles"
  | "selected_modules";

export type ConversationFieldSource =
  | "user_explicit"
  | "user_inferred"
  | "profile_default"
  | "assistant_derived";

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
  | "helper";
export type DestinationSuggestionSelectionStatus =
  | "suggested"
  | "leading"
  | "confirmed";
export type PlannerChecklistStatus = "known" | "needed";
export type PlanningModeCardStatus = "available" | "in_development";
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

export type PlannerChecklistItem = {
  id: string;
  label: string;
  status: PlannerChecklistStatus;
  value?: string | null;
};

export type TripDetailsCollectionFormState = {
  from_location?: string | null;
  to_location?: string | null;
  selected_modules: TripDetailsBoardModuleSelection;
  travel_window?: string | null;
  trip_length?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  adults?: number | null;
  children?: number | null;
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
  priority: number;
  status: ConversationQuestionStatus;
};

export type ConversationFieldMemory = {
  field: TripFieldKey;
  value: unknown;
  confidence: number;
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
  open_questions: ConversationQuestion[];
  decision_cards: PlannerDecisionCard[];
  last_turn_summary?: string | null;
  active_goals: string[];
  suggestion_board: TripSuggestionBoardState;
  memory: TripConversationMemory;
};

export type CheckpointConversationMessage = {
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string | null;
};
