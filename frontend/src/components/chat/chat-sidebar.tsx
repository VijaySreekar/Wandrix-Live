"use client";

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronDown,
  PanelLeftClose,
  PanelLeftOpen,
  PencilLine,
  Plus,
  Search,
  SlidersHorizontal,
  Trash2,
} from "lucide-react";

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/animate-ui/components/radix/dialog";
import { Button } from "@/components/ui/button";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";

const INITIAL_VISIBLE = 5;
const LOAD_MORE_COUNT = 5;
const EXPANDED_ROW_HEIGHT = 42;
const COLLAPSED_ROW_HEIGHT = 48;
const SHOW_MORE_RESERVE = 38;
let sidebarHydrated = false;

function subscribeSidebarHydration(onStoreChange: () => void) {
  if (sidebarHydrated) {
    return () => {};
  }

  queueMicrotask(() => {
    sidebarHydrated = true;
    onStoreChange();
  });

  return () => {};
}

function getSidebarHydrationSnapshot() {
  return sidebarHydrated;
}

type ChatSidebarProps = {
  activeTripId: string | null;
  chatRoute?: string;
  collapsed: boolean;
  onSelectTrip: (tripId: string) => void;
  onPrefetchTrip: (tripId: string) => void;
  onToggleCollapsed: () => void;
  onCreateTrip: () => void;
  onRenameTrip: (tripId: string, nextTitle: string) => Promise<void>;
  onDeleteTrip: (tripId: string) => Promise<void>;
  isCreatingTrip: boolean;
  renamingTripId: string | null;
  deletingTripId: string | null;
  workspace: PlannerWorkspaceState | null;
  recentTrips: TripListItemResponse[];
};

