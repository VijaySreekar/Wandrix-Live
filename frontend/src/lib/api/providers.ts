import { getJson } from "@/lib/api/client";
import type {
  PlannerLocationSuggestionKind,
  PlannerLocationSuggestionResponse,
} from "@/types/location-suggestions";
import type { ProviderStatusResponse } from "@/types/provider-status";
import type { ProviderUsageResponse } from "@/types/provider-usage";


export function getProviderStatuses(accessToken?: string) {
  return getJson<ProviderStatusResponse>("/api/v1/providers/status", {
    accessToken,
  });
}

export function getProviderUsage(accessToken?: string) {
  return getJson<ProviderUsageResponse>("/api/v1/providers/usage", {
    accessToken,
  });
}

export function searchProviderLocations(
  query: string,
  kind: PlannerLocationSuggestionKind,
  accessToken?: string,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    query,
    kind,
  });

  return getJson<PlannerLocationSuggestionResponse>(
    `/api/v1/providers/locations/search?${params.toString()}`,
    {
      accessToken,
      signal,
    },
  );
}
