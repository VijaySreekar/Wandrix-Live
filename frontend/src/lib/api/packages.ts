import { postJson } from "@/lib/api/client";
import type { TravelPackageRequest, TravelPackageResponse } from "@/types/package";


export function generateTravelPackage(payload: TravelPackageRequest) {
  return postJson<TravelPackageResponse, TravelPackageRequest>(
    "/api/v1/packages/generate",
    payload,
  );
}
