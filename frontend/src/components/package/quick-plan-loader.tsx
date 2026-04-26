"use client";

import { CalendarRange, Hotel, MapPinned, Plane, Route } from "lucide-react";

import {
  MultiStepLoader,
  type MultiStepLoadingState,
} from "@/components/ui/multi-step-loader";

const QUICK_PLAN_LOADING_STATES: MultiStepLoadingState[] = [
  { text: "Reading the confirmed brief" },
  { text: "Checking safe planning scope" },
  { text: "Shaping route and timing" },
  { text: "Looking across stays and local rhythm" },
  { text: "Drafting an editable day structure" },
  { text: "Reviewing the plan before it appears" },
];

const QUICK_PLAN_SIGNALS = [
  {
    icon: CalendarRange,
    label: "Dates",
    text: "Editable working window",
  },
  {
    icon: Plane,
    label: "Flights",
    text: "Best timing first",
  },
  {
    icon: Hotel,
    label: "Stay",
    text: "Fit before filler",
  },
  {
    icon: MapPinned,
    label: "Days",
    text: "Routed, not scattered",
  },
];

export function QuickPlanLoaderBoard() {
  return (
    <section className="relative flex h-full min-h-0 flex-col overflow-hidden bg-[var(--planner-board-bg)]">
      <div className="border-b border-[var(--planner-board-border)] px-8 py-8">
        <p className="font-label text-[10px] uppercase tracking-[0.2em] text-[var(--planner-board-muted-strong)]">
          Quick Plan
        </p>
        <h2 className="mt-2 font-display text-[2rem] font-bold tracking-tight text-[var(--planner-board-title)]">
          Building your first draft
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--planner-board-muted)]">
          Wandrix is turning the confirmed brief into working dates, logistics,
          stay direction, and a scheduled itinerary you can still change in chat.
        </p>
      </div>

      <div className="flex flex-1 items-center px-8 py-10">
        <div className="mx-auto grid w-full max-w-3xl gap-4 sm:grid-cols-2">
          {QUICK_PLAN_SIGNALS.map((signal) => {
            const Icon = signal.icon;

            return (
              <div
                key={signal.label}
                className="rounded-2xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-5 shadow-[var(--chat-shadow-soft)]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[color:var(--accent)]/10 text-[color:var(--accent)]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[var(--planner-board-text)]">
                      {signal.label}
                    </p>
                    <p className="mt-1 text-sm text-[var(--planner-board-muted)]">
                      {signal.text}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-8 right-8 hidden items-center gap-2 rounded-full border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-4 py-2 text-xs font-semibold text-[var(--planner-board-muted)] shadow-[var(--chat-shadow-soft)] md:flex">
        <Route className="h-3.5 w-3.5 text-[color:var(--accent)]" />
        Keeping the plan editable
      </div>

      <MultiStepLoader
        loadingStates={QUICK_PLAN_LOADING_STATES}
        loading
        duration={1800}
        mode="progress"
      />
    </section>
  );
}
