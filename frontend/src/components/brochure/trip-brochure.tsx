"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  downloadTripBrochurePdf,
  getLatestTripBrochure,
  getTripBrochure,
  listTripBrochures,
} from "@/lib/api/brochures";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type {
  BrochureHistoryItem,
  BrochureSnapshot,
  BrochureWarning,
} from "@/types/brochure";
import type { TimelineItem } from "@/types/trip-draft";

type TripBrochureProps = {
  tripId: string;
  requestedVersion?: string | null;
};

export function TripBrochure({
  tripId,
  requestedVersion = null,
}: TripBrochureProps) {
  const [snapshot, setSnapshot] = useState<BrochureSnapshot | null>(null);
  const [history, setHistory] = useState<BrochureHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
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

        const historyResponse = await listTripBrochures(
          tripId,
          session.access_token,
        );
        const nextHistory = historyResponse.items;
        const selectedHistoryItem =
          resolveRequestedVersion(nextHistory, requestedVersion) ?? nextHistory[0] ?? null;

        const nextSnapshot = selectedHistoryItem
          ? await getTripBrochure(
              tripId,
              selectedHistoryItem.snapshot_id,
              session.access_token,
            )
          : await getLatestTripBrochure(tripId, session.access_token);

        if (!cancelled) {
          setHistory(nextHistory);
          setSnapshot(nextSnapshot);
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
  }, [requestedVersion, tripId]);

  const warningMap = useMemo(() => {
    const map = new Map<string, BrochureWarning[]>();
    for (const warning of snapshot?.payload.warnings ?? []) {
      for (const relatedTimelineId of warning.related_timeline_ids) {
        const existing = map.get(relatedTimelineId) ?? [];
        existing.push(warning);
        map.set(relatedTimelineId, existing);
      }
    }
    return map;
  }, [snapshot]);

  async function handleDownloadPdf() {
    if (!snapshot || isDownloading) {
      return;
    }

    setIsDownloading(true);

    try {
      const supabase = createSupabaseBrowserClient();
      const {
        data: { session },
        error: sessionError,
      } = await supabase.auth.getSession();

      if (sessionError || !session?.access_token) {
        throw new Error("Sign in to download this brochure.");
      }

      const { blob, fileName } = await downloadTripBrochurePdf(
        tripId,
        snapshot.snapshot_id,
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
          : "Could not download this brochure PDF.",
      );
    } finally {
      setIsDownloading(false);
    }
  }

  if (isLoading) {
    return <BrochureMessage message="Loading brochure snapshot..." />;
  }

  if (error || !snapshot) {
    return (
      <BrochureMessage message={error ?? "This brochure is unavailable right now."} />
    );
  }

  const payload = snapshot.payload;

  return (
    <section className="grid gap-5 pb-8">
      <header
        className="relative overflow-hidden rounded-[2rem] border border-shell-border bg-shell p-6 sm:p-8"
        style={{
          backgroundImage: `linear-gradient(180deg, rgba(23, 20, 17, 0.18) 0%, rgba(23, 20, 17, 0.68) 100%), url(${payload.hero_image.url})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.22),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.08),transparent_24%)]" />
        <div className="relative flex min-h-[25rem] flex-col justify-between gap-10">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              <MetaPill label="Wandrix brochure" />
              <MetaPill label={`Version ${snapshot.version_number}`} />
              <MetaPill label={payload.travel_window_text} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/chat?trip=${tripId}`}
                className="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/16"
              >
                Return to chat
              </Link>
              <Link
                href="/trips?filter=brochure"
                className="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/16"
              >
                Saved trips
              </Link>
              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={isDownloading}
                className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-stone-900 transition hover:bg-white/92 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isDownloading ? "Preparing PDF..." : "Download PDF"}
              </button>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(15rem,0.8fr)]">
            <div className="max-w-4xl">
              <p className="font-display text-sm uppercase tracking-[0.24em] text-white/72">
                {payload.route_text}
              </p>
              <h1 className="mt-3 font-display text-5xl font-semibold tracking-tight text-white sm:text-6xl">
                {payload.title}
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-8 text-white/82 sm:text-lg">
                {payload.executive_summary}
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <MetaPill label={payload.party_text} subtle />
                <MetaPill label={payload.budget_text} subtle />
                {payload.style_tags.map((tag) => (
                  <MetaPill key={tag} label={tag} subtle />
                ))}
              </div>
            </div>

            <aside
              id="history"
              className="self-end rounded-[1.5rem] border border-white/16 bg-white/10 p-4 backdrop-blur-md"
            >
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">
                Brochure history
              </p>
              <div className="mt-3 grid gap-2">
                {history.length > 0 ? (
                  history.map((item) => (
                    <Link
                      key={item.snapshot_id}
                      href={`/brochure/${tripId}?version=${item.version_number}`}
                      className={`rounded-2xl border px-3 py-3 text-sm transition ${
                        item.snapshot_id === snapshot.snapshot_id
                          ? "border-white/30 bg-white/18 text-white"
                          : "border-white/10 bg-black/10 text-white/72 hover:bg-white/12"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">Version {item.version_number}</span>
                        {item.is_latest ? (
                          <span className="rounded-full border border-white/18 px-2 py-0.5 text-[11px] uppercase tracking-[0.16em] text-white/72">
                            Latest
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 text-xs text-white/64">
                        Saved {formatDate(item.finalized_at)}
                      </p>
                    </Link>
                  ))
                ) : (
                  <p className="text-sm leading-6 text-white/72">
                    This trip does not have brochure history yet.
                  </p>
                )}
              </div>
            </aside>
          </div>
        </div>
      </header>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.12fr)_minmax(18rem,0.88fr)]">
        <div className="grid gap-5">
          <Panel>
            <SectionKicker kicker="Trip at a glance" title={payload.route_text} />
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <InsightCard label="Trip window" value={payload.travel_window_text} />
              <InsightCard label="Travel party" value={payload.party_text} />
              <InsightCard label="Budget posture" value={payload.budget_text} />
              <InsightCard
                label="Modules"
                value={
                  payload.module_tags.length > 0
                    ? payload.module_tags.join(", ")
                    : "Module mix still open"
                }
              />
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {payload.metrics.map((metric) => (
                <MetricCard key={metric.label} metric={metric} />
              ))}
            </div>
          </Panel>

          <Panel>
            <SectionKicker
              kicker="Warnings"
              title="What still needs care before you travel"
              summary="Warnings are frozen into this brochure snapshot so they survive reopening or later replanning."
            />
            <div className="mt-6 grid gap-3">
              {payload.warnings.length > 0 ? (
                payload.warnings.map((warning) => (
                  <article
                    key={warning.id}
                    className="rounded-[1.4rem] border border-shell-border bg-accent-soft px-4 py-4"
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-accent-strong">
                      {warning.category.replaceAll("_", " ")}
                    </p>
                    <h3 className="mt-2 text-base font-semibold text-foreground">
                      {warning.title}
                    </h3>
                    <p className="mt-2 text-sm leading-7 text-foreground/70">
                      {warning.message}
                    </p>
                  </article>
                ))
              ) : (
                <EmptyState message="No structured warnings were captured in this brochure version." />
              )}
            </div>
          </Panel>

          <Panel>
            <SectionKicker
              kicker="Day by day itinerary"
              title="The trip arc from departure through return"
              summary="This section is rendered from the immutable brochure snapshot rather than the live draft."
            />
            <div className="mt-6 grid gap-5">
              {payload.itinerary_days.length > 0 ? (
                payload.itinerary_days.map((day) => (
                  <article
                    key={day.id}
                    className="rounded-[1.6rem] border border-shell-border bg-panel px-5 py-5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-accent-strong">
                          {day.label}
                        </p>
                        <h3 className="mt-2 font-display text-3xl font-semibold text-foreground">
                          {day.summary ?? day.label}
                        </h3>
                      </div>
                      <span className="rounded-full border border-shell-border bg-background px-3 py-1 text-xs text-foreground/58">
                        {day.items.length} itinerary moments
                      </span>
                    </div>

                    <div className="mt-5 grid gap-4">
                      {day.items.map((item) => (
                        <TimelineMoment
                          key={item.id}
                          item={item}
                          warnings={warningMap.get(item.id) ?? []}
                        />
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState message="The itinerary was still sparse when this brochure version was created." />
              )}
            </div>
          </Panel>
        </div>

        <div className="grid gap-5">
          <Panel>
            <SectionKicker
              kicker="Flights and transfers"
              title="Movement posture"
              summary="The brochure keeps the saved flight and transfer details together so timing risk stays visible."
            />
            <div className="mt-6 grid gap-3">
              {payload.flights.length > 0 ? (
                payload.flights.map((flight) => (
                  <DetailCard
                    key={flight.id}
                    title={`${flight.carrier}${flight.flight_number ? ` ${flight.flight_number}` : ""}`}
                    subtitle={`${flight.departure_airport} to ${flight.arrival_airport}`}
                    body={`${formatDateTime(flight.departure_time)} to ${formatDateTime(flight.arrival_time)}${flight.duration_text ? ` | ${flight.duration_text}` : ""}`}
                    notes={flight.notes}
                  />
                ))
              ) : (
                <EmptyState message="Flight inventory was not locked into this brochure version." />
              )}
            </div>
          </Panel>

          <Panel>
            <SectionKicker
              kicker="Stay section"
              title="Where the trip settles"
              summary="Hotels appear here exactly as they were frozen at finalize time."
            />
            <div className="mt-6 grid gap-3">
              {payload.stays.length > 0 ? (
                payload.stays.map((stay) => (
                  <DetailCard
                    key={stay.id}
                    title={stay.hotel_name}
                    subtitle={stay.area ?? "Area still open"}
                    body={`${formatDateTime(stay.check_in)} to ${formatDateTime(stay.check_out)}`}
                    notes={stay.notes}
                  />
                ))
              ) : (
                <EmptyState message="Hotel selection was still open when this brochure version was saved." />
              )}
            </div>
          </Panel>

          <Panel>
            <SectionKicker
              kicker="Budget and movement"
              title="What this itinerary is asking of the traveler"
            />
            <div className="mt-6 grid gap-3">
              <EditorialNote
                title={payload.budget_summary.headline}
                body={payload.budget_summary.detail}
              />
              <EditorialNote
                title={payload.travel_summary.headline}
                body={payload.travel_summary.detail}
              />
            </div>
          </Panel>

          <Panel>
            <SectionKicker
              kicker="Highlights and notes"
              title="The destination moments driving the trip"
            />
            <div className="mt-6 grid gap-3">
              {payload.highlights.length > 0 ? (
                payload.highlights.map((highlight) => (
                  <DetailCard
                    key={highlight.id}
                    title={highlight.title}
                    subtitle={
                      [highlight.category, highlight.day_label, highlight.time_label]
                        .filter(Boolean)
                        .join(" | ") || "Destination highlight"
                    }
                    body={highlight.notes[0] ?? "Saved as a notable destination moment."}
                    notes={highlight.notes.slice(1)}
                  />
                ))
              ) : (
                <EmptyState message="Highlights were still being curated when this brochure version was created." />
              )}
              {payload.planning_notes.map((note, index) => (
                <EditorialNote
                  key={`${note}-${index}`}
                  title="Planning note"
                  body={note}
                  compact
                />
              ))}
            </div>
          </Panel>

          <Panel>
            <SectionKicker
              kicker="Brochure metadata"
              title="Snapshot provenance"
              summary="Brochure versions are immutable. Reopening the trip never rewrites older versions."
            />
            <div className="mt-6 grid gap-3 text-sm leading-7 text-foreground/70">
              <MetadataRow label="Version" value={`v${snapshot.version_number}`} />
              <MetadataRow label="Saved at" value={formatDate(snapshot.finalized_at)} />
              <MetadataRow label="PDF file" value={snapshot.pdf_file_name} />
              <MetadataRow
                label="Hero image"
                value={payload.hero_image.attribution ?? "Destination imagery"}
              />
            </div>
          </Panel>
        </div>
      </section>
    </section>
  );
}

function resolveRequestedVersion(
  history: BrochureHistoryItem[],
  requestedVersion: string | null,
) {
  if (!requestedVersion) {
    return null;
  }

  const parsedVersion = Number(requestedVersion);
  if (!Number.isFinite(parsedVersion)) {
    return null;
  }

  return history.find((item) => item.version_number === parsedVersion) ?? null;
}

function BrochureMessage({ message }: { message: string }) {
  return (
    <section className="rounded-[1.8rem] border border-shell-border bg-shell px-6 py-10 text-sm text-foreground/72">
      {message}
    </section>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <section className="rounded-[1.8rem] border border-shell-border bg-shell px-5 py-5 sm:px-6 sm:py-6">
      {children}
    </section>
  );
}

function SectionKicker({
  kicker,
  title,
  summary,
}: {
  kicker: string;
  title: string;
  summary?: string;
}) {
  return (
    <header>
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-accent-strong">
        {kicker}
      </p>
      <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight text-foreground sm:text-[2.2rem]">
        {title}
      </h2>
      {summary ? (
        <p className="mt-3 max-w-2xl text-sm leading-7 text-foreground/68">
          {summary}
        </p>
      ) : null}
    </header>
  );
}

function MetaPill({
  label,
  subtle = false,
}: {
  label: string;
  subtle?: boolean;
}) {
  return (
    <span
      className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] ${
        subtle
          ? "border-white/16 bg-white/10 text-white/82"
          : "border-white/18 bg-black/12 text-white/76"
      }`}
    >
      {label}
    </span>
  );
}

function InsightCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-shell-border bg-panel px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-[0.18em] text-foreground/45">
        {label}
      </p>
      <p className="mt-3 text-base font-semibold text-foreground">{value}</p>
    </div>
  );
}