export function ChatSidebar({
  activeTripId,
  chatRoute = "/chat",
  collapsed,
  onSelectTrip,
  onPrefetchTrip,
  onToggleCollapsed,
  onCreateTrip,
  onRenameTrip,
  onDeleteTrip,
  isCreatingTrip,
  renamingTripId,
  deletingTripId,
  workspace,
  recentTrips,
}: ChatSidebarProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [autoVisibleCount, setAutoVisibleCount] = useState(INITIAL_VISIBLE);
  const [manualVisibleCount, setManualVisibleCount] = useState(0);
  const listViewportRef = useRef<HTMLDivElement | null>(null);
  const isHydrated = useSyncExternalStore(
    subscribeSidebarHydration,
    getSidebarHydrationSnapshot,
    () => false,
  );

  const currentTripId = activeTripId ?? workspace?.trip.trip_id ?? null;
  const recentSessions = useMemo(
    () =>
      recentTrips
        .filter((trip) => matchesTripQuery(trip, query))
        .map((trip) => ({
          id: trip.trip_id,
          title:
            trip.trip_id === currentTripId && workspace?.trip.trip_id === trip.trip_id
              ? workspace.tripDraft.title
              : trip.title,
          activityTime: isHydrated
            ? formatTripActivityTime(trip.updated_at)
            : "Recently updated",
          isCurrent: trip.trip_id === currentTripId,
        })),
    [currentTripId, isHydrated, query, recentTrips, workspace],
  );
  const currentSessionIndex = recentSessions.findIndex((session) => session.isCurrent);
  const visibleCount = autoVisibleCount + manualVisibleCount;
  const effectiveVisibleCount =
    currentSessionIndex >= 0
      ? Math.max(visibleCount, currentSessionIndex + 1)
      : visibleCount;

  const visibleSessions = recentSessions.slice(0, effectiveVisibleCount);
  const hasMore = recentSessions.length > effectiveVisibleCount;

  function handleNewChat() {
    onCreateTrip();
  }

  function handleShowMore() {
    setManualVisibleCount((prev) => prev + LOAD_MORE_COUNT);
  }

  useEffect(() => {
    const node = listViewportRef.current;
    if (!node) {
      return;
    }

    function updateVisibleCount() {
      if (!node) {
        return;
      }

      const availableHeight = node.clientHeight;
      const rowHeight = collapsed ? COLLAPSED_ROW_HEIGHT : EXPANDED_ROW_HEIGHT;
      const nextCount = Math.max(
        1,
        Math.floor(Math.max(availableHeight - SHOW_MORE_RESERVE, rowHeight) / rowHeight),
      );

      setAutoVisibleCount(nextCount);
    }

    updateVisibleCount();

    const observer = new ResizeObserver(() => {
      updateVisibleCount();
    });

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, [collapsed]);

  return (
    <aside
      className={[
        "flex h-full min-h-0 flex-col overflow-hidden border-r border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-shell-bg)] text-[color:var(--sidebar-text)]",
        collapsed ? "w-[72px]" : "w-full",
      ].join(" ")}
    >
      <div className={collapsed ? "px-2 pb-2 pt-3" : "px-3 pb-3 pt-3"}>
        <div className={collapsed ? "flex flex-col items-center gap-2" : "flex items-center gap-2"}>
          <button
            type="button"
            onClick={handleNewChat}
            disabled={isCreatingTrip}
            className={[
              "inline-flex items-center justify-center rounded-lg bg-[color:var(--accent)] text-white transition-opacity hover:opacity-90 disabled:cursor-wait disabled:opacity-75",
              collapsed
                ? "h-10 w-10"
                : "h-9 flex-1 gap-2 text-[0.8rem] font-semibold",
            ].join(" ")}
            aria-label="New trip"
            title="New trip"
          >
            <Plus className="h-3.5 w-3.5" />
            {!collapsed ? (isCreatingTrip ? "Creating..." : "New Trip") : null}
          </button>

          <button
            type="button"
            onClick={onToggleCollapsed}
            className={[
              "inline-flex items-center justify-center rounded-lg border border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-surface)] text-[color:var(--sidebar-muted-text)] transition-colors hover:bg-[color:var(--sidebar-hover)] hover:text-[color:var(--sidebar-text)]",
              collapsed ? "h-10 w-10" : "h-9 w-9",
            ].join(" ")}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {!collapsed ? (
        <div className="px-3 pb-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[color:var(--sidebar-muted-text)]" />
            <input
              id="chat-sidebar-search"
              name="chat-sidebar-search"
              type="search"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setManualVisibleCount(0);
              }}
              placeholder="Search…"
              className="w-full rounded-lg border border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-surface)] py-1.5 pl-8 pr-3 text-[0.8rem] text-[color:var(--sidebar-text)] outline-none placeholder:text-[color:var(--sidebar-muted-text)] focus:border-[color:var(--accent)]/30"
            />
          </div>
        </div>
      ) : (
        <div className="px-2 pb-2">
          <div className="flex justify-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-surface)] text-[color:var(--sidebar-muted-text)]">
              <Search className="h-4 w-4" />
            </div>
          </div>
        </div>
      )}

      <div
        ref={listViewportRef}
        className="min-h-0 flex-1 overflow-y-auto px-2 pt-1"
      >
        {!collapsed ? (
          <>
            <div className="space-y-0.5">
              {isHydrated && visibleSessions.length > 0 ? (
                visibleSessions.map((session) => (
                  <div
                    key={session.id}
                    className={[
                      "group flex items-start gap-1 rounded-lg px-1 py-0.5",
                      session.isCurrent
                        ? "bg-[color:var(--sidebar-surface-strong)]"
                        : "hover:bg-[color:var(--sidebar-surface)]",
                    ].join(" ")}
                  >
                    <button
                      type="button"
                      onMouseEnter={() => onPrefetchTrip(session.id)}
                      onFocus={() => onPrefetchTrip(session.id)}
                      onClick={() => {
                        if (session.isCurrent) {
                          return;
                        }

                        onSelectTrip(session.id);
                        router.push(`${chatRoute}?trip=${session.id}`);
                      }}
                      className="flex min-w-0 flex-1 items-start gap-2.5 rounded-md px-1.5 py-1.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--accent)]/40"
                    >
                      <span
                        className={[
                          "mt-[0.4rem] h-1.5 w-1.5 shrink-0 rounded-full transition-colors",
                          session.isCurrent
                            ? "bg-[color:var(--accent)]"
                            : "bg-[color:var(--sidebar-shell-border)] group-hover:bg-[color:var(--sidebar-muted-text)]",
                        ].join(" ")}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-[0.8rem] font-medium leading-snug text-[color:var(--sidebar-text)]">
                          {session.title}
                        </div>
                        <div className="mt-0.5 truncate text-[0.7rem] leading-normal text-[color:var(--sidebar-muted-text)]">
                          {session.activityTime}
                        </div>
                      </div>
                    </button>
                    <RenameTripDialogButton
                      tripId={session.id}
                      tripTitle={session.title}
                      disabled={Boolean(deletingTripId || renamingTripId)}
                      isRenaming={renamingTripId === session.id}
                      onRenameTrip={onRenameTrip}
                    />
                    <DeleteTripDialogButton
                      tripId={session.id}
                      tripTitle={session.title}
                      disabled={Boolean(deletingTripId || renamingTripId)}
                      isDeleting={deletingTripId === session.id}
                      onDeleteTrip={onDeleteTrip}
                    />
                  </div>
                ))
              ) : (
                <p className="px-2.5 py-6 text-center text-[0.78rem] leading-relaxed text-[color:var(--sidebar-muted-text)]">
                  Your trips will appear here once you start planning.
                </p>
              )}
            </div>

            {hasMore && (
              <button
                type="button"
                onClick={handleShowMore}
                className="mt-1 inline-flex w-full items-center justify-center gap-1 rounded-lg py-1.5 text-[0.75rem] font-medium text-[color:var(--sidebar-muted-text)] transition-colors hover:bg-[color:var(--sidebar-surface)] hover:text-[color:var(--sidebar-text)]"
              >
                Show more
                <ChevronDown className="h-3 w-3" />
              </button>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 pb-3">
            {isHydrated && visibleSessions.length > 0 ? (
              visibleSessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  onMouseEnter={() => onPrefetchTrip(session.id)}
                  onFocus={() => onPrefetchTrip(session.id)}
                  onClick={() => {
                    if (session.isCurrent) {
                      return;
                    }

                    onSelectTrip(session.id);
                    router.push(`${chatRoute}?trip=${session.id}`);
                  }}
                  className={[
                    "flex h-10 w-10 items-center justify-center rounded-lg border text-[0.72rem] font-semibold uppercase transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--accent)]/40",
                    session.isCurrent
                      ? "border-[color:var(--accent)] bg-[color:var(--sidebar-surface-strong)] text-[color:var(--accent)]"
                      : "border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-surface)] text-[color:var(--sidebar-muted-text)] hover:bg-[color:var(--sidebar-hover)] hover:text-[color:var(--sidebar-text)]",
                  ].join(" ")}
                  aria-label={session.title}
                  title={session.title}
                >
                  {getTripMonogram(session.title)}
                </button>
              ))
            ) : (
              <p className="px-1 text-center text-[0.72rem] leading-6 text-[color:var(--sidebar-muted-text)]">
                No trips
              </p>
            )}
          </div>
        )}
      </div>

      <div
        className={[
          "flex items-center border-t border-[color:var(--sidebar-shell-border)] py-2",
          collapsed ? "justify-center px-2" : "px-2",
        ].join(" ")}
      >
        <button
          type="button"
          disabled
          className={[
            "inline-flex items-center justify-center gap-1.5 rounded-lg text-[0.78rem] font-medium text-[color:var(--sidebar-muted-text)] opacity-60",
            collapsed ? "h-10 w-10" : "flex-1 py-1.5",
          ].join(" ")}
          aria-label="Configuration"
          title="Configuration"
        >
          <SlidersHorizontal className="h-3.5 w-3.5" />
          {!collapsed ? "Configuration" : null}
        </button>
      </div>
    </aside>
  );
}

