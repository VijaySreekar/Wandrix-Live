import { getApiBaseUrl, getJson } from "@/lib/api/client";
import type {
  BrochureHistoryResponse,
  BrochureSnapshot,
} from "@/types/brochure";

export function listTripBrochures(
  tripId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<BrochureHistoryResponse>(`/api/v1/trips/${tripId}/brochures`, {
    accessToken,
    signal,
  });
}

export function getLatestTripBrochure(
  tripId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<BrochureSnapshot>(`/api/v1/trips/${tripId}/brochures/latest`, {
    accessToken,
    signal,
  });
}

export function getTripBrochure(
  tripId: string,
  snapshotId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  return getJson<BrochureSnapshot>(
    `/api/v1/trips/${tripId}/brochures/${snapshotId}`,
    {
      accessToken,
      signal,
    },
  );
}

export async function downloadTripBrochurePdf(
  tripId: string,
  snapshotId: string,
  accessToken?: string,
  signal?: AbortSignal,
) {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/trips/${tripId}/brochures/${snapshotId}/pdf`,
    {
      method: "POST",
      headers,
      cache: "no-store",
      signal,
    },
  );

  if (!response.ok) {
    let message = `PDF request failed with status ${response.status}.`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition");
  const fileName = contentDisposition?.match(/filename="(.+)"/)?.[1] ?? "wandrix-brochure.pdf";

  return { blob, fileName };
}
