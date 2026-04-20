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

export type PlanningModuleKey = "flights" | "weather" | "activities" | "hotels";
export type TimelineItemType =
  | "flight"
  | "transfer"
  | "hotel"
  | "activity"
  | "meal"
  | "weather"
  | "note";

export type TimelineItemStatus = "draft" | "confirmed";

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
  to_location: string | null;
  start_date: string | null;
  end_date: string | null;
  travel_window: string | null;
  trip_length: string | null;
  travelers: PlannerTravelerDetails;
  budget_posture: BudgetPosture | null;
  budget_gbp: number | null;
  selected_modules: TripModuleSelection;
  activity_styles: ActivityStyle[];
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
  notes: string[];
};

export type HotelStayDetail = {
  id: string;
  hotel_name: string;
  area: string | null;
  check_in: string | null;
  check_out: string | null;
  notes: string[];
};

export type WeatherDetail = {
  id: string;
  day_label: string;
  summary: string;
  high_c: number | null;
  low_c: number | null;
  notes: string[];
};

export type ActivityDetail = {
  id: string;
  title: string;
  category: string | null;
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

export type TimelineItem = {
  id: string;
  type: TimelineItemType;
  title: string;
  day_label: string | null;
  start_at: string | null;
  end_at: string | null;
  location_label: string | null;
  summary: string | null;
  details: string[];
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
  status: TripDraftStatus;
  conversation: TripConversationState;
};

export type TripDraftUpsertRequest = Omit<TripDraft, "trip_id" | "thread_id">;
