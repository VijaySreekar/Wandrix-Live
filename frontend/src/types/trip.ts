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
  phase: string | null;
  from_location: string | null;
  to_location: string | null;
  start_date: string | null;
  end_date: string | null;
  selected_modules: string[];
  timeline_item_count: number;
};

export type TripListResponse = {
  items: TripListItemResponse[];
};
