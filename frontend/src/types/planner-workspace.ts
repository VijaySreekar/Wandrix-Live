import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { TripDraft } from "@/types/trip-draft";
import type { TripCreateResponse } from "@/types/trip";


export type PlannerWorkspaceState = {
  browserSession: BrowserSessionCreateResponse;
  trip: TripCreateResponse;
  tripDraft: TripDraft;
};
