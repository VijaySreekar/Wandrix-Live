import { postJson } from "@/lib/api/client";
import type {
  CheckpointConversationHistoryResponse,
  OpeningTurnRequest,
  OpeningTurnResponse,
  TripConversationMessageRequest,
  TripConversationMessageResponse,
} from "@/types/conversation";
import { getJson } from "@/lib/api/client";

const TRIP_CONVERSATION_TIMEOUT_MS = 15 * 60 * 1000;

export function getOpeningTurnResponse(
  payload: OpeningTurnRequest,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return postJson<OpeningTurnResponse, OpeningTurnRequest>(
    "/api/v1/chat/opening-turn",
    payload,
    { accessToken, signal, timeoutMs: 20000 },
  );
}


export function sendTripConversationMessage(
  tripId: string,
  payload: TripConversationMessageRequest,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return postJson<TripConversationMessageResponse, TripConversationMessageRequest>(
    `/api/v1/trips/${tripId}/conversation`,
    payload,
    { accessToken, signal, timeoutMs: TRIP_CONVERSATION_TIMEOUT_MS },
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