function MetricCard({
  metric,
}: {
  metric: { label: string; value: string; note: string | null };
}) {
  return (
    <div className="rounded-[1.2rem] border border-shell-border bg-background px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-[0.18em] text-foreground/45">
        {metric.label}
      </p>
      <p className="mt-3 font-display text-3xl font-semibold text-foreground">
        {metric.value}
      </p>
      {metric.note ? (
        <p className="mt-2 text-sm leading-6 text-foreground/62">{metric.note}</p>
      ) : null}
    </div>
  );
}

function TimelineMoment({
  item,
  warnings,
}: {
  item: TimelineItem;
  warnings: BrochureWarning[];
}) {
  return (
    <article className="rounded-[1.3rem] border border-shell-border bg-background px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold text-foreground">{item.title}</h4>
          <p className="mt-1 text-sm text-foreground/58">{item.type}</p>
        </div>
        <span className="text-xs font-medium uppercase tracking-[0.16em] text-foreground/52">
          {formatTimelineTiming(item)}
        </span>
      </div>
      {item.summary ? (
        <p className="mt-3 text-sm leading-7 text-foreground/70">{item.summary}</p>
      ) : null}
      {item.details.length > 0 ? (
        <div className="mt-3 grid gap-2">
          {item.details.map((detail, index) => (
            <p key={`${detail}-${index}`} className="text-sm leading-7 text-foreground/62">
              {detail}
            </p>
          ))}
        </div>
      ) : null}
      {warnings.length > 0 ? (
        <div className="mt-4 grid gap-2">
          {warnings.map((warning) => (
            <div
              key={warning.id}
              className="rounded-[1rem] border border-transparent bg-accent-soft px-3 py-3 text-sm leading-6 text-accent-strong"
            >
              <span className="font-semibold">{warning.title}:</span> {warning.message}
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function DetailCard({
  title,
  subtitle,
  body,
  notes,
}: {
  title: string;
  subtitle: string;
  body: string;
  notes: string[];
}) {
  return (
    <article className="rounded-[1.3rem] border border-shell-border bg-panel px-4 py-4">
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-sm text-foreground/58">{subtitle}</p>
      <p className="mt-3 text-sm leading-7 text-foreground/72">{body}</p>
      {notes.length > 0 ? (
        <div className="mt-3 grid gap-2">
          {notes.map((note, index) => (
            <p key={`${note}-${index}`} className="text-sm leading-6 text-foreground/62">
              {note}
            </p>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function EditorialNote({
  title,
  body,
  compact = false,
}: {
  title: string;
  body: string;
  compact?: boolean;
}) {
  return (
    <article
      className={`rounded-[1.3rem] border border-shell-border bg-panel ${
        compact ? "px-4 py-4" : "px-5 py-5"
      }`}
    >
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-3 text-sm leading-7 text-foreground/70">{body}</p>
    </article>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-t border-shell-border pt-3 first:border-t-0 first:pt-0">
      <dt className="text-xs font-medium uppercase tracking-[0.18em] text-foreground/48">
        {label}
      </dt>
      <dd className="text-right text-sm font-medium text-foreground">{value}</dd>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-[1.3rem] border border-shell-border bg-panel px-4 py-4 text-sm leading-7 text-foreground/68">
      {message}
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "TBD";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
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
