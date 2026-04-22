"use client";

import { TripDetailsBoard } from "@/components/package/trip-details-board";
import { TripLiveBoard } from "@/components/package/trip-live-board";
import { TripSuggestionBoard } from "@/components/package/trip-suggestion-board";
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
  onAction: (action: PlannerBoardActionIntent) => void;
};

export function TripBoardPreview({
  authSnapshot,
  workspace,
  isBootstrapping,
  isSwitchingTrips,
  requestedTripId,
  onAction,
}: TripBoardPreviewProps) {
  const conversation = workspace?.tripDraft.conversation;
  const suggestionBoard = conversation?.suggestion_board;
  const showInitialBoardShell = isBootstrapping && !workspace;

  if (workspace && conversation?.planning_mode === "quick") {
    return (
      <section className="relative flex h-full min-h-0 flex-col bg-shell">
        <div
          data-switching={isSwitchingTrips ? "true" : "false"}
          className="trip-switch-content flex h-full min-h-0 flex-col"
        >
          <BoardHeader />
          <TripLiveBoard workspace={workspace} onAction={onAction} />
        </div>
        {isSwitchingTrips ? <BoardSwitchOverlay requestedTripId={requestedTripId} /> : null}
      </section>
    );
  }

  if (
    workspace &&
    suggestionBoard &&
    [
      "destination_suggestions",
      "decision_cards",
      "planning_mode_choice",
      "advanced_date_resolution",
      "advanced_anchor_choice",
      "advanced_next_step",
      "advanced_stay_choice",
      "advanced_stay_selected",
      "advanced_stay_review",
      "advanced_stay_hotel_choice",
      "advanced_stay_hotel_selected",
      "advanced_stay_hotel_review",
    ].includes(suggestionBoard.mode)
  ) {
    return (
      <section className="relative flex h-full min-h-0 flex-col bg-shell">
        <div
          data-switching={isSwitchingTrips ? "true" : "false"}
          className="trip-switch-content flex h-full min-h-0 flex-col"
        >
          <TripSuggestionBoard
            board={suggestionBoard}
            decisionCards={conversation?.decision_cards ?? []}
            disabled={isBootstrapping || isSwitchingTrips}
            onAction={onAction}
          />
        </div>
        {isSwitchingTrips ? (
          <BoardSwitchOverlay requestedTripId={requestedTripId} />
        ) : null}
      </section>
    );
  }

  if (workspace && suggestionBoard?.mode === "details_collection") {
    return (
      <section className="relative flex h-full min-h-0 flex-col bg-shell">
        <div
          data-switching={isSwitchingTrips ? "true" : "false"}
          className="trip-switch-content flex h-full min-h-0 flex-col"
        >
          <TripDetailsBoard
            key={JSON.stringify(suggestionBoard.details_form ?? {})}
            accessToken={authSnapshot?.accessToken}
            board={suggestionBoard}
            disabled={isBootstrapping || isSwitchingTrips}
            onAction={onAction}
          />
        </div>
        {isSwitchingTrips ? (
          <BoardSwitchOverlay requestedTripId={requestedTripId} />
        ) : null}
      </section>
    );
  }

  if (showInitialBoardShell) {
    return (
      <section className="flex h-full min-h-0 flex-col bg-shell">
        <BoardHeader />
        <InitialBoardShell />
      </section>
    );
  }

  const helperCopy = getHelperCopy({ workspace, isBootstrapping });
  const isLoading = isBootstrapping;

  return (
    <section className="flex h-full min-h-0 flex-col bg-shell">
      <BoardHeader />
      <div className="flex flex-1 items-center justify-center px-8 py-10">
        <div className="mx-auto max-w-md text-center">
          {isLoading ? (
            <div className="mb-8">
              <TravelBoardSpinner />
            </div>
          ) : null}
          <p className="text-base font-medium leading-7 text-foreground transition-opacity duration-200">
            {helperCopy.title}
          </p>
          <p className="mt-3 text-sm leading-7 text-foreground/60">
            {helperCopy.description}
          </p>
        </div>
      </div>
    </section>
  );
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

function getHelperCopy({
  workspace,
  isBootstrapping,
}: {
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
}) {
  if (isBootstrapping) {
    return {
      title: "Loading your planning board.",
      description:
        "Wandrix is pulling your trip workspace into place so the next planning step can start cleanly.",
    };
  }

  if (!workspace) {
    return {
      title: "This board is reserved for the final itinerary stage.",
      description:
        "Use the chat to shape the trip first. Later, once the trip is properly confirmed, this space can become the full itinerary board.",
    };
  }

  return {
    title: "We will use this board later, not during the early planning pass.",
    description:
      "For now, Wandrix should collect the route, timing, travelers, and preferences through chat. Once the trip is confirmed and ready for itinerary generation, the full board can take over here.",
  };
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