function RenameTripDialogButton({
  tripId,
  tripTitle,
  disabled,
  isRenaming,
  onRenameTrip,
}: {
  tripId: string;
  tripTitle: string;
  disabled: boolean;
  isRenaming: boolean;
  onRenameTrip: (tripId: string, nextTitle: string) => Promise<void>;
}) {
  const [draftTitle, setDraftTitle] = useState(tripTitle);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setDraftTitle(tripTitle)}
          className={[
            "mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md transition-all",
            "text-[color:var(--sidebar-muted-text)]/55 opacity-0",
            "group-hover:opacity-100 focus-visible:opacity-100",
            "hover:bg-[color:var(--sidebar-shell-bg)] hover:text-[color:var(--sidebar-text)]",
            "disabled:cursor-wait disabled:opacity-60",
            isRenaming ? "opacity-100" : "",
          ].join(" ")}
          aria-label={`Rename ${tripTitle}`}
          title="Rename trip"
        >
          {isRenaming ? (
            <span className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent" />
          ) : (
            <PencilLine className="h-3.5 w-3.5" />
          )}
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Rename this trip</DialogTitle>
          <DialogDescription>
            Give this saved chat a clearer name so it is easier to find later.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <label
            htmlFor={`rename-trip-${tripId}`}
            className="text-sm font-medium text-foreground"
          >
            Trip name
          </label>
          <input
            id={`rename-trip-${tripId}`}
            type="text"
            value={draftTitle}
            onChange={(event) => setDraftTitle(event.target.value)}
            placeholder="Spring Kyoto food week"
            className="w-full rounded-xl border border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-surface)] px-3 py-2.5 text-sm text-[color:var(--sidebar-text)] outline-none transition-colors focus:border-[color:var(--accent)]/35"
          />
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline" size="lg">
              Cancel
            </Button>
          </DialogClose>
          <DialogClose asChild>
            <Button
              type="button"
              size="lg"
              disabled={!draftTitle.trim() || isRenaming}
              onClick={() => void onRenameTrip(tripId, draftTitle)}
            >
              <PencilLine className="h-4 w-4" />
              Save name
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DeleteTripDialogButton({
  tripId,
  tripTitle,
  disabled,
  isDeleting,
  onDeleteTrip,
}: {
  tripId: string;
  tripTitle: string;
  disabled: boolean;
  isDeleting: boolean;
  onDeleteTrip: (tripId: string) => Promise<void>;
}) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          disabled={disabled}
          className={[
            "mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md transition-all",
            "text-[color:var(--sidebar-muted-text)]/55 opacity-0",
            "group-hover:opacity-100 focus-visible:opacity-100",
            "hover:bg-[color:var(--sidebar-shell-bg)] hover:text-destructive",
            "disabled:cursor-wait disabled:opacity-60",
            isDeleting ? "opacity-100" : "",
          ].join(" ")}
          aria-label={`Delete ${tripTitle}`}
          title="Delete trip"
        >
          {isDeleting ? (
            <span className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" />
          )}
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete this trip?</DialogTitle>
          <DialogDescription>
            This will permanently delete {tripTitle} from Wandrix, including its
            chat history, live board state, and brochure snapshots. This action
            cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline" size="lg">
              Cancel
            </Button>
          </DialogClose>
          <DialogClose asChild>
            <Button
              type="button"
              variant="destructive"
              size="lg"
              onClick={() => void onDeleteTrip(tripId)}
            >
              <Trash2 className="h-4 w-4" />
              Delete trip
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function getTripMonogram(title: string) {
  const words = title
    .split(/\s+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (words.length === 0) {
    return "T";
  }

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0] ?? ""}${words[1][0] ?? ""}`.toUpperCase();
}

function matchesTripQuery(trip: TripListItemResponse, query: string) {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return true;
  }

  const searchableText = [
    trip.title,
    trip.from_location,
    trip.to_location,
    trip.phase,
    ...trip.selected_modules,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return searchableText.includes(normalizedQuery);
}

function formatTripActivityTime(updatedAt: string) {
  const updatedAtDate = new Date(updatedAt);
  if (Number.isNaN(updatedAtDate.getTime())) {
    return "Recently updated";
  }

  const now = new Date();
  const diffMs = now.getTime() - updatedAtDate.getTime();
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  if (diffMs < minuteMs) {
    return "Just now";
  }

  if (diffMs < hourMs) {
    const minutes = Math.max(1, Math.floor(diffMs / minuteMs));
    return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  }

  if (diffMs < dayMs) {
    const hours = Math.max(1, Math.floor(diffMs / hourMs));
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }

  if (diffMs < 7 * dayMs) {
    const days = Math.max(1, Math.floor(diffMs / dayMs));
    return `${days} day${days === 1 ? "" : "s"} ago`;
  }

  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
  }).format(updatedAtDate);
}
