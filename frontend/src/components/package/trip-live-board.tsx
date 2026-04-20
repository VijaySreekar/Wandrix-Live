"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  BedDouble,
  CalendarRange,
  ChevronRight,
  CloudSun,
  MapPinned,
  Plane,
  Sparkles,
  UtensilsCrossed,
  UsersRound,
} from "lucide-react";

import {
  ActivityFeature,
  FlightCard,
  HotelSummary,
  WeatherCard,
  getLiveDestinationImage,
} from "@/components/package/trip-board-cards";
import { cn } from "@/lib/utils";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TimelineItem } from "@/types/trip-draft";

type TripLiveBoardProps = {
  workspace: PlannerWorkspaceState;
};

type BoardTab = "itinerary" | "selections";

export function TripLiveBoard({ workspace }: TripLiveBoardProps) {
  const [activeTab, setActiveTab] = useState<BoardTab>("itinerary");
  const { tripDraft, trip } = workspace;
  const { configuration, module_outputs: moduleOutputs, conversation, status } =
    tripDraft;
  const outboundFlight = moduleOutputs.flights.find(
    (flight) => flight.direction === "outbound",
  );
  const stay = moduleOutputs.hotels[0] ?? null;
  const leadActivity = moduleOutputs.activities[0] ?? null;
  const weather = moduleOutputs.weather.slice(0, 3);
  const timelineSections = useMemo(
    () => buildTimelineSections(tripDraft.timeline),
    [tripDraft.timeline],
  );
  const selectedModules = Object.entries(configuration.selected_modules)
    .filter(([, enabled]) => enabled)
    .map(([name]) => labelize(name));
  const tripStyles = configuration.activity_styles.map((style) => labelize(style));
  const pendingFields = status.missing_fields.map((field) =>
    field.replaceAll("_", " "),
  );

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 xl:px-6">
      <div className="space-y-10">
        <BoardHero
          tripId={trip.trip_id}
          destination={configuration.to_location}
          fromLocation={configuration.from_location}
          startDate={configuration.start_date}
          endDate={configuration.end_date}
          adults={configuration.travelers.adults}
          childCount={configuration.travelers.children}
          summary={
            conversation.last_turn_summary ||
            "This is the first working draft of the trip. Keep refining it in chat and the board will tighten around the same plan."
          }
        />

        <div className="space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                {activeTab === "itinerary" ? "Itinerary" : "Selections"}
              </h3>
              <p className="mt-1 text-sm text-foreground/58">
                {activeTab === "itinerary"
                  ? `${tripDraft.timeline.length} timeline blocks are shaping this trip right now.`
                  : "This side keeps the trip choices and soft defaults visible while the chat keeps refining the plan."}
              </p>
            </div>
            <div className="rounded-lg border border-border/70 bg-background p-1">
              <BoardTabButton
                active={activeTab === "itinerary"}
                onClick={() => setActiveTab("itinerary")}
              >
                Itinerary
              </BoardTabButton>
              <BoardTabButton
                active={activeTab === "selections"}
                onClick={() => setActiveTab("selections")}
              >
                Selections
              </BoardTabButton>
            </div>
          </div>

          {activeTab === "itinerary" ? (
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.22fr)_minmax(320px,0.78fr)] xl:items-start">
              <section className="space-y-5">
                <div className="rounded-xl border border-shell-border/70 bg-background px-5 py-4">
                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <SummaryStat
                      icon={MapPinned}
                      label="Route"
                      value={formatRouteSummary(
                        configuration.from_location,
                        configuration.to_location,
                      )}
                    />
                    <SummaryStat
                      icon={CalendarRange}
                      label="Timing"
                      value={formatCompactDateRange(
                        configuration.start_date,
                        configuration.end_date,
                        configuration.travel_window,
                        configuration.trip_length,
                      )}
                    />
                    <SummaryStat
                      icon={UsersRound}
                      label="Party"
                      value={formatTravelers(
                        configuration.travelers.adults,
                        configuration.travelers.children,
                      )}
                    />
                    <SummaryStat
                      icon={Sparkles}
                      label="Planning mode"
                      value="Quick Plan"
                    />
                  </div>
                </div>

                <div className="relative max-h-[46rem] overflow-y-auto pr-2 pl-8">
                  <div className="absolute bottom-0 left-[11px] top-0 w-px bg-[color:color-mix(in_srgb,var(--shell-border)_88%,transparent)]" />
                  <div className="space-y-6">
                    {timelineSections.length > 0 ? (
                      timelineSections.map((section, index) => (
                        <TimelineDaySection
                          key={section.id}
                          section={section}
                          isLead={index === 0}
                        />
                      ))
                    ) : (
                      <EmptyPanel message="Wandrix has not saved a full itinerary yet. Keep pushing the trip in chat and the timeline will fill in here." />
                    )}
                  </div>
                </div>
              </section>

              <div className="space-y-6 xl:sticky xl:top-4">
                <FlightCard flight={outboundFlight} />
                <WeatherCard forecasts={weather} />
                <InfoCard
                  icon={BedDouble}
                  title="Stay details"
                  subtitle={stay ? "Current stay direction" : "Hotel still open"}
                >
                  {stay ? (
                    <HotelSummary hotel={stay} />
                  ) : (
                    <EmptyPanel message="Hotel recommendations will settle here once Wandrix has enough destination and pacing context." />
                  )}
                </InfoCard>

                <InfoCard
                  icon={MapPinned}
                  title="Highlights"
                  subtitle={
                    leadActivity
                      ? "Current standout recommendation"
                      : "Destination highlights still forming"
                  }
                >
                  {leadActivity ? (
                    <ActivityFeature
                      activity={leadActivity}
                      destination={configuration.to_location}
                    />
                  ) : (
                    <EmptyPanel message="Local highlights will appear here as soon as activities are strong enough to elevate." />
                  )}
                </InfoCard>
              </div>
            </div>
          ) : (
            <div className="grid gap-6 2xl:grid-cols-2">
              <InfoCard
                icon={Sparkles}
                title="Trip choices"
                subtitle="These are the active trip defaults and planning signals shaping the current draft."
              >
                <FilterStack
                  items={[
                    {
                      label: "Modules",
                      values: selectedModules,
                      fallback: "No modules selected yet",
                    },
                    {
                      label: "Trip style",
                      values: tripStyles,
                      fallback: "No style saved yet",
                    },
                    {
                      label: "Pending details",
                      values: pendingFields,
                      fallback: "Nothing critical is blocking the draft right now",
                    },
                  ]}
                />
              </InfoCard>

              <InfoCard
                icon={CloudSun}
                title="Planner notes"
                subtitle="What Wandrix is holding onto from the latest turn."
              >
                <div className="space-y-4">
                  <SelectionCard
                    title="Current board summary"
                    description={
                      conversation.last_turn_summary ||
                      "Wandrix will keep the running trip summary here as the itinerary changes."
                    }
                  />
                  <SelectionCard
                    title="Conversation phase"
                    description={labelize(status.phase)}
                  />
                  <SelectionCard
                    title="Refinement loop"
                    description="Keep editing this same itinerary in chat. Wandrix should refine the draft instead of starting over."
                  />
                </div>
              </InfoCard>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function BoardHero({
  tripId,
  destination,
  fromLocation,
  startDate,
  endDate,
  adults,
  childCount,
  summary,
}: {
  tripId: string;
  destination: string | null;
  fromLocation: string | null;
  startDate: string | null;
  endDate: string | null;
  adults: number | null;
  childCount: number | null;
  summary: string;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-shell-border/70 bg-[color:color-mix(in_srgb,var(--background)_88%,var(--panel))]">
      <div className="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="relative min-h-[11.5rem] overflow-hidden lg:min-h-[14rem]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt={destination ? `${destination} destination view` : "Travel destination view"}
            src={getLiveDestinationImage(destination)}
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,29,72,0.05),rgba(0,29,72,0.44))]" />
          <div className="absolute left-5 top-5 rounded-full bg-[rgba(255,255,255,0.8)] px-3 py-1.5 backdrop-blur-md">
            <p className="font-label text-[10px] font-bold uppercase tracking-[0.18em] text-[color:var(--accent)]">
              Live destination
            </p>
          </div>
        </div>

        <div className="flex flex-col justify-between gap-4 px-5 py-5 md:px-6 md:py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-label text-[10px] uppercase tracking-[0.2em] text-foreground/48">
                Upcoming trip - {formatTripLength(startDate, endDate)}
              </p>
              <h2 className="mt-3 text-[2rem] font-semibold tracking-tight text-foreground md:text-[2.35rem]">
                {destination || "Your next destination"}
              </h2>
            </div>
            <Link
              href={`/brochure/${tripId}`}
              className="inline-flex items-center gap-2 rounded-lg bg-[color:var(--secondary,#ac3509)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-white transition-opacity hover:opacity-92"
            >
              Brochure
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-border/60 bg-background px-4 py-4">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_12%,white)] text-[color:var(--accent)]">
                  <MapPinned className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/44">
                    Route
                  </p>
                  <p className="mt-2 text-base font-semibold leading-tight text-foreground">
                    {formatRouteSummary(fromLocation, destination)}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-foreground/60">
                    {summary}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <HeroInlineDetail
                icon={CalendarRange}
                label="Travel window"
                value={formatCompactDateRange(
                  startDate,
                  endDate,
                  null,
                  null,
                )}
              />
              <HeroInlineDetail
                icon={UsersRound}
                label="Party"
                value={formatTravelers(adults, childCount)}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function HeroInlineDetail({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-background px-4 py-3 text-foreground">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] text-[color:var(--accent)]">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/44">
          {label}
        </p>
        <p className="mt-1 text-sm font-semibold leading-5 text-foreground">
          {value}
        </p>
      </div>
    </div>
  );
}

function BoardTabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-lg px-4 py-2 text-sm font-semibold transition-colors",
        active
          ? "bg-[color:var(--accent)] text-white"
          : "text-foreground/66 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

function SummaryStat({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] text-[color:var(--accent)]">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/44">
          {label}
        </p>
        <p className="mt-1 text-sm font-semibold leading-5 text-foreground">
          {value}
        </p>
      </div>
    </div>
  );
}

function TimelineDaySection({
  section,
  isLead,
}: {
  section: {
    id: string;
    dayLabel: string;
    summary: string;
    items: TimelineItem[];
  };
  isLead: boolean;
}) {
  return (
    <article className="relative">
      <div className="absolute left-[-2rem] top-6 flex h-6 w-6 items-center justify-center rounded-full bg-background ring-2 ring-background">
        {isLead ? (
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[color:var(--accent)] text-white shadow-[0_8px_24px_rgba(0,49,120,0.18)]">
            <CalendarRange className="h-3 w-3" />
          </span>
        ) : (
          <span className="h-3 w-3 rounded-full bg-foreground/22" />
        )}
      </div>

      <div className="rounded-[1.25rem] border border-shell-border/70 bg-[color:color-mix(in_srgb,var(--background)_82%,var(--panel))] px-6 py-5">
        <div>
          <p className="text-[1.15rem] font-semibold tracking-tight text-[color:var(--accent)]">
            {section.dayLabel}
          </p>
          <p className="mt-1 text-sm leading-6 text-foreground/58">
            {section.summary}
          </p>
        </div>

        <div className="mt-5 space-y-4">
          {section.items.map((item) => (
            <div key={item.id} className="flex items-start gap-4">
              <span className="w-16 pt-3 text-sm font-semibold text-[color:var(--accent)]">
                {item.start_at ? formatTime(item.start_at) : "TBD"}
              </span>
              <div className="min-w-0 flex-1 rounded-xl bg-background px-4 py-3">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_8%,white)] text-[color:var(--accent)]">
                    <TimelineItemIcon itemType={item.type} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground">
                      {item.title}
                    </p>
                    <p className="mt-1 text-xs leading-6 text-foreground/56">
                      {buildTimelineDescription(item)}
                    </p>
                    {item.details.length > 1 ? (
                      <ul className="mt-2 space-y-1">
                        {item.details.slice(1, 3).map((detail) => (
                          <li
                            key={detail}
                            className="text-xs leading-6 text-foreground/54"
                          >
                            {detail}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}

function InfoCard({
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-shell-border/70 bg-[color:color-mix(in_srgb,var(--background)_82%,var(--panel))] px-5 py-5">
      <div className="flex items-center gap-2 text-[color:var(--accent)]">
        <Icon className="h-4 w-4" />
        <p className="font-label text-[11px] font-bold uppercase tracking-[0.16em]">
          {title}
        </p>
      </div>
      <p className="mt-3 text-sm text-foreground/56">{subtitle}</p>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function SelectionCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <article className="rounded-xl bg-background px-4 py-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-7 text-foreground/64">{description}</p>
    </article>
  );
}

function FilterStack({
  items,
}: {
  items: Array<{ label: string; values: string[]; fallback: string }>;
}) {
  return (
    <div className="space-y-5">
      {items.map((item) => (
        <div key={item.label}>
          <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/46">
            {item.label}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(item.values.length > 0 ? item.values : [item.fallback]).map((value) => (
              <span
                key={value}
                className="rounded-full bg-background px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-foreground/72"
              >
                {value}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="rounded-xl bg-background px-4 py-4 text-sm leading-7 text-foreground/66">
      {message}
    </div>
  );
}

function TimelineItemIcon({ itemType }: { itemType: TimelineItem["type"] }) {
  const Icon =
    itemType === "flight"
      ? Plane
      : itemType === "hotel"
        ? BedDouble
        : itemType === "meal"
          ? UtensilsCrossed
          : itemType === "weather"
            ? CloudSun
            : itemType === "activity" || itemType === "transfer"
              ? MapPinned
              : Sparkles;

  return <Icon className="h-4 w-4" />;
}

function buildTimelineSections(timeline: TimelineItem[]) {
  const sections = new Map<
    string,
    {
      id: string;
      dayLabel: string;
      summary: string;
      items: TimelineItem[];
    }
  >();

  timeline.forEach((item, index) => {
    const dayLabel = item.day_label || `Day ${index + 1}`;
    const existingSection = sections.get(dayLabel);

    if (existingSection) {
      existingSection.items.push(item);
      return;
    }

    sections.set(dayLabel, {
      id: `${dayLabel}-${index}`,
      dayLabel,
      summary: item.summary || item.location_label || item.title,
      items: [item],
    });
  });

  return Array.from(sections.values());
}

function buildTimelineDescription(item: TimelineItem) {
  const startLabel = item.start_at ? formatTime(item.start_at) : null;
  const endLabel = item.end_at ? formatTime(item.end_at) : null;
  const timeRange =
    startLabel && endLabel ? `${startLabel} to ${endLabel}` : startLabel || endLabel;
  const parts = [item.location_label, timeRange, item.details[0]].filter(Boolean);
  return parts.join(" - ") || "Timing still being shaped";
}

function formatTripLength(startDate: string | null, endDate: string | null) {
  if (!startDate || !endDate) {
    return "open timing";
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return "open timing";
  }

  const differenceInDays = Math.max(
    1,
    Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1,
  );

  return `${differenceInDays} days`;
}

function formatRouteSummary(
  fromLocation: string | null,
  destination: string | null,
) {
  if (fromLocation && destination) {
    return `${fromLocation} to ${destination}`;
  }

  if (destination) {
    return `Destination set to ${destination}`;
  }

  if (fromLocation) {
    return `Leaving from ${fromLocation}`;
  }

  return "Route still being shaped";
}

function formatTravelers(adults: number | null, children: number | null) {
  const safeAdults = adults ?? 1;
  const safeChildren = children ?? 0;
  return `${safeAdults} adult${safeAdults === 1 ? "" : "s"}${safeChildren ? `, ${safeChildren} child${safeChildren === 1 ? "" : "ren"}` : ""}`;
}

function formatCompactDateRange(
  startDate: string | null,
  endDate: string | null,
  travelWindow: string | null,
  tripLength: string | null,
) {
  if (!startDate && !endDate) {
    return [travelWindow, tripLength].filter(Boolean).join(" - ") || "TBD";
  }

  if (!startDate || !endDate) {
    return formatDateShort(startDate ?? endDate);
  }

  const start = new Date(startDate);
  const end = new Date(endDate);

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return `${formatDateShort(startDate)} - ${formatDateShort(endDate)}`;
  }

  const startLabel = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
  }).format(start);
  const endLabel = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
  }).format(end);

  return `${startLabel} - ${endLabel}`;
}

function formatDateShort(value: string | null) {
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
  }).format(parsed);
}

function formatTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value || "TBD";
  }

  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function labelize(value: string) {
  return value.replaceAll("_", " ");
}
