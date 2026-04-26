import { deleteJson, getJson, postJson, putJson } from "@/lib/api/client";
import type {
  TripDeleteResponse,
  TripCreateRequest,
  TripCreateResponse,
  TripListResponse,
} from "@/types/trip";
import type { TripDraft, TripDraftUpsertRequest } from "@/types/trip-draft";


export function createTrip(
  payload: TripCreateRequest,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return postJson<TripCreateResponse, TripCreateRequest>("/api/v1/trips", payload, {
    accessToken,
    signal,
  });
}


export function getTrip(
  tripId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<TripCreateResponse>(`/api/v1/trips/${tripId}`, {
    accessToken,
    signal,
  });
}


export function deleteTrip(
  tripId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return deleteJson<TripDeleteResponse>(`/api/v1/trips/${tripId}`, {
    accessToken,
    signal,
  });
}


export function listTrips(
  limit = 12,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<TripListResponse>(`/api/v1/trips?limit=${limit}`, {
    accessToken,
    signal,
  });
}


export function getTripDraft(
  tripId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<TripDraft>(`/api/v1/trips/${tripId}/draft`, {
    accessToken,
    signal,
  });
}


export function saveTripDraft(
  tripId: string,
  payload: TripDraftUpsertRequest,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return putJson<TripDraft, TripDraftUpsertRequest>(
    `/api/v1/trips/${tripId}/draft`,
    payload,
    { accessToken, signal },
  );
}
