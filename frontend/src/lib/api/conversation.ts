import { postJson } from "@/lib/api/client";
import type {
  TripConversationMessageRequest,
  TripConversationMessageResponse,
} from "@/types/conversation";


export function sendTripConversationMessage(
  tripId: string,
  payload: TripConversationMessageRequest,
  accessToken?: string,
) {
  return postJson<TripConversationMessageResponse, TripConversationMessageRequest>(
    `/api/v1/trips/${tripId}/conversation`,
    payload,
    { accessToken },
  );
}
