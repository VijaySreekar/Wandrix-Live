"use client";

import type {
  TripDetailsFieldMeta,
  TripDetailsStepKey,
  TripFieldKey,
} from "@/types/trip-conversation";

const STEP_FIELD_PRIORITY: Record<TripDetailsStepKey, TripFieldKey[]> = {
  modules: ["selected_modules"],
  route: ["to_location", "from_location", "from_location_flexible"],
  timing: [
    "travel_window",
    "start_date",
    "trip_length",
    "end_date",
    "weather_preference",
  ],
  travellers: ["adults", "children", "travelers_flexible"],
  vibe: ["activity_styles", "custom_style"],
  budget: ["budget_currency", "budget_amount", "budget_gbp", "budget_posture"],
};

export function getTripDetailsStepMeta(
  detailsFieldMeta:
    | Partial<Record<TripFieldKey, TripDetailsFieldMeta>>
    | null
    | undefined,
  step: TripDetailsStepKey,
) {
  if (!detailsFieldMeta) {
    return null;
  }
  for (const field of STEP_FIELD_PRIORITY[step]) {
    const meta = detailsFieldMeta[field];
    if (meta?.label) {
      return meta;
    }
  }
  return null;
}

export function TripDetailsFieldSourceLabel({
  meta,
}: {
  meta?: TripDetailsFieldMeta | null;
}) {
  if (!meta?.label) {
    return null;
  }

  return (
    <span className="inline-flex shrink-0 items-center rounded-md border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--planner-board-muted-strong)]">
      {meta.label}
    </span>
  );
}
