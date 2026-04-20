"use client";

import { useMemo, useState } from "react";

import {
  TripDetailsFooter,
  TripDetailsStepper,
  getFirstIncompleteStep,
  type TripDetailsStepKey,
} from "@/components/package/trip-details-board-sections";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  ChatPlannerPhase,
  TripDetailsCollectionFormState,
  TripSuggestionBoardState,
} from "@/types/trip-conversation";
import type { TripModuleSelection } from "@/types/trip-draft";

type TripDetailsBoardProps = {
  accessToken?: string;
  board: TripSuggestionBoardState;
  phase: ChatPlannerPhase;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
};

const EMPTY_FORM: TripDetailsCollectionFormState = {
  from_location: null,
  to_location: null,
  selected_modules: {
    flights: true,
    hotels: true,
    activities: true,
    weather: true,
  },
  travel_window: null,
  trip_length: null,
  start_date: null,
  end_date: null,
  adults: 1,
  children: 0,
  activity_styles: [],
  custom_style: null,
  budget_posture: null,
  budget_gbp: null,
};

export function TripDetailsBoard({
  accessToken,
  board,
  phase,
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
      phase={phase}
    />
  );
}

function TripDetailsBoardContent({
  accessToken,
  board,
  disabled,
  initialForm,
  onAction,
  phase,
}: TripDetailsBoardProps & {
  initialForm: TripDetailsCollectionFormState;
}) {
  const [form, setForm] = useState<TripDetailsCollectionFormState>(initialForm);
  const [activeStep, setActiveStep] = useState<TripDetailsStepKey>(
    getFirstIncompleteStep(initialForm),
  );

  const activeModules = useMemo(
    () =>
      Object.entries(form.selected_modules)
        .filter(([, enabled]) => enabled)
        .map(([moduleName]) => moduleName as keyof TripModuleSelection),
    [form.selected_modules],
  );

  const focusNote = buildFocusNote(activeModules);

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
            activeStep={activeStep}
            disabled={disabled}
            focusNote={focusNote}
            form={form}
            onActiveStepChange={setActiveStep}
            onAdultsChange={(value) =>
              setForm((current) => ({
                ...current,
                adults: value,
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
                children: value,
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
              disabled={disabled}
              onConfirm={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type:
                    phase === "awaiting_confirmation"
                      ? "confirm_trip_brief"
                      : "confirm_trip_details",
                  from_location: form.from_location ?? null,
                  to_location: form.to_location ?? null,
                  selected_modules: form.selected_modules,
                  travel_window: form.travel_window ?? null,
                  trip_length: form.trip_length ?? null,
                  start_date: form.start_date ?? null,
                  end_date: form.end_date ?? null,
                  adults: form.adults ?? null,
                  children: form.children ?? null,
                  activity_styles: form.activity_styles,
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

function buildFocusNote(activeModules: Array<keyof TripModuleSelection>) {
  if (activeModules.length === 0) {
    return "If everything is turned off, Wandrix will have very little to shape. Keep at least one module active before confirming.";
  }
  if (activeModules.length === 1 && activeModules[0] === "activities") {
    return "This keeps the trip centered on activities. Origin stays in the background unless you later expand back into flights.";
  }
  if (activeModules.length === 1 && activeModules[0] === "weather") {
    return "This keeps the flow weather-first. Rough timing is enough to move forward cleanly from here.";
  }
  if (activeModules.length === 1 && activeModules[0] === "flights") {
    return "This keeps the flow flight-first. Timing and traveller count will matter most right after confirmation.";
  }
  if (activeModules.length === 1 && activeModules[0] === "hotels") {
    return "This keeps the flow hotel-first. Stay timing and traveller count will do most of the work next.";
  }
  return "Leave the full scope on if you want Wandrix to shape flights, stays, activities, and weather together.";
}
