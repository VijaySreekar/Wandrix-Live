"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getTrip, getTripDraft } from "@/lib/api/trips";
import { formatTripWindowDisplay } from "@/lib/trip-timing";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { TimelineItem, TripDraft } from "@/types/trip-draft";
import type { TripCreateResponse } from "@/types/trip";

type TripBrochureProps = {
  tripId: string;
};

type LoadedTripData = {
  trip: TripCreateResponse;
  draft: TripDraft;
};

export function TripBrochure({ tripId }: TripBrochureProps) {
  const [data, setData] = useState<LoadedTripData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadBrochure() {
      setIsLoading(true);
      setError(null);

      try {
        const supabase = createSupabaseBrowserClient();
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError || !session?.access_token) {
          throw new Error("Sign in to view this brochure.");
        }

        const [trip, draft] = await Promise.all([
          getTrip(tripId, session.access_token),
          getTripDraft(tripId, session.access_token),
        ]);

        if (!cancelled) {
          setData({ trip, draft });
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not load this brochure.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadBrochure();

    return () => {
      cancelled = true;
    };
  }, [tripId]);

  const timelineGroups = useMemo(() => {
    if (!data) {
      return [];
    }

    return groupTimelineByDay(data.draft.timeline);
  }, [data]);

  if (isLoading) {
    return <BrochureMessage message="Loading brochure..." />;
  }

  if (error || !data) {
    return <BrochureMessage message={error ?? "This brochure is unavailable."} />;
  }

  const { trip, draft } = data;
  const { configuration, module_outputs: moduleOutputs } = draft;
  const activeModules = Object.entries(configuration.selected_modules)
    .filter(([, enabled]) => enabled)
    .map(([key]) => key);

  return (
    <section className="grid gap-4">
      <header className="rounded-xl border border-shell-border bg-shell px-6 py-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-foreground/62">Travel brochure</p>
            <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight text-foreground">
              {draft.title}
            </h1>
            <p className="mt-3 max-w-3xl text-base leading-8 text-foreground/72">
              {formatRoute(configuration.from_location, configuration.to_location)} |{" "}
              {formatTripWindowDisplay(
                {
                  start_date: configuration.start_date,
                  end_date: configuration.end_date,
                  travel_window: configuration.travel_window,
                  trip_length: configuration.trip_length,
                },
                {
                  emptyLabel: "Travel dates still open",
                  includeYear: true,
                },
              )}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              href={`/chat?trip=${trip.trip_id}`}
              className="rounded-md border border-shell-border px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-panel"
            >
              Return to chat
            </Link>
            <Link
              href="/trips"
              className="rounded-md border border-shell-border px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-panel"
            >
              Saved trips
            </Link>
          </div>
        </div>
      </header>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <div className="rounded-xl border border-shell-border bg-shell px-6 py-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <BrochureStat
              label="Travelers"
              value={`${configuration.travelers.adults} adults, ${configuration.travelers.children} children`}
            />
            <BrochureStat
              label="Budget"
              value={
                configuration.budget_gbp
                  ? `GBP ${configuration.budget_gbp.toLocaleString()}`
                  : "Budget open"
              }
            />
            <BrochureStat
              label="Planning phase"
              value={draft.status.phase.replaceAll("_", " ")}
            />
            <BrochureStat
              label="Timeline blocks"
              value={String(draft.timeline.length)}
            />
          </div>

          <div className="mt-6 grid gap-3">
            <SectionTitle title="Trip framing" />
            <div className="grid gap-3 lg:grid-cols-2">
              <div className="rounded-lg border border-shell-border bg-panel px-4 py-4">
                <p className="text-sm font-semibold text-foreground">Modules</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {activeModules.length > 0 ? (
                    activeModules.map((moduleName) => (
                      <span
                        key={moduleName}
                        className="rounded-md border border-shell-border bg-background px-3 py-1 text-xs font-medium text-foreground/72"
                      >
                        {moduleName}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-foreground/68">
                      Modules are still being selected.
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-shell-border bg-panel px-4 py-4">
                <p className="text-sm font-semibold text-foreground">Trip tone</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {configuration.activity_styles.length > 0 ? (
                    configuration.activity_styles.map((style) => (
                      <span
                        key={style}
                        className="rounded-md border border-shell-border bg-background px-3 py-1 text-xs font-medium text-foreground/72"
                      >
                        {style}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-foreground/68">
                      Activity style is still being shaped through conversation.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-3">
            <SectionTitle title="Day by day" />
            {timelineGroups.length > 0 ? (
              <div className="grid gap-3">
                {timelineGroups.map((group, index) => (
                  <article
                    key={`${group.label}-${index}`}
                    className="rounded-lg border border-shell-border bg-panel px-4 py-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-foreground">
                          {group.label}
                        </h3>
                        <p className="mt-1 text-sm text-foreground/60">
                          {group.items.length} planned moments
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 grid gap-3">
                      {group.items.map((item) => (
                        <div
                          key={item.id}
                          className="rounded-md border border-shell-border bg-background px-3 py-3"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-sm font-semibold text-foreground">
                              {item.title}
                            </p>
                            <span className="text-xs text-foreground/55">
                              {item.type}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-foreground/65">
                            {formatTimelineTiming(item)}
                          </p>
                          {item.summary ? (
                            <p className="mt-2 text-sm leading-7 text-foreground/72">
                              {item.summary}
                            </p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <PanelMessage message="The brochure will grow once the planner saves more timeline detail." />
            )}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
            <SectionTitle title="Flights" />
            {moduleOutputs.flights.length > 0 ? (
              <div className="mt-4 grid gap-3">
                {moduleOutputs.flights.map((flight) => (
                  <div
                    key={flight.id}
                    className="rounded-lg border border-shell-border bg-panel px-4 py-4"
                  >
                    <p className="text-sm font-semibold text-foreground">
                      {flight.carrier}
                      {flight.flight_number ? ` ${flight.flight_number}` : ""}
                    </p>
                    <p className="mt-1 text-sm text-foreground/65">
                      {flight.departure_airport} to {flight.arrival_airport}
                    </p>
                    <p className="mt-2 text-sm text-foreground/72">
                      {formatDateTime(flight.departure_time)} to{" "}
                      {formatDateTime(flight.arrival_time)}
                      {flight.duration_text ? ` | ${flight.duration_text}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <PanelMessage message="Flight details have not been structured yet." />
            )}
          </div>

          <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
            <SectionTitle title="Stays" />
            {moduleOutputs.hotels.length > 0 ? (
              <div className="mt-4 grid gap-3">
                {moduleOutputs.hotels.map((hotel) => (
                  <div
                    key={hotel.id}
                    className="rounded-lg border border-shell-border bg-panel px-4 py-4"
                  >
                    <p className="text-sm font-semibold text-foreground">
                      {hotel.hotel_name}
                    </p>
                    <p className="mt-1 text-sm text-foreground/65">
                      {hotel.area ?? "Area still open"}
                    </p>
                    <p className="mt-2 text-sm text-foreground/72">
                      {formatDateTime(hotel.check_in)} through {formatDateTime(hotel.check_out)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <PanelMessage message="Hotel details have not been structured yet." />
            )}
          </div>

          <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
            <SectionTitle title="Weather outlook" />
            {moduleOutputs.weather.length > 0 ? (
              <div className="mt-4 grid gap-3">
                {moduleOutputs.weather.slice(0, 4).map((forecast) => (
                  <div
                    key={forecast.id}
                    className="rounded-lg border border-shell-border bg-panel px-4 py-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-foreground">
                          {forecast.day_label}
                        </p>
                        <p className="mt-1 text-sm text-foreground/65">
                          {forecast.summary}
                        </p>
                      </div>
                      <p className="text-sm font-medium text-foreground/72">
                        {formatTemperatureBand(forecast.high_c, forecast.low_c)}
                      </p>
                    </div>
                    {forecast.notes.length > 0 ? (
                      <p className="mt-2 text-sm leading-7 text-foreground/72">
                        {forecast.notes[0]}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <PanelMessage message="Forecast details will appear here once the planner has enough trip timing context." />
            )}
          </div>

          <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
            <SectionTitle title="Highlights" />
            {moduleOutputs.activities.length > 0 ? (
              <div className="mt-4 grid gap-3">
                {moduleOutputs.activities.slice(0, 5).map((activity) => (
                  <div
                    key={activity.id}
                    className="rounded-lg border border-shell-border bg-panel px-4 py-4"
                  >
                    <p className="text-sm font-semibold text-foreground">
                      {activity.title}
                    </p>
                    <p className="mt-1 text-sm text-foreground/65">
                      {[activity.category, activity.day_label].filter(Boolean).join(" | ") ||
                        "Destination highlight"}
                    </p>
                    {activity.time_label ? (
                      <p className="mt-2 text-sm text-foreground/72">
                        {activity.time_label}
                      </p>
                    ) : null}
                    {activity.notes.length > 0 ? (
                      <p className="mt-2 text-sm leading-7 text-foreground/72">
                        {activity.notes[0]}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <PanelMessage message="Destination highlights will appear here once the planner saves more local recommendations." />
            )}
          </div>

          <div className="rounded-xl border border-shell-border bg-shell px-5 py-5">
            <SectionTitle title="Planning notes" />
            <div className="mt-4 grid gap-2 text-sm leading-7 text-foreground/70">
              {draft.status.missing_fields.length > 0 ? (
                draft.status.missing_fields.map((fieldName) => (
                  <div
                    key={fieldName}
                    className="rounded-lg border border-shell-border bg-panel px-4 py-3"
                  >
                    Still refining: {fieldName}
                  </div>
                ))
              ) : (
                <div className="rounded-lg border border-shell-border bg-panel px-4 py-3">
                  The trip has the core planning fields needed to move into a polished brochure state.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </section>
  );
}

function BrochureMessage({ message }: { message: string }) {
  return (
    <section className="rounded-xl border border-shell-border bg-shell px-6 py-6 text-sm text-foreground/72">
      {message}
    </section>
  );
}

function BrochureStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-shell-border bg-panel px-4 py-4">
      <p className="text-xs font-medium text-foreground/55">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function SectionTitle({ title }: { title: string }) {
  return <h2 className="text-base font-semibold text-foreground">{title}</h2>;
}

function PanelMessage({ message }: { message: string }) {
  return (
    <div className="mt-4 rounded-lg border border-shell-border bg-panel px-4 py-4 text-sm text-foreground/68">
      {message}
    </div>
  );
}

function groupTimelineByDay(items: TimelineItem[]) {
  const groups = new Map<string, TimelineItem[]>();

  for (const item of items) {
    const key = item.day_label ?? "Trip flow";
    const currentGroup = groups.get(key) ?? [];
    currentGroup.push(item);
    groups.set(key, currentGroup);
  }

  return Array.from(groups.entries()).map(([label, groupedItems]) => ({
    label,
    items: groupedItems,
  }));
}

function formatRoute(fromLocation: string | null, toLocation: string | null) {
  if (fromLocation || toLocation) {
    return `${fromLocation ?? "Origin"} to ${toLocation ?? "Destination"}`;
  }

  return "Route still being shaped";
}

function formatTimelineTiming(item: TimelineItem) {
  const timing = [formatDateTime(item.start_at), formatDateTime(item.end_at)]
    .filter((value) => value !== "TBD")
    .join(" to ");

  if (timing) {
    return timing;
  }

  return item.location_label ?? "Timing still open";
}

function formatDateTime(
  value: string | null,
  options?: {
    includeTime?: boolean;
  },
) {
  if (!value) {
    return "TBD";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  const includeTime =
    options?.includeTime ?? (value.includes("T") || value.includes(":"));

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...(includeTime === false
      ? {}
      : {
          hour: "2-digit",
          minute: "2-digit",
        }),
  }).format(parsed);
}

function formatTemperatureBand(high: number | null, low: number | null) {
  if (high == null && low == null) {
    return "Temperatures pending";
  }

  if (high != null && low != null) {
    return `${Math.round(low)}C to ${Math.round(high)}C`;
  }

  return `${Math.round(high ?? low ?? 0)}C`;
}
