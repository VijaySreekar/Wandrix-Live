import type { TripListItemResponse } from "@/types/trip";
import type { ChatPlannerPhase } from "@/types/trip-conversation";

const RECENT_TRIPS_CACHE_PREFIX = "wandrix:recent-trips:";
const VALID_CHAT_PHASES: ChatPlannerPhase[] = [
  "opening",
  "collecting_requirements",
  "shaping_trip",
  "enriching_modules",
  "reviewing",
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

      return shouldKeepRecentTrip(trip) ? [trip] : [];
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
    JSON.stringify(trips.filter(shouldKeepRecentTrip)),
  );
}

function shouldKeepRecentTrip(trip: TripListItemResponse) {
  const hasTripSignal = Boolean(
    trip.from_location ||
      trip.to_location ||
      trip.start_date ||
      trip.end_date ||
      trip.travel_window ||
      trip.trip_length ||
      trip.selected_modules.length > 0 ||
      trip.timeline_item_count > 0 ||
      trip.brochure_ready,
  );

  if (hasTripSignal) {
    return true;
  }

  const normalizedTitle = trip.title.trim().toLowerCase();
  const looksGeneric =
    normalizedTitle === "trip planner" || /^trip [0-9a-f]{6}$/i.test(trip.title.trim());

  return !(
    looksGeneric &&
    trip.phase === "opening" &&
    trip.created_at === trip.updated_at
  );
}
