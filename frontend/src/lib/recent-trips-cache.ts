import type { TripListItemResponse } from "@/types/trip";
import type { ChatPlannerPhase } from "@/types/trip-conversation";

const RECENT_TRIPS_CACHE_PREFIX = "wandrix:recent-trips:";
const VALID_CHAT_PHASES: ChatPlannerPhase[] = [
  "opening",
  "collecting_requirements",
  "shaping_trip",
  "enriching_modules",
  "reviewing",
  "finalized",
];

export function getRecentTripsCacheKey(userId: string) {
  return `${RECENT_TRIPS_CACHE_PREFIX}${userId}`;
}

export function readRecentTripsCache(cacheKey: string) {
  const rawValue = window.localStorage.getItem(cacheKey);

  if (!rawValue) {
    return [] satisfies TripListItemResponse[];
  }

  try {
    const parsed = JSON.parse(rawValue);

    if (!Array.isArray(parsed)) {
      return [] satisfies TripListItemResponse[];
    }

    return parsed.flatMap((entry) => {
      if (!entry || typeof entry !== "object") {
        return [];
      }

      const candidate = entry as Record<string, unknown>;

      if (
        typeof candidate.trip_id !== "string" ||
        typeof candidate.browser_session_id !== "string" ||
        typeof candidate.thread_id !== "string" ||
        typeof candidate.title !== "string" ||
        candidate.trip_status !== "collecting_requirements" ||
        candidate.thread_status !== "ready" ||
        typeof candidate.created_at !== "string" ||
        typeof candidate.updated_at !== "string"
      ) {
        return [];
      }

      const trip = {
          trip_id: candidate.trip_id,
          browser_session_id: candidate.browser_session_id,
          thread_id: candidate.thread_id,
          title: candidate.title,
          trip_status: "collecting_requirements",
          thread_status: "ready",
          created_at: candidate.created_at,
          updated_at: candidate.updated_at,
          phase:
            typeof candidate.phase === "string" &&
            VALID_CHAT_PHASES.includes(candidate.phase as ChatPlannerPhase)
              ? (candidate.phase as ChatPlannerPhase)
              : null,
          brochure_ready:
            typeof candidate.brochure_ready === "boolean"
              ? candidate.brochure_ready
              : false,
          latest_brochure_snapshot_id:
            typeof candidate.latest_brochure_snapshot_id === "string"
              ? candidate.latest_brochure_snapshot_id
              : null,
          latest_brochure_version:
            typeof candidate.latest_brochure_version === "number"
              ? candidate.latest_brochure_version
              : null,
          brochure_versions_count:
            typeof candidate.brochure_versions_count === "number"
              ? candidate.brochure_versions_count
              : 0,
          from_location:
            typeof candidate.from_location === "string"
              ? candidate.from_location
              : null,
          to_location:
            typeof candidate.to_location === "string"
              ? candidate.to_location
              : null,
          start_date:
            typeof candidate.start_date === "string"
              ? candidate.start_date
              : null,
          end_date:
            typeof candidate.end_date === "string" ? candidate.end_date : null,
          travel_window:
            typeof candidate.travel_window === "string"
              ? candidate.travel_window
              : null,
          trip_length:
            typeof candidate.trip_length === "string"
              ? candidate.trip_length
              : null,
          selected_modules: Array.isArray(candidate.selected_modules)
            ? candidate.selected_modules.filter(
                (value): value is string => typeof value === "string",
              )
            : [],
          timeline_item_count:
            typeof candidate.timeline_item_count === "number"
              ? candidate.timeline_item_count
              : 0,
        } satisfies TripListItemResponse;

      return isMeaningfulRecentTrip(trip) ? [trip] : [];
    });
  } catch {
    return [] satisfies TripListItemResponse[];
  }
}

export function writeRecentTripsCache(
  cacheKey: string,
  trips: TripListItemResponse[],
) {
  window.localStorage.setItem(
    cacheKey,
    JSON.stringify(sortRecentTripsByActivity(filterMeaningfulRecentTrips(trips))),
  );
}

export function filterMeaningfulRecentTrips(trips: TripListItemResponse[]) {
  return trips.filter(isMeaningfulRecentTrip);
}

export function sortRecentTripsByActivity(trips: TripListItemResponse[]) {
  return [...trips].sort(compareRecentTripActivity);
}

export function mergeRecentTripsForSidebarRefresh(
  currentTrips: TripListItemResponse[],
  nextTrips: TripListItemResponse[],
) {
  const filteredNextTrips = filterMeaningfulRecentTrips(nextTrips);

  if (currentTrips.length === 0) {
    return sortRecentTripsByActivity(filteredNextTrips);
  }

  const nextTripById = new Map(
    filteredNextTrips.map((trip) => [trip.trip_id, trip] as const),
  );
  const preservedTrips = currentTrips.flatMap((trip) => {
    const refreshedTrip = nextTripById.get(trip.trip_id);
    return refreshedTrip ? [mergeRecentTripRows(trip, refreshedTrip)] : [];
  });
  const unseenTrips = sortRecentTripsByActivity(
    filteredNextTrips.filter(
      (trip) => !currentTrips.some((currentTrip) => currentTrip.trip_id === trip.trip_id),
    ),
  );

  return [...preservedTrips, ...unseenTrips];
}

function mergeRecentTripRows(
  currentTrip: TripListItemResponse,
  refreshedTrip: TripListItemResponse,
) {
  const currentUpdatedAt = toRecentTripTimestamp(currentTrip.updated_at);
  const refreshedUpdatedAt = toRecentTripTimestamp(refreshedTrip.updated_at);
  const currentCreatedAt = toRecentTripTimestamp(currentTrip.created_at);
  const refreshedCreatedAt = toRecentTripTimestamp(refreshedTrip.created_at);

  return {
    ...currentTrip,
    ...refreshedTrip,
    created_at:
      refreshedCreatedAt >= currentCreatedAt
        ? refreshedTrip.created_at
        : currentTrip.created_at,
    updated_at:
      refreshedUpdatedAt >= currentUpdatedAt
        ? refreshedTrip.updated_at
        : currentTrip.updated_at,
  } satisfies TripListItemResponse;
}

export function isMeaningfulRecentTrip(trip: TripListItemResponse) {
  if (
    trip.trip_id.startsWith("draft_trip_") ||
    trip.browser_session_id.startsWith("draft_browser_session_") ||
    trip.thread_id.startsWith("draft_thread_")
  ) {
    return false;
  }

  return true;
}

function compareRecentTripActivity(
  left: TripListItemResponse,
  right: TripListItemResponse,
) {
  const updatedAtDifference =
    toRecentTripTimestamp(right.updated_at) - toRecentTripTimestamp(left.updated_at);

  if (updatedAtDifference !== 0) {
    return updatedAtDifference;
  }

  const createdAtDifference =
    toRecentTripTimestamp(right.created_at) - toRecentTripTimestamp(left.created_at);

  if (createdAtDifference !== 0) {
    return createdAtDifference;
  }

  return right.trip_id.localeCompare(left.trip_id);
}

function toRecentTripTimestamp(value: string) {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}
