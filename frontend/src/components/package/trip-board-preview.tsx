"use client";

import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { TripDetailsBoard } from "@/components/package/trip-details-board";
import { TripLiveBoard } from "@/components/package/trip-live-board";
import { QuickPlanLoaderBoard } from "@/components/package/quick-plan-loader";
import { TripSuggestionBoard } from "@/components/package/trip-suggestion-board";
import { TripTimingChoiceBoard } from "@/components/package/trip-timing-choice-board";
import { TravelBoardSpinner } from "@/components/package/travel-board-spinner";
import type { BrowserAuthSnapshot } from "@/lib/supabase/auth-snapshot";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { PlannerBoardActionIntent } from "@/types/planner-board";

type TripBoardPreviewProps = {
  authSnapshot: BrowserAuthSnapshot | null;
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  isSwitchingTrips: boolean;
  requestedTripId: string | null;
  pendingBoardAction: PlannerBoardActionIntent | null;
  onAction: (action: PlannerBoardActionIntent) => void;
};

type BoardPreviewDirection = "forward" | "backward";

const BOARD_VIEW_TRANSITION = {
  enter: (direction: BoardPreviewDirection) => ({
    opacity: 0,
    filter: "blur(10px)",
    scale: 0.988,
    x: direction === "forward" ? 28 : -18,
  }),
  center: {
    opacity: 1,
    filter: "blur(0px)",
    scale: 1,
    x: 0,
  },
  exit: (direction: BoardPreviewDirection) => ({
    opacity: 0,
    filter: "blur(6px)",
    scale: 0.996,
    x: direction === "forward" ? -18 : 18,
  }),
};

const REDUCED_BOARD_VIEW_TRANSITION = {
  enter: { opacity: 0 },
  center: { opacity: 1 },
  exit: { opacity: 0 },
};

const STARTER_BOARD_SLIDES = [
  {
    id: "conversation",
    eyebrow: "Conversation first",
    title: "Start with a sentence",
    description:
      "A destination, a feeling, a budget worry, or a half-formed idea is enough. Wandrix turns it into the next useful question.",
    note: "Start wherever the idea is.",
    details: ["Trip idea captured", "Next question ready", "Board still flexible"],
    image:
      "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=80",
  },
  {
    id: "board",
    eyebrow: "Live board",
    title: "Details become decisions",
    description:
      "When something is firm enough to use, it appears here as structured trip state instead of disappearing into chat history.",
    note: "Destination, dates, stays, flights, and activities stay visible.",
    details: ["Route and timing", "Stay direction", "Activity style"],
    image:
      "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1400&q=80",
  },
  {
    id: "brochure",
    eyebrow: "Final output",
    title: "Leave with something shareable",
    description:
      "Once the plan feels right, Wandrix turns the working draft into a polished itinerary you can review, share, and refine.",
    note: "The brochure comes after the plan, not before it.",
    details: ["Daily rhythm", "Shareable summary", "Final review"],
    image:
      "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80",
  },
];

export function TripBoardPreview({
  authSnapshot,
  workspace,
  isBootstrapping,
  isSwitchingTrips,
  requestedTripId,
  pendingBoardAction,
  onAction,
}: TripBoardPreviewProps) {
  const reduceMotion = useReducedMotion();
  const conversation = workspace?.tripDraft.conversation;
  const suggestionBoard = conversation?.suggestion_board;
  const showInitialBoardShell = isBootstrapping && !workspace;
  const view = buildBoardPreviewView({
    authSnapshot,
    workspace,
    suggestionBoard,
    conversation,
    showInitialBoardShell,
    isBootstrapping,
    isSwitchingTrips,
    pendingBoardAction,
    onAction,
  });

  return (
    <section className="relative h-full min-h-0 overflow-hidden bg-shell">
      <AnimatePresence
        initial={false}
        mode="sync"
        custom={view.direction}
      >
        <motion.div
          key={view.key}
          className="absolute inset-0 flex min-h-0 flex-col"
          custom={view.direction}
          variants={
            reduceMotion
              ? REDUCED_BOARD_VIEW_TRANSITION
              : BOARD_VIEW_TRANSITION
          }
          initial="enter"
          animate="center"
          exit="exit"
          transition={{
            opacity: { duration: reduceMotion ? 0.01 : 0.28, ease: "easeOut" },
            filter: { duration: reduceMotion ? 0.01 : 0.34, ease: "easeOut" },
            scale: {
              duration: reduceMotion ? 0.01 : 0.44,
              ease: [0.16, 1, 0.3, 1],
            },
            x: {
              duration: reduceMotion ? 0.01 : 0.5,
              ease: [0.16, 1, 0.3, 1],
            },
          }}
        >
          <div
            data-switching={isSwitchingTrips ? "true" : "false"}
            className="trip-switch-content flex h-full min-h-0 flex-col"
          >
            {view.content}
          </div>
        </motion.div>
      </AnimatePresence>
      {isSwitchingTrips ? (
        <BoardSwitchOverlay requestedTripId={requestedTripId} />
      ) : null}
    </section>
  );
}

