import { postJson } from "@/lib/api/client";
import type {
  BrowserSessionCreateRequest,
  BrowserSessionCreateResponse,
} from "@/types/browser-session";


export function createBrowserSession(
  payload: BrowserSessionCreateRequest = {},
  accessToken?: string,
  signal?: AbortSignal,
) {
  return postJson<BrowserSessionCreateResponse, BrowserSessionCreateRequest>(
    "/api/v1/browser-sessions",
    payload,
    { accessToken, signal },
  );
}
