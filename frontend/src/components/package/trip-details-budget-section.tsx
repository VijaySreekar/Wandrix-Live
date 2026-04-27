"use client";

import type { ReactNode } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { TripDetailsCollectionFormState } from "@/types/trip-conversation";
import type { BudgetPosture } from "@/types/trip-draft";

const BUDGET_OPTIONS: Array<{ value: BudgetPosture; label: string }> = [
  { value: "budget", label: "Budget" },
  { value: "mid_range", label: "Mid-range" },
  { value: "premium", label: "Premium" },
];

const CURRENCY_OPTIONS = ["GBP", "EUR", "USD", "CAD", "AUD"] as const;

export function TripDetailsBudgetSection({
  actions,
  disabled,
  form,
  onBudgetAmountChange,
  onBudgetCurrencyChange,
  onBudgetPostureToggle,
}: {
  actions: ReactNode;
  disabled: boolean;
  form: TripDetailsCollectionFormState;
  onBudgetAmountChange: (value: number | null) => void;
  onBudgetCurrencyChange: (value: string | null) => void;
  onBudgetPostureToggle: (posture: BudgetPosture) => void;
}) {
  const amount = form.budget_amount ?? form.budget_gbp ?? null;
  const currency = form.budget_currency ?? "";

  return (
    <div className="space-y-5">
      <p className="text-sm leading-7 text-[var(--planner-board-muted)]">
        Set the budget tone you want Wandrix to work within. A posture or currency
        on its own is enough for early planning, and the amount can stay optional
        if you do not know it yet.
      </p>
      <div className="space-y-3">
        <Label className="text-sm font-medium text-[var(--planner-board-text)]">
          Budget posture
        </Label>
        <div className="grid gap-2.5 sm:grid-cols-3">
          {BUDGET_OPTIONS.map((option) => (
            <BudgetChoiceButton
              key={option.value}
              disabled={disabled}
              selected={form.budget_posture === option.value}
              onClick={() => onBudgetPostureToggle(option.value)}
            >
              {option.label}
            </BudgetChoiceButton>
          ))}
        </div>
      </div>
      <div className="grid gap-3 border-t border-[var(--planner-board-border)] pt-5 sm:grid-cols-[minmax(0,1fr)_9rem]">
        <div className="space-y-3">
          <Label className="text-sm font-medium text-[var(--planner-board-text)]">
            Budget amount
          </Label>
          <Input
            type="number"
            min={0}
            step="50"
            inputMode="numeric"
            disabled={disabled}
            placeholder="e.g. 1800"
            value={amount ?? ""}
            onChange={(event) => {
              const rawValue = event.target.value.trim();
              if (!rawValue) {
                onBudgetAmountChange(null);
                return;
              }
              const parsed = Number(rawValue);
              onBudgetAmountChange(Number.isFinite(parsed) ? parsed : null);
            }}
            className="h-11 rounded-lg border-[var(--planner-board-border)] bg-white/50 transition-colors duration-150 focus:border-[var(--planner-board-cta)]"
          />
        </div>
        <div className="space-y-3">
          <Label className="text-sm font-medium text-[var(--planner-board-text)]">
            Currency
          </Label>
          <select
            disabled={disabled}
            value={currency}
            onChange={(event) => onBudgetCurrencyChange(event.target.value || null)}
            className={cn(
              "h-11 w-full rounded-lg border border-[var(--planner-board-border)] bg-white/50 px-3 text-sm font-medium text-[var(--planner-board-text)] transition-colors duration-150 focus:border-[var(--planner-board-cta)] focus:outline-none",
              disabled && "cursor-not-allowed opacity-50",
            )}
          >
            <option value="">Currency</option>
            {CURRENCY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <p className="text-sm leading-6 text-[var(--planner-board-muted)] sm:col-span-2">
          Keep only the currency if that is all you know. Wandrix will not invent
          a total budget amount from the currency preference alone.
        </p>
      </div>
      {actions}
    </div>
  );
}

function BudgetChoiceButton({
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
      onClick={onClick}
      className={cn(
        "rounded-lg border px-4 py-3 text-sm font-medium transition-colors duration-150",
        selected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)] text-white"
          : "border-[var(--planner-board-border)] bg-white text-[var(--planner-board-text)] hover:border-[var(--planner-board-cta)]",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      {children}
    </button>
  );
}
