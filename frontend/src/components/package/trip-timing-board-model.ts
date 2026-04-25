"use client";

import type { TripDetailsCollectionFormState } from "@/types/trip-conversation";

export const TIMING_WINDOW_OPTIONS = [
  "This month",
  "Next month",
  "Spring",
  "Summer",
  "Autumn",
  "Winter",
  "Flexible timing",
] as const;

export const TIMING_LENGTH_OPTIONS = [
  "Weekend",
  "3 days",
  "5 days",
  "1 week",
  "10 days",
  "2 weeks",
] as const;

export type TimingChoiceDraft = {
  destination?: string | null;
  travel_window?: string | null;
  trip_length?: string | null;
  start_date?: string | null;
  end_date?: string | null;
};

export function buildInitialTimingChoice(
  form: TripDetailsCollectionFormState | null | undefined,
): TimingChoiceDraft {
  return {
    destination: form?.to_location ?? null,
    travel_window: form?.travel_window ?? null,
    trip_length: form?.trip_length ?? null,
    start_date: form?.start_date ?? null,
    end_date: form?.end_date ?? null,
  };
}

export function canSubmitTimingChoice(choice: TimingChoiceDraft) {
  return hasExactDates(choice) || hasRoughTiming(choice);
}

export function buildTimingChatPrompt(choice: TimingChoiceDraft) {
  const destination = choice.destination?.trim();
  const destinationText = destination ? ` for ${destination}` : "";

  if (hasExactDates(choice)) {
    return `Use exact dates ${choice.start_date} to ${choice.end_date}${destinationText}.`;
  }

  const travelWindow = choice.travel_window?.trim();
  const tripLength = choice.trip_length?.trim();
  if (travelWindow && tripLength) {
    return destination
      ? `Let's do ${destination} ${travelWindow} for ${tripLength}.`
      : `Let's do ${travelWindow} for ${tripLength}.`;
  }

  if (travelWindow) {
    return destination
      ? `Let's keep ${destination} around ${travelWindow}.`
      : `Let's keep the trip around ${travelWindow}.`;
  }

  if (tripLength) {
    return destination
      ? `Let's make ${destination} ${tripLength}.`
      : `Let's make the trip ${tripLength}.`;
  }

  return destination
    ? `Let's keep timing flexible for ${destination} for now.`
    : "Let's keep timing flexible for now.";
}

function hasExactDates(choice: TimingChoiceDraft) {
  return Boolean(choice.start_date && choice.end_date);
}

function hasRoughTiming(choice: TimingChoiceDraft) {
  return Boolean(choice.travel_window?.trim() && choice.trip_length?.trim());
}

export function formatDateForPlanner(date: Date | undefined) {
  if (!date) {
    return null;
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
