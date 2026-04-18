import { getJson, postJson, putJson } from "@/lib/api/client";
import type {
  TripCreateRequest,
  TripCreateResponse,
  TripListResponse,
} from "@/types/trip";
import type { TripDraft, TripDraftUpsertRequest } from "@/types/trip-draft";


export function createTrip(payload: TripCreateRequest, accessToken?: string) {
  return postJson<TripCreateResponse, TripCreateRequest>("/api/v1/trips", payload, {
    accessToken,
  });
}


export function getTrip(tripId: string, accessToken?: string) {
  return getJson<TripCreateResponse>(`/api/v1/trips/${tripId}`, {
    accessToken,
  });
}


export function listTrips(limit = 12, accessToken?: string) {
  return getJson<TripListResponse>(`/api/v1/trips?limit=${limit}`, {
    accessToken,
  });
}


export function getTripDraft(tripId: string, accessToken?: string) {
  return getJson<TripDraft>(`/api/v1/trips/${tripId}/draft`, {
    accessToken,
  });
}


export function saveTripDraft(
  tripId: string,
  payload: TripDraftUpsertRequest,
  accessToken?: string,
) {
  return putJson<TripDraft, TripDraftUpsertRequest>(
    `/api/v1/trips/${tripId}/draft`,
    payload,
    { accessToken },
  );
}