type BoardPreviewView = {
  key: string;
  direction: BoardPreviewDirection;
  content: ReactNode;
};

function buildBoardPreviewView({
  authSnapshot,
  workspace,
  suggestionBoard,
  conversation,
  showInitialBoardShell,
  isBootstrapping,
  isSwitchingTrips,
  pendingBoardAction,
  onAction,
}: {
  authSnapshot: BrowserAuthSnapshot | null;
  workspace: PlannerWorkspaceState | null;
  suggestionBoard: PlannerWorkspaceState["tripDraft"]["conversation"]["suggestion_board"] | undefined;
  conversation: PlannerWorkspaceState["tripDraft"]["conversation"] | undefined;
  showInitialBoardShell: boolean;
  isBootstrapping: boolean;
  isSwitchingTrips: boolean;
  pendingBoardAction: PlannerBoardActionIntent | null;
  onAction: (action: PlannerBoardActionIntent) => void;
}): BoardPreviewView {
  if (workspace && pendingBoardAction?.type === "select_quick_plan") {
    return {
      key: `quick-plan-loading:${workspace.trip.trip_id}:${pendingBoardAction.action_id}`,
      direction: "forward",
      content: <QuickPlanLoaderBoard />,
    };
  }

  if (
    workspace &&
    suggestionBoard?.mode === "timing_choice"
  ) {
    return {
      key: `timing:${workspace.trip.trip_id}`,
      direction: "forward",
      content: (
        <TripTimingChoiceBoard
          board={suggestionBoard}
          disabled={isBootstrapping || isSwitchingTrips}
          onAction={onAction}
        />
      ),
    };
  }

  if (
    workspace &&
    suggestionBoard &&
    [
      "destination_suggestions",
      "planning_mode_choice",
      "advanced_date_resolution",
      "advanced_anchor_choice",
      "advanced_next_step",
      "advanced_flights_workspace",
      "advanced_trip_style_direction",
      "advanced_trip_style_pace",
      "advanced_trip_style_tradeoffs",
      "advanced_activities_workspace",
      "advanced_stay_choice",
      "advanced_stay_selected",
      "advanced_stay_review",
      "advanced_stay_hotel_choice",
      "advanced_stay_hotel_selected",
      "advanced_stay_hotel_review",
      "advanced_review_workspace",
    ].includes(suggestionBoard.mode)
  ) {
    return {
      key: `suggestion:${workspace.trip.trip_id}:${suggestionBoard.mode}`,
      direction: "forward",
      content: (
        <TripSuggestionBoard
          board={suggestionBoard}
          decisionCards={conversation?.decision_cards ?? []}
          disabled={isBootstrapping || isSwitchingTrips}
          onAction={onAction}
        />
      ),
    };
  }

  if (workspace && suggestionBoard?.mode === "details_collection") {
    return {
      key: `details:${workspace.trip.trip_id}`,
      direction: "forward",
      content: (
        <TripDetailsBoard
          key={JSON.stringify(suggestionBoard.details_form ?? {})}
          accessToken={authSnapshot?.accessToken}
          board={suggestionBoard}
          disabled={isBootstrapping || isSwitchingTrips}
          onAction={onAction}
        />
      ),
    };
  }

  if (workspace && conversation?.planning_mode === "quick") {
    return {
      key: `live:${workspace.trip.trip_id}`,
      direction: "forward",
      content: (
        <>
          <BoardHeader />
          <TripLiveBoard workspace={workspace} onAction={onAction} />
        </>
      ),
    };
  }

  if (showInitialBoardShell) {
    return {
      key: "initial-shell",
      direction: "backward",
      content: (
        <>
          <BoardHeader />
          <InitialBoardShell />
        </>
      ),
    };
  }

  return {
    key: `starter:${isBootstrapping ? "loading" : "idle"}`,
    direction: "backward",
    content: (
      <>
        <BoardHeader />
        <StarterBoardCarousel isLoading={isBootstrapping} />
      </>
    ),
  };
}

function BoardHeader() {
  return (
    <div className="border-b border-shell-border/70 px-6 py-4 xl:px-8">
      <p className="font-label text-[11px] uppercase tracking-[0.22em] text-foreground/48">
        Live travel board
      </p>
    </div>
  );
}

