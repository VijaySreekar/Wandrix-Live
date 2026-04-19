import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { TripDraft } from "@/types/trip-draft";
import type { TripCreateResponse } from "@/types/trip";


export type PlannerWorkspaceState = {
  isEphemeral: boolean;
  browserSession: BrowserSessionCreateResponse;
  trip: TripCreateResponse;
  tripDraft: TripDraft;
};
