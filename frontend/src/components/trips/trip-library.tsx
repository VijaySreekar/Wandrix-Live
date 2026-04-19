"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { listTrips } from "@/lib/api/trips";
import { formatTripWindowDisplay } from "@/lib/trip-timing";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { TripListItemResponse } from "@/types/trip";

type TripLibraryFilter = "all" | "active" | "review" | "brochure";

export function TripLibrary() {
  const searchParams = useSearchParams();
  const [trips, setTrips] = useState<TripListItemResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<TripLibraryFilter>(() =>
    resolveTripLibraryFilter(searchParams.get("filter")),
  );

  useEffect(() => {
    let cancelled = false;

    async function loadTrips() {
      setIsLoading(true);
      setError(null);

      try {
        const supabase = createSupabaseBrowserClient();
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError || !session?.access_token) {
          throw new Error("Sign in to view your saved trips.");
        }

        const response = await listTrips(50, session.access_token);

        if (!cancelled) {
          setTrips(response.items);
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not load saved trips.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadTrips();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredTrips = useMemo(
    () =>
      trips.filter((trip) => {
        if (!matchesTripQuery(trip, query)) {
          return false;
        }

        if (filter === "active") {
          return !trip.brochure_ready;
        }

        if (filter === "review") {
          return (trip.phase ?? trip.trip_status) === "reviewing";
        }

        if (filter === "brochure") {
          return trip.brochure_ready;
        }

        return true;
      }),
    [filter, query, trips],
  );

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-4 rounded-xl border border-shell-border bg-shell px-5 py-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Trip library
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-7 text-foreground/70">
            Every persisted trip lives here. Use the brochure-ready filter for
            finished trips that are ready to open as brochure-style output.
          </p>
        </div>
        <Link
          href="/chat?new=1"
          className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
        >
          Start new trip
        </Link>
      </div>

      <div className="flex flex-col gap-3 rounded-xl border border-shell-border bg-shell px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {[
            { label: "All trips", value: "all" },
            { label: "In progress", value: "active" },
            { label: "Ready for review", value: "review" },
            { label: "Brochure-ready", value: "brochure" },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setFilter(option.value as TripLibraryFilter)}
              className={`rounded-md border px-3 py-2 text-sm transition-colors ${
                filter === option.value
                  ? "border-accent/35 bg-accent-soft text-foreground"
                  : "border-shell-border bg-panel text-foreground/70 hover:bg-panel-strong"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by title, city, or module"
          className="w-full rounded-md border border-shell-border bg-panel px-3 py-2 text-sm text-foreground outline-none placeholder:text-foreground/45 focus:border-accent/40 lg:max-w-sm"
        />
      </div>

      {isLoading ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          Loading your saved trips...
        </div>
      ) : error ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          {error}
        </div>
      ) : trips.length === 0 ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          You do not have any trips yet. Start a chat and the session will appear here.
        </div>
      ) : filteredTrips.length === 0 ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          No trips match that filter yet. Try a different search or switch between in-progress and brochure-ready trips.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filteredTrips.map((trip) => (
            <article
              key={trip.trip_id}
              className="rounded-xl border border-shell-border bg-shell p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-foreground">{trip.title}</h2>
                  <p className="mt-1 text-sm text-foreground/60">
                    {formatPhase(trip.phase ?? trip.trip_status)}
                  </p>
                </div>
                <span className="rounded-md border border-shell-border bg-panel px-2 py-1 text-xs text-foreground/60">
                  {formatDate(trip.updated_at)}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/chat?trip=${trip.trip_id}`}
                  className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel"
                >
                  Open chat
                </Link>
                <Link
                  href={`/brochure/${trip.trip_id}`}
                  className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel"
                >
                  Brochure
                </Link>
              </div>

              <div className="mt-4 rounded-lg border border-shell-border bg-panel px-3 py-3">
                <p className="text-sm font-medium text-foreground">
                  {formatRoute(trip)}
                </p>
                <p className="mt-1 text-sm text-foreground/62">
                  {formatTripWindow(trip)}
                </p>
              </div>

              <div className="mt-3 flex flex-wrap gap-1.5">
                {trip.selected_modules.length > 0 ? (
                  trip.selected_modules.map((moduleName) => (
                    <span
                      key={moduleName}
                      className="rounded-md border border-shell-border bg-panel px-2 py-1 text-[11px] text-foreground/62"
                    >
                      {moduleName}
                    </span>
                  ))
                ) : (
                  <span className="rounded-md border border-shell-border bg-panel px-2 py-1 text-[11px] text-foreground/62">
                    Modules still open
                  </span>
                )}
              </div>

              <dl className="mt-5 grid gap-3 text-sm text-foreground/68">
                <div>
                  <dt className="text-xs font-medium text-foreground/52">Timeline</dt>
                  <dd className="mt-1 font-medium text-foreground">
                    {trip.timeline_item_count} planned items
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-foreground/52">Thread</dt>
                  <dd className="mt-1 font-medium text-foreground">{trip.thread_id}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-foreground/52">Created</dt>
                  <dd className="mt-1">{formatDate(trip.created_at)}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function resolveTripLibraryFilter(value: string | null): TripLibraryFilter {
  if (value === "active" || value === "review" || value === "brochure") {
    return value;
  }

  return "all";
}

function formatPhase(value: string) {
  return value.replaceAll("_", " ");
}

function formatRoute(trip: TripListItemResponse) {
  if (trip.from_location || trip.to_location) {
    return `${trip.from_location ?? "Origin"} to ${trip.to_location ?? "Destination"}`;
  }

  return "Route still being shaped";
}

function formatTripWindow(trip: TripListItemResponse) {
  return formatTripWindowDisplay(
    {
      start_date: trip.start_date,
      end_date: trip.end_date,
      travel_window: trip.travel_window,
      trip_length: trip.trip_length,
    },
    { emptyLabel: "Travel dates still open" },
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
  }).format(new Date(value));
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
