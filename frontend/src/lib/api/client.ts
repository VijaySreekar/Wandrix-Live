const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_API_TIMEOUT_MS = 15000;


export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}


type JsonRequestOptions = {
  accessToken?: string;
  method?: "GET" | "POST" | "PUT";
  payload?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
};


async function requestJson<TResponse>(
  path: string,
  {
    accessToken,
    method = "GET",
    payload,
    signal,
    timeoutMs,
  }: JsonRequestOptions = {},
): Promise<TResponse> {
  const baseUrls = getCandidateApiBaseUrls();
  let lastError: unknown = null;

  for (const baseUrl of baseUrls) {
    try {
      const response = await requestJsonFromBaseUrl<TResponse>(baseUrl, path, {
        accessToken,
        method,
        payload,
        signal,
        timeoutMs,
      });
      return response;
    } catch (error) {
      lastError = error;

      if (!shouldRetryWithAnotherBaseUrl(error)) {
        throw error;
      }
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Request failed.");
}

async function requestJsonFromBaseUrl<TResponse>(
  baseUrl: string,
  path: string,
  {
    accessToken,
    method = "GET",
    payload,
    signal,
    timeoutMs,
  }: JsonRequestOptions = {},
): Promise<TResponse> {
  const headers = new Headers();

  if (payload !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => {
    controller.abort(new DOMException("API request timed out.", "TimeoutError"));
  }, timeoutMs ?? DEFAULT_API_TIMEOUT_MS);

  const relayAbort = () => {
    controller.abort(signal?.reason);
  };

  if (signal) {
    if (signal.aborted) {
      relayAbort();
    } else {
      signal.addEventListener("abort", relayAbort, { once: true });
    }
  }

  let response: Response;

  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: payload !== undefined ? JSON.stringify(payload) : undefined,
      cache: "no-store",
      signal: controller.signal,
    });
  } catch (error) {
    if (
      controller.signal.aborted &&
      !(signal?.aborted)
    ) {
      throw new Error("API request timed out.");
    }

    throw error;
  } finally {
    window.clearTimeout(timeout);
    if (signal) {
      signal.removeEventListener("abort", relayAbort);
    }
  }

  if (!response.ok) {
    let message = "Request failed.";

    try {
      const errorPayload = (await response.json()) as {
        detail?: string | { msg?: string }[];
      };

      if (typeof errorPayload.detail === "string") {
        message = errorPayload.detail;
      } else if (Array.isArray(errorPayload.detail)) {
        message = errorPayload.detail.map((item) => item.msg).filter(Boolean).join(", ");
      }
    } catch {
      message = `Request failed with status ${response.status}.`;
    }

    throw new Error(message);
  }

  return (await response.json()) as TResponse;
}

function getCandidateApiBaseUrls() {
  return [getApiBaseUrl()];
}

function shouldRetryWithAnotherBaseUrl(error: unknown) {
  if (error instanceof Error) {
    return (
      error.message === "API request timed out." ||
      error.name === "TypeError"
    );
  }

  return false;
}


export function getJson<TResponse>(
  path: string,
  options?: Omit<JsonRequestOptions, "method" | "payload">,
): Promise<TResponse> {
  return requestJson<TResponse>(path, { ...options, method: "GET" });
}


export async function postJson<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  options?: Omit<JsonRequestOptions, "method" | "payload">,
): Promise<TResponse> {
  return requestJson<TResponse>(path, {
    ...options,
    method: "POST",
    payload,
  });
}


export function putJson<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  options?: Omit<JsonRequestOptions, "method" | "payload">,
): Promise<TResponse> {
  return requestJson<TResponse>(path, {
    ...options,
    method: "PUT",
    payload,
  });
}
