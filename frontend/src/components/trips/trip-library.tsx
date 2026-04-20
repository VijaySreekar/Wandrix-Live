"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { downloadTripBrochurePdf } from "@/lib/api/brochures";
import { listTrips } from "@/lib/api/trips";
import { formatTripWindowDisplay } from "@/lib/trip-timing";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { TripListItemResponse } from "@/types/trip";

export function TripLibrary() {
  const [trips, setTrips] = useState<TripListItemResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [downloadingTripId, setDownloadingTripId] = useState<string | null>(null);

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

  const brochureTrips = useMemo(
    () =>
      trips.filter((trip) => {
        return trip.brochure_ready && matchesTripQuery(trip, query);
      }),
    [query, trips],
  );

  async function handleDownloadPdf(trip: TripListItemResponse) {
    if (!trip.latest_brochure_snapshot_id || downloadingTripId === trip.trip_id) {
      return;
    }

    setDownloadingTripId(trip.trip_id);

    try {
      const supabase = createSupabaseBrowserClient();
      const {
        data: { session },
        error: sessionError,
      } = await supabase.auth.getSession();

      if (sessionError || !session?.access_token) {
        throw new Error("Sign in to download brochure PDFs.");
      }

      const { blob, fileName } = await downloadTripBrochurePdf(
        trip.trip_id,
        trip.latest_brochure_snapshot_id,
        session.access_token,
      );

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = fileName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not download the brochure PDF.",
      );
    } finally {
      setDownloadingTripId(null);
    }
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-4 rounded-xl border border-shell-border bg-shell px-5 py-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Saved brochures
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-7 text-foreground/70">
            Only finalized trips appear here. Each card represents a brochure-ready
            trip with its latest saved version, PDF download, and version history.
          </p>
        </div>
        <Link
          href="/chat?new=1"
          className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
        >
          Start new trip
        </Link>
      </div>

      <div className="rounded-xl border border-shell-border bg-shell px-5 py-4">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search finalized brochures by title, city, or module"
          className="w-full rounded-md border border-shell-border bg-panel px-3 py-2 text-sm text-foreground outline-none placeholder:text-foreground/45 focus:border-accent/40"
        />
      </div>

      {isLoading ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          Loading your saved brochures...
        </div>
      ) : error ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          {error}
        </div>
      ) : brochureTrips.length === 0 && trips.length === 0 ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          You do not have any finalized brochures yet. Confirm a trip in chat and it will appear here once the brochure version is saved.
        </div>
      ) : brochureTrips.length === 0 ? (
        <div className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
          No finalized brochures match that search yet.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {brochureTrips.map((trip) => (
            <article
              key={trip.trip_id}
              className="rounded-xl border border-shell-border bg-shell p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-foreground">{trip.title}</h2>
                  <p className="mt-1 text-sm text-foreground/60">
                    Finalized brochure | v{trip.latest_brochure_version ?? 1}
                  </p>
                </div>
                <span className="rounded-md border border-shell-border bg-panel px-2 py-1 text-xs text-foreground/60">
                  {formatDate(trip.updated_at)}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/brochure/${trip.trip_id}`}
                  className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel"
                >
                  Open brochure
                </Link>
                <button
                  type="button"
                  onClick={() => handleDownloadPdf(trip)}
                  className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel"
                >
                  {downloadingTripId === trip.trip_id ? "Preparing PDF..." : "Download PDF"}
                </button>
                <Link
                  href={`/brochure/${trip.trip_id}#history`}
                  className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel"
                >
                  View history
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
                <div>
                  <dt className="text-xs font-medium text-foreground/52">Brochure</dt>
                  <dd className="mt-1 font-medium text-foreground">
                    v{trip.latest_brochure_version ?? 1} | {trip.brochure_versions_count} saved versions
                  </dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
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
