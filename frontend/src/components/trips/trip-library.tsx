"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Calendar,
  Download,
  Loader2,
  MapPin,
  MessageCircle,
  Plus,
  Search,
} from "lucide-react";

import { downloadTripBrochurePdf } from "@/lib/api/brochures";
import { listTrips } from "@/lib/api/trips";
import { getLiveDestinationImage } from "@/components/package/trip-board-cards";
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
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        if (sessionError || !session?.access_token) {
          throw new Error("Sign in to view your saved trips.");
        }
        const response = await listTrips(50, session.access_token);
        if (!cancelled) setTrips(response.items);
      } catch (caughtError) {
        if (!cancelled) {
          setError(caughtError instanceof Error ? caughtError.message : "Could not load saved trips.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void loadTrips();
    return () => { cancelled = true; };
  }, []);

  const { brochureTrips, inProgressTrips } = useMemo(() => {
    const lowerQuery = query.trim().toLowerCase();
    const filtered = lowerQuery
      ? trips.filter((t) => matchesTripQuery(t, lowerQuery))
      : trips;
    return {
      brochureTrips: filtered.filter((t) => t.brochure_ready),
      inProgressTrips: filtered.filter((t) => !t.brochure_ready),
    };
  }, [query, trips]);

  async function handleDownloadPdf(trip: TripListItemResponse) {
    if (!trip.latest_brochure_snapshot_id || downloadingTripId === trip.trip_id) return;
    setDownloadingTripId(trip.trip_id);
    try {
      const supabase = createSupabaseBrowserClient();
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      if (sessionError || !session?.access_token) throw new Error("Sign in to download brochure PDFs.");
      const { blob, fileName } = await downloadTripBrochurePdf(
        trip.trip_id,
        trip.latest_brochure_snapshot_id,
        session.access_token,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Could not download the brochure PDF.");
    } finally {
      setDownloadingTripId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl pb-20 pt-2">

      {/* ── HEADER ──────────────────────────────────────────────── */}
      <div className="mb-8 flex items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Saved Trips</h1>
          <p className="mt-1 text-sm text-foreground/45">
            {isLoading
              ? "Loading..."
              : trips.length === 0
                ? "No trips yet."
                : brochureTrips.length + (brochureTrips.length === 1 ? " finalized" : " finalized") +
                  (inProgressTrips.length > 0 ? " · " + inProgressTrips.length + " in progress" : "")}
          </p>
        </div>
        <Link
          href="/chat?new=1"
          className="flex items-center gap-2 rounded-full bg-[color:var(--accent)] px-5 py-2 text-sm font-semibold text-white transition hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          New trip
        </Link>
      </div>

      {/* ── SEARCH ──────────────────────────────────────────────── */}
      <div className="relative mb-10">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/30" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search destinations, titles..."
          className="w-full rounded-xl border border-[color:var(--planner-board-border)] bg-white py-2.5 pl-10 pr-4 text-sm text-foreground outline-none placeholder:text-foreground/35 focus:border-[color:var(--accent)]/40 focus:ring-2 focus:ring-[color:var(--accent)]/10 transition"
        />
      </div>

      {/* ── STATES ──────────────────────────────────────────────── */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-6 w-6 animate-spin text-foreground/25" />
        </div>
      ) : error ? (
        <p className="text-sm text-foreground/50">{error}</p>
      ) : trips.length === 0 ? (
        <EmptyLibrary />
      ) : (
        <div className="space-y-12">

          {/* Finalized brochures */}
          {brochureTrips.length > 0 && (
            <section>
              <p className="mb-5 text-xs font-semibold uppercase tracking-widest text-foreground/35">
                Finalized
              </p>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {brochureTrips.map((trip) => (
                  <BrochureCard
                    key={trip.trip_id}
                    trip={trip}
                    isDownloading={downloadingTripId === trip.trip_id}
                    onDownload={() => handleDownloadPdf(trip)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* In progress */}
          {inProgressTrips.length > 0 && (
            <section>
              <p className="mb-5 text-xs font-semibold uppercase tracking-widest text-foreground/35">
                In progress
              </p>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {inProgressTrips.map((trip) => (
                  <InProgressCard key={trip.trip_id} trip={trip} />
                ))}
              </div>
            </section>
          )}

          {brochureTrips.length === 0 && inProgressTrips.length === 0 && (
            <p className="py-12 text-center text-sm text-foreground/40">
              No trips match that search.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── BROCHURE CARD ─────────────────────────────────────────────────────────────

function BrochureCard({
  trip,
  isDownloading,
  onDownload,
}: {
  trip: TripListItemResponse;
  isDownloading: boolean;
  onDownload: () => void;
}) {
  const destination = trip.to_location ?? null;
  const travelWindow = formatTripWindow(trip);

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-[color:var(--planner-board-border)] bg-white transition hover:shadow-[0_4px_20px_rgba(0,0,0,0.07)]">

      {/* Image */}
      <Link href={"/brochure/" + trip.trip_id} className="relative block shrink-0 overflow-hidden" style={{ height: "7.5rem" }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={getLiveDestinationImage(destination)}
          alt={destination ?? "Destination"}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/10 to-transparent" />
        {trip.latest_brochure_version && (
          <span className="absolute right-3 top-3 rounded-full bg-black/30 px-2.5 py-0.5 text-[10px] font-semibold text-white/90 backdrop-blur-sm">
            v{trip.latest_brochure_version}
          </span>
        )}
      </Link>

      {/* Body */}
      <div className="flex flex-1 flex-col px-4 py-4">
        <p className="truncate text-sm font-semibold text-foreground">
          {destination ?? trip.title}
        </p>

        <div className="mt-1.5 flex items-center gap-3 text-xs text-foreground/45">
          {(trip.from_location || destination) && (
            <span className="flex items-center gap-1 truncate">
              <MapPin className="h-3 w-3 shrink-0" />
              {formatRouteShort(trip)}
            </span>
          )}
          <span className="flex items-center gap-1 shrink-0">
            <Calendar className="h-3 w-3 shrink-0" />
            {travelWindow}
          </span>
        </div>

        {/* Divider */}
        <div className="my-3.5 border-t border-[color:var(--planner-board-border)]" />

        {/* Actions — single text row */}
        <div className="flex items-center gap-1">
          <Link
            href={"/brochure/" + trip.trip_id}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-[color:var(--accent)] transition hover:bg-[color:var(--accent)]/8"
          >
            <BookOpen className="h-3.5 w-3.5" />
            Open
          </Link>
          <button
            type="button"
            onClick={onDownload}
            disabled={isDownloading}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-foreground/45 transition hover:bg-[color:var(--planner-board-soft)] hover:text-foreground/70 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isDownloading
              ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
              : <Download className="h-3.5 w-3.5" />}
            PDF
          </button>
          <Link
            href={"/chat?trip=" + trip.trip_id}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-foreground/45 transition hover:bg-[color:var(--planner-board-soft)] hover:text-foreground/70"
          >
            <MessageCircle className="h-3.5 w-3.5" />
            Chat
          </Link>
        </div>
      </div>
    </article>
  );
}

// ── IN-PROGRESS CARD ──────────────────────────────────────────────────────────

function InProgressCard({ trip }: { trip: TripListItemResponse }) {
  const destination = trip.to_location ?? null;
  const travelWindow = formatTripWindow(trip);
  const phaseLabel = trip.phase ? trip.phase.replaceAll("_", " ") : "in progress";

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-[color:var(--planner-board-border)] bg-white transition hover:shadow-[0_4px_20px_rgba(0,0,0,0.07)]">

      {/* Image */}
      <Link href={"/chat?trip=" + trip.trip_id} className="relative block shrink-0 overflow-hidden" style={{ height: "7.5rem" }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={getLiveDestinationImage(destination)}
          alt={destination ?? "Destination"}
          className="h-full w-full object-cover opacity-70 transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-black/5 to-transparent" />
        <span className="absolute right-3 top-3 rounded-full bg-black/28 px-2.5 py-0.5 text-[10px] font-medium capitalize text-white/80 backdrop-blur-sm">
          {phaseLabel}
        </span>
      </Link>

      {/* Body */}
      <div className="flex flex-1 flex-col px-4 py-4">
        <p className="truncate text-sm font-semibold text-foreground/70">
          {destination ?? trip.title}
        </p>

        <div className="mt-1.5 flex items-center gap-3 text-xs text-foreground/38">
          {(trip.from_location || destination) && (
            <span className="flex items-center gap-1 truncate">
              <MapPin className="h-3 w-3 shrink-0" />
              {formatRouteShort(trip)}
            </span>
          )}
          <span className="flex items-center gap-1 shrink-0">
            <Calendar className="h-3 w-3 shrink-0" />
            {travelWindow}
          </span>
        </div>

        <div className="my-3.5 border-t border-[color:var(--planner-board-border)]" />

        <Link
          href={"/chat?trip=" + trip.trip_id}
          className="flex items-center gap-1.5 self-start rounded-lg px-2.5 py-1.5 text-xs font-medium text-foreground/45 transition hover:bg-[color:var(--planner-board-soft)] hover:text-foreground/70"
        >
          <MessageCircle className="h-3.5 w-3.5" />
          Continue planning
        </Link>
      </div>
    </article>
  );
}

// ── EMPTY STATE ───────────────────────────────────────────────────────────────

function EmptyLibrary() {
  return (
    <div className="py-24 text-center">
      <p className="text-sm font-medium text-foreground/50">No saved trips yet</p>
      <p className="mt-1.5 text-sm text-foreground/35">
        Your in-progress and finalized trips will appear here once you start planning.
      </p>
      <Link
        href="/chat?new=1"
        className="mt-6 inline-flex items-center gap-2 rounded-full bg-[color:var(--accent)] px-5 py-2 text-sm font-semibold text-white transition hover:opacity-90"
      >
        <Plus className="h-4 w-4" />
        Start a trip
      </Link>
    </div>
  );
}

// ── HELPERS ───────────────────────────────────────────────────────────────────

function formatRouteShort(trip: TripListItemResponse) {
  if (trip.from_location && trip.to_location) return trip.from_location + " → " + trip.to_location;
  if (trip.to_location) return trip.to_location;
  if (trip.from_location) return trip.from_location;
  return "";
}

function formatTripWindow(trip: TripListItemResponse) {
  return formatTripWindowDisplay(
    {
      start_date: trip.start_date,
      end_date: trip.end_date,
      travel_window: trip.travel_window,
      trip_length: trip.trip_length,
    },
    { emptyLabel: "Dates open" },
  );
}

function matchesTripQuery(trip: TripListItemResponse, lowerQuery: string) {
  return [trip.title, trip.from_location, trip.to_location, trip.phase, ...trip.selected_modules]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .includes(lowerQuery);
}
