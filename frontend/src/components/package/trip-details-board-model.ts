"use client";

import type {
  TripDetailsCollectionFormState,
  TripDetailsStepKey,
} from "@/types/trip-conversation";
import type { TripModuleSelection } from "@/types/trip-draft";
import { isTripDetailsTimingComplete } from "@/components/package/trip-details-timing-model";

export const TRIP_DETAILS_STEP_ORDER: TripDetailsStepKey[] = [
  "modules",
  "route",
  "timing",
  "travellers",
  "vibe",
  "budget",
];

export function getActiveModules(selectedModules: TripModuleSelection) {
  return Object.entries(selectedModules)
    .filter(([, enabled]) => enabled)
    .map(([moduleName]) => moduleName as keyof TripModuleSelection);
}

export function getVisibleSteps(
  form: TripDetailsCollectionFormState,
): TripDetailsStepKey[] {
  const activeModules = getActiveModules(form.selected_modules);
  const hasFlights = activeModules.includes("flights");
  const hasHotels = activeModules.includes("hotels");
  const hasActivities = activeModules.includes("activities");

  const visibleSteps: TripDetailsStepKey[] = ["modules", "route", "timing"];

  if (hasFlights || hasHotels || hasActivities) {
    visibleSteps.push("travellers");
  }

  if (hasActivities) {
    visibleSteps.push("vibe");
  }

  if (hasFlights || hasHotels) {
    visibleSteps.push("budget");
  }

  return visibleSteps;
}

export function getRequiredSteps(
  form: TripDetailsCollectionFormState,
): TripDetailsStepKey[] {
  const activeModules = getActiveModules(form.selected_modules);
  const hasFlights = activeModules.includes("flights");
  const hasHotels = activeModules.includes("hotels");
  const hasActivities = activeModules.includes("activities");

  const requiredSteps: TripDetailsStepKey[] = ["modules", "route", "timing"];

  if (hasFlights || hasHotels || hasActivities) {
    requiredSteps.push("travellers");
  }

  if (hasActivities) {
    requiredSteps.push("vibe");
  }

  if (hasFlights || hasHotels) {
    requiredSteps.push("budget");
  }

  return requiredSteps;
}

export function isStepRequired(
  step: TripDetailsStepKey,
  form: TripDetailsCollectionFormState,
) {
  return getRequiredSteps(form).includes(step);
}

export function isStepComplete(
  step: TripDetailsStepKey,
  form: TripDetailsCollectionFormState,
) {
  const activeModules = getActiveModules(form.selected_modules);
  const flightsActive = activeModules.includes("flights");

  if (step === "modules") {
    return activeModules.length > 0;
  }

  if (step === "route") {
    const hasDestination = Boolean(form.to_location?.trim());
    if (!hasDestination) {
      return false;
    }
    if (!flightsActive) {
      return true;
    }
    return Boolean(form.from_location?.trim() || form.from_location_flexible);
  }

  if (step === "timing") {
    return isTripDetailsTimingComplete(form);
  }

  if (step === "travellers") {
    if (!isStepRequired(step, form)) {
      return true;
    }
    return (form.adults ?? 0) > 0 || Boolean(form.travelers_flexible);
  }

  if (step === "vibe") {
    if (!isStepRequired(step, form)) {
      return true;
    }
    return form.activity_styles.length > 0 || Boolean(form.custom_style?.trim());
  }

  if (step === "budget") {
    if (!isStepRequired(step, form)) {
      return true;
    }
    const amount = form.budget_amount ?? form.budget_gbp ?? null;
    return Boolean(
      form.budget_posture ||
        (amount !== null && amount !== undefined && amount > 0),
    );
  }

  return false;
}

export function getFirstIncompleteStep(
  form: TripDetailsCollectionFormState,
): TripDetailsStepKey {
  const visibleSteps = getVisibleSteps(form);
  return visibleSteps.find((step) => !isStepComplete(step, form)) ?? "modules";
}

export function getNextVisibleStep(
  currentStep: TripDetailsStepKey,
  form: TripDetailsCollectionFormState,
): TripDetailsStepKey | null {
  const visibleSteps = getVisibleSteps(form);
  const currentIndex = visibleSteps.indexOf(currentStep);
  if (currentIndex === -1 || currentIndex === visibleSteps.length - 1) {
    return null;
  }
  return visibleSteps[currentIndex + 1] ?? null;
}

export function canConfirmTripDetails(
  form: TripDetailsCollectionFormState,
): boolean {
  return getRequiredSteps(form).every((step) => isStepComplete(step, form));
}

export function buildFocusNote(activeModules: Array<keyof TripModuleSelection>) {
  if (activeModules.length === 0) {
    return "Pick at least one part of the trip to plan before you confirm.";
  }
  if (activeModules.length === 1 && activeModules[0] === "activities") {
    return "This keeps the board centered on destination, timing, travellers, and trip style. Departure stays in the background unless you add flights later.";
  }
  if (activeModules.length === 1 && activeModules[0] === "weather") {
    return "This keeps the board focused on destination and timing so Wandrix can shape the weather view cleanly.";
  }
  if (activeModules.length === 1 && activeModules[0] === "flights") {
    return "This keeps the next step flight-first, so route, timing, travellers, and budget matter most.";
  }
  if (activeModules.length === 1 && activeModules[0] === "hotels") {
    return "This keeps the next step hotel-first, so destination, timing, travellers, and budget stay in focus.";
  }
  return "Leave the full scope on if you want Wandrix to shape flights, stays, activities, and weather together.";
}
