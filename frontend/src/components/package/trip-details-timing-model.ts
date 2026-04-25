import type { TripDetailsCollectionFormState } from "@/types/trip-conversation";

export function isTripDetailsTimingComplete(
  form: TripDetailsCollectionFormState,
) {
  const hasWindow = Boolean(form.travel_window?.trim());
  const hasLength = Boolean(form.trip_length?.trim());
  const hasExactDates = Boolean(form.start_date && form.end_date);
  if (!hasDetailedTimingRequirement(form)) {
    return hasAnyTimingSignal(form);
  }
  return hasExactDates || (hasWindow && hasLength);
}

export function getTripDetailsTimingSummary(
  form: TripDetailsCollectionFormState,
) {
  if (form.start_date && form.end_date) {
    return [
      `${form.start_date} to ${form.end_date}`,
      form.weather_preference ? capitalizeLabel(form.weather_preference) : null,
    ]
      .filter(Boolean)
      .join(" / ");
  }

  const parts = [
    form.travel_window,
    form.trip_length,
    form.weather_preference ? capitalizeLabel(form.weather_preference) : null,
  ].filter(Boolean);
  return parts.length ? parts.join(" / ") : "Add rough timing or exact dates.";
}

function hasDetailedTimingRequirement(form: TripDetailsCollectionFormState) {
  return form.selected_modules.flights || form.selected_modules.hotels;
}

function hasAnyTimingSignal(form: TripDetailsCollectionFormState) {
  return Boolean(
    form.travel_window?.trim() ||
      form.trip_length?.trim() ||
      form.start_date ||
      form.end_date,
  );
}

function capitalizeLabel(value: string) {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
