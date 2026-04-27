"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  BedDouble,
  BookOpen,
  Calendar,
  Car,
  ChevronDown,
  Clock,
  CloudSun,
  Download,
  ExternalLink,
  Loader2,
  MapPin,
  Plane,
  Sparkles,
  Star,
  UtensilsCrossed,
  Users,
  Wallet,
} from "lucide-react";

import {
  downloadTripBrochurePdf,
  getLatestTripBrochure,
  getTripBrochure,
  listTripBrochures,
} from "@/lib/api/brochures";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type {
  BrochureAdvancedSectionSummary,
  BrochureHistoryItem,
  BrochureSnapshot,
  BrochureSnapshotPayload,
  BrochureWarning,
} from "@/types/brochure";
import type { ActivityDetail, FlightDetail, HotelStayDetail, TimelineItem } from "@/types/trip-draft";

type TripBrochureProps = {
  tripId: string;
  requestedVersion: string | null;
};

export function TripBrochure({ tripId, requestedVersion }: TripBrochureProps) {
  const [snapshot, setSnapshot] = useState<BrochureSnapshot | null>(null);
  const [history, setHistory] = useState<BrochureHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const supabase = createSupabaseBrowserClient();
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        const [historyResponse, snapshotData] = await Promise.all([
          listTripBrochures(tripId, token, controller.signal),
          requestedVersion
            ? null
            : getLatestTripBrochure(tripId, token, controller.signal),
        ]);

        if (cancelled) return;
        setHistory(historyResponse.items);

        if (snapshotData) {
          setSnapshot(snapshotData);
        } else if (requestedVersion) {
          const resolved = resolveRequestedVersion(historyResponse.items, requestedVersion);
          if (resolved) {
            const versionData = await getTripBrochure(tripId, resolved.snapshot_id, token, controller.signal);
            if (!cancelled) setSnapshot(versionData);
          } else {
            if (!cancelled) setError("Requested version not found.");
          }
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(caughtError instanceof Error ? caughtError.message : "Could not load this brochure.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; controller.abort(); };
  }, [tripId, requestedVersion]);

  const warningMap = useMemo(() => {
    const map = new Map<string, BrochureWarning[]>();
    if (!snapshot) return map;
    for (const warning of snapshot.payload.warnings) {
      for (const id of warning.related_timeline_ids) {
        const existing = map.get(id) ?? [];
        existing.push(warning);
        map.set(id, existing);
      }
    }
    return map;
  }, [snapshot]);

  async function handleDownloadPdf() {
    if (!snapshot) return;
    setIsDownloading(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { data: { session } } = await supabase.auth.getSession();
      const { blob, fileName } = await downloadTripBrochurePdf(tripId, snapshot.snapshot_id, session?.access_token);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);
    } catch (caughtError) {
      console.error(caughtError instanceof Error ? caughtError.message : "Could not download PDF.");
    } finally {
      setIsDownloading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-[color:var(--accent)]" />
          <p className="text-sm text-foreground/50">Loading brochure...</p>
        </div>
      </div>
    );
  }

  if (error || !snapshot) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <div className="max-w-md text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[color:var(--accent)]/10">
            <BookOpen className="h-7 w-7 text-[color:var(--accent)]" />
          </div>
          <p className="mt-5 text-base font-semibold text-foreground">Brochure unavailable</p>
          <p className="mt-2 text-sm leading-relaxed text-foreground/55">
            {error ?? "This brochure could not be loaded right now."}
          </p>
          <Link
            href={"/chat?trip=" + tripId}
            className="mt-6 inline-flex items-center gap-2 rounded-full bg-[color:var(--accent)] px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to trip
          </Link>
        </div>
      </div>
    );
  }

  const payload = normalizeBrochurePayload(snapshot.payload);
  const advancedSections = payload.advanced_section_summaries ?? [];
  const flexibleItems = payload.flexible_items ?? [];
  const worthReviewingNotes = payload.worth_reviewing_notes ?? [];
  const quickPlanReviewRows = buildQuickPlanReviewRows(payload);
  const proposalSummary =
    payload.advanced_review_summary ||
    payload.trip_character_summary ||
    payload.executive_summary;
  const totalDays = payload.itinerary_days.length;
  const totalEvents = payload.itinerary_days.reduce((s, d) => s + d.items.length, 0);

  return (
    <div className="min-w-0 pb-16">
      <div className="relative overflow-hidden rounded-[1.75rem] border border-white/40 shadow-[0_24px_80px_rgba(16,24,40,0.16)]" style={{ minHeight: "34rem" }}>
        <div
          className="absolute inset-0"
          aria-hidden="true"
          style={{
            backgroundImage: "url(" + payload.hero_image.url + ")",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div
          className="absolute inset-0 bg-[linear-gradient(180deg,rgba(7,19,18,0.18)_0%,rgba(7,19,18,0.58)_58%,rgba(7,19,18,0.88)_100%)]"
          aria-hidden="true"
        />
        <div
          className="absolute inset-x-0 bottom-0 h-28 bg-[linear-gradient(180deg,transparent,rgba(248,246,240,0.96))]"
          aria-hidden="true"
        />

        <div className="relative flex items-center justify-between gap-4 px-6 pt-6 sm:px-8 sm:pt-8">
          <Link
            href={"/chat?trip=" + tripId}
            className="flex items-center gap-2 rounded-full border border-white/18 bg-black/24 px-4 py-2 text-sm font-medium text-white/90 backdrop-blur-sm transition hover:bg-black/36"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to chat
          </Link>
          <div className="flex items-center gap-2">
            <Link
              href="/trips"
              className="hidden rounded-full border border-white/18 bg-black/24 px-4 py-2 text-sm font-medium text-white/90 backdrop-blur-sm transition hover:bg-black/36 sm:block"
            >
              My trips
            </Link>
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={isDownloading}
              className="flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-gray-900 transition hover:bg-white/92 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isDownloading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
              <span className="hidden sm:inline">{isDownloading ? "Preparing..." : "Download PDF"}</span>
            </button>
          </div>
        </div>

        <div className="relative px-6 pb-14 pt-20 sm:px-8 sm:pb-16 sm:pt-24 lg:px-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-white/22 bg-white/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-white/82 backdrop-blur-sm">
              Private proposal
            </span>
            <span className="rounded-full border border-white/14 bg-white/6 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/60">
              v{snapshot.version_number}{snapshot.status === "latest" ? " · Latest" : " · Historical"}
            </span>
          </div>

          <h1 className="mt-6 max-w-4xl text-[2.8rem] font-bold leading-[1.02] tracking-tight text-white sm:text-6xl lg:text-[4.5rem]">
            {payload.title}
          </h1>
          <p className="mt-3 text-sm font-semibold uppercase tracking-[0.2em] text-white/50">
            {payload.route_text}
          </p>
          <p className="mt-6 max-w-2xl text-base leading-7 text-white/80 sm:text-lg">
            {proposalSummary}
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-2.5">
            <HeroPill icon={Calendar} label={payload.travel_window_text} />
            <HeroPill icon={Users} label={payload.party_text} />
            <HeroPill icon={Wallet} label={payload.budget_text} />
            {payload.style_tags.slice(0, 3).map((tag) => (
              <HeroPill key={tag} label={tag} />
            ))}
          </div>
        </div>
      </div>

      <div className="-mt-8 grid gap-3 px-3 sm:grid-cols-3 sm:px-6">
        <ProposalStatusCard
          label="Selected"
          value={selectedSummaryLabel(advancedSections, payload.metrics)}
          body="Working choices captured in this saved version."
        />
        <ProposalStatusCard
          label="Still flexible"
          value={String(flexibleItems.length)}
          body={flexibleItems[0] || "No intentionally flexible items were captured."}
        />
        <ProposalStatusCard
          label="Worth reviewing"
          value={String(worthReviewingNotes.length || payload.warnings.length)}
          body={worthReviewingNotes[0] || "No extra review notes were captured."}
        />
      </div>

      <div className="mt-10 grid min-w-0 gap-7 xl:grid-cols-[minmax(0,1fr)_minmax(320px,380px)] xl:items-start">
        <div className="min-w-0 space-y-7">
          {payload.planning_mode === "quick" && quickPlanReviewRows.length > 0 ? (
            <section className="rounded-[1.5rem] border border-[color:var(--planner-board-border)] bg-white px-6 py-6 shadow-[0_12px_40px_rgba(16,24,40,0.06)]">
              <div className="grid gap-6 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[color:var(--accent)]">
                    Quick Plan review
                  </p>
                  <h2 className="mt-2 max-w-sm text-2xl font-semibold tracking-tight text-foreground">
                    Why this plan was accepted
                  </h2>
                  <p className="mt-4 text-sm leading-7 text-foreground/62">
                    {getQuickPlanRationale(payload) ||
                      "This brochure was saved from an accepted Quick Plan that passed private completeness and quality checks."}
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {quickPlanReviewRows.map((row) => (
                    <QuickPlanReviewCard key={row.title} title={row.title} body={row.body} />
                  ))}
                </div>
              </div>
            </section>
          ) : null}

          {(payload.trip_character_summary || payload.planned_experience_summary || advancedSections.length > 0) && (
            <section className="rounded-[1.5rem] border border-[color:var(--planner-board-border)] bg-white px-6 py-6 shadow-[0_12px_40px_rgba(16,24,40,0.06)]">
              <div className="grid gap-6 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[color:var(--accent)]">
                    Trip character
                  </p>
                  <h2 className="mt-2 max-w-sm text-2xl font-semibold tracking-tight text-foreground">
                    The point of view behind this proposal
                  </h2>
                  {payload.trip_character_summary ? (
                    <p className="mt-4 text-sm leading-7 text-foreground/62">
                      {payload.trip_character_summary}
                    </p>
                  ) : null}
                  {payload.planned_experience_summary ? (
                    <p className="mt-3 text-sm leading-7 text-foreground/62">
                      {payload.planned_experience_summary}
                    </p>
                  ) : null}
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {advancedSections.slice(0, 6).map((section) => (
                    <AdvancedProposalCard key={section.id} section={section} />
                  ))}
                </div>
              </div>
            </section>
          )}

          {(flexibleItems.length > 0 || worthReviewingNotes.length > 0 || payload.warnings.length > 0) && (
            <section className="grid gap-4 md:grid-cols-2">
              <ProposalNotePanel
                title="Still flexible"
                notes={flexibleItems}
                empty="No intentionally flexible items were captured."
              />
              <ProposalNotePanel
                title="Worth reviewing"
                notes={worthReviewingNotes.length ? worthReviewingNotes : payload.warnings.map((warning) => warning.message)}
                empty="No additional review notes were captured."
                tone="warning"
              />
            </section>
          )}

          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[color:var(--accent)]">Day by day</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">Proposal itinerary</h2>
            </div>
            {totalDays > 0 && (
              <p className="shrink-0 text-sm text-foreground/42">
                {totalDays} day{totalDays === 1 ? "" : "s"} &middot; {totalEvents} event{totalEvents === 1 ? "" : "s"}
              </p>
            )}
          </div>

          {payload.itinerary_days.length > 0 ? (
            payload.itinerary_days.map((day, dayIndex) => (
              <BrochureDayCard
                key={day.id}
                day={day}
                dayIndex={dayIndex}
                totalDays={totalDays}
                warningMap={warningMap}
              />
            ))
          ) : (
            <BrochureEmptyBlock message="The itinerary was still sparse when this brochure version was saved. Refine the trip in chat to generate a fuller snapshot." />
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <EditorialCard icon={Wallet} title={payload.budget_summary.headline} body={payload.budget_summary.detail} />
            <EditorialCard icon={MapPin} title={payload.travel_summary.headline} body={payload.travel_summary.detail} />
          </div>

          {payload.planning_notes.length > 0 && (
            <div className="rounded-2xl border border-[color:var(--planner-board-border)] bg-white px-5 py-5">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)]">Planning notes</p>
              <ul className="mt-4 space-y-3">
                {payload.planning_notes.map((note, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm leading-relaxed text-foreground/62">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--accent)]/40" />
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="min-w-0 space-y-5 xl:sticky xl:top-6">
          <BrochureVersionPanel tripId={tripId} history={history} currentSnapshotId={snapshot.snapshot_id} />

          <BrochureSidePanel kicker="Flights" icon={Plane} emptyMessage="Flight inventory was not locked into this brochure version.">
            {payload.flights.length > 0 ? payload.flights.map((f) => <FlightRow key={f.id} flight={f} />) : null}
          </BrochureSidePanel>

          <BrochureSidePanel kicker="Accommodation" icon={BedDouble} emptyMessage="Hotel selection was still open when this brochure was saved.">
            {payload.stays.length > 0 ? payload.stays.map((s) => <StayRow key={s.id} stay={s} />) : null}
          </BrochureSidePanel>

          <BrochureSidePanel kicker="Highlights" icon={Star} emptyMessage="Highlights were still being curated when this brochure was created.">
            {payload.highlights.length > 0 ? payload.highlights.map((h) => <HighlightRow key={h.id} highlight={h} />) : null}
          </BrochureSidePanel>

          <BrochureSidePanel kicker="Weather" icon={CloudSun} emptyMessage="No forecast signal was captured in this brochure version.">
            {payload.weather.length > 0 ? payload.weather.slice(0, 4).map((item) => (
              <div key={item.id} className="px-5 py-4">
                <p className="text-sm font-semibold text-foreground">{item.day_label || item.forecast_date || "Weather note"}</p>
                <p className="mt-1 text-xs leading-relaxed text-foreground/52">{item.summary}</p>
              </div>
            )) : null}
          </BrochureSidePanel>

          {payload.resources.length > 0 && (
            <div className="rounded-2xl border border-[color:var(--planner-board-border)] bg-white px-5 py-5">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)]">Resources</p>
              <ul className="mt-4 space-y-1.5">
                {payload.resources.map((r) => (
                  <li key={r.url}>
                    <a href={r.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 rounded-lg px-1 py-1.5 text-sm font-medium text-[color:var(--accent)] transition hover:underline">
                      <BookOpen className="h-3.5 w-3.5 shrink-0 opacity-70" />
                      {r.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-[color:var(--planner-board-border)] pt-6 text-xs text-foreground/38">
        <span>Wandrix · Brochure v{snapshot.version_number} · Saved {formatDate(snapshot.finalized_at)}</span>
        <Link href={"/chat?trip=" + tripId} className="transition hover:text-foreground/68">Return to planning →</Link>
      </div>
    </div>
  );
}

function normalizeBrochurePayload(
  payload: BrochureSnapshotPayload,
): BrochureSnapshotPayload {
  const hasAdvancedContext = Boolean(
    payload.advanced_section_summaries?.length ||
      payload.advanced_review_summary ||
      payload.trip_character_summary ||
      payload.planned_experience_summary,
  );
  if (!hasAdvancedContext) {
    return payload;
  }

  const travelDates = parseTravelWindowDates(payload.travel_window_text);
  const flights = payload.flights.filter((flight) =>
    flightMatchesTravelDates(flight, travelDates),
  );
  const selectedStay = resolveDisplayStay(payload);
  const selectedStayIds = new Set(selectedStay.map((stay) => stay.id));
  const selectedStayNames = new Set(
    selectedStay.map((stay) => stay.hotel_name.trim().toLowerCase()),
  );
  const itineraryDays = payload.itinerary_days
    .map((day) => ({
      ...day,
      items: day.items.filter((item) =>
        shouldKeepBrochureTimelineItem(
          item,
          travelDates,
          selectedStayIds,
          selectedStayNames,
        ),
      ),
    }))
    .filter((day) => day.items.length > 0);

  return {
    ...payload,
    flights,
    stays: selectedStay,
    itinerary_days: itineraryDays,
  };
}

type TravelWindowDates = {
  startDate: string | null;
  endDate: string | null;
};

function parseTravelWindowDates(value: string): TravelWindowDates {
  const match = value.match(
    /(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+to\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})/,
  );
  if (!match) {
    return { startDate: null, endDate: null };
  }

  return {
    startDate: toIsoDate(match[1], match[2], match[3]),
    endDate: toIsoDate(match[4], match[5], match[6]),
  };
}

function toIsoDate(day: string, month: string, year: string) {
  const monthIndex = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
  ].indexOf(month.toLowerCase());
  if (monthIndex < 0) {
    return null;
  }

  return new Date(Date.UTC(Number(year), monthIndex, Number(day)))
    .toISOString()
    .slice(0, 10);
}

function flightMatchesTravelDates(
  flight: FlightDetail,
  travelDates: TravelWindowDates,
) {
  const expectedDate =
    flight.direction === "outbound" ? travelDates.startDate : travelDates.endDate;
  if (!expectedDate || !flight.departure_time) {
    return true;
  }

  return flight.departure_time.slice(0, 10) === expectedDate;
}

function resolveDisplayStay(payload: BrochureSnapshotPayload): HotelStayDetail[] {
  if (payload.stays.length <= 1) {
    return payload.stays;
  }

  const currentStaySection = payload.advanced_section_summaries?.find(
    (section) => section.id === "stay" || section.title.toLowerCase() === "current stay",
  );
  const sectionText = [
    currentStaySection?.summary,
    ...(currentStaySection?.notes ?? []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  const explicitStay = payload.stays.find(
    (stay) =>
      sectionText.includes(stay.hotel_name.toLowerCase()) ||
      (stay.area && sectionText.includes(stay.area.toLowerCase())),
  );

  return [explicitStay ?? payload.stays[0]];
}

function shouldKeepBrochureTimelineItem(
  item: TimelineItem,
  travelDates: TravelWindowDates,
  selectedStayIds: Set<string>,
  selectedStayNames: Set<string>,
) {
  if (item.type === "flight" || item.source_module === "flights") {
    const expectedDate = item.title.toLowerCase().includes("return")
      ? travelDates.endDate
      : travelDates.startDate;
    if (!expectedDate || !item.start_at) {
      return true;
    }

    return item.start_at.slice(0, 10) === expectedDate;
  }

  if (item.type === "hotel" || item.source_module === "hotels") {
    if (!selectedStayIds.size && !selectedStayNames.size) {
      return true;
    }

    return (
      selectedStayIds.has(item.id) ||
      selectedStayIds.has(item.id.replace(/^timeline_/, "")) ||
      selectedStayNames.has(item.title.trim().toLowerCase())
    );
  }

  return true;
}

function ProposalStatusCard({
  label,
  value,
  body,
}: {
  label: string;
  value: string;
  body: string;
}) {
  return (
    <div className="relative rounded-2xl border border-white/70 bg-white/90 px-5 py-4 shadow-[0_16px_44px_rgba(16,24,40,0.10)] backdrop-blur">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/42">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--accent)]">
        {value}
      </p>
      <p className="mt-1 text-xs leading-5 text-foreground/52">{body}</p>
    </div>
  );
}

function AdvancedProposalCard({ section }: { section: BrochureAdvancedSectionSummary }) {
  return (
    <article className="rounded-2xl border border-[color:var(--planner-board-border)] bg-[color:var(--planner-board-soft)] px-4 py-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground">{section.title}</h3>
        <span className="rounded-full bg-white px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em] text-foreground/48">
          {formatAdvancedStatus(section.status)}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-foreground/58">{section.summary}</p>
      {section.notes.length > 0 ? (
        <ul className="mt-3 space-y-1.5">
          {section.notes.slice(0, 2).map((note) => (
            <li key={note} className="text-xs leading-5 text-foreground/46">
              {note}
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function QuickPlanReviewCard({ title, body }: { title: string; body: string }) {
  return (
    <article className="rounded-2xl border border-[color:var(--planner-board-border)] bg-[color:var(--planner-board-soft)] px-4 py-4">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[color:var(--accent)]">
        {title}
      </p>
      <p className="mt-2 text-xs leading-5 text-foreground/58">{body}</p>
    </article>
  );
}

function buildQuickPlanReviewRows(payload: BrochureSnapshotPayload) {
  if (payload.planning_mode !== "quick") {
    return [];
  }
  const providerNotes = payload.quick_plan_provider_confidence_notes ?? [];
  const excludedModules = payload.quick_plan_excluded_modules ?? [];
  const moduleScope = payload.quick_plan_module_scope ?? [];
  const assumptions = payload.quick_plan_assumptions ?? [];
  const rows = [
    {
      title: "Review outcome",
      body: [
        payload.quick_plan_review_status
          ? `Completeness ${payload.quick_plan_review_status}`
          : null,
        payload.quick_plan_quality_status
          ? `quality ${payload.quick_plan_quality_status}`
          : null,
      ]
        .filter(Boolean)
        .join(", "),
    },
    {
      title: "Accepted scope",
      body: moduleScope.length
        ? moduleScope.map(formatModuleLabel).join(", ")
        : "Accepted module scope was not stored on this snapshot.",
    },
    {
      title: "Provider confidence",
      body: providerNotes[0] || "Provider confidence notes were not stored on this snapshot.",
    },
    {
      title: "Assumptions",
      body:
        assumptions
          .slice(0, 2)
          .map(formatAssumption)
          .filter(Boolean)
          .join(" · ") ||
        excludedModules
          .slice(0, 2)
          .map((item) => `${formatModuleLabel(String(item.module ?? ""))}: ${item.reason ?? "Excluded by request"}`)
          .join(" · ") ||
        "No major assumptions were stored on this snapshot.",
    },
  ];
  return rows.filter((row) => row.body);
}

function getQuickPlanRationale(payload: BrochureSnapshotPayload) {
  const summary = payload.quick_plan_intelligence_summary ?? {};
  const rationale = summary.plan_rationale;
  return typeof rationale === "string" ? rationale : null;
}

function formatAssumption(value: Record<string, unknown>) {
  const label = value.label ?? value.type ?? value.field;
  const detail = value.value ?? value.description;
  if (label && detail) {
    return `${String(label)}: ${String(detail)}`;
  }
  if (detail) {
    return String(detail);
  }
  if (label) {
    return String(label).replace(/_/g, " ");
  }
  return "";
}

function formatModuleLabel(value: string) {
  if (!value) {
    return "Module";
  }
  if (value === "hotels") {
    return "Stays";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function ProposalNotePanel({
  title,
  notes,
  empty,
  tone = "neutral",
}: {
  title: string;
  notes: string[];
  empty: string;
  tone?: "neutral" | "warning";
}) {
  const displayNotes = notes.length ? notes : [empty];
  return (
    <div className="min-w-0 rounded-[1.25rem] border border-[color:var(--planner-board-border)] bg-white px-5 py-5">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)]">
        {title}
      </p>
      <div className="mt-4 space-y-3">
        {displayNotes.slice(0, 5).map((note) => (
          <p
            key={note}
            className={
              "break-words text-sm leading-6 " +
              (tone === "warning" ? "text-amber-800" : "text-foreground/60")
            }
          >
            {note}
          </p>
        ))}
      </div>
    </div>
  );
}

function selectedSummaryLabel(
  sections: BrochureAdvancedSectionSummary[],
  metrics: { value: string }[],
) {
  const readyCount = sections.filter((section) => section.status === "ready").length;
  if (readyCount > 0) return String(readyCount);
  return metrics[0]?.value ?? "0";
}

function formatAdvancedStatus(status: BrochureAdvancedSectionSummary["status"]) {
  if (status === "needs_review") return "Worth review";
  if (status === "ready") return "Selected";
  return "Flexible";
}

function HeroPill({ icon: Icon, label }: { icon?: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <span className="flex max-w-full items-center gap-1.5 rounded-full border border-white/16 bg-black/22 px-3.5 py-1.5 text-xs font-medium text-white/80 backdrop-blur-sm">
      {Icon && <Icon className="h-3.5 w-3.5 opacity-70" />}
      <span className="min-w-0 break-words">{label}</span>
    </span>
  );
}

function BrochureDayCard({
  day, dayIndex, totalDays, warningMap,
}: {
  day: { id: string; label: string; summary: string | null; items: TimelineItem[] };
  dayIndex: number;
  totalDays: number;
  warningMap: Map<string, BrochureWarning[]>;
}) {
  const isFirst = dayIndex === 0;
  const isLast = dayIndex === totalDays - 1;

  return (
    <article className="min-w-0 overflow-hidden rounded-2xl border border-[color:var(--planner-board-border)] bg-white shadow-[0_1px_4px_rgba(0,0,0,0.04)]">
      <div
        className="flex flex-col items-start gap-3 px-5 py-4 sm:flex-row sm:items-center sm:gap-4"
        style={{
          background: isFirst
            ? "linear-gradient(135deg, color-mix(in srgb, var(--accent) 12%, white), color-mix(in srgb, var(--accent) 5%, white))"
            : "color-mix(in srgb, var(--planner-board-soft) 60%, white)",
        }}
      >
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold"
          style={isFirst ? { background: "var(--accent)", color: "white" } : { background: "color-mix(in srgb, var(--accent) 12%, white)", color: "var(--accent)" }}
        >
          {dayIndex + 1}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold tracking-tight" style={{ color: isFirst ? "var(--accent)" : "var(--planner-board-text)" }}>
            {day.label}
          </p>
          {day.summary && <p className="mt-0.5 break-words text-xs leading-5 text-foreground/50">{day.summary}</p>}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-1.5">
          {isFirst && (
            <span className="rounded-full bg-[color:var(--accent)] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-white">Start</span>
          )}
          {isLast && totalDays > 1 && (
            <span className="rounded-full bg-[color:var(--planner-board-accent-soft)] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-[color:var(--planner-board-accent-text)]">Final</span>
          )}
          <span className="text-xs text-foreground/36">{day.items.length} event{day.items.length === 1 ? "" : "s"}</span>
        </div>
      </div>

      <div className="divide-y divide-[color:var(--planner-board-border)]/50">
        {day.items.map((item) => (
          <BrochureEventRow key={item.id} item={item} warnings={warningMap.get(item.id) ?? []} />
        ))}
      </div>
    </article>
  );
}

type ItemType = TimelineItem["type"];

function getItemStyle(type: ItemType): { bg: string; text: string; label: string } {
  switch (type) {
    case "flight":   return { bg: "rgba(29,78,216,0.10)",   text: "#1d4ed8", label: "Flight" };
    case "hotel":    return { bg: "rgba(5,150,105,0.10)",   text: "#059669", label: "Stay" };
    case "meal":     return { bg: "rgba(217,119,6,0.10)",   text: "#d97706", label: "Meal" };
    case "weather":  return { bg: "rgba(14,165,233,0.10)",  text: "#0ea5e9", label: "Weather" };
    case "transfer": return { bg: "rgba(99,102,241,0.10)",  text: "#6366f1", label: "Transfer" };
    case "activity": return { bg: "rgba(236,72,153,0.10)",  text: "#ec4899", label: "Activity" };
    default:         return { bg: "rgba(100,116,139,0.10)", text: "#64748b", label: "Event" };
  }
}

function ItemTypeIcon({ type, color }: { type: ItemType; color?: string }) {
  const Icon =
    type === "flight"   ? Plane
    : type === "hotel"    ? BedDouble
    : type === "meal"     ? UtensilsCrossed
    : type === "weather"  ? CloudSun
    : type === "transfer" ? Car
    : type === "activity" ? MapPin
    : Sparkles;
  return <Icon className="h-4 w-4" style={{ color: color ?? "var(--accent)" }} />;
}

function BrochureEventRow({ item, warnings }: { item: TimelineItem; warnings: BrochureWarning[] }) {
  const { bg, text, label } = getItemStyle(item.type);

  return (
    <div className="flex min-w-0 items-start transition-colors hover:bg-[color:var(--planner-board-soft)]/50">
      <div className="flex w-14 shrink-0 flex-col items-end px-2 py-4 pt-[1.1rem] sm:w-20 sm:px-4">
        {item.start_at ? (
          <>
            <span className="text-xs font-bold tabular-nums" style={{ color: text }}>{formatTime(item.start_at)}</span>
            {item.end_at && <span className="mt-0.5 text-[10px] tabular-nums text-foreground/36">{formatTime(item.end_at)}</span>}
          </>
        ) : (
          <span className="flex items-center gap-1 text-[10px] text-foreground/30">
            <Clock className="h-2.5 w-2.5" />Needs timing
          </span>
        )}
      </div>

      <div className="shrink-0 pt-[1.05rem]">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: bg }}>
          <ItemTypeIcon type={item.type} color={text} />
        </div>
      </div>

      <div className="min-w-0 flex-1 px-3 py-4 sm:px-4">
        <div className="flex min-w-0 flex-wrap items-start gap-2">
          <p className="min-w-0 flex-1 break-words text-sm font-semibold leading-snug text-[color:var(--planner-board-text)]">{item.title}</p>
          <span className="mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.1em]" style={{ background: bg, color: text }}>{label}</span>
        </div>

        {item.type === "event" && item.image_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={item.image_url}
            alt={item.title}
            className="mt-3 h-24 w-full max-w-[13rem] rounded-lg object-cover"
          />
        )}

        {item.location_label && (
          <div className="mt-1 flex min-w-0 items-center gap-1 text-xs text-foreground/46">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="min-w-0 truncate">
              {item.venue_name && item.type === "event"
                ? `${item.venue_name} · ${item.location_label}`
                : item.location_label}
            </span>
          </div>
        )}

        {item.summary && <p className="mt-1.5 break-words text-xs leading-relaxed text-foreground/52">{item.summary}</p>}

        {(item.status_text || item.price_text || item.availability_text) && (
          <div className="mt-2 flex flex-wrap gap-2">
            {[item.status_text, item.price_text, item.availability_text]
              .filter(Boolean)
              .map((detail) => (
                <span
                  key={detail}
                  className="rounded-full bg-[color:var(--planner-board-soft)] px-2 py-0.5 text-[10px] font-medium text-foreground/58"
                >
                  {detail}
                </span>
              ))}
          </div>
        )}

        {item.details.length > 0 && (
          <ul className="mt-2 space-y-1">
            {item.details.slice(0, 2).map((detail, i) => (
              <li key={i} className="flex items-start gap-1.5 break-words text-xs leading-relaxed text-foreground/44">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-foreground/22" />{detail}
              </li>
            ))}
          </ul>
        )}

        {item.type === "event" && item.source_url && (
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[color:var(--accent)] transition hover:underline"
          >
            {item.source_label ? `Open on ${item.source_label}` : "Open event listing"}
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}

        {warnings.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {warnings.map((w) => (
              <div key={w.id} className="flex min-w-0 items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-2 text-xs text-amber-800">
                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-amber-500" />
                <span className="min-w-0 break-words"><span className="font-semibold">{w.title}:</span> {w.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EditorialCard({ icon: Icon, title, body }: { icon: React.ComponentType<{ className?: string }>; title: string; body: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--planner-board-border)] bg-white px-5 py-5">
      <div className="flex items-center gap-2 text-[color:var(--accent)]">
        <Icon className="h-4 w-4" />
        <p className="text-xs font-bold uppercase tracking-[0.16em]">{title}</p>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-foreground/60">{body}</p>
    </div>
  );
}

function BrochureVersionPanel({ tripId, history, currentSnapshotId }: { tripId: string; history: BrochureHistoryItem[]; currentSnapshotId: string }) {
  const [open, setOpen] = useState(false);
  if (history.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-2xl border border-[color:var(--planner-board-border)] bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-[color:var(--planner-board-soft)]"
      >
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)]">Version history</p>
          <p className="mt-0.5 text-xs text-foreground/48">{history.length} saved snapshot{history.length === 1 ? "" : "s"}</p>
        </div>
        <ChevronDown className={"h-4 w-4 shrink-0 text-foreground/38 transition-transform duration-200 " + (open ? "rotate-180" : "")} />
      </button>

      {open && (
        <div className="space-y-2 border-t border-[color:var(--planner-board-border)] px-4 py-3">
          {history.map((item) => {
            const isCurrent = item.snapshot_id === currentSnapshotId;
            return (
              <Link
                key={item.snapshot_id}
                href={"/brochure/" + tripId + "?version=" + item.version_number}
                className={"flex items-center justify-between gap-3 rounded-xl px-3.5 py-3 text-sm transition " + (isCurrent ? "bg-[color:var(--accent)] text-white" : "bg-[color:var(--planner-board-soft)] text-foreground hover:bg-[color:var(--planner-board-soft-hover)]")}
              >
                <span className="font-semibold">Version {item.version_number}</span>
                <div className="flex items-center gap-2">
                  {item.is_latest && (
                    <span className={"rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em] " + (isCurrent ? "bg-white/20 text-white" : "bg-[color:var(--accent)]/10 text-[color:var(--accent)]")}>
                      Latest
                    </span>
                  )}
                  <span className={"text-xs " + (isCurrent ? "text-white/62" : "text-foreground/42")}>{formatDateShort(item.finalized_at)}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function BrochureSidePanel({ kicker, icon: Icon, emptyMessage, children }: { kicker: string; icon: React.ComponentType<{ className?: string }>; emptyMessage: string; children: React.ReactNode }) {
  const hasChildren = Array.isArray(children) ? children.some(Boolean) : !!children;
  return (
    <div className="overflow-hidden rounded-2xl border border-[color:var(--planner-board-border)] bg-white">
      <div className="flex items-center gap-2.5 border-b border-[color:var(--planner-board-border)] px-5 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[color:var(--accent)]/10">
          <Icon className="h-3.5 w-3.5 text-[color:var(--accent)]" />
        </div>
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)]">{kicker}</p>
      </div>
      {hasChildren ? (
        <div className="divide-y divide-[color:var(--planner-board-border)]/50">{children}</div>
      ) : (
        <p className="px-5 py-4 text-sm leading-relaxed text-foreground/48">{emptyMessage}</p>
      )}
    </div>
  );
}

function FlightRow({ flight }: { flight: FlightDetail }) {
  return (
    <div className="px-5 py-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-foreground">{flight.departure_airport}</span>
          <Plane className="h-3.5 w-3.5 text-foreground/28" />
          <span className="text-sm font-bold text-foreground">{flight.arrival_airport}</span>
        </div>
        {flight.direction && (
          <span className="rounded-full bg-[rgba(29,78,216,0.08)] px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.1em] text-[#1d4ed8]">{flight.direction}</span>
        )}
      </div>
      <p className="mt-1 text-xs text-foreground/52">{flight.carrier}{flight.flight_number ? " · " + flight.flight_number : ""}{flight.duration_text ? " · " + flight.duration_text : ""}</p>
      <p className="mt-1 text-xs text-foreground/42">{formatDateTime(flight.departure_time)} to {formatDateTime(flight.arrival_time)}</p>
    </div>
  );
}

function StayRow({ stay }: { stay: HotelStayDetail }) {
  return (
    <div className="px-5 py-4">
      <p className="text-sm font-semibold text-foreground">{stay.hotel_name}</p>
      {stay.area && <p className="mt-0.5 text-xs text-foreground/50">{stay.area}</p>}
      <p className="mt-1.5 text-xs text-foreground/42">{formatDateShort(stay.check_in)} to {formatDateShort(stay.check_out)}</p>
    </div>
  );
}

function HighlightRow({ highlight }: { highlight: ActivityDetail }) {
  return (
    <div className="px-5 py-4">
      <p className="text-sm font-semibold text-foreground">{highlight.title}</p>
      <p className="mt-0.5 text-xs text-foreground/48">{[highlight.category, highlight.day_label].filter(Boolean).join(" · ") || "Highlight"}</p>
      {highlight.notes[0] && <p className="mt-1.5 text-xs leading-relaxed text-foreground/48">{highlight.notes[0]}</p>}
    </div>
  );
}

function BrochureEmptyBlock({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[color:var(--planner-board-border)] bg-[color:var(--planner-board-soft)] px-8 py-12 text-center">
      <p className="max-w-xs text-sm leading-relaxed text-foreground/48">{message}</p>
    </div>
  );
}

function resolveRequestedVersion(history: BrochureHistoryItem[], requestedVersion: string | null) {
  if (!requestedVersion) return null;
  const parsed = Number(requestedVersion);
  if (!Number.isFinite(parsed)) return null;
  return history.find((item) => item.version_number === parsed) ?? null;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function formatDateShort(value: string | null) {
  if (!value) return "Timing open";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" }).format(parsed);
}

function formatDateTime(value: string | null) {
  if (!value) return "Timing open";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(parsed);
}

function formatTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value || "Needs timing";
  return new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" }).format(parsed);
}
