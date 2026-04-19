"use client";

import { useState } from "react";
import Link from "next/link";
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

import type {
  ActivityDetail,
  FlightDetail,
  HotelStayDetail,
  TimelineItem,
  WeatherDetail,
} from "@/types/trip-draft";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import { cn } from "@/lib/utils";

type TripBoardPreviewProps = {
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
};

type BoardTab = "board" | "selections";

export function TripBoardPreview({
  workspace,
  isBootstrapping,
}: TripBoardPreviewProps) {
  const [activeTab, setActiveTab] = useState<BoardTab>("board");

  if (isBootstrapping) {
    return (
      <section className="flex h-full min-h-0 flex-col bg-shell">
        <BoardHeader />
        <div className="flex flex-1 items-center justify-center px-6">
          <div className="max-w-xl text-center">
            <p className="font-display text-3xl text-foreground">
              Loading the live board
            </p>
            <p className="mt-3 text-sm leading-7 text-foreground/66">
              Wandrix is pulling the trip draft into place so the itinerary and
              decision rail can settle properly.
            </p>
          </div>
        </div>
      </section>
    );
  }

  if (!workspace) {
    return (
      <section className="flex h-full min-h-0 flex-col bg-shell">
        <BoardHeader />
        <div className="flex flex-1 items-center justify-center px-6">
          <div className="max-w-xl text-center">
            <p className="font-display text-3xl text-foreground">
              No trip loaded
            </p>
            <p className="mt-3 text-sm leading-7 text-foreground/66">
              Open a trip from chat and the board will turn into the itinerary
              companion on the right.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const draft = workspace.tripDraft;
  const config = draft.configuration;
  const outboundFlight = draft.module_outputs.flights.find(
    (flight) => flight.direction === "outbound",
  );
  const stay = draft.module_outputs.hotels[0] ?? null;
  const leadActivity = draft.module_outputs.activities[0] ?? null;
  const weather = draft.module_outputs.weather.slice(0, 3);
  const selectedModules = Object.entries(config.selected_modules)
    .filter(([, enabled]) => enabled)
    .map(([name]) => name);
  const selectionCards = buildSelectionCards(draft);
  const timelineSections = buildTimelineSections(draft.timeline);

  return (
    <section className="flex h-full min-h-0 flex-col bg-shell">
      <BoardHeader />

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 xl:px-6">
        <div className="space-y-10">
          <BoardHero
            tripId={workspace.trip.trip_id}
            fromLocation={config.from_location}
            destination={config.to_location}
            startDate={config.start_date}
            endDate={config.end_date}
            adults={config.travelers.adults}
            childCount={config.travelers.children}
          />

          <div className="space-y-10">
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                {activeTab === "board" ? "Itinerary" : "Selections"}
              </h3>
              <div className="rounded-lg border border-border/70 bg-background p-1">
                <BoardTabButton
                  active={activeTab === "board"}
                  onClick={() => setActiveTab("board")}
                >
                  Itinerary
                </BoardTabButton>
                <BoardTabButton
                  active={activeTab === "selections"}
                  onClick={() => setActiveTab("selections")}
                >
                  Choices
                </BoardTabButton>
              </div>
            </div>

            {activeTab === "board" ? (
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1.22fr)_minmax(320px,0.78fr)] xl:items-start">
                <section className="space-y-5">
                  <div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        Itinerary flow
                      </p>
                      <p className="mt-1 text-sm text-foreground/58">
                        {draft.timeline.length > 0
                          ? `${draft.timeline.length} timeline items shaped so far`
                          : "The conversation will build the trip flow here."}
                      </p>
                    </div>
                  </div>

                  <div className="itinerary-scroll relative max-h-[42rem] overflow-y-auto pr-2 pl-8">
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
                        <EmptyPanel message="The itinerary will start to build here once the conversation locks in enough route, timing, and module detail." />
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
                    subtitle={stay ? "Selected hotel" : "Hotel still open"}
                  >
                    {stay ? (
                      <HotelSummary hotel={stay} />
                    ) : (
                      <EmptyPanel message="Once Wandrix narrows down the stay, the hotel choice will live here with check-in details and fit notes." />
                    )}
                  </InfoCard>

                  <InfoCard
                    icon={MapPinned}
                    title="Highlights"
                    subtitle={
                      leadActivity
                        ? "Current standout recommendation"
                        : "Activity highlights still forming"
                    }
                  >
                    {leadActivity ? (
                      <ActivityFeature
                        activity={leadActivity}
                        destination={config.to_location}
                      />
                    ) : (
                      <EmptyPanel message="The lead experiences should be elevated here once the planner starts locking stronger activity recommendations." />
                    )}
                  </InfoCard>
                </div>
              </div>
            ) : (
              <div className="grid gap-6 2xl:grid-cols-2">
                <InfoCard
                  icon={Sparkles}
                  title="Decision queue"
                  subtitle="Use this side for explicit user choices"
                >
                  <div className="space-y-4">
                    {selectionCards.length > 0 ? (
                      selectionCards.map((card) => (
                        <SelectionCard
                          key={card.title}
                          title={card.title}
                          description={card.description}
                          options={card.options}
                        />
                      ))
                    ) : (
                      <EmptyPanel message="No explicit choices are blocking the trip right now. When the agent needs a decision, it should show up here instead of hiding in the chat text." />
                    )}
                  </div>
                </InfoCard>

                <InfoCard
                  icon={CalendarRange}
                  title="Trip filters"
                  subtitle="Soft preferences and active planning signals"
                >
                  <FilterStack
                    items={[
                      {
                        label: "Modules",
                        values: selectedModules,
                        fallback: "No modules selected yet",
                      },
                      {
                        label: "Trip tone",
                        values: config.activity_styles,
                        fallback: "No styles selected yet",
                      },
                      {
                        label: "Phase",
                        values: [draft.status.phase.replaceAll("_", " ")],
                        fallback: "Collecting requirements",
                      },
                    ]}
                  />
                </InfoCard>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function BoardHeader() {
  return (
    <div className="border-b border-shell-border/70 px-6 py-4 xl:px-8">
      <p className="font-label text-[11px] uppercase tracking-[0.22em] text-foreground/48">
        Live travel board
      </p>
    </div>
  );
}

function BoardHero(props: {
  tripId: string;
  fromLocation: string | null;
  destination: string | null;
  startDate: string | null;
  endDate: string | null;
  adults: number;
  childCount: number;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-shell-border/70 bg-[color:color-mix(in_srgb,var(--background)_86%,var(--panel))]">
      <div className="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="relative min-h-[11.5rem] overflow-hidden lg:min-h-[14rem]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt={props.destination ? `${props.destination} destination view` : "Travel destination view"}
            src={getLiveDestinationImage(props.destination)}
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,29,72,0.04),rgba(0,29,72,0.42))]" />
          <div className="absolute left-5 top-5 rounded-full bg-[rgba(255,255,255,0.76)] px-3 py-1.5 backdrop-blur-md">
            <p className="font-label text-[10px] font-bold uppercase tracking-[0.18em] text-[color:var(--accent)]">
              Live destination
            </p>
          </div>
        </div>

        <div className="flex flex-col justify-between gap-4 px-5 py-5 md:px-6 md:py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-label text-[10px] uppercase tracking-[0.2em] text-foreground/48">
                Upcoming trip • {formatTripLength(props.startDate, props.endDate)}
              </p>
              <h2 className="mt-3 text-[2rem] font-semibold tracking-tight text-foreground md:text-[2.35rem]">
                {props.destination || "Your next destination"}
              </h2>
            </div>
            <Link
              href={`/brochure/${props.tripId}`}
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
                    {formatRouteSummary(props.fromLocation, props.destination)}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <HeroInlineDetail
                icon={CalendarRange}
                label="Travel window"
                value={formatCompactDateRange(props.startDate, props.endDate)}
              />
              <HeroInlineDetail
                icon={UsersRound}
                label="Party"
                value={formatTravelers(props.adults, props.childCount)}
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
    <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-background px-4 py-3 text-[color:var(--foreground)]">
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
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[color:var(--accent)] text-white shadow-[0_8px_24px_rgba(0,49,120,0.2)]">
            <CalendarRange className="h-3 w-3" />
          </span>
        ) : (
          <span className="h-3 w-3 rounded-full bg-foreground/22" />
        )}
      </div>

      <div className="rounded-[1.35rem] border border-shell-border/70 bg-[color:color-mix(in_srgb,var(--background)_82%,var(--panel))] px-6 py-5">
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
              <span className="w-14 pt-3 text-sm font-semibold text-[color:var(--accent)]">
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

function FlightCard({ flight }: { flight: FlightDetail | undefined }) {
  return (
    <section className="rounded-xl bg-[color:var(--accent)] px-5 py-5 text-white">
      <p className="font-label text-[10px] uppercase tracking-[0.16em] text-white/68">
        Outbound flight
      </p>
      {flight ? (
        <>
          <div className="mt-5 flex items-end justify-between gap-4">
            <AirportCode code={flight.departure_airport} />
            <div className="flex flex-1 flex-col items-center px-3">
              <Plane className="h-4 w-4 text-white/74" />
              <div className="mt-2 h-px w-full border-t border-dashed border-white/34" />
              <p className="mt-2 text-[10px] uppercase tracking-[0.16em] text-white/66">
                {flight.duration_text || "Flight time"}
              </p>
            </div>
            <AirportCode code={flight.arrival_airport} align="right" />
          </div>
          <div className="mt-5 rounded-lg bg-white/12 px-4 py-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span>{flight.carrier}</span>
              <span className="font-semibold">
                {flight.flight_number || "TBD"}
              </span>
            </div>
          </div>
        </>
      ) : (
        <p className="mt-4 text-sm leading-7 text-white/78">
          Flight details will appear here once the planner has enough route and
          date context.
        </p>
      )}
    </section>
  );
}

function AirportCode({
  code,
  align = "left",
}: {
  code: string;
  align?: "left" | "right";
}) {
  return (
    <div className={cn("min-w-[4rem]", align === "right" && "text-right")}>
      <p className="font-display text-4xl leading-none">{code}</p>
    </div>
  );
}

function WeatherCard({ forecasts }: { forecasts: WeatherDetail[] }) {
  const displayForecasts =
    forecasts.length > 0
      ? forecasts
      : [
          { id: "a", day_label: "Wed", summary: "", high_c: null, low_c: null, notes: [] },
          { id: "b", day_label: "Thu", summary: "", high_c: null, low_c: null, notes: [] },
          { id: "c", day_label: "Fri", summary: "", high_c: null, low_c: null, notes: [] },
        ];

  return (
    <section className="rounded-xl border border-shell-border/70 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_10%,white),color-mix(in_srgb,var(--accent2)_10%,white))] px-5 py-5">
      <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/50">
        Forecast
      </p>
      <div className="mt-4 flex items-center gap-4">
        <CloudSun className="h-12 w-12 text-[color:var(--accent)]" />
        <div>
          <p className="font-display text-4xl leading-none text-[color:var(--accent)]">
            {forecasts[0] ? formatPrimaryTemperature(forecasts[0]) : "—"}
          </p>
          <p className="mt-1 text-sm text-foreground/60">
            {forecasts[0]?.summary || "Weather will appear when dates are locked."}
          </p>
        </div>
      </div>
      <div className="mt-5 grid grid-cols-3 gap-3 rounded-lg bg-white/55 px-4 py-3">
        {displayForecasts.map((forecast) => (
          <div key={forecast.id} className="text-center">
            <p className="text-[10px] uppercase tracking-[0.16em] text-foreground/50">
              {forecast.day_label}
            </p>
            <CloudSun className="mx-auto mt-2 h-4 w-4 text-[color:var(--accent)]" />
            <p className="mt-2 text-xs font-semibold text-foreground">
              {formatTemperatureBand(forecast.high_c, forecast.low_c)}
            </p>
          </div>
        ))}
      </div>
    </section>
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

function HotelSummary({ hotel }: { hotel: HotelStayDetail }) {
  return (
    <div className="overflow-hidden rounded-xl bg-background">
      <div className="h-28 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_18%,transparent),color-mix(in_srgb,var(--accent2)_16%,transparent))]" />
      <div className="px-4 py-4">
        <p className="text-lg font-semibold text-foreground">{hotel.hotel_name}</p>
        <p className="mt-1 text-sm text-foreground/58">
          {hotel.area || "Area still being refined"}
        </p>
        <p className="mt-3 text-sm leading-7 text-foreground/66">
          {formatDateRange(hotel.check_in, hotel.check_out)}
        </p>
        {hotel.notes[0] ? (
          <p className="mt-2 text-sm leading-7 text-foreground/66">
            {hotel.notes[0]}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ActivityFeature({
  activity,
  destination,
}: {
  activity: ActivityDetail;
  destination: string | null;
}) {
  return (
    <div className="overflow-hidden rounded-xl bg-background">
      <div
        className="h-32"
        style={buildActivityVisualStyle(destination, activity)}
        aria-hidden="true"
      />
      <div className="px-4 py-4">
        <p className="text-lg font-semibold text-foreground">{activity.title}</p>
        <p className="mt-1 text-sm text-foreground/56">
          {[activity.category, activity.day_label].filter(Boolean).join(" • ") ||
            "Trip highlight"}
        </p>
        {activity.notes[0] ? (
          <p className="mt-3 text-sm leading-7 text-foreground/66">
            {activity.notes[0]}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function SelectionCard({
  title,
  description,
  options,
}: {
  title: string;
  description: string;
  options: string[];
}) {
  return (
    <article className="rounded-xl bg-background px-4 py-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-7 text-foreground/64">{description}</p>
      {options.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {options.map((option) => (
            <span
              key={option}
              className="rounded-full bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--accent)]"
            >
              {option}
            </span>
          ))}
        </div>
      ) : null}
    </article>
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

function buildSelectionCards(draft: PlannerWorkspaceState["tripDraft"]) {
  const cards = draft.status.missing_fields.map((fieldName) => {
    switch (fieldName) {
      case "from_location":
        return {
          title: "Choose the departure point",
          description: "The trip still needs a clear origin city or airport.",
          options: ["Use saved home airport", "Choose another airport", "Keep flexible"],
        };
      case "to_location":
        return {
          title: "Confirm the destination",
          description: "The route needs a final destination before the board can sharpen.",
          options: ["Lock destination", "Compare two cities", "Ask for ideas"],
        };
      case "start_date":
      case "end_date":
        return {
          title: "Set the travel window",
          description: "Dates are still missing, so flights and weather remain approximate.",
          options: ["Choose exact dates", "Keep flexible", "Use a rough month"],
        };
      default:
        return {
          title: `Refine ${fieldName.replaceAll("_", " ")}`,
          description: "Wandrix is waiting on a clearer user choice for this field.",
          options: [],
        };
    }
  });

  if (cards.length === 0 && draft.configuration.activity_styles.length === 0) {
    cards.push({
      title: "Pick a trip feel",
      description: "A trip tone would help the board shape better recommendations.",
      options: ["Culture", "Food", "Relaxed", "Luxury"],
    });
  }

  return cards;
}

function getLiveDestinationImage(destination: string | null) {
  const normalized = destination?.toLowerCase() ?? "";

  if (normalized.includes("kyoto")) {
    return "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1400&q=80";
  }

  if (normalized.includes("barcelona")) {
    return "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?auto=format&fit=crop&w=1400&q=80";
  }

  if (normalized.includes("lisbon")) {
    return "https://images.unsplash.com/photo-1513735492246-483525079686?auto=format&fit=crop&w=1400&q=80";
  }

  if (normalized.includes("amalfi")) {
    return "https://images.unsplash.com/photo-1612698093158-e07ac200d44e?auto=format&fit=crop&w=1400&q=80";
  }

  if (destination) {
    return `https://source.unsplash.com/1400x900/?${encodeURIComponent(`${destination} travel landscape`)}`;
  }

  return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80";
}

function buildActivityVisualStyle(
  destination: string | null,
  activity: ActivityDetail,
) {
  const query = encodeURIComponent(
    [destination, activity.category, activity.title].filter(Boolean).join(" "),
  );

  return {
    backgroundImage: `linear-gradient(135deg, color-mix(in srgb, var(--accent) 14%, transparent), color-mix(in srgb, var(--accent2) 12%, transparent)), url(https://source.unsplash.com/900x700/?${query})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
  } as const;
}

function buildTimelineDescription(item: TimelineItem) {
  const parts = [
    item.location_label,
    item.end_at
      ? `${formatTime(item.start_at || item.end_at || "")} to ${formatTime(item.end_at)}`
      : null,
    item.details[0],
  ].filter(Boolean);

  return parts.join(" • ") || "Timing still being shaped";
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

function formatTravelers(adults: number, children: number) {
  return `${adults} adults${children ? `, ${children} children` : ""}`;
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

function formatDateRange(startDate: string | null, endDate: string | null) {
  return `${formatDateShort(startDate)} through ${formatDateShort(endDate)}`;
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

function formatCompactDateRange(startDate: string | null, endDate: string | null) {
  if (!startDate && !endDate) {
    return "TBD";
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

function formatTemperatureBand(high: number | null, low: number | null) {
  if (high == null && low == null) {
    return "TBD";
  }

  if (high != null && low != null) {
    return `${Math.round(low)}° to ${Math.round(high)}°`;
  }

  return `${Math.round(high ?? low ?? 0)}°`;
}

function formatPrimaryTemperature(forecast: WeatherDetail) {
  if (forecast.high_c == null && forecast.low_c == null) {
    return "—";
  }

  return `${Math.round(forecast.high_c ?? forecast.low_c ?? 0)}°`;
}
