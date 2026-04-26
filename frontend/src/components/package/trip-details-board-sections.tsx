"use client";

import type { ReactNode } from "react";
import {
  Baby,
  CalendarRange,
  CheckCircle2,
  ChevronDown,
  Cloud,
  Compass,
  Heart,
  Hotel,
  MapPinned,
  Minus,
  Mountain,
  Palmtree,
  Plane,
  Plus,
  Sparkles,
  UsersRound,
  UtensilsCrossed,
  Wine,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import {
  getNextVisibleStep,
  getRequiredSteps,
  isStepComplete,
} from "@/components/package/trip-details-board-model";
import { TripDetailsBudgetSection } from "@/components/package/trip-details-budget-section";
import {
  getTripDetailsStepMeta,
  TripDetailsFieldSourceLabel,
} from "@/components/package/trip-details-field-meta";
import { RouteLocationInput } from "@/components/package/route-location-input";
import { getTripDetailsTimingSummary } from "@/components/package/trip-details-timing-model";
import { TripDetailsTimingSection } from "@/components/package/trip-details-timing-section";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type {
  TripDetailsCollectionFormState,
  TripDetailsFieldMeta,
  TripDetailsStepKey,
  TripFieldKey,
} from "@/types/trip-conversation";
import type {
  ActivityStyle,
  BudgetPosture,
  TripModuleSelection,
} from "@/types/trip-draft";

type TripDetailsStepperProps = {
  accessToken?: string;
  activeStep: TripDetailsStepKey;
  disabled: boolean;
  focusNote: string;
  form: TripDetailsCollectionFormState;
  visibleSteps: TripDetailsStepKey[];
  detailsFieldMeta?: Partial<Record<TripFieldKey, TripDetailsFieldMeta>>;
  onActiveStepChange: (step: TripDetailsStepKey) => void;
  onAdultsChange: (value: number | null) => void;
  onBudgetAmountChange: (value: number | null) => void;
  onBudgetCurrencyChange: (value: string | null) => void;
  onBudgetPostureToggle: (posture: BudgetPosture) => void;
  onChildrenChange: (value: number | null) => void;
  onOriginFlexibleToggle: () => void;
  onTravelersFlexibleToggle: () => void;
  onFieldChange: (
    field:
      | "from_location"
      | "to_location"
      | "travel_window"
      | "trip_length"
      | "weather_preference"
      | "start_date"
      | "end_date"
      | "custom_style",
    value: string | null,
  ) => void;
  onModuleToggle: (moduleName: keyof TripModuleSelection) => void;
  onStyleToggle: (style: ActivityStyle) => void;
};

type TripDetailsFooterProps = {
  ctaLabel: string;
  disabled: boolean;
  onConfirm: () => void;
};

type StepCardProps = {
  children: ReactNode;
  disabled: boolean;
  isComplete: boolean;
  isOpen: boolean;
  isRequired: boolean;
  fieldMeta?: TripDetailsFieldMeta | null;
  stepNumber: number;
  summary: string | null;
  title: string;
  onToggle: () => void;
};

type ChoiceButtonProps = {
  children: ReactNode;
  disabled: boolean;
  selected: boolean;
  onClick: () => void;
};

type StepActionsProps = {
  disabled: boolean;
  nextLabel: string | null;
  onNext?: () => void;
};

type TravellerCardProps = {
  accent: "primary" | "secondary";
  description: string;
  disabled: boolean;
  label: string;
  onDecrement: () => void;
  onIncrement: () => void;
  value: number;
};

const STEP_TITLES: Record<TripDetailsStepKey, string> = {
  modules: "Trip modules",
  route: "Route",
  timing: "Timing",
  travellers: "Travellers",
  vibe: "Trip style",
  budget: "Budget",
};

const STYLE_OPTIONS: ActivityStyle[] = [
  "food",
  "culture",
  "relaxed",
  "luxury",
  "romantic",
  "family",
  "adventure",
  "outdoors",
];

const MODULE_ORDER: Array<keyof TripModuleSelection> = [
  "flights",
  "hotels",
  "activities",
  "weather",
];

export function TripDetailsStepper({
  accessToken,
  activeStep,
  disabled,
  focusNote,
  form,
  visibleSteps,
  detailsFieldMeta,
  onActiveStepChange,
  onAdultsChange,
  onBudgetAmountChange,
  onBudgetCurrencyChange,
  onBudgetPostureToggle,
  onChildrenChange,
  onOriginFlexibleToggle,
  onTravelersFlexibleToggle,
  onFieldChange,
  onModuleToggle,
  onStyleToggle,
}: TripDetailsStepperProps) {
  const requiredSteps = getRequiredSteps(form);
  const flightsActive = form.selected_modules.flights;

  return (
    <div className="space-y-3">
      {visibleSteps.map((step, index) => {
        const complete = isStepComplete(step, form);
        const isOpen = activeStep === step;
        const isRequired = requiredSteps.includes(step);
        const nextStep = getNextVisibleStep(step, form);
        const fieldMeta = getTripDetailsStepMeta(detailsFieldMeta, step);

        return (
          <StepCard
            key={step}
            disabled={disabled}
            isComplete={complete}
            isOpen={isOpen}
            isRequired={isRequired}
            fieldMeta={fieldMeta}
            stepNumber={index + 1}
            summary={getStepSummary(step, form)}
            title={STEP_TITLES[step]}
            onToggle={() => onActiveStepChange(step)}
          >
            {step === "modules" ? (
              <div className="space-y-5">
                <StepIntro>
                  Choose what you want Wandrix to actively plan right now. Nothing here is mandatory. Full trip is just the default, and you can switch anything off if you only need a focused pass.
                </StepIntro>
                <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]/55 px-4 py-3">
                  <p className="text-sm font-medium text-[var(--planner-board-text)]">
                    How this works
                  </p>
                  <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
                    Keep all four on for a full trip. If you only want part of the plan, turn on just those modules and the rest of the board will simplify around them.
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {MODULE_ORDER.map((moduleName) => {
                    const config = getModuleConfig(moduleName);
                    const selected = form.selected_modules[moduleName];
                    return (
                      <button
                        key={moduleName}
                        type="button"
                        disabled={disabled}
                        onClick={() => onModuleToggle(moduleName)}
                        className={cn(
                          "flex items-start gap-4 rounded-xl border px-4 py-4 text-left transition-colors duration-150",
                          selected
                            ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5"
                            : "border-[var(--planner-board-border)] bg-white hover:border-[var(--planner-board-cta)]",
                          disabled && "cursor-not-allowed opacity-50",
                        )}
                      >
                        <div
                          className={cn(
                            "mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-full",
                            selected
                              ? "bg-[var(--planner-board-cta)] text-white"
                              : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
                          )}
                        >
                          {config.icon}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-3">
                            <h4 className="font-medium text-[var(--planner-board-text)]">
                              {config.label}
                            </h4>
                            {selected ? (
                              <CheckCircle2 className="size-4 shrink-0 text-[var(--planner-board-cta)]" />
                            ) : null}
                          </div>
                          <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
                            {config.description}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
                <p className="text-sm leading-7 text-[var(--planner-board-muted)]">
                  {focusNote}
                </p>
                <StepActions
                  disabled={disabled || !complete}
                  nextLabel={
                    nextStep
                      ? `Continue to ${STEP_TITLES[nextStep].toLowerCase()}`
                      : null
                  }
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {step === "route" ? (
              <div className="space-y-5">
                <StepIntro>
                  {flightsActive
                    ? form.from_location_flexible
                      ? "Keep the destination clear and leave departure flexible for now if you are not ready to lock the route yet."
                      : "Lock the route you want to plan around. Departure and destination both matter once flights are in scope."
                    : "Keep the destination clear. Departure can stay in the background until you add flights back in."}
                </StepIntro>
                <div className={cn("grid gap-4", flightsActive && "sm:grid-cols-2")}>
                  {flightsActive ? (
                    <RouteLocationInput
                      accessToken={accessToken}
                      disabled={disabled}
                      kind="origin"
                      label="From"
                      placeholder="London or Heathrow"
                      value={form.from_location ?? ""}
                      onChange={(value) => onFieldChange("from_location", value)}
                    />
                  ) : null}
                  <RouteLocationInput
                    accessToken={accessToken}
                    disabled={disabled}
                    kind="destination"
                    label={flightsActive ? "To" : "Destination"}
                    placeholder="Marrakech or Kyoto"
                    value={form.to_location ?? ""}
                    onChange={(value) => onFieldChange("to_location", value)}
                    />
                  {!flightsActive ? (
                    <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]/55 p-4">
                      <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                        Departure point
                      </Label>
                      <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                        Optional for the current scope. If you bring flights back in later, Wandrix will surface this again.
                      </p>
                    </div>
                  ) : null}
                  {flightsActive ? (
                    <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]/55 p-4 sm:col-span-2">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                            Departure still flexible
                          </Label>
                          <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                            Keep this on if you want Wandrix to continue building the brief without locking the exact departure city yet.
                          </p>
                        </div>
                        <ChoiceButton
                          disabled={disabled}
                          selected={Boolean(form.from_location_flexible)}
                          onClick={onOriginFlexibleToggle}
                        >
                          {form.from_location_flexible
                            ? "Flexible for now"
                            : "Mark flexible"}
                        </ChoiceButton>
                      </div>
                    </div>
                  ) : null}
                  {flightsActive && form.from_location_flexible ? (
                    <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]/55 p-4 sm:col-span-2">
                      <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                        Departure point
                      </Label>
                      <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                        Wandrix has this marked as flexible for now, so you can
                        keep building the brief without locking a departure city
                        yet. If you add one here, later flight comparisons can
                        become more precise.
                      </p>
                    </div>
                  ) : null}
                </div>
                <StepActions
                  disabled={disabled || !complete}
                  nextLabel={
                    nextStep
                      ? `Continue to ${STEP_TITLES[nextStep].toLowerCase()}`
                      : null
                  }
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {step === "timing" ? (
              <div className="space-y-6">
                <TripDetailsTimingSection
                  disabled={disabled}
                  form={form}
                  onFieldChange={onFieldChange}
                />
                <StepActions
                  disabled={disabled || !complete}
                  nextLabel={
                    nextStep
                      ? `Continue to ${STEP_TITLES[nextStep].toLowerCase()}`
                      : null
                  }
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {step === "travellers" ? (
              <div className="space-y-5">
                <StepIntro>
                  Tell Wandrix who the trip is for. If the exact headcount is still moving around, you can keep it flexible for now and firm it up later.
                </StepIntro>
                <div className="grid gap-4 sm:grid-cols-2">
                  <TravellerCard
                    accent="primary"
                    description="18 years and older"
                    disabled={disabled}
                    label="Adults"
                    onDecrement={() => onAdultsChange(Math.max(0, (form.adults ?? 0) - 1))}
                    onIncrement={() => onAdultsChange((form.adults ?? 0) + 1)}
                    value={form.adults ?? 0}
                  />
                  <TravellerCard
                    accent="secondary"
                    description="Under 18 years"
                    disabled={disabled}
                    label="Children"
                    onDecrement={() =>
                      onChildrenChange(Math.max(0, (form.children ?? 0) - 1))
                    }
                    onIncrement={() => onChildrenChange((form.children ?? 0) + 1)}
                    value={form.children ?? 0}
                  />
                </div>
                <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]/55 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                        Traveller count still flexible
                      </Label>
                      <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                        Use this if you roughly know the trip shape but the final
                        headcount is not locked yet.
                      </p>
                    </div>
                    <ChoiceButton
                      disabled={disabled}
                      selected={Boolean(form.travelers_flexible)}
                      onClick={onTravelersFlexibleToggle}
                    >
                      {form.travelers_flexible ? "Flexible for now" : "Mark flexible"}
                    </ChoiceButton>
                  </div>
                </div>
                <StepActions
                  disabled={disabled || !complete}
                  nextLabel={
                    nextStep
                      ? `Continue to ${STEP_TITLES[nextStep].toLowerCase()}`
                      : null
                  }
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {step === "vibe" ? (
              <div className="space-y-5">
                <StepIntro>
                  Choose the trip mood you want Wandrix to optimize around. Pick more than one if the plan has mixed priorities.
                </StepIntro>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {STYLE_OPTIONS.map((style) => {
                    const config = getStyleConfig(style);
                    const isSelected = form.activity_styles.includes(style);
                    return (
                      <button
                        key={style}
                        type="button"
                        disabled={disabled}
                        onClick={() => onStyleToggle(style)}
                        className={cn(
                          "relative flex flex-col items-center gap-3 rounded-xl border px-4 py-4 text-center transition-colors duration-150",
                          isSelected
                            ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5"
                            : "border-[var(--planner-board-border)] bg-white hover:border-[var(--planner-board-cta)]",
                          disabled && "cursor-not-allowed opacity-50",
                        )}
                      >
                        <div
                          className={cn(
                            "flex size-11 items-center justify-center rounded-full",
                            isSelected
                              ? "bg-[var(--planner-board-cta)] text-white"
                              : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
                          )}
                        >
                          {config.icon}
                        </div>
                        <span className="text-sm font-medium text-[var(--planner-board-text)]">
                          {config.label}
                        </span>
                        {isSelected ? (
                          <CheckCircle2 className="absolute right-2 top-2 size-4 text-[var(--planner-board-cta)]" />
                        ) : null}
                      </button>
                    );
                  })}
                </div>
                <div className="space-y-3 border-t border-[var(--planner-board-border)] pt-5">
                  <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                    Or describe your own style
                  </Label>
                  <Input
                    disabled={disabled}
                    placeholder="e.g. photography-focused, wellness retreat, nightlife"
                    value={form.custom_style ?? ""}
                    onChange={(event) =>
                      onFieldChange("custom_style", event.target.value || null)
                    }
                    className="h-11 rounded-lg border-[var(--planner-board-border)] bg-white/50 transition-colors duration-150 focus:border-[var(--planner-board-cta)]"
                  />
                </div>
                <StepActions
                  disabled={disabled || !complete}
                  nextLabel={
                    nextStep
                      ? `Continue to ${STEP_TITLES[nextStep].toLowerCase()}`
                      : null
                  }
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {step === "budget" ? (
              <TripDetailsBudgetSection
                actions={
                  <StepActions disabled={disabled || !complete} nextLabel={null} />
                }
                disabled={disabled}
                form={form}
                onBudgetAmountChange={onBudgetAmountChange}
                onBudgetCurrencyChange={onBudgetCurrencyChange}
                onBudgetPostureToggle={onBudgetPostureToggle}
              />
            ) : null}
          </StepCard>
        );
      })}
    </div>
  );
}

export function TripDetailsFooter({
  ctaLabel,
  disabled,
  onConfirm,
}: TripDetailsFooterProps) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--planner-board-border)] bg-white px-5 py-4">
      <div>
        <p className="text-sm font-medium text-[var(--planner-board-text)]">
          Confirm the trip details
        </p>
        <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
          This sends one structured update back into chat and lets Wandrix move forward from the confirmed brief.
        </p>
      </div>
      <Button
        type="button"
        disabled={disabled}
        className="h-11 rounded-lg bg-[var(--planner-board-cta)] px-5 text-sm font-medium text-white hover:bg-[var(--planner-board-cta)]/90"
        onClick={onConfirm}
      >
        {ctaLabel}
      </Button>
    </div>
  );
}

function StepCard({
  children,
  disabled,
  fieldMeta,
  isComplete,
  isOpen,
  isRequired,
  stepNumber,
  summary,
  title,
  onToggle,
}: StepCardProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      layout={!reduceMotion}
      className={cn(
        "overflow-hidden rounded-2xl border transition-colors duration-150",
        isOpen
          ? "border-[var(--planner-board-cta)] bg-white"
          : "border-[var(--planner-board-border)] bg-white",
      )}
      transition={{
        layout: {
          duration: reduceMotion ? 0.01 : 0.34,
          ease: [0.16, 1, 0.3, 1],
        },
      }}
    >
      <button
        type="button"
        disabled={disabled}
        onClick={onToggle}
        className={cn(
          "flex w-full items-start gap-4 px-5 py-4 text-left transition-colors duration-150",
          !disabled && !isOpen && "hover:bg-[var(--planner-board-soft)]/45",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        <div
          className={cn(
            "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold",
            isComplete
              ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)] text-white"
              : "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
          )}
        >
          {isComplete ? <CheckCircle2 className="size-4" /> : stepNumber}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-medium text-[var(--planner-board-text)]">
              {title}
            </h3>
            {!isRequired ? (
              <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-0.5 text-[11px] font-medium text-[var(--planner-board-muted-strong)]">
                Optional
              </span>
            ) : null}
          </div>
          {summary ? (
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <p className="text-sm leading-6 text-[var(--planner-board-muted)]">
                {summary}
              </p>
              <TripDetailsFieldSourceLabel meta={fieldMeta} />
            </div>
          ) : null}
        </div>
        <ChevronDown
          className={cn(
            "mt-1 size-4 shrink-0 text-[var(--planner-board-muted)] transition-transform duration-150",
            isOpen && "rotate-180",
          )}
        />
      </button>
      <AnimatePresence initial={false}>
        {isOpen ? (
          <motion.div
            key="step-content"
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
            animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -6 }}
            transition={{
              duration: reduceMotion ? 0.01 : 0.22,
              ease: [0.16, 1, 0.3, 1],
            }}
            className="border-t border-[var(--planner-board-border)] px-5 pb-5 pt-5"
          >
            {children}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.section>
  );
}

function StepIntro({ children }: { children: ReactNode }) {
  return (
    <p className="text-sm leading-7 text-[var(--planner-board-muted)]">
      {children}
    </p>
  );
}

function StepActions({ disabled, nextLabel, onNext }: StepActionsProps) {
  if (!nextLabel || !onNext) {
    return null;
  }

  return (
    <div className="flex justify-end border-t border-[var(--planner-board-border)] pt-5">
      <Button
        type="button"
        variant="outline"
        disabled={disabled}
        className="h-10 rounded-lg border-[var(--planner-board-border)] px-4 text-sm"
        onClick={onNext}
      >
        {nextLabel}
      </Button>
    </div>
  );
}

function ChoiceButton({
  children,
  disabled,
  selected,
  onClick,
}: ChoiceButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors duration-150",
        selected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5 text-[var(--planner-board-text)]"
          : "border-[var(--planner-board-border)] bg-white text-[var(--planner-board-muted-strong)] hover:border-[var(--planner-board-cta)]",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      {children}
    </button>
  );
}

function TravellerCard({
  accent,
  description,
  disabled,
  label,
  onDecrement,
  onIncrement,
  value,
}: TravellerCardProps) {
  const icon =
    accent === "primary" ? (
      <UsersRound className="size-5" />
    ) : (
      <Baby className="size-5" />
    );

  return (
    <div className="rounded-xl border border-[var(--planner-board-border)] bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div
            className={cn(
              "mb-3 flex size-10 items-center justify-center rounded-full",
              accent === "primary"
                ? "bg-[var(--planner-board-cta)]/10 text-[var(--planner-board-cta)]"
                : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
            )}
          >
            {icon}
          </div>
          <p className="font-medium text-[var(--planner-board-text)]">{label}</p>
          <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
            {description}
          </p>
        </div>
        <div className="text-3xl font-semibold tracking-tight text-[var(--planner-board-text)]">
          {value}
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2">
        <CounterButton disabled={disabled || value <= 0} onClick={onDecrement}>
          <Minus className="size-4" />
        </CounterButton>
        <CounterButton disabled={disabled} onClick={onIncrement}>
          <Plus className="size-4" />
        </CounterButton>
      </div>
    </div>
  );
}

function CounterButton({
  children,
  disabled,
  onClick,
}: {
  children: ReactNode;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex size-9 items-center justify-center rounded-lg border border-[var(--planner-board-border)] bg-white text-[var(--planner-board-text)] transition-colors duration-150 hover:border-[var(--planner-board-cta)]",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      {children}
    </button>
  );
}

function getStepSummary(
  step: TripDetailsStepKey,
  form: TripDetailsCollectionFormState,
) {
  if (step === "modules") {
    const activeModules = Object.entries(form.selected_modules)
      .filter(([, enabled]) => enabled)
      .map(([moduleName]) => capitalizeLabel(moduleName));
    if (!activeModules.length) {
      return "Choose at least one planning module.";
    }
    if (activeModules.length === 4) {
      return "Full trip";
    }
    return activeModules.join(" / ");
  }

  if (step === "route") {
    if (form.selected_modules.flights) {
      if (form.from_location_flexible && form.to_location) {
        return form.from_location
          ? `${form.from_location} (flexible) -> ${form.to_location}`
          : `Flexible departure -> ${form.to_location}`;
      }
      const route = [form.from_location, form.to_location].filter(Boolean);
      return route.length ? route.join(" -> ") : "Add the route you want to plan around.";
    }
    return form.to_location || "Choose the destination you want Wandrix to center on.";
  }

  if (step === "timing") {
    return getTripDetailsTimingSummary(form);
  }

  if (step === "travellers") {
    const adults = form.adults ?? 0;
    const children = form.children ?? 0;
    const parts: string[] = [];
    if (adults > 0) {
      parts.push(`${adults} adult${adults === 1 ? "" : "s"}`);
    }
    if (children > 0) {
      parts.push(`${children} child${children === 1 ? "" : "ren"}`);
    }
    if (form.travelers_flexible) {
      if (parts.length) {
        return `${parts.join(" / ")} / still flexible`;
      }
      return "Traveller count still flexible";
    }
    return parts.length ? parts.join(" / ") : "Add who is travelling.";
  }

  if (step === "vibe") {
    const styles = form.activity_styles.map((style) => capitalizeLabel(style));
    if (form.custom_style?.trim()) {
      styles.push(form.custom_style.trim());
    }
    return styles.length ? styles.join(" / ") : "Choose the trip mood.";
  }

  if (step === "budget") {
    const amount = form.budget_amount ?? form.budget_gbp ?? null;
    let amountLabel: string | null = null;
    if (amount && form.budget_currency) {
      amountLabel = formatCurrency(amount, form.budget_currency);
    } else if (amount) {
      amountLabel = `${amount}`;
    }
    const parts = [
      form.budget_posture
        ? capitalizeLabel(form.budget_posture.replace("_", "-"))
        : null,
      form.budget_currency && amount === null ? form.budget_currency : null,
      amountLabel,
    ].filter(Boolean);
    return parts.length ? parts.join(" / ") : "Set the working budget direction.";
  }

  return null;
}

function getModuleConfig(moduleName: keyof TripModuleSelection) {
  return {
    flights: {
      label: "Flights",
      description: "Departure, timing, and fare-sensitive planning.",
      icon: <Plane className="size-5" />,
    },
    hotels: {
      label: "Hotels",
      description: "Stay timing, room fit, and budget-aware accommodation.",
      icon: <Hotel className="size-5" />,
    },
    activities: {
      label: "Activities",
      description: "Day shape, interests, and trip personality.",
      icon: <Compass className="size-5" />,
    },
    weather: {
      label: "Weather",
      description: "Destination conditions and timing-sensitive suggestions.",
      icon: <Cloud className="size-5" />,
    },
  }[moduleName];
}

function getStyleConfig(style: ActivityStyle) {
  return {
    food: { label: "Food", icon: <UtensilsCrossed className="size-5" /> },
    culture: { label: "Culture", icon: <MapPinned className="size-5" /> },
    relaxed: { label: "Relaxed", icon: <Palmtree className="size-5" /> },
    luxury: { label: "Luxury", icon: <Sparkles className="size-5" /> },
    romantic: { label: "Romantic", icon: <Heart className="size-5" /> },
    family: { label: "Family", icon: <UsersRound className="size-5" /> },
    adventure: { label: "Adventure", icon: <Mountain className="size-5" /> },
    outdoors: { label: "Outdoors", icon: <CalendarRange className="size-5" /> },
    nightlife: { label: "Nightlife", icon: <Wine className="size-5" /> },
  }[style];
}

function capitalizeLabel(value: string) {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}
