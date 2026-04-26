"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  BookOpen,
  ChevronDown,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
} from "lucide-react";

import { formatTripWindowDisplay } from "@/lib/trip-timing";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";

const INITIAL_VISIBLE = 5;
const LOAD_MORE_COUNT = 5;

type ChatSidebarProps = {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  workspace: PlannerWorkspaceState | null;
  recentTrips: TripListItemResponse[];
};

export function ChatSidebar({
  collapsed,
  onToggleCollapsed,
  workspace,
  recentTrips,
}: ChatSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE);

  const currentTripId = workspace?.trip.trip_id ?? searchParams.get("trip");
  const recentSessions = useMemo(
    () =>
      recentTrips
        .filter((trip) => matchesTripQuery(trip, query))
        .map((trip) => ({
          id: trip.trip_id,
          title: trip.title,
          subtitle: trip.phase ?? trip.trip_status,
          route:
            trip.from_location || trip.to_location
              ? `${trip.from_location ?? "Origin"} to ${trip.to_location ?? "Destination"}`
              : "Route still being shaped",
          dates: formatTripDates(trip),
          isCurrent: trip.trip_id === currentTripId,
        })),
    [currentTripId, query, recentTrips],
  );

  const visibleSessions = recentSessions.slice(0, visibleCount);
  const hasMore = recentSessions.length > visibleCount;

  function handleNewChat() {
    const params = new URLSearchParams(searchParams.toString());
    params.set("new", Date.now().toString());
    params.delete("trip");
    router.push(`${pathname}?${params.toString()}`);
  }

  function handleShowMore() {
    setVisibleCount((prev) => prev + LOAD_MORE_COUNT);
  }

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
            className={[
              "inline-flex items-center justify-center rounded-lg bg-[color:var(--accent)] text-white transition-opacity hover:opacity-90",
              collapsed
                ? "h-10 w-10"
                : "h-9 flex-1 gap-2 text-[0.8rem] font-semibold",
            ].join(" ")}
            aria-label="New trip"
            title="New trip"
          >
            <Plus className="h-3.5 w-3.5" />
            {!collapsed ? "New Trip" : null}
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
              type="search"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setVisibleCount(INITIAL_VISIBLE);
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

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pt-1">
        {!collapsed ? (
          <>
            <div className="space-y-0.5">
              {visibleSessions.length > 0 ? (
                visibleSessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    onClick={() => router.push(`${pathname}?trip=${session.id}`)}
                    className={[
                      "group flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--accent)]/40",
                      session.isCurrent
                        ? "bg-[color:var(--sidebar-surface-strong)]"
                        : "hover:bg-[color:var(--sidebar-surface)]",
                    ].join(" ")}
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
                        {session.dates ?? session.route}
                      </div>
                    </div>
                  </button>
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
            {visibleSessions.length > 0 ? (
              visibleSessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => router.push(`${pathname}?trip=${session.id}`)}
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
        <Link
          href="/trips?filter=brochure"
          className={[
            "inline-flex items-center justify-center gap-1.5 rounded-lg text-[0.78rem] font-medium text-[color:var(--sidebar-muted-text)] transition-colors hover:bg-[color:var(--sidebar-surface)] hover:text-[color:var(--sidebar-text)]",
            collapsed ? "h-10 w-10" : "flex-1 py-1.5",
          ].join(" ")}
          aria-label="Brochures"
          title="Brochures"
        >
          <BookOpen className="h-3.5 w-3.5" />
          {!collapsed ? "Brochures" : null}
        </Link>
      </div>
    </aside>
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

function formatTripDates(trip: TripListItemResponse) {
  const summary = formatTripWindowDisplay(
    {
      start_date: trip.start_date,
      end_date: trip.end_date,
      travel_window: trip.travel_window,
      trip_length: trip.trip_length,
    },
    { emptyLabel: "" },
  ).trim();

  return summary || null;
}
