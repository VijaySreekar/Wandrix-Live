"use client";

import { useMemo, useState } from "react";

import {
  TripDetailsFooter,
  TripDetailsStepper,
} from "@/components/package/trip-details-board-sections";
import {
  buildFocusNote,
  canConfirmTripDetails,
  getActiveModules,
  getFirstIncompleteStep,
  getVisibleSteps,
} from "@/components/package/trip-details-board-model";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  TripDetailsStepKey,
  TripDetailsCollectionFormState,
  TripSuggestionBoardState,
} from "@/types/trip-conversation";

type TripDetailsBoardProps = {
  accessToken?: string;
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
};

const EMPTY_FORM: TripDetailsCollectionFormState = {
  from_location: null,
  from_location_flexible: null,
  to_location: null,
  selected_modules: {
    flights: true,
    hotels: true,
    activities: true,
    weather: true,
  },
  travel_window: null,
  trip_length: null,
  weather_preference: null,
  start_date: null,
  end_date: null,
  adults: null,
  children: null,
  travelers_flexible: null,
  activity_styles: [],
  custom_style: null,
  budget_posture: null,
  budget_gbp: null,
};

export function TripDetailsBoard({
  accessToken,
  board,
  disabled,
  onAction,
}: TripDetailsBoardProps) {
  const initialForm = useMemo(
    () => normalizeForm(board.details_form),
    [board.details_form],
  );
  const formKey = useMemo(() => JSON.stringify(initialForm), [initialForm]);

  return (
    <TripDetailsBoardContent
      accessToken={accessToken}
      key={formKey}
      board={board}
      disabled={disabled}
      initialForm={initialForm}
      onAction={onAction}
    />
  );
}

function TripDetailsBoardContent({
  accessToken,
  board,
  disabled,
  initialForm,
  onAction,
}: TripDetailsBoardProps & {
  initialForm: TripDetailsCollectionFormState;
}) {
  const [form, setForm] = useState<TripDetailsCollectionFormState>(initialForm);
  const [activeStep, setActiveStep] = useState<TripDetailsStepKey>(
    getFirstIncompleteStep(initialForm),
  );
  const activeModules = useMemo(
    () => getActiveModules(form.selected_modules),
    [form.selected_modules],
  );
  const visibleSteps = useMemo(() => getVisibleSteps(form), [form]);
  const resolvedActiveStep = visibleSteps.includes(activeStep)
    ? activeStep
    : (visibleSteps[0] ?? "modules");

  const focusNote = buildFocusNote(activeModules);
  const canConfirm = canConfirmTripDetails(form);

  return (
    <section className="flex h-full min-h-0 flex-col bg-[var(--planner-board-bg)] px-8 pb-10 pt-8">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl">
          <header className="pb-8">
            <h2 className="font-display text-[2rem] font-bold tracking-tight text-[var(--planner-board-title)]">
              {board.title || "Trip details"}
            </h2>
            <p className="mt-2 max-w-2xl text-base leading-relaxed text-[var(--planner-board-muted)]">
              {board.subtitle ||
                "Move through the key trip details step by step, or keep sending them naturally in chat."}
            </p>
          </header>

          <TripDetailsStepper
            accessToken={accessToken}
            activeStep={resolvedActiveStep}
            disabled={disabled}
            focusNote={focusNote}
            form={form}
            visibleSteps={visibleSteps}
            onActiveStepChange={setActiveStep}
            onAdultsChange={(value) =>
              setForm((current) => ({
                ...current,
                adults: value && value > 0 ? value : null,
              }))
            }
            onBudgetAmountChange={(value) =>
              setForm((current) => ({
                ...current,
                budget_gbp: value,
              }))
            }
            onBudgetPostureToggle={(posture) =>
              setForm((current) => ({
                ...current,
                budget_posture:
                  current.budget_posture === posture ? null : posture,
              }))
            }
            onChildrenChange={(value) =>
              setForm((current) => ({
                ...current,
                children: value && value > 0 ? value : null,
              }))
            }
            onTravelersFlexibleToggle={() =>
              setForm((current) => ({
                ...current,
                travelers_flexible: !current.travelers_flexible,
              }))
            }
            onOriginFlexibleToggle={() =>
              setForm((current) => ({
                ...current,
                from_location_flexible: !current.from_location_flexible,
              }))
            }
            onFieldChange={(field, value) =>
              setForm((current) => ({
                ...current,
                [field]: value,
              }))
            }
            onModuleToggle={(moduleName) =>
              setForm((current) => ({
                ...current,
                selected_modules: {
                  ...current.selected_modules,
                  [moduleName]: !current.selected_modules[moduleName],
                },
              }))
            }
            onStyleToggle={(style) =>
              setForm((current) => ({
                ...current,
                activity_styles: current.activity_styles.includes(style)
                  ? current.activity_styles.filter((item) => item !== style)
                  : [...current.activity_styles, style],
              }))
            }
          />

          <div className="mt-8">
            <TripDetailsFooter
              ctaLabel={board.confirm_cta_label || "Confirm trip details"}
              disabled={disabled || !canConfirm}
              onConfirm={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "confirm_trip_details",
                  from_location: form.from_location ?? null,
                  from_location_flexible: form.from_location_flexible ?? null,
                  to_location: form.to_location ?? null,
                  selected_modules: form.selected_modules,
                  travel_window: form.travel_window ?? null,
                  trip_length: form.trip_length ?? null,
                  weather_preference: form.weather_preference ?? null,
                  start_date: form.start_date ?? null,
                  end_date: form.end_date ?? null,
                  adults:
                    form.adults !== null &&
                    form.adults !== undefined &&
                    form.adults > 0
                      ? form.adults
                      : null,
                  children:
                    form.children !== null &&
                    form.children !== undefined &&
                    form.children > 0
                      ? form.children
                      : null,
                  travelers_flexible: form.travelers_flexible ?? null,
                  activity_styles: form.activity_styles,
                  custom_style: form.custom_style ?? null,
                  budget_posture: form.budget_posture ?? null,
                  budget_gbp: form.budget_gbp ?? null,
                })
              }
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function normalizeForm(
  form: TripDetailsCollectionFormState | null | undefined,
): TripDetailsCollectionFormState {
  return {
    ...EMPTY_FORM,
    ...form,
    adults: form?.adults ?? EMPTY_FORM.adults,
    children: form?.children ?? EMPTY_FORM.children,
    selected_modules: {
      ...EMPTY_FORM.selected_modules,
      ...(form?.selected_modules ?? {}),
    },
    activity_styles: form?.activity_styles ?? [],
  };
}
