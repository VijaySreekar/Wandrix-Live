"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getProviderStatuses } from "@/lib/api/providers";
import { getTripDraft, listTrips } from "@/lib/api/trips";
import { formatTripWindowDisplay } from "@/lib/trip-timing";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type {
  ActivityDetail,
  FlightDetail,
  HotelStayDetail,
  TimelineItem,
  TripDraft,
} from "@/types/trip-draft";
import type { ProviderStatusItem } from "@/types/provider-status";
import type { TripListItemResponse } from "@/types/trip";

type ModuleKind = "flights" | "hotels" | "activities";

type TripModuleWorkspaceProps = {
  module: ModuleKind;
  initialTripId?: string;
};

export function TripModuleWorkspace({
  module,
  initialTripId,
}: TripModuleWorkspaceProps) {
  const router = useRouter();
  const [trips, setTrips] = useState<TripListItemResponse[]>([]);
  const [activeTripId, setActiveTripId] = useState<string | null>(initialTripId ?? null);
  const [draft, setDraft] = useState<TripDraft | null>(null);
  const [providerStatuses, setProviderStatuses] = useState<ProviderStatusItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadWorkspace() {
      setIsLoading(true);
      setError(null);

      try {
        const supabase = createSupabaseBrowserClient();
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError || !session?.access_token) {
          throw new Error("Sign in to view this reference view.");
        }

        const [tripResponse, providerStatusResponse] = await Promise.all([
          listTrips(50, session.access_token),
          getProviderStatuses(session.access_token),
        ]);
        const selectedTrip =
          tripResponse.items.find((trip) => trip.trip_id === initialTripId) ??
          tripResponse.items[0] ??
          null;

        if (!selectedTrip) {
          if (!cancelled) {
            setTrips([]);
            setDraft(null);
            setProviderStatuses(providerStatusResponse.items);
          }
          return;
        }

        const draftResponse = await getTripDraft(
          selectedTrip.trip_id,
          session.access_token,
        );

        if (!cancelled) {
          setTrips(tripResponse.items);
          setActiveTripId(selectedTrip.trip_id);
          setDraft(draftResponse);
          setProviderStatuses(providerStatusResponse.items);
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not load the module reference view.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadWorkspace();

    return () => {
      cancelled = true;
    };
  }, [initialTripId]);

  const activeTrip =
    trips.find((trip) => trip.trip_id === activeTripId) ?? null;
  const moduleMeta = getModuleMeta(module);

  const moduleItems = useMemo(() => {
    if (!draft) {
      return [];
    }

    switch (module) {
      case "flights":
        return draft.module_outputs.flights;
      case "hotels":
        return draft.module_outputs.hotels;
      case "activities":
        return draft.module_outputs.activities;
      default:
        return [];
    }
  }, [draft, module]);

  const timelineItems = useMemo(() => {
    if (!draft) {
      return [];
    }

    return draft.timeline.filter(
      (item) => item.type === getModuleMeta(module).timelineType,
    );
  }, [draft, module]);

  const moduleEnabled = draft
    ? module === "flights"
      ? draft.configuration.selected_modules.flights
      : module === "hotels"
        ? draft.configuration.selected_modules.hotels
        : draft.configuration.selected_modules.activities
    : false;
  const moduleProviderStatus =
    module === "flights"
      ? providerStatuses.find((item) => item.provider === "amadeus") ?? null
      : null;

  return (
    <section className="grid min-h-[calc(100vh-4.5rem)] gap-3 lg:grid-cols-[290px_minmax(0,1fr)]">
      <aside className="flex min-h-0 flex-col rounded-xl border border-shell-border bg-shell">
        <div className="border-b border-shell-border px-4 py-4">
          <h1 className="text-lg font-semibold text-foreground">{moduleMeta.label}</h1>
          <p className="mt-1 text-sm text-foreground/68">
            {moduleMeta.sidebarCopy}
          </p>
        </div>

        <div className="border-b border-shell-border px-4 py-4">
          <Link
            href="/chat?new=1"
            className="inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
          >
            Start new trip
          </Link>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          <div className="grid gap-2">
            {trips.length > 0 ? (
              trips.map((trip) => (
                <button
                  key={trip.trip_id}
                  type="button"
                  onClick={() => router.replace(`/${module}?trip=${trip.trip_id}`)}
                  className={`rounded-lg border px-3 py-3 text-left transition-colors ${
                    trip.trip_id === activeTripId
                      ? "border-accent/30 bg-accent-soft"
                      : "border-shell-border bg-panel hover:bg-panel-strong"
                  }`}
                >
                  <p className="text-sm font-medium text-foreground">{trip.title}</p>
                  <p className="mt-1 text-xs text-foreground/58">
                    {formatRoute(trip)}
                  </p>
                </button>
              ))
            ) : (
              <div className="rounded-lg border border-shell-border bg-panel px-3 py-3 text-sm text-foreground/65">
                Start a trip in chat first and it will appear here.
              </div>
            )}
          </div>
        </div>
      </aside>

      <div className="grid gap-3">
        <header className="rounded-xl border border-shell-border bg-shell px-5 py-4">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="text-3xl font-semibold tracking-tight text-foreground">
                {moduleMeta.heading}
              </h2>
              <p className="mt-1 max-w-3xl text-sm leading-7 text-foreground/70">
                {moduleMeta.description}
              </p>
            </div>
            {activeTrip ? (
              <Link
                href={`/chat?trip=${activeTrip.trip_id}`}
                className="rounded-md border border-shell-border px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-panel"
              >
                Open in chat
              </Link>
            ) : null}
          </div>
        </header>

        {moduleProviderStatus ? (
          <ProviderStatusBanner status={moduleProviderStatus} />
        ) : null}

        {isLoading ? (
          <ModuleMessage message="Loading the reference view..." />
        ) : error ? (
          <ModuleMessage message={error} />
        ) : !activeTrip || !draft ? (
          <ModuleMessage message="No saved trip is selected yet." />
        ) : (
          <>
            <section className="grid gap-3 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      {activeTrip.title}
                    </p>
                    <p className="mt-1 text-sm text-foreground/62">
                      {formatRoute(activeTrip)}
                    </p>
                  </div>
                  <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5 text-xs text-foreground/60">
                    {formatPhase(activeTrip.phase ?? activeTrip.trip_status)}
                  </span>
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <StatCard
                    label="Travel window"
                    value={formatDateWindow(activeTrip)}
                  />
                  <StatCard
                    label="Module status"
                    value={moduleEnabled ? "Enabled" : "Not selected"}
                  />
                  <StatCard
                    label="Structured items"
                    value={String(moduleItems.length)}
                  />
                  <StatCard
                    label="Timeline blocks"
                    value={String(timelineItems.length)}
                  />
                </div>
              </div>

              <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
                <h3 className="text-base font-semibold text-foreground">
                  Planning notes
                </h3>
                <ul className="mt-4 grid gap-2 text-sm leading-7 text-foreground/70">
                  <li className="rounded-lg border border-shell-border bg-panel px-3 py-2">
                    {moduleMeta.primaryNote}
                  </li>
                  <li className="rounded-lg border border-shell-border bg-panel px-3 py-2">
                    This view already reads from the saved trip draft, so it will improve as the planner fills richer module data.
                  </li>
                  <li className="rounded-lg border border-shell-border bg-panel px-3 py-2">
                    The chat workspace remains the main place for planning while these module pages stay focused on inspection and reference.
                  </li>
                </ul>
              </div>
            </section>

            <section className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
                <h3 className="text-base font-semibold text-foreground">
                  {moduleMeta.itemsHeading}
                </h3>
                {module === "flights" ? (
                  <FlightList items={moduleItems as FlightDetail[]} />
                ) : module === "hotels" ? (
                  <HotelList items={moduleItems as HotelStayDetail[]} />
                ) : (
                  <ActivityList items={moduleItems as ActivityDetail[]} />
                )}
              </div>

              <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
                <h3 className="text-base font-semibold text-foreground">
                  Timeline blocks
                </h3>
                <TimelineList items={timelineItems} />
              </div>
            </section>
          </>
        )}
      </div>
    </section>
  );
}

