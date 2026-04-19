"use client";

import type { PlannerLocationContext, PlannerProfileContext } from "@/types/conversation";
import type { TripDraft } from "@/types/trip-draft";

type StoredPlannerLocation =
  | {
      status: "resolved";
      value: PlannerLocationContext;
    }
  | {
      status: "unavailable";
    };

const LOCATION_STORAGE_PREFIX = "wandrix:planner-location:";

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

  if (cached?.status === "unavailable") {
    return null;
  }

  if (!("geolocation" in navigator)) {
    writeStoredPlannerLocation(tripId, { status: "unavailable" });
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
  } catch {
    writeStoredPlannerLocation(tripId, { status: "unavailable" });
    return null;
  }
}

function readStoredPlannerLocation(tripId: string): StoredPlannerLocation | null {
  try {
    const raw = window.sessionStorage.getItem(`${LOCATION_STORAGE_PREFIX}${tripId}`);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as StoredPlannerLocation;
    if (!parsed || typeof parsed !== "object" || !("status" in parsed)) {
      return null;
    }

    return parsed;
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
      timeout: 4500,
      maximumAge: 1000 * 60 * 30,
    });
  });
}
