import type { ChatPlannerPhase } from "@/types/trip-conversation";

export type TripCreateRequest = {
  browser_session_id: string;
  title?: string;
};

export type TripCreateResponse = {
  trip_id: string;
  browser_session_id: string;
  thread_id: string;
  title: string;
  trip_status: "collecting_requirements";
  thread_status: "ready";
  created_at: string;
};

export type TripListItemResponse = TripCreateResponse & {
  updated_at: string;
  phase: ChatPlannerPhase | null;
  brochure_ready: boolean;
  latest_brochure_snapshot_id: string | null;
  latest_brochure_version: number | null;
  brochure_versions_count: number;
  from_location: string | null;
  to_location: string | null;
  start_date: string | null;
  end_date: string | null;
  travel_window: string | null;
  trip_length: string | null;
  selected_modules: string[];
  timeline_item_count: number;
};

export type TripListResponse = {
  items: TripListItemResponse[];
};

export type TripDeleteResponse = {
  trip_id: string;
  deleted: true;
};