function ProviderStatusBanner({ status }: { status: ProviderStatusItem }) {
  return (
    <section className="rounded-xl border border-shell-border bg-shell px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">
            Live provider status
          </p>
          <p className="mt-1 text-sm text-foreground/72">{status.message}</p>
        </div>
        <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5 text-xs text-foreground/60">
          {status.status.replaceAll("_", " ")}
        </span>
      </div>
    </section>
  );
}

function ModuleMessage({ message }: { message: string }) {
  return (
    <section className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
      {message}
    </section>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-shell-border bg-panel px-4 py-4">
      <p className="text-xs font-medium text-foreground/55">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function FlightList({ items }: { items: FlightDetail[] }) {
  if (items.length === 0) {
    return (
      <EmptyModuleState message="No structured flights have been saved for this trip yet." />
    );
  }

  return (
    <div className="mt-4 grid gap-3">
      {items.map((flight) => (
        <article
          key={flight.id}
          className="rounded-lg border border-shell-border bg-panel px-4 py-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">
                {flight.carrier}
                {flight.flight_number ? ` ${flight.flight_number}` : ""}
              </p>
              <p className="mt-1 text-sm text-foreground/62">
                {flight.departure_airport} to {flight.arrival_airport}
              </p>
            </div>
            <span className="rounded-md border border-shell-border bg-background px-2 py-1 text-xs text-foreground/60">
              {flight.direction}
            </span>
          </div>
          <p className="mt-3 text-sm text-foreground/70">
            {flight.departure_time ?? "TBD"} to {flight.arrival_time ?? "TBD"}
            {flight.duration_text ? ` - ${flight.duration_text}` : ""}
          </p>
          {flight.notes.length > 0 ? (
            <ul className="mt-3 grid gap-2 text-sm text-foreground/65">
              {flight.notes.map((note) => (
                <li
                  key={note}
                  className="rounded-md border border-shell-border bg-background px-3 py-2"
                >
                  {note}
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function HotelList({ items }: { items: HotelStayDetail[] }) {
  if (items.length === 0) {
    return (
      <EmptyModuleState message="No structured hotel stays have been saved for this trip yet." />
    );
  }

  return (
    <div className="mt-4 grid gap-3">
      {items.map((hotel) => (
        <article
          key={hotel.id}
          className="rounded-lg border border-shell-border bg-panel px-4 py-4"
        >
          <p className="text-sm font-semibold text-foreground">{hotel.hotel_name}</p>
          <p className="mt-1 text-sm text-foreground/62">
            {hotel.area ?? "Area still open"}
          </p>
          <p className="mt-3 text-sm text-foreground/70">
            {hotel.check_in ?? "TBD"} through {hotel.check_out ?? "TBD"}
          </p>
          {hotel.notes.length > 0 ? (
            <ul className="mt-3 grid gap-2 text-sm text-foreground/65">
              {hotel.notes.map((note) => (
                <li
                  key={note}
                  className="rounded-md border border-shell-border bg-background px-3 py-2"
                >
                  {note}
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function ActivityList({ items }: { items: ActivityDetail[] }) {
  if (items.length === 0) {
    return (
      <EmptyModuleState message="No structured activity highlights have been saved for this trip yet." />
    );
  }

  return (
    <div className="mt-4 grid gap-3">
      {items.map((activity) => (
        <article
          key={activity.id}
          className="rounded-lg border border-shell-border bg-panel px-4 py-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">{activity.title}</p>
              <p className="mt-1 text-sm text-foreground/62">
                {activity.category ?? "Destination highlight"}
              </p>
            </div>
            <span className="rounded-md border border-shell-border bg-background px-2 py-1 text-xs text-foreground/60">
              {activity.day_label ?? "Trip flow"}
            </span>
          </div>
          <p className="mt-3 text-sm text-foreground/70">
            {activity.time_label ?? "Timing still open"}
          </p>
          {activity.notes.length > 0 ? (
            <ul className="mt-3 grid gap-2 text-sm text-foreground/65">
              {activity.notes.map((note) => (
                <li
                  key={note}
                  className="rounded-md border border-shell-border bg-background px-3 py-2"
                >
                  {note}
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function TimelineList({ items }: { items: TimelineItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyModuleState message="The planner has not saved matching timeline blocks for this module yet." />
    );
  }

  return (
    <div className="mt-4 grid gap-3">
      {items.map((item) => (
        <article
          key={item.id}
          className="rounded-lg border border-shell-border bg-panel px-4 py-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">{item.title}</p>
              <p className="mt-1 text-sm text-foreground/62">
                {[item.day_label, item.location_label].filter(Boolean).join(" - ") ||
                  "Draft block"}
              </p>
            </div>
            <span className="rounded-md border border-shell-border bg-background px-2 py-1 text-xs text-foreground/60">
              {item.status}
            </span>
          </div>
          {item.summary ? (
            <p className="mt-3 text-sm text-foreground/70">{item.summary}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function EmptyModuleState({ message }: { message: string }) {
  return (
    <div className="mt-4 rounded-lg border border-shell-border bg-panel px-4 py-4 text-sm text-foreground/68">
      {message}
    </div>
  );
}

function formatRoute(trip: TripListItemResponse) {
  if (trip.from_location || trip.to_location) {
    return `${trip.from_location ?? "Origin"} to ${trip.to_location ?? "Destination"}`;
  }

  return "Route still being shaped";
}

function formatDateWindow(trip: TripListItemResponse) {
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

function formatPhase(value: string) {
  return value.replaceAll("_", " ");
}

function getModuleMeta(module: ModuleKind) {
  switch (module) {
    case "flights":
      return {
        label: "Flights",
        heading: "Flight reference",
        sidebarCopy: "Choose a saved trip and inspect the route and flight layer for that plan.",
        description:
          "Use this surface to inspect route context, flight placeholders, and timeline movement for the selected trip while continuing to plan inside chat.",
        primaryNote:
          "Flight discovery will eventually bring in carrier, timing, and route options here, but final trip shaping still happens in chat.",
        itemsHeading: "Structured flight items",
        timelineType: "flight" as const,
      };
    case "hotels":
      return {
        label: "Hotels",
        heading: "Hotel reference",
        sidebarCopy: "Choose a saved trip and inspect the stay and neighborhood layer for that plan.",
        description:
          "Use this surface to inspect stay details, hotel placeholders, and lodging blocks for the selected trip while continuing to plan inside chat.",
        primaryNote:
          "Hotel discovery will eventually bring in stay options, areas, and check-in details here, but final trip shaping still happens in chat.",
        itemsHeading: "Structured hotel items",
        timelineType: "hotel" as const,
      };
    case "activities":
      return {
        label: "Activities",
        heading: "Activity reference",
        sidebarCopy: "Choose a saved trip and inspect the destination highlights and itinerary moments for that plan.",
        description:
          "Use this surface to inspect saved destination highlights, activity suggestions, and the moments they occupy in the itinerary while continuing to plan inside chat.",
        primaryNote:
          "This view already reflects live Geoapify-backed highlights when the planner has enough destination context, but final trip shaping still happens in chat.",
        itemsHeading: "Structured activity items",
        timelineType: "activity" as const,
      };
  }
}
