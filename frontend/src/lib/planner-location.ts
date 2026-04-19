"use client";

import type {
  PlannerLocationContext,
  PlannerProfileContext,
} from "@/types/conversation";
import type { TripDraft } from "@/types/trip-draft";

type ResolvedPlannerLocation = {
  status: "resolved";
  value: PlannerLocationContext;
};

type BlockedPlannerLocation = {
  status: "blocked";
  reason: "permission_denied" | "unsupported";
};

type StoredPlannerLocation = ResolvedPlannerLocation | BlockedPlannerLocation;

const LOCATION_STORAGE_PREFIX = "wandrix:planner-location:";
const GEOLOCATION_TIMEOUT_MS = 15000;
const GEOLOCATION_MAX_AGE_MS = 1000 * 60 * 30;

export async function resolvePlannerLocationForTurn({
  tripId,
  profileContext,
  tripDraft,
}: {
  tripId: string | null;
  profileContext: PlannerProfileContext | null;
  tripDraft: TripDraft | null;
}): Promise<PlannerLocationContext | null> {
  if (
    !tripId ||
    !profileContext?.location_assist_enabled ||
    tripDraft?.configuration.to_location
  ) {
    return null;
  }

  if (
    tripDraft &&
    !["opening", "collecting_requirements", "shaping_trip"].includes(
      tripDraft.conversation.phase,
    )
  ) {
    return null;
  }

  const cached = readStoredPlannerLocation(tripId);
  if (cached?.status === "resolved") {
    return cached.value;
  }

  if (cached?.status === "blocked") {
    return null;
  }

  if (!("geolocation" in navigator)) {
    writeStoredPlannerLocation(tripId, {
      status: "blocked",
      reason: "unsupported",
    });
    return null;
  }

  try {
    const position = await readBrowserPosition();
    const value: PlannerLocationContext = {
      source: "browser_location",
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
    };

    writeStoredPlannerLocation(tripId, {
      status: "resolved",
      value,
    });

    return value;
  } catch (error) {
    if (isPermissionDenied(error)) {
      writeStoredPlannerLocation(tripId, {
        status: "blocked",
        reason: "permission_denied",
      });
    }

    return null;
  }
}

function readStoredPlannerLocation(tripId: string): StoredPlannerLocation | null {
  try {
    const raw = window.sessionStorage.getItem(
      `${LOCATION_STORAGE_PREFIX}${tripId}`,
    );
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as { status?: string };
    if (!parsed || typeof parsed !== "object") {
      return null;
    }

    if (parsed.status === "resolved") {
      return parsed as ResolvedPlannerLocation;
    }

    if (parsed.status === "blocked") {
      return parsed as BlockedPlannerLocation;
    }

    window.sessionStorage.removeItem(`${LOCATION_STORAGE_PREFIX}${tripId}`);
    return null;
  } catch {
    return null;
  }
}

function writeStoredPlannerLocation(tripId: string, value: StoredPlannerLocation) {
  try {
    window.sessionStorage.setItem(
      `${LOCATION_STORAGE_PREFIX}${tripId}`,
      JSON.stringify(value),
    );
  } catch {
    // Keep the planner usable even if session storage is unavailable.
  }
}

function readBrowserPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: false,
      timeout: GEOLOCATION_TIMEOUT_MS,
      maximumAge: GEOLOCATION_MAX_AGE_MS,
    });
  });
}

function isPermissionDenied(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    Number((error as { code?: unknown }).code) === 1
  );
}
