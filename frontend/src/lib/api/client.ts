const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";


export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}


type JsonRequestOptions = {
  accessToken?: string;
  method?: "GET" | "POST" | "PUT";
  payload?: unknown;
};


async function requestJson<TResponse>(
  path: string,
  { accessToken, method = "GET", payload }: JsonRequestOptions = {},
): Promise<TResponse> {
  const headers = new Headers();

  if (payload !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers,
    body: payload !== undefined ? JSON.stringify(payload) : undefined,
    cache: "no-store",
  });

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
