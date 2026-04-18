import { getJson } from "@/lib/api/client";
import type { ProviderStatusResponse } from "@/types/provider-status";


export function getProviderStatuses(accessToken?: string) {
  return getJson<ProviderStatusResponse>("/api/v1/providers/status", {
    accessToken,
  });
}
