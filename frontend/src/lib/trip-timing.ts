type TripTimingLike = {
  start_date: string | null;
  end_date: string | null;
  travel_window?: string | null;
  trip_length?: string | null;
};

type TripTimingOptions = {
  emptyLabel?: string;
  includeYear?: boolean;
};

export function formatTripWindowDisplay(
  timing: TripTimingLike,
  options?: TripTimingOptions,
) {
  const parts = buildTripTimingParts(timing, options);

  if (parts.length === 0) {
    return options?.emptyLabel ?? "Timing open";
  }

  return parts.join(" / ");
}

export function formatTripLengthDisplay(
  timing: TripTimingLike,
  emptyLabel = "open timing",
) {
  const exactLength = formatExactTripLength(timing.start_date, timing.end_date);

  if (exactLength) {
    return exactLength;
  }

  const roughLength = cleanTimingLabel(timing.trip_length);
  if (roughLength) {
    return roughLength;
  }

  return emptyLabel;
}

export function hasTripTiming(timing: TripTimingLike) {
  return buildTripTimingParts(timing).length > 0;
}

function buildTripTimingParts(
  timing: TripTimingLike,
  options?: TripTimingOptions,
) {
  const startLabel = formatTripDate(timing.start_date, options);
  const endLabel = formatTripDate(timing.end_date, options);
  const travelWindow = cleanTimingLabel(timing.travel_window);
  const tripLength = cleanTimingLabel(timing.trip_length);

  if (startLabel && endLabel) {
    return [`${startLabel} - ${endLabel}`];
  }

  return [startLabel ?? travelWindow, endLabel ?? tripLength].filter(
    (value): value is string => Boolean(value),
  );
}

function formatExactTripLength(startDate: string | null, endDate: string | null) {
  if (!startDate || !endDate) {
    return null;
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return null;
  }

  const differenceInDays = Math.max(
    1,
    Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1,
  );

  return `${differenceInDays} days`;
}

function formatTripDate(value: string | null, options?: TripTimingOptions) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    ...(options?.includeYear ? { year: "numeric" } : {}),
    timeZone: "UTC",
  }).format(parsed);
}

function cleanTimingLabel(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  const cleaned = value.trim();
  return cleaned.length > 0 ? cleaned : null;
}