function InitialBoardShell() {
  return (
    <div className="flex flex-1 items-center px-8 py-10 xl:px-10">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
        <div className="rounded-[1.75rem] border border-shell-border/70 bg-background/92 p-6 shadow-[var(--chat-shadow-card)]">
          <div className="space-y-4">
            <div className="h-3 w-28 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]" />
            <div className="space-y-3">
              <div className="h-8 w-[68%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/90" />
              <div className="h-4 w-full animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/70" />
              <div className="h-4 w-[82%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/55" />
            </div>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div className="space-y-4 rounded-[1.4rem] border border-shell-border/70 bg-background/86 p-5 shadow-[var(--chat-shadow-soft)]">
            <div className="h-3 w-24 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]" />
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="rounded-2xl border border-shell-border/70 bg-[color:var(--chat-rail-surface)] p-4"
              >
                <div className="space-y-3">
                  <div className="h-4 w-40 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/90" />
                  <div className="h-3 w-full animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/65" />
                  <div className="h-3 w-[74%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/50" />
                </div>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, index) => (
              <div
                key={index}
                className="rounded-[1.35rem] border border-shell-border/70 bg-background/86 p-5 shadow-[var(--chat-shadow-soft)]"
              >
                <div className="space-y-3">
                  <div className="h-3 w-24 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]" />
                  <div className="h-6 w-[58%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/85" />
                  <div className="h-3 w-full animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/65" />
                  <div className="h-3 w-[80%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/50" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StarterBoardCarousel({
  isLoading,
}: {
  isLoading: boolean;
}) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeSlide = STARTER_BOARD_SLIDES[activeIndex];

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % STARTER_BOARD_SLIDES.length);
    }, 5200);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="relative min-h-0 flex-1 overflow-hidden bg-[color:var(--planner-board-bg)]">
      {STARTER_BOARD_SLIDES.map((slide, index) => (
        <div
          key={slide.id}
          aria-hidden={index !== activeIndex}
          className={[
            "absolute inset-0 bg-cover bg-center transition-opacity duration-700 ease-out",
            index === activeIndex ? "opacity-100" : "opacity-0",
          ].join(" ")}
          style={{
            backgroundImage: `linear-gradient(180deg, rgba(10, 18, 16, 0.08), rgba(10, 18, 16, 0.72)), url("${slide.image}")`,
          }}
        />
      ))}

      <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(8,13,12,0.42),rgba(8,13,12,0.12)_46%,rgba(8,13,12,0.38))]" />

      <div className="relative flex h-full min-h-0 flex-col p-5 xl:p-6">
        {isLoading ? (
          <div className="w-fit rounded-full border border-white/20 bg-black/18 px-3 py-2 backdrop-blur-md">
            <TravelBoardSpinner />
          </div>
        ) : null}

        <div className="mt-auto grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]">
          <div className="max-w-xl self-end text-white">
            <p className="text-[0.68rem] font-medium uppercase tracking-[0.22em] text-white/70">
              {activeSlide.eyebrow}
            </p>
            <h2 className="mt-2 max-w-md text-2xl font-semibold leading-tight tracking-normal xl:text-3xl">
              {activeSlide.title}
            </h2>
            <p className="mt-3 max-w-md text-sm leading-7 text-white/78">
              {activeSlide.description}
            </p>
          </div>

          <div className="hidden self-end rounded-xl border border-white/16 bg-black/22 p-3 text-white shadow-[0_18px_50px_-36px_rgba(0,0,0,0.75)] backdrop-blur-md lg:block">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[0.66rem] font-medium uppercase tracking-[0.18em] text-white/56">
                Board draft
              </p>
              <span className="rounded-full bg-white/12 px-2 py-1 text-[0.68rem] text-white/66">
                0{activeIndex + 1}/03
              </span>
            </div>
            <div className="mt-3 space-y-2">
              {activeSlide.details.map((detail) => (
                <div
                  key={detail}
                  className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-white/72" />
                  <span className="text-[0.78rem] leading-5 text-white/78">
                    {detail}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[0.76rem] leading-5 text-white/62">
              {activeSlide.note}
            </p>
          </div>
        </div>

        <div className="mt-5 flex items-center gap-2">
          {STARTER_BOARD_SLIDES.map((slide, index) => (
            <button
              key={slide.id}
              type="button"
              onClick={() => setActiveIndex(index)}
              className={[
                "h-1.5 rounded-full transition-all",
                index === activeIndex ? "w-8 bg-white" : "w-2 bg-white/42",
              ].join(" ")}
              aria-label={`Show ${slide.title}`}
              aria-current={index === activeIndex ? "true" : undefined}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function BoardSwitchOverlay({
  requestedTripId,
}: {
  requestedTripId: string | null;
}) {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex justify-center px-6 pt-8">
      <div className="trip-switch-overlay-card inline-flex items-center gap-2 rounded-full border border-shell-border/80 bg-background/94 px-3 py-1.5 text-[0.78rem] text-foreground/62 shadow-[var(--chat-shadow-soft)]">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--accent)]" />
        <span>
          Opening {requestedTripId ? "the selected trip" : "the next trip"}
        </span>
      </div>
    </div>
  );
}
