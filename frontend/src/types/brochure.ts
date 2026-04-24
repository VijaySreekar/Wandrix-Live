import type {
  ActivityDetail,
  FlightDetail,
  HotelStayDetail,
  TimelineItem,
  WeatherDetail,
} from "@/types/trip-draft";

export type BrochureWarningCategory =
  | "timing"
  | "logistics"
  | "budget"
  | "weather"
  | "selection_pending"
  | "review";

export type BrochureSnapshotStatus = "latest" | "historical";
export type BrochureAdvancedReviewStatus = "ready" | "needs_review" | "flexible";

export type BrochureHeroImage = {
  url: string;
  alt_text: string;
  attribution: string | null;
};

export type BrochureMetric = {
  label: string;
  value: string;
  note: string | null;
};

export type BrochureWarning = {
  id: string;
  category: BrochureWarningCategory;
  title: string;
  message: string;
  related_timeline_ids: string[];
};

export type BrochureSection = {
  id: string;
  title: string;
  summary: string | null;
};

export type BrochureAdvancedSectionSummary = {
  id: string;
  title: string;
  status: BrochureAdvancedReviewStatus;
  summary: string;
  notes: string[];
};

export type BrochureResourceLink = {
  label: string;
  url: string;
};

export type BrochureItineraryDay = {
  id: string;
  label: string;
  summary: string | null;
  items: TimelineItem[];
};

export type BrochureBudgetSummary = {
  headline: string;
  detail: string;
};

export type BrochureTravelSummary = {
  headline: string;
  detail: string;
};

export type BrochureSnapshotPayload = {
  title: string;
  route_text: string;
  origin_label: string | null;
  destination_label: string | null;
  travel_window_text: string;
  party_text: string;
  budget_text: string;
  style_tags: string[];
  module_tags: string[];
  executive_summary: string;
  hero_image: BrochureHeroImage;
  metrics: BrochureMetric[];
  sections: BrochureSection[];
  advanced_review_status?: BrochureAdvancedReviewStatus | null;
  advanced_review_summary?: string | null;
  advanced_section_summaries?: BrochureAdvancedSectionSummary[];
  trip_character_summary?: string | null;
  planned_experience_summary?: string | null;
  flexible_items?: string[];
  worth_reviewing_notes?: string[];
  warnings: BrochureWarning[];
  itinerary_days: BrochureItineraryDay[];
  flights: FlightDetail[];
  stays: HotelStayDetail[];
  weather: WeatherDetail[];
  highlights: ActivityDetail[];
  planning_notes: string[];
  budget_summary: BrochureBudgetSummary;
  travel_summary: BrochureTravelSummary;
  resources: BrochureResourceLink[];
};

export type BrochureSnapshotSummary = {
  snapshot_id: string;
  trip_id: string;
  version_number: number;
  status: BrochureSnapshotStatus;
  finalized_at: string;
  created_at: string;
  pdf_file_name: string;
};

export type BrochureHistoryItem = BrochureSnapshotSummary & {
  is_latest: boolean;
};

export type BrochureSnapshot = BrochureSnapshotSummary & {
  payload: BrochureSnapshotPayload;
};

export type BrochureHistoryResponse = {
  items: BrochureHistoryItem[];
};
