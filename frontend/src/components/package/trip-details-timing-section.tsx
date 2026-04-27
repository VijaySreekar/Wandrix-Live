"use client";

import type { ReactNode } from "react";

import { DatePicker } from "@/components/ui/date-picker";
import { Label } from "@/components/ui/label";
import { formatDateForPlanner } from "@/components/package/trip-timing-board-model";
import { cn } from "@/lib/utils";
import type { TripDetailsCollectionFormState } from "@/types/trip-conversation";

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

const WEATHER_PREFERENCE_OPTIONS = [
  "Warm",
  "Sunny",
  "Mild",
  "Cool",
  "Snowy",
  "Dry",
] as const;

type TimingField =
  | "travel_window"
  | "trip_length"
  | "weather_preference"
  | "start_date"
  | "end_date";

type TripDetailsTimingSectionProps = {
  disabled: boolean;
  form: TripDetailsCollectionFormState;
  onFieldChange: (field: TimingField, value: string | null) => void;
};

export function TripDetailsTimingSection({
  disabled,
  form,
  onFieldChange,
}: TripDetailsTimingSectionProps) {
  return (
    <div className="space-y-6">
      <p className="text-sm leading-7 text-[var(--planner-board-muted)]">
        Rough timing is enough to move forward. Add exact dates only if you already know them.
      </p>
      <div className="space-y-5">
        <div className="space-y-3">
          <Label className="text-sm font-medium text-[var(--planner-board-text)]">
            When are you thinking?
          </Label>
          <div className="grid grid-cols-3 gap-2.5">
            {TRAVEL_WINDOW_OPTIONS.map((option) => (
              <TimingChoiceButton
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
              </TimingChoiceButton>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <Label className="text-sm font-medium text-[var(--planner-board-text)]">
            How long should it be?
          </Label>
          <div className="grid grid-cols-3 gap-2.5">
            {TRIP_LENGTH_OPTIONS.map((option) => (
              <TimingChoiceButton
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
              </TimingChoiceButton>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <Label className="text-sm font-medium text-[var(--planner-board-text)]">
            What weather would you prefer?
          </Label>
          <div className="grid grid-cols-3 gap-2.5">
            {WEATHER_PREFERENCE_OPTIONS.map((option) => {
              const value = option.toLowerCase();
              return (
                <TimingChoiceButton
                  key={option}
                  disabled={disabled}
                  selected={form.weather_preference === value}
                  onClick={() =>
                    onFieldChange(
                      "weather_preference",
                      form.weather_preference === value ? null : value,
                    )
                  }
                >
                  {option}
                </TimingChoiceButton>
              );
            })}
          </div>
          <p className="text-sm leading-6 text-[var(--planner-board-muted)]">
            Optional, but it helps Wandrix steer timing and destination fit earlier in the planning flow.
          </p>
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
            date={
              form.start_date
                ? new Date(`${form.start_date}T00:00:00`)
                : undefined
            }
            onDateChange={(date) => {
              const nextStartDate = formatDateForPlanner(date);
              onFieldChange("start_date", nextStartDate);
              if (nextStartDate && form.end_date && form.end_date < nextStartDate) {
                onFieldChange("end_date", null);
              }
            }}
          />
          <DatePicker
            disabled={disabled}
            placeholder="End date"
            date={
              form.end_date
                ? new Date(`${form.end_date}T00:00:00`)
                : undefined
            }
            disabledDays={
              form.start_date
                ? { before: new Date(`${form.start_date}T00:00:00`) }
                : undefined
            }
            onDateChange={(date) =>
              onFieldChange("end_date", formatDateForPlanner(date))
            }
          />
        </div>
      </div>
    </div>
  );
}

function TimingChoiceButton({
  children,
  disabled,
  selected,
  onClick,
}: {
  children: ReactNode;
  disabled: boolean;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={cn(
        "rounded-lg border px-3 py-2 text-sm font-semibold transition-colors duration-150",
        selected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)] text-white"
          : "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)] hover:border-[var(--planner-board-cta)]",
        disabled && "cursor-not-allowed opacity-50",
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
