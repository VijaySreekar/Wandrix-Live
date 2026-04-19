"use client";

import { TripSuggestionBoard } from "@/components/package/trip-suggestion-board";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { PlannerBoardActionIntent } from "@/types/planner-board";

type TripBoardPreviewProps = {
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
};

export function TripBoardPreview({
  workspace,
  isBootstrapping,
  onAction,
}: TripBoardPreviewProps) {
  const conversation = workspace?.tripDraft.conversation;
  const suggestionBoard = conversation?.suggestion_board;

  if (
    workspace &&
    suggestionBoard &&
    ["destination_suggestions", "decision_cards"].includes(suggestionBoard.mode)
  ) {
    return (
      <TripSuggestionBoard
        board={suggestionBoard}
        decisionCards={conversation?.decision_cards ?? []}
        disabled={isBootstrapping}
        onAction={onAction}
      />
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
            <div className="mb-5 flex items-center justify-center gap-2">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-foreground/35 [animation-delay:-0.2s]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-foreground/35" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-foreground/35 [animation-delay:0.2s]" />
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
