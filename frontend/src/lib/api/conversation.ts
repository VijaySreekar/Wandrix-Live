import { postJson } from "@/lib/api/client";
import type {
  CheckpointConversationHistoryResponse,
  TripConversationMessageRequest,
  TripConversationMessageResponse,
} from "@/types/conversation";
import { getJson } from "@/lib/api/client";


export function sendTripConversationMessage(
  tripId: string,
  payload: TripConversationMessageRequest,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return postJson<TripConversationMessageResponse, TripConversationMessageRequest>(
    `/api/v1/trips/${tripId}/conversation`,
    payload,
    { accessToken, signal, timeoutMs: 45000 },
  );
}


export function getTripConversationHistory(
  tripId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<CheckpointConversationHistoryResponse>(
    `/api/v1/trips/${tripId}/conversation/history`,
    {
      accessToken,
      signal,
      timeoutMs: 20000,
    },
  );
}
