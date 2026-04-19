"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BookOpen, ChevronDown, Plus, Search } from "lucide-react";

import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";

const INITIAL_VISIBLE = 5;
const LOAD_MORE_COUNT = 5;

type ChatSidebarProps = {
  workspace: PlannerWorkspaceState | null;
  recentTrips: TripListItemResponse[];
};

export function ChatSidebar({ workspace, recentTrips }: ChatSidebarProps) {
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
          dates: formatTripDates(trip.start_date, trip.end_date),
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
    <aside className="flex h-full min-h-0 flex-col overflow-hidden border-r border-[color:var(--sidebar-shell-border)] bg-[color:var(--sidebar-shell-bg)] text-[color:var(--sidebar-text)]">
      {/* ── New Trip ── */}
      <div className="px-3 pt-4 pb-3">
        <button
          type="button"
          onClick={handleNewChat}
          className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] text-[0.8rem] font-semibold text-white transition-opacity hover:opacity-90"
        >
          <Plus className="h-3.5 w-3.5" />
          New Trip
        </button>
      </div>

      {/* ── Search ── */}
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

      {/* ── Trip list ── */}
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pt-1">
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
      </div>

      {/* ── Footer ── */}
      <div className="flex items-center border-t border-[color:var(--sidebar-shell-border)] px-2 py-2">
        <Link
          href="/trips?filter=brochure"
          className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-[0.78rem] font-medium text-[color:var(--sidebar-muted-text)] transition-colors hover:bg-[color:var(--sidebar-surface)] hover:text-[color:var(--sidebar-text)]"
        >
          <BookOpen className="h-3.5 w-3.5" />
          Brochures
        </Link>
      </div>
    </aside>
  );
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

function formatTripDates(startDate: string | null, endDate: string | null) {
  const startLabel = formatDate(startDate);
  const endLabel = formatDate(endDate);

  if (startLabel && endLabel) {
    return `${startLabel} to ${endLabel}`;
  }

  if (startLabel) {
    return `Starts ${startLabel}`;
  }

  if (endLabel) {
    return `Ends ${endLabel}`;
  }

  return null;
}

function formatDate(value: string | null) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
