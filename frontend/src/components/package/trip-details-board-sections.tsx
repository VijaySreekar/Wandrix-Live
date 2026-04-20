"use client";

import type { ReactNode } from "react";
import {
  Baby,
  CalendarRange,
  CheckCircle2,
  ChevronDown,
  CircleDollarSign,
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
  SlidersHorizontal,
  Sparkles,
  UtensilsCrossed,
  UsersRound,
  Users,
  Wine,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DatePicker } from "@/components/ui/date-picker";
import { RouteLocationInput } from "@/components/package/route-location-input";
import { cn } from "@/lib/utils";
import type { TripDetailsCollectionFormState } from "@/types/trip-conversation";
import type {
  ActivityStyle,
  BudgetPosture,
  TripModuleSelection,
} from "@/types/trip-draft";

export type TripDetailsStepKey =
  | "route"
  | "timing"
  | "travellers"
  | "vibe"
  | "budget"
  | "modules";

type TripDetailsStepperProps = {
  accessToken?: string;
  activeStep: TripDetailsStepKey;
  disabled: boolean;
  focusNote: string;
  form: TripDetailsCollectionFormState;
  onActiveStepChange: (step: TripDetailsStepKey) => void;
  onAdultsChange: (value: number | null) => void;
  onBudgetAmountChange: (value: number) => void;
  onBudgetPostureToggle: (posture: BudgetPosture) => void;
  onChildrenChange: (value: number | null) => void;
  onFieldChange: (
    field:
      | "from_location"
      | "to_location"
      | "travel_window"
      | "trip_length"
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

const STEP_ORDER: TripDetailsStepKey[] = [
  "route",
  "timing",
  "travellers",
  "vibe",
  "budget",
  "modules",
];

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

function getStyleConfig(style: ActivityStyle) {
  const configs: Record<ActivityStyle, { icon: ReactNode }> = {
    food: { icon: <UtensilsCrossed className="size-5" /> },
    culture: { icon: <Compass className="size-5" /> },
    relaxed: { icon: <Palmtree className="size-5" /> },
    luxury: { icon: <Wine className="size-5" /> },
    romantic: { icon: <Heart className="size-5" /> },
    family: { icon: <UsersRound className="size-5" /> },
    adventure: { icon: <Mountain className="size-5" /> },
    outdoors: { icon: <Mountain className="size-5" /> },
    nightlife: { icon: <Sparkles className="size-5" /> },
  };
  return configs[style];
}

function getModuleConfig(moduleName: keyof TripModuleSelection) {
  const configs: Record<keyof TripModuleSelection, { icon: ReactNode; description: string }> = {
    flights: { icon: <Plane className="size-5" />, description: "Find and book flights" },
    hotels: { icon: <Hotel className="size-5" />, description: "Search accommodations" },
    activities: { icon: <Sparkles className="size-5" />, description: "Discover things to do" },
    weather: { icon: <Cloud className="size-5" />, description: "Check weather forecasts" },
  };
  return configs[moduleName];
}

const TRAVEL_WINDOW_OPTIONS = [
  "This month",
  "Next month",
  "Summer",
  "Autumn",
  "Winter",
  "Flexible",
] as const;

const TRIP_LENGTH_OPTIONS = [
  "Weekend",
  "3 days",
  "5 days",
  "1 week",
  "10 days",
  "2 weeks",
] as const;

const MODULE_ORDER: Array<keyof TripModuleSelection> = [
  "flights",
  "hotels",
  "activities",
  "weather",
];

const BUDGET_OPTIONS: Array<{ value: BudgetPosture; label: string }> = [
  { value: "budget", label: "Essential" },
  { value: "mid_range", label: "Premium" },
  { value: "premium", label: "Luxury" },
];

export function TripDetailsStepper({
  accessToken,
  activeStep,
  disabled,
  focusNote,
  form,
  onActiveStepChange,
  onAdultsChange,
  onBudgetAmountChange,
  onBudgetPostureToggle,
  onChildrenChange,
  onFieldChange,
  onModuleToggle,
  onStyleToggle,
}: TripDetailsStepperProps) {
  const firstIncomplete = getFirstIncompleteStep(form);
  const firstIncompleteIndex = STEP_ORDER.indexOf(firstIncomplete);

  const stepItems = STEP_ORDER.map((step, index) => ({
    step,
    index,
    icon: STEP_ICONS[step],
    title: STEP_TITLES[step],
    summary: getStepSummary(step, form),
    complete: isStepComplete(step, form),
    locked:
      firstIncompleteIndex !== -1 &&
      index > firstIncompleteIndex &&
      !STEP_ORDER.slice(0, index).every((priorStep) =>
        isStepComplete(priorStep, form),
      ),
  }));

  return (
    <div className="space-y-1">
      {stepItems.map((item) => {
        const stepIsOpen = activeStep === item.step;
        const stepIndex = item.index;
        const nextStep =
          stepIndex < STEP_ORDER.length - 1 ? STEP_ORDER[stepIndex + 1] : null;

        return (
          <StepCard
            key={item.step}
            disabled={disabled}
            isComplete={item.complete}
            isLocked={item.locked}
            isOpen={stepIsOpen}
            stepNumber={stepIndex + 1}
            summary={item.summary}
            title={item.title}
            onToggle={() => {
              if (!item.locked) {
                onActiveStepChange(item.step);
              }
            }}
          >
            {item.step === "route" ? (
              <div className="space-y-5">
                <StepIntro>
                  Start with the route you have in mind. Both points stay editable
                  later if the plan shifts.
                </StepIntro>
                <div className="grid gap-4 sm:grid-cols-2">
                  <RouteLocationInput
                    accessToken={accessToken}
                    disabled={disabled}
                    kind="origin"
                    label="From"
                    placeholder="London or Heathrow"
                    value={form.from_location ?? ""}
                    onChange={(value) => onFieldChange("from_location", value)}
                  />
                  <RouteLocationInput
                    accessToken={accessToken}
                    disabled={disabled}
                    kind="destination"
                    label="To"
                    placeholder="Marrakech or Kyoto"
                    value={form.to_location ?? ""}
                    onChange={(value) => onFieldChange("to_location", value)}
                  />
                </div>
                <StepActions
                  disabled={disabled || !item.complete}
                  nextLabel={nextStep ? "Continue to timing" : null}
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {item.step === "timing" ? (
              <div className="space-y-6">
                <StepIntro>
                  Rough timing is enough to move forward. Add exact dates only if
                  you already know them.
                </StepIntro>
                <div className="space-y-5">
                  <div className="space-y-3">
                    <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                      When are you thinking?
                    </Label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {TRAVEL_WINDOW_OPTIONS.map((option) => (
                        <ChoiceButton
                          key={option}
                          disabled={disabled}
                          selected={form.travel_window === option}
                          onClick={() =>
                            onFieldChange(
                              "travel_window",
                              form.travel_window === option ? null : option,
                            )
                          }
                        >
                          {option}
                        </ChoiceButton>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                      How long should it be?
                    </Label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {TRIP_LENGTH_OPTIONS.map((option) => (
                        <ChoiceButton
                          key={option}
                          disabled={disabled}
                          selected={form.trip_length === option}
                          onClick={() =>
                            onFieldChange(
                              "trip_length",
                              form.trip_length === option ? null : option,
                            )
                          }
                        >
                          {option}
                        </ChoiceButton>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="space-y-3 border-t border-[var(--planner-board-border)] pt-5">
                  <Label className="text-sm font-medium text-[var(--planner-board-text)]">
                    Or set exact dates
                  </Label>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <DatePicker
                      disabled={disabled}
                      placeholder="Start date"
                      date={form.start_date ? new Date(form.start_date + 'T00:00:00') : undefined}
                      onDateChange={(date) => {
                        if (date) {
                          const year = date.getFullYear();
                          const month = String(date.getMonth() + 1).padStart(2, '0');
                          const day = String(date.getDate()).padStart(2, '0');
                          const nextStartDate = `${year}-${month}-${day}`;
                          onFieldChange("start_date", nextStartDate);
                          if (form.end_date && form.end_date < nextStartDate) {
                            onFieldChange("end_date", null);
                          }
                        } else {
                          onFieldChange("start_date", null);
                        }
                      }}
                    />
                    <DatePicker
                      disabled={disabled}
                      placeholder="End date"
                      date={form.end_date ? new Date(form.end_date + 'T00:00:00') : undefined}
                      disabledDays={
                        form.start_date
                          ? {
                              before: new Date(form.start_date + "T00:00:00"),
                            }
                          : undefined
                      }
                      onDateChange={(date) => {
                        if (date) {
                          const year = date.getFullYear();
                          const month = String(date.getMonth() + 1).padStart(2, '0');
                          const day = String(date.getDate()).padStart(2, '0');
                          onFieldChange("end_date", `${year}-${month}-${day}`);
                        } else {
                          onFieldChange("end_date", null);
                        }
                      }}
                    />
                  </div>
                </div>
                <StepActions
                  disabled={disabled || !item.complete}
                  nextLabel={nextStep ? "Continue to travellers" : null}
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {item.step === "travellers" ? (
              <div className="space-y-5">
                <StepIntro>
                  Tell Wandrix who the trip is for. Adults are required, children
                  are optional.
                </StepIntro>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="group rounded-xl border border-[var(--planner-board-border)] bg-gradient-to-br from-white to-[var(--planner-board-soft)] p-5 transition-all duration-200 hover:border-[var(--planner-board-cta)] hover:shadow-sm">
                    <div className="mb-4 flex items-center gap-3">
                      <div className="flex size-10 items-center justify-center rounded-full bg-[var(--planner-board-cta)]/10">
                        <Users className="size-5 text-[var(--planner-board-cta)]" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-[var(--planner-board-text)]">Adults</h4>
                        <p className="text-xs text-[var(--planner-board-muted)]">18 years and older</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-center gap-4">
                      <CounterButton
                        disabled={disabled || (form.adults ?? 1) <= 1}
                        onClick={() => onAdultsChange(Math.max(1, (form.adults ?? 1) - 1))}
                      >
                        <Minus className="size-4" />
                      </CounterButton>
                      <span className="min-w-12 text-center text-2xl font-bold text-[var(--planner-board-text)]">
                        {form.adults ?? 1}
                      </span>
                      <CounterButton
                        disabled={disabled}
                        onClick={() => onAdultsChange((form.adults ?? 1) + 1)}
                      >
                        <Plus className="size-4" />
                      </CounterButton>
                    </div>
                  </div>

                  <div className="group rounded-xl border border-[var(--planner-board-border)] bg-gradient-to-br from-white to-[var(--planner-board-soft)] p-5 transition-all duration-200 hover:border-[var(--planner-board-cta)] hover:shadow-sm">
                    <div className="mb-4 flex items-center gap-3">
                      <div className="flex size-10 items-center justify-center rounded-full bg-[var(--planner-board-accent-soft)]">
                        <Baby className="size-5 text-[var(--planner-board-accent-text)]" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-[var(--planner-board-text)]">Children</h4>
                        <p className="text-xs text-[var(--planner-board-muted)]">Under 18 years</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-center gap-4">
                      <CounterButton
                        disabled={disabled || (form.children ?? 0) <= 0}
                        onClick={() => onChildrenChange(Math.max(0, (form.children ?? 0) - 1))}
                      >
                        <Minus className="size-4" />
                      </CounterButton>
                      <span className="min-w-12 text-center text-2xl font-bold text-[var(--planner-board-text)]">
                        {form.children ?? 0}
                      </span>
                      <CounterButton
                        disabled={disabled}
                        onClick={() => onChildrenChange((form.children ?? 0) + 1)}
                      >
                        <Plus className="size-4" />
                      </CounterButton>
                    </div>
                  </div>
                </div>
                <StepActions
                  disabled={disabled || !item.complete}
                  nextLabel={nextStep ? "Continue to style" : null}
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {item.step === "vibe" ? (
              <div className="space-y-5">
                <StepIntro>
                  Choose the trip mood you want Wandrix to optimize around. Pick
                  more than one if the plan has mixed priorities.
                </StepIntro>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {STYLE_OPTIONS.map((style) => {
                    const isSelected = form.activity_styles.includes(style);
                    const styleConfig = getStyleConfig(style);
                    return (
                      <button
                        key={style}
                        type="button"
                        disabled={disabled}
                        onClick={() => onStyleToggle(style)}
                        className={cn(
                          "group relative flex flex-col items-center gap-3 rounded-xl border p-4 transition-all duration-200",
                          isSelected
                            ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5 shadow-sm"
                            : "border-[var(--planner-board-border)] bg-white hover:border-[var(--planner-board-cta)] hover:bg-[var(--planner-board-soft)]",
                          disabled && "cursor-not-allowed opacity-50"
                        )}
                      >
                        <div
                          className={cn(
                            "flex size-12 items-center justify-center rounded-full transition-all duration-200",
                            isSelected
                              ? "bg-[var(--planner-board-cta)] text-white"
                              : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)] group-hover:bg-[var(--planner-board-cta)]/10 group-hover:text-[var(--planner-board-cta)]"
                          )}
                        >
                          {styleConfig.icon}
                        </div>
                        <span
                          className={cn(
                            "text-sm font-medium transition-colors duration-200",
                            isSelected
                              ? "text-[var(--planner-board-cta)]"
                              : "text-[var(--planner-board-text)]"
                          )}
                        >
                          {capitalizeLabel(style)}
                        </span>
                        {isSelected && (
                          <div className="absolute right-2 top-2">
                            <CheckCircle2 className="size-4 text-[var(--planner-board-cta)]" />
                          </div>
                        )}
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
                    placeholder="e.g., photography-focused, wellness retreat, nightlife..."
                    value={form.custom_style ?? ""}
                    onChange={(e) => onFieldChange("custom_style", e.target.value || null)}
                    className="h-11 rounded-lg border-[var(--planner-board-border)] bg-white/50 transition-all duration-200 focus:border-[var(--planner-board-cta)]"
                  />
                </div>
                <StepActions
                  disabled={disabled || !item.complete}
                  nextLabel={nextStep ? "Continue to budget and scope" : null}
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {item.step === "budget" ? (
              <div className="space-y-5">
                <StepIntro>
                  Set your trip budget. This helps Wandrix plan accommodations, activities, and dining that fit your spending comfort.
                </StepIntro>
                <div className="rounded-xl border border-[var(--planner-board-border)] bg-gradient-to-br from-white to-[var(--planner-board-soft)] p-5">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex size-10 items-center justify-center rounded-full bg-[var(--planner-board-cta)]/10">
                        <CircleDollarSign className="size-5 text-[var(--planner-board-cta)]" />
                      </div>
                      <Label className="text-base font-semibold text-[var(--planner-board-text)]">
                        Total Budget
                      </Label>
                    </div>
                    <span className="text-2xl font-bold text-[var(--planner-board-cta)]">
                      {formatCurrency(form.budget_gbp ?? 2200)}
                    </span>
                  </div>
                  <div className="space-y-3">
                    <input
                      type="range"
                      min="500"
                      max="10000"
                      step="100"
                      disabled={disabled}
                      value={form.budget_gbp ?? 2200}
                      onChange={(event) =>
                        onBudgetAmountChange(Number(event.target.value))
                      }
                      className="trip-budget-slider h-2 w-full cursor-pointer appearance-none rounded-full bg-[var(--planner-board-card)]"
                    />
                    <div className="flex items-center justify-between text-xs font-medium text-[var(--planner-board-muted-strong)]">
                      <span>£500</span>
                      <span>£10,000</span>
                    </div>
                  </div>
                </div>
                <div>
                  <Label className="mb-3 block text-sm font-medium text-[var(--planner-board-text)]">
                    Budget style
                  </Label>
                  <div className="grid grid-cols-3 gap-3">
                    {BUDGET_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        disabled={disabled}
                        onClick={() => onBudgetPostureToggle(option.value)}
                        className={cn(
                          "flex flex-col items-center gap-2 rounded-xl border p-4 transition-all duration-200",
                          form.budget_posture === option.value
                            ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5 shadow-sm"
                            : "border-[var(--planner-board-border)] bg-white hover:border-[var(--planner-board-cta)] hover:bg-[var(--planner-board-soft)]",
                          disabled && "cursor-not-allowed opacity-50"
                        )}
                      >
                        <span
                          className={cn(
                            "text-sm font-medium transition-colors duration-200",
                            form.budget_posture === option.value
                              ? "text-[var(--planner-board-cta)]"
                              : "text-[var(--planner-board-text)]"
                          )}
                        >
                          {option.label}
                        </span>
                        {form.budget_posture === option.value && (
                          <CheckCircle2 className="size-4 text-[var(--planner-board-cta)]" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
                <StepActions
                  disabled={disabled || !item.complete}
                  nextLabel={nextStep ? "Continue to modules (optional)" : null}
                  onNext={nextStep ? () => onActiveStepChange(nextStep) : undefined}
                />
              </div>
            ) : null}

            {item.step === "modules" ? (
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <StepIntro>
                    Choose which parts of the trip to plan. All modules are enabled by default.
                  </StepIntro>
                  <span className="shrink-0 rounded-full bg-[var(--planner-board-accent-soft)] px-2.5 py-0.5 text-xs font-medium text-[var(--planner-board-accent-text)]">
                    Optional
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {MODULE_ORDER.map((moduleName) => {
                    const isSelected = form.selected_modules[moduleName];
                    const moduleConfig = getModuleConfig(moduleName);
                    return (
                      <button
                        key={moduleName}
                        type="button"
                        disabled={disabled}
                        onClick={() => onModuleToggle(moduleName)}
                        className={cn(
                          "group flex items-center gap-4 rounded-xl border p-4 text-left transition-all duration-200",
                          isSelected
                            ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5"
                            : "border-[var(--planner-board-border)] bg-white hover:border-[var(--planner-board-cta)] hover:bg-[var(--planner-board-soft)]",
                          disabled && "cursor-not-allowed opacity-50"
                        )}
                      >
                        <div
                          className={cn(
                            "flex size-12 shrink-0 items-center justify-center rounded-full transition-all duration-200",
                            isSelected
                              ? "bg-[var(--planner-board-cta)] text-white"
                              : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)] group-hover:bg-[var(--planner-board-cta)]/10 group-hover:text-[var(--planner-board-cta)]"
                          )}
                        >
                          {moduleConfig.icon}
                        </div>
                        <div className="flex-1">
                          <h4
                            className={cn(
                              "font-semibold transition-colors duration-200",
                              isSelected
                                ? "text-[var(--planner-board-cta)]"
                                : "text-[var(--planner-board-text)]"
                            )}
                          >
                            {capitalizeLabel(moduleName)}
                          </h4>
                          <p className="mt-0.5 text-xs text-[var(--planner-board-muted)]">
                            {moduleConfig.description}
                          </p>
                        </div>
                        {isSelected && (
                          <CheckCircle2 className="size-5 shrink-0 text-[var(--planner-board-cta)]" />
                        )}
                      </button>
                    );
                  })}
                </div>
                <p className="text-sm leading-6 text-[var(--planner-board-muted)]">
                  {focusNote}
                </p>
                <StepActions
                  disabled={disabled || !item.complete}
                  nextLabel={null}
                  onNext={undefined}
                />
              </div>
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
    <div className="flex justify-end pt-2">
      <Button
        type="button"
        disabled={disabled}
        onClick={onConfirm}
        className="h-12 rounded-lg bg-[var(--planner-board-cta)] px-8 text-base font-semibold text-white shadow-[0_8px_20px_color-mix(in_srgb,var(--planner-board-cta)_24%,transparent)] transition-all duration-200 hover:bg-[var(--planner-board-cta-hover)] hover:shadow-[0_12px_28px_color-mix(in_srgb,var(--planner-board-cta)_28%,transparent)]"
      >
        {ctaLabel}
      </Button>
    </div>
  );
}

export function getFirstIncompleteStep(
  form: TripDetailsCollectionFormState,
): TripDetailsStepKey {
  return STEP_ORDER.find((step) => !isStepComplete(step, form)) ?? "modules";
}

function StepCard({
  children,
  disabled,
  isComplete,
  isLocked,
  isOpen,
  onToggle,
  stepNumber,
  summary,
  title,
}: {
  children: ReactNode;
  disabled: boolean;
  isComplete: boolean;
  isLocked: boolean;
  isOpen: boolean;
  onToggle: () => void;
  stepNumber: number;
  summary: string;
  title: string;
}) {
  return (
    <section
      className={cn(
        "group relative transition-all duration-200",
        isLocked && "opacity-50",
      )}
    >
      <button
        type="button"
        disabled={disabled || isLocked}
        onClick={onToggle}
        className={cn(
          "flex w-full items-center gap-4 py-5 text-left transition-all duration-200",
          isOpen ? "" : "hover:opacity-80",
        )}
      >
        <div className={cn(
          "relative flex size-10 shrink-0 items-center justify-center rounded-full transition-all duration-200",
          isComplete
            ? "bg-[var(--planner-board-cta)] text-white"
            : isOpen
            ? "bg-[var(--planner-board-cta)] text-white"
            : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
        )}>
          {isComplete ? (
            <CheckCircle2 className="size-5" />
          ) : (
            <span className="text-sm font-bold">{stepNumber}</span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-lg font-semibold text-[var(--planner-board-text)]">
            {title}
          </h3>
          {!isOpen && (
            <p className="mt-0.5 text-sm text-[var(--planner-board-muted)]">
              {summary}
            </p>
          )}
        </div>
        {isComplete && !isOpen && (
          <span className="rounded-full bg-[var(--planner-board-accent-soft)] px-2.5 py-1 text-xs font-medium text-[var(--planner-board-accent-text)]">
            Done
          </span>
        )}
        <ChevronDown
          className={cn(
            "size-5 shrink-0 text-[var(--planner-board-muted)] transition-transform duration-200",
            isOpen && "rotate-180",
          )}
        />
      </button>
      {isOpen ? (
        <div className="pb-8 pl-14 pr-0">
          {children}
        </div>
      ) : null}
      {!isOpen && (
        <div className="ml-5 h-px bg-[var(--planner-board-border)]" />
      )}
    </section>
  );
}

function StepIntro({ children }: { children: ReactNode }) {
  return (
    <p className="text-sm leading-7 text-[var(--planner-board-muted)]">
      {children}
    </p>
  );
}

function StepActions({
  disabled,
  nextLabel,
  onNext,
}: {
  disabled: boolean;
  nextLabel: string | null;
  onNext?: (() => void) | undefined;
}) {
  if (!nextLabel || !onNext) {
    return null;
  }

  return (
    <div className="flex justify-end">
      <Button
        type="button"
        disabled={disabled}
        onClick={onNext}
        variant="outline"
        className="h-10 rounded-lg border-[var(--planner-board-border)] bg-white/50 px-5 text-sm font-medium text-[var(--planner-board-text)] transition-all duration-200 hover:bg-white hover:border-[var(--planner-board-cta)]"
      >
        {nextLabel}
      </Button>
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
      className="flex size-9 items-center justify-center rounded-full border border-[var(--planner-board-border)] bg-white/50 text-[var(--planner-board-text)] transition-all duration-200 hover:bg-white hover:border-[var(--planner-board-cta)] disabled:cursor-not-allowed disabled:opacity-40"
    >
      {children}
    </button>
  );
}

function ChoiceButton({
  children,
  compact = false,
  disabled,
  selected,
  onClick,
}: {
  children: ReactNode;
  compact?: boolean;
  disabled: boolean;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "rounded-lg border px-4 text-center text-sm font-medium transition-all duration-200",
        compact ? "py-2.5" : "py-3",
        selected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)] text-white"
          : "border-[var(--planner-board-border)] bg-white/50 text-[var(--planner-board-text)] hover:bg-white hover:border-[var(--planner-board-cta)]",
      )}
    >
      {children}
    </button>
  );
}

function ToggleRow({
  children,
  disabled,
  onClick,
  selected,
}: {
  children: ReactNode;
  disabled: boolean;
  onClick: () => void;
  selected: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex items-center justify-between rounded-lg border px-4 py-3 text-left transition-all duration-200",
        selected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)]/5"
          : "border-[var(--planner-board-border)] bg-white/50 hover:bg-white hover:border-[var(--planner-board-cta)]",
      )}
    >
      <span className="text-sm font-medium text-[var(--planner-board-text)]">
        {children}
      </span>
      <span
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors",
          selected
            ? "bg-[var(--planner-board-cta)]"
            : "bg-[var(--planner-board-border)]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-4 rounded-full bg-white shadow-sm transition-all",
            selected ? "left-4" : "left-0.5",
          )}
        />
      </span>
    </button>
  );
}

function isStepComplete(
  step: TripDetailsStepKey,
  form: TripDetailsCollectionFormState,
) {
  if (step === "route") {
    return Boolean(form.from_location?.trim() && form.to_location?.trim());
  }

  if (step === "timing") {
    const hasWindow = Boolean(form.travel_window?.trim());
    const hasLength = Boolean(form.trip_length?.trim());
    const hasExactDates = Boolean(form.start_date && form.end_date);
    return hasExactDates || (hasWindow && hasLength);
  }

  if (step === "travellers") {
    return (form.adults ?? 0) > 0;
  }

  if (step === "vibe") {
    return form.activity_styles.length > 0;
  }

  if (step === "budget") {
    return (
      form.budget_posture !== null &&
      form.budget_posture !== undefined &&
      form.budget_gbp !== null &&
      form.budget_gbp !== undefined
    );
  }

  if (step === "modules") {
    // Modules step is always complete since it's optional and all are enabled by default
    return true;
  }

  return false;
}

function getStepSummary(
  step: TripDetailsStepKey,
  form: TripDetailsCollectionFormState,
) {
  if (step === "route") {
    if (form.from_location?.trim() && form.to_location?.trim()) {
      return `${form.from_location} to ${form.to_location}`;
    }
    return "Set your departure point and destination.";
  }

  if (step === "timing") {
    const parts = [form.travel_window, form.trip_length].filter(Boolean);
    if (parts.length > 0) {
      return parts.join(" · ");
    }
    if (form.start_date && form.end_date) {
      return `${form.start_date} to ${form.end_date}`;
    }
    return "Add rough timing and trip length.";
  }

  if (step === "travellers") {
    const adults = form.adults ?? 0;
    const children = form.children ?? 0;
    if (adults > 0 || children > 0) {
      return [
        adults > 0 ? `${adults} adult${adults > 1 ? "s" : ""}` : null,
        children > 0 ? `${children} child${children > 1 ? "ren" : ""}` : null,
      ]
        .filter(Boolean)
        .join(" · ");
    }
    return "Tell Wandrix who is travelling.";
  }

  if (step === "vibe") {
    if (form.activity_styles.length > 0) {
      return form.activity_styles.map(capitalizeLabel).join(" · ");
    }
    return "Choose the trip style you want to optimize for.";
  }

  if (step === "budget") {
    if (
      form.budget_posture &&
      form.budget_gbp !== null &&
      form.budget_gbp !== undefined
    ) {
      return `${capitalizeLabel(form.budget_posture)} · ${formatCurrency(
        form.budget_gbp,
      )}`;
    }
    return "Set your trip budget and spending style.";
  }

  if (step === "modules") {
    const enabledModules = MODULE_ORDER.filter(
      (moduleName) => form.selected_modules[moduleName],
    ).map(capitalizeLabel);
    
    if (enabledModules.length > 0) {
      return enabledModules.join(" · ");
    }
    return "All modules enabled by default (optional).";
  }

  return "";
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(value);
}

function capitalizeLabel(value: string) {
  return value.replace("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}


const STEP_TITLES: Record<TripDetailsStepKey, string> = {
  route: "Route details",
  timing: "Travel timing",
  travellers: "Traveller count",
  vibe: "Trip style",
  budget: "Budget",
  modules: "Trip modules",
};

const STEP_ICONS: Record<TripDetailsStepKey, typeof MapPinned> = {
  route: MapPinned,
  timing: CalendarRange,
  travellers: UsersRound,
  vibe: Sparkles,
  budget: CircleDollarSign,
  modules: SlidersHorizontal,
};
