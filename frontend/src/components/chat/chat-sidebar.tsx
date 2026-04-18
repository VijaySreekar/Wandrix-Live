"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";


type ChatSidebarProps = {
  workspace: PlannerWorkspaceState | null;
  recentTrips: TripListItemResponse[];
};


export function ChatSidebar({ workspace, recentTrips }: ChatSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");

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
          modules: trip.selected_modules,
          isCurrent: trip.trip_id === currentTripId,
        })),
    [currentTripId, query, recentTrips],
  );

  function handleNewChat() {
    const params = new URLSearchParams(searchParams.toString());
    params.set("new", Date.now().toString());
    params.delete("trip");
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <aside className="flex h-full min-h-0 flex-col rounded-xl border border-shell-border bg-shell">
      <div className="border-b border-shell-border p-4">
        <button
          type="button"
          onClick={handleNewChat}
          className="inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
        >
          New chat
        </button>
      </div>

      <div className="border-b border-shell-border px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Saved trips</h2>
            <p className="mt-1 text-sm text-foreground/68">
              View every saved board and brochure-ready plan.
            </p>
          </div>
          <Link
            href="/trips"
            className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground/72 transition-colors hover:bg-panel"
          >
            Open
          </Link>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-foreground">Recent sessions</h2>
          <span className="text-xs text-foreground/55">{recentSessions.length}</span>
        </div>

        <div className="mt-3">
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search trips"
            className="w-full rounded-md border border-shell-border bg-panel px-3 py-2 text-sm text-foreground outline-none placeholder:text-foreground/45 focus:border-accent/40"
          />
        </div>

        <div className="mt-4 grid gap-2">
          {recentSessions.length > 0 ? (
            recentSessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => router.push(`${pathname}?trip=${session.id}`)}
                className={`rounded-lg border px-3 py-3 text-left transition-colors ${
                  session.isCurrent
                    ? "border-accent/30 bg-accent-soft"
                    : "border-shell-border bg-panel hover:bg-panel-strong"
                }`}
              >
                <p className="text-sm font-medium text-foreground">{session.title}</p>
                <p className="mt-1 text-xs text-foreground/58">{session.route}</p>
                <p className="mt-2 text-xs text-foreground/58">
                  {session.subtitle.replaceAll("_", " ")}
                </p>
                {session.modules.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {session.modules.slice(0, 3).map((moduleName) => (
                      <span
                        key={moduleName}
                        className="rounded-md border border-shell-border bg-background px-2 py-1 text-[11px] text-foreground/62"
                      >
                        {moduleName}
                      </span>
                    ))}
                  </div>
                ) : null}
              </button>
            ))
          ) : (
            <div className="rounded-lg border border-shell-border bg-panel px-3 py-3 text-sm text-foreground/65">
              Your recent trip sessions will appear here once you start planning.
            </div>
          )}
        </div>
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
