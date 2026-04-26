"use client";

import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { CalendarRange, CheckCircle2, Clock } from "lucide-react";

import { DatePicker } from "@/components/ui/date-picker";
import { Button } from "@/components/ui/button";
import {
  buildInitialTimingChoice,
  formatDateForPlanner,
  buildTimingChatPrompt,
  canSubmitTimingChoice,
  TIMING_LENGTH_OPTIONS,
  TIMING_WINDOW_OPTIONS,
} from "@/components/package/trip-timing-board-model";
import { cn } from "@/lib/utils";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type { TripSuggestionBoardState } from "@/types/trip-conversation";

type TripTimingChoiceBoardProps = {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
};

export function TripTimingChoiceBoard({
  board,
  disabled,
  onAction,
}: TripTimingChoiceBoardProps) {
  const initialChoice = useMemo(
    () => buildInitialTimingChoice(board.details_form),
    [board.details_form],
  );
  const [travelWindow, setTravelWindow] = useState(initialChoice.travel_window);
  const [tripLength, setTripLength] = useState(initialChoice.trip_length);
  const [startDate, setStartDate] = useState(initialChoice.start_date);
  const [endDate, setEndDate] = useState(initialChoice.end_date);
  const destination = initialChoice.destination || "this trip";
  const choice = {
    destination: initialChoice.destination,
    travel_window: travelWindow,
    trip_length: tripLength,
    start_date: startDate,
    end_date: endDate,
  };
  const canSubmit = canSubmitTimingChoice(choice);
  const prompt = buildTimingChatPrompt(choice);

  return (
    <section className="flex h-full min-h-0 flex-col bg-[var(--planner-board-bg)] px-8 pb-10 pt-8">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl">
          <header className="pb-8">
            <div className="flex items-center gap-3 text-sm font-semibold text-[var(--planner-board-muted-strong)]">
              <CalendarRange className="size-4" />
              Timing
            </div>
            <h2 className="mt-3 font-display text-[2rem] font-bold tracking-tight text-[var(--planner-board-title)]">
              {board.title || `When should ${destination} happen?`}
            </h2>
            <p className="mt-2 max-w-2xl text-base leading-relaxed text-[var(--planner-board-muted)]">
              {board.subtitle ||
                "Choose a rough window and length, or use exact dates if you already know them."}
            </p>
          </header>

          <div className="space-y-5">
            <TimingPanel
              icon={<CalendarRange className="size-5" />}
              title="Rough window"
              description="A month, season, or flexible timing is enough for now."
            >
              <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                {TIMING_WINDOW_OPTIONS.map((option) => (
                  <TimingChoiceButton
                    key={option}
                    disabled={disabled}
                    selected={travelWindow === option}
                    onClick={() => {
                      setTravelWindow(travelWindow === option ? null : option);
                      setStartDate(null);
                      setEndDate(null);
                    }}
                  >
                    {option}
                  </TimingChoiceButton>
                ))}
              </div>
            </TimingPanel>

            <TimingPanel
              icon={<Clock className="size-5" />}
              title="Trip length"
              description="Pick the amount of time Wandrix should pace around."
            >
              <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                {TIMING_LENGTH_OPTIONS.map((option) => (
                  <TimingChoiceButton
                    key={option}
                    disabled={disabled}
                    selected={tripLength === option}
                    onClick={() =>
                      setTripLength(tripLength === option ? null : option)
                    }
                  >
                    {option}
                  </TimingChoiceButton>
                ))}
              </div>
            </TimingPanel>

            <TimingPanel
              icon={<CheckCircle2 className="size-5" />}
              title="Exact dates"
              description="Use this only if the calendar is already fixed."
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <DatePicker
                  disabled={disabled}
                  placeholder="Start date"
                  date={startDate ? new Date(`${startDate}T00:00:00`) : undefined}
                  onDateChange={(date) => {
                    const nextDate = formatDateForPlanner(date);
                    setStartDate(nextDate);
                    if (nextDate && endDate && endDate < nextDate) {
                      setEndDate(null);
                    }
                  }}
                />
                <DatePicker
                  disabled={disabled}
                  placeholder="End date"
                  date={endDate ? new Date(`${endDate}T00:00:00`) : undefined}
                  disabledDays={
                    startDate ? { before: new Date(`${startDate}T00:00:00`) } : undefined
                  }
                  onDateChange={(date) => setEndDate(formatDateForPlanner(date))}
                />
              </div>
            </TimingPanel>
          </div>

          <div className="mt-8 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-5">
            <p className="text-sm font-semibold text-[var(--planner-board-text)]">
              This will send
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
              {prompt}
            </p>
            <Button
              className="mt-5"
              disabled={disabled || !canSubmit}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "chat_prompt",
                  prompt_text: prompt,
                })
              }
            >
              Send timing
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

function TimingPanel({
  children,
  description,
  icon,
  title,
}: {
  children: ReactNode;
  description: string;
  icon: ReactNode;
  title: string;
}) {
  return (
    <article className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]">
          {icon}
        </div>
        <div>
          <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
            {title}
          </h3>
          <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
            {description}
          </p>
        </div>
      </div>
      {children}
    </article>
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
      onClick={onClick}
      className={cn(
        "min-h-11 rounded-lg border px-3 py-2 text-sm font-semibold transition-colors duration-150",
        selected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-cta)] text-white"
          : "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)] hover:border-[var(--planner-board-cta)]",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      {children}
    </button>
  );
}
