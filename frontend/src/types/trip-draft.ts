import type {
  ChatPlannerPhase,
  PlannerConfirmationStatus,
  PlannerFinalizedVia,
  TripConversationState,
  TripFieldKey,
} from "@/types/trip-conversation";


export type ActivityStyle =
  | "relaxed"
  | "adventure"
  | "luxury"
  | "family"
  | "culture"
  | "nightlife"
  | "romantic"
  | "food"
  | "outdoors";

export type BudgetPosture = "budget" | "mid_range" | "premium";
export type BudgetEstimateCategoryKey =
  | "flights"
  | "stay"
  | "activities"
  | "food"
  | "local_transport";
export type BudgetEstimateSource =
  | "provider_price"
  | "planner_estimate"
  | "unavailable";

export type PlanningModuleKey = "flights" | "weather" | "activities" | "hotels";
export type TimelineItemType =
  | "flight"
  | "transfer"
  | "hotel"
  | "activity"
  | "event"
  | "meal"
  | "weather"
  | "note";

export type TimelineItemStatus = "draft" | "confirmed";
export type TimelineTimingSource =
  | "provider_exact"
  | "planner_estimate"
  | "user_confirmed";

export type TripPlanningPhase = ChatPlannerPhase;

export type PlannerTravelerDetails = {
  adults: number | null;
  children: number | null;
};

export type TripModuleSelection = {
  flights: boolean;
  weather: boolean;
  activities: boolean;
  hotels: boolean;
};

export type TripConfiguration = {
  from_location: string | null;
  from_location_flexible?: boolean | null;
  to_location: string | null;
  start_date: string | null;
  end_date: string | null;
  travel_window: string | null;
  trip_length: string | null;
  weather_preference?: string | null;
  travelers: PlannerTravelerDetails;
  travelers_flexible?: boolean | null;
  budget_posture: BudgetPosture | null;
  budget_amount?: number | null;
  budget_currency?: string | null;
  budget_gbp: number | null;
  selected_modules: TripModuleSelection;
  activity_styles: ActivityStyle[];
  custom_style?: string | null;
};

export type FlightLegDetail = {
  carrier?: string | null;
  flight_number?: string | null;
  departure_airport: string;
  arrival_airport: string;
  departure_time?: string | null;
  arrival_time?: string | null;
  duration_text?: string | null;
};

export type FlightDetail = {
  id: string;
  direction: "outbound" | "return";
  carrier: string;
  flight_number: string | null;
  departure_airport: string;
  arrival_airport: string;
  departure_time: string | null;
  arrival_time: string | null;
  duration_text: string | null;
  price_text?: string | null;
  fare_amount?: number | null;
  fare_currency?: string | null;
  stop_count?: number | null;
  stop_details_available?: boolean | null;
  layover_summary?: string | null;
  legs?: FlightLegDetail[];
  timing_quality?: string | null;
  inventory_notice?: string | null;
  inventory_source?: "live" | "cached" | "placeholder" | null;
  notes: string[];
};

export type HotelStayDetail = {
  id: string;
  hotel_name: string;
  hotel_key?: string | null;
  area: string | null;
  address?: string | null;
  image_url?: string | null;
  source_url?: string | null;
  source_label?: string | null;
  nightly_rate_amount?: number | null;
  nightly_rate_currency?: string | null;
  nightly_tax_amount?: number | null;
  rate_provider_name?: string | null;
  check_in: string | null;
  check_out: string | null;
  notes: string[];
};

export type WeatherDetail = {
  id: string;
  day_label: string;
  summary: string;
  forecast_date?: string | null;
  weather_code?: number | null;
  condition_tags?: string[];
  temperature_band?: string | null;
  weather_risk_level?: "low" | "medium" | "high" | null;
  high_c: number | null;
  low_c: number | null;
  notes: string[];
};

export type ActivityDetail = {
  id: string;
  title: string;
  category: string | null;
  latitude?: number | null;
  longitude?: number | null;
  venue_name?: string | null;
  location_label?: string | null;
  source_label?: string | null;
  source_url?: string | null;
  image_url?: string | null;
  availability_text?: string | null;
  price_text?: string | null;
  status_text?: string | null;
  estimated_duration_minutes?: number | null;
  start_at?: string | null;
  end_at?: string | null;
  day_label: string | null;
  time_label: string | null;
  notes: string[];
};

export type TripModuleOutputs = {
  flights: FlightDetail[];
  hotels: HotelStayDetail[];
  weather: WeatherDetail[];
  activities: ActivityDetail[];
};

export type TripBudgetEstimateCategory = {
  category: BudgetEstimateCategoryKey;
  label: string;
  low_amount: number | null;
  high_amount: number | null;
  currency: string | null;
  source: BudgetEstimateSource;
  notes: string[];
};

export type TripBudgetEstimate = {
  total_low_amount: number | null;
  total_high_amount: number | null;
  currency: string | null;
  categories: TripBudgetEstimateCategory[];
  caveat: string;
};

export type TimelineItem = {
  id: string;
  type: TimelineItemType;
  title: string;
  day_label: string | null;
  start_at: string | null;
  end_at: string | null;
  timing_source?: TimelineTimingSource | null;
  timing_note?: string | null;
  venue_name?: string | null;
  location_label: string | null;
  summary: string | null;
  details: string[];
  source_label?: string | null;
  source_url?: string | null;
  image_url?: string | null;
  availability_text?: string | null;
  price_text?: string | null;
  status_text?: string | null;
  source_module: PlanningModuleKey | null;
  status: TimelineItemStatus;
};

export type TripDraftStatus = {
  phase: TripPlanningPhase;
  confirmation_status: PlannerConfirmationStatus;
  finalized_at: string | null;
  finalized_via: PlannerFinalizedVia | null;
  missing_fields: string[];
  confirmed_fields: TripFieldKey[];
  inferred_fields: TripFieldKey[];
  brochure_ready: boolean;
  last_updated_at: string | null;
};

export type TripDraft = {
  trip_id: string;
  thread_id: string;
  title: string;
  configuration: TripConfiguration;
  timeline: TimelineItem[];
  module_outputs: TripModuleOutputs;
  budget_estimate?: TripBudgetEstimate | null;
  status: TripDraftStatus;
  conversation: TripConversationState;
};

export type TripDraftUpsertRequest = Omit<TripDraft, "trip_id" | "thread_id">;
