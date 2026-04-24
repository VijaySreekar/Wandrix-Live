"use client";

import Link from "next/link";
import {
  ArrowRight,
  CalendarRange,
  CheckCircle2,
  Clock,
  MapPin,
  Plane,
  Route,
} from "lucide-react";
import type { ReactNode } from "react";

import { FlightCard } from "@/components/package/trip-board-cards";
import { TripSuggestionBoard } from "@/components/package/trip-suggestion-board";
import type {
  AdvancedFlightOptionCard,
  AdvancedFlightStrategyCard,
  TripSuggestionBoardState,
} from "@/types/trip-conversation";
import type { FlightDetail, TimelineItem } from "@/types/trip-draft";

type FlightPreviewKey =
  | "overview"
  | "live-board"
  | "reference"
  | "advanced-ready"
  | "advanced-blocked";

type FlightPreviewShellProps = {
  active: FlightPreviewKey;
  title: string;
  subtitle: string;
  children: ReactNode;
};

const PREVIEW_LINKS: Array<{
  key: FlightPreviewKey;
  label: string;
  href: string;
}> = [
  { key: "overview", label: "Overview", href: "/flight-previews" },
  { key: "live-board", label: "Live board", href: "/flight-previews/live-board" },
  { key: "reference", label: "Reference", href: "/flight-previews/reference" },
  {
    key: "advanced-ready",
    label: "Advanced options",
    href: "/flight-previews/advanced-ready",
  },
  {
    key: "advanced-blocked",
    label: "Missing details",
    href: "/flight-previews/advanced-blocked",
  },
];

const SAMPLE_OUTBOUND_FLIGHT: FlightDetail = {
  id: "sample-flight-lisbon-outbound",
  direction: "outbound",
  carrier: "British Airways",
  flight_number: "BA502",
  departure_airport: "LHR",
  arrival_airport: "LIS",
  departure_time: "2026-05-15T08:40:00Z",
  arrival_time: "2026-05-15T11:25:00Z",
  duration_text: "2h 45m direct",
  price_text: "GBP 216 pp",
  stop_count: 0,
  timing_quality: "Best arrival",
  inventory_notice: "Sample fare shown for UI review.",
  notes: [
    "Morning departure keeps the first Lisbon afternoon usable.",
    "Direct route avoids connection risk for a short trip.",
  ],
};

const SAMPLE_RETURN_FLIGHT: FlightDetail = {
  id: "sample-flight-lisbon-return",
  direction: "return",
  carrier: "British Airways",
  flight_number: "BA503",
  departure_airport: "LIS",
  arrival_airport: "LHR",
  departure_time: "2026-05-18T18:55:00Z",
  arrival_time: "2026-05-18T21:35:00Z",
  duration_text: "2h 40m direct",
  price_text: "GBP 198 pp",
  stop_count: 0,
  timing_quality: "Best final day",
  notes: [
    "Evening return leaves room for a relaxed final lunch.",
    "Direct route keeps the short-break structure clean.",
  ],
};

const SAMPLE_TIMELINE_ITEMS: TimelineItem[] = [
  {
    id: "sample-flight-timeline-outbound",
    type: "flight",
    title: "Outbound to Lisbon",
    day_label: "Day 1",
    start_at: SAMPLE_OUTBOUND_FLIGHT.departure_time,
    end_at: SAMPLE_OUTBOUND_FLIGHT.arrival_time,
    location_label: "London Heathrow to Lisbon",
    summary: "Arrive before lunch and keep the first afternoon light.",
    details: ["Build in a low-pressure check-in window after landing."],
    source_module: "flights",
    status: "confirmed",
  },
  {
    id: "sample-flight-timeline-return",
    type: "flight",
    title: "Return to London",
    day_label: "Day 4",
    start_at: SAMPLE_RETURN_FLIGHT.departure_time,
    end_at: SAMPLE_RETURN_FLIGHT.arrival_time,
    location_label: "Lisbon to London Heathrow",
    summary: "Evening return protects the final day from feeling rushed.",
    details: ["Keep luggage storage near the hotel or final lunch area."],
    source_module: "flights",
    status: "confirmed",
  },
];

const FLIGHT_STRATEGIES: AdvancedFlightStrategyCard[] = [
  {
    id: "best_timing",
    title: "Best trip rhythm",
    description:
      "Prioritize flights that protect the first afternoon and keep the final day relaxed.",
    bullets: [
      "Morning outbound gives more usable time in Lisbon.",
      "Evening return keeps the final day open.",
      "Usually the most coherent choice for a short city break.",
    ],
    recommended: true,
  },
  {
    id: "smoothest_route",
    title: "Smoothest route",
    description:
      "Keep the route direct and predictable, even if the times are less expressive.",
    bullets: [
      "Avoids connection risk.",
      "Keeps airport transfers easy to reason about.",
      "Good fit when the itinerary is already dense.",
    ],
    recommended: false,
  },
  {
    id: "best_value",
    title: "Best value",
    description:
      "Trade a little timing comfort for a lower fare while keeping the trip workable.",
    bullets: [
      "Cheaper fare class and less ideal departure time.",
      "Still avoids awkward overnight connections.",
      "Useful when budget pressure matters more than arrival shape.",
    ],
    recommended: false,
  },
  {
    id: "keep_flexible",
    title: "Keep flights flexible",
    description:
      "Use placeholder flight assumptions for now and avoid locking carrier or time.",
    bullets: [
      "Useful while dates or airport preference are still soft.",
      "Keeps the itinerary from overfitting to sample inventory.",
      "Can still shape arrival and departure day assumptions.",
    ],
    recommended: false,
  },
];

const OUTBOUND_OPTIONS: AdvancedFlightOptionCard[] = [
  {
    id: "advanced-outbound-ba502",
    direction: "outbound",
    carrier: "British Airways",
    flight_number: "BA502",
    departure_airport: "LHR",
    arrival_airport: "LIS",
    departure_time: "2026-05-15T08:40:00Z",
    arrival_time: "2026-05-15T11:25:00Z",
    duration_text: "2h 45m",
    price_text: "GBP 216 pp",
    stop_count: 0,
    timing_quality: "Best arrival",
    summary:
      "The cleanest arrival-day shape: early enough for lunch, late enough to avoid a punishing start.",
    tradeoffs: ["Direct", "Better first afternoon", "Moderate fare"],
    source_kind: "provider",
    recommended: true,
  },
  {
    id: "advanced-outbound-u28515",
    direction: "outbound",
    carrier: "easyJet",
    flight_number: "U28515",
    departure_airport: "LGW",
    arrival_airport: "LIS",
    departure_time: "2026-05-15T06:20:00Z",
    arrival_time: "2026-05-15T09:05:00Z",
    duration_text: "2h 45m",
    price_text: "GBP 142 pp",
    stop_count: 0,
    timing_quality: "Earliest arrival",
    summary:
      "The strongest value option, but the departure is early enough to make the first day feel sharper.",
    tradeoffs: ["Lower fare", "Very early start", "More usable morning"],
    source_kind: "provider",
    recommended: false,
  },
  {
    id: "advanced-outbound-tp1363",
    direction: "outbound",
    carrier: "TAP Air Portugal",
    flight_number: "TP1363",
    departure_airport: "LHR",
    arrival_airport: "LIS",
    departure_time: "2026-05-15T13:45:00Z",
    arrival_time: "2026-05-15T16:30:00Z",
    duration_text: "2h 45m",
    price_text: "GBP 174 pp",
    stop_count: 0,
    timing_quality: "Soft morning",
    summary:
      "A gentler departure from London, but it compresses the first Lisbon afternoon.",
    tradeoffs: ["No early alarm", "Less first-day time", "Direct"],
    source_kind: "provider",
    recommended: false,
  },
];

const RETURN_OPTIONS: AdvancedFlightOptionCard[] = [
  {
    id: "advanced-return-ba503",
    direction: "return",
    carrier: "British Airways",
    flight_number: "BA503",
    departure_airport: "LIS",
    arrival_airport: "LHR",
    departure_time: "2026-05-18T18:55:00Z",
    arrival_time: "2026-05-18T21:35:00Z",
    duration_text: "2h 40m",
    price_text: "GBP 198 pp",
    stop_count: 0,
    timing_quality: "Best final day",
    summary:
      "The best fit for a final-day lunch and unhurried airport transfer before heading home.",
    tradeoffs: ["Direct", "Better final day", "Later arrival home"],
    source_kind: "provider",
    recommended: true,
  },
  {
    id: "advanced-return-u28516",
    direction: "return",
    carrier: "easyJet",
    flight_number: "U28516",
    departure_airport: "LIS",
    arrival_airport: "LGW",
    departure_time: "2026-05-18T12:15:00Z",
    arrival_time: "2026-05-18T14:55:00Z",
    duration_text: "2h 40m",
    price_text: "GBP 126 pp",
    stop_count: 0,
    timing_quality: "Best value",
    summary:
      "Cheaper and still direct, but it turns the final day into a checkout-and-airport morning.",
    tradeoffs: ["Lower fare", "Compressed final day", "Direct"],
    source_kind: "provider",
    recommended: false,
  },
  {
    id: "advanced-return-tp1366",
    direction: "return",
    carrier: "TAP Air Portugal",
    flight_number: "TP1366",
    departure_airport: "LIS",
    arrival_airport: "LHR",
    departure_time: "2026-05-18T20:10:00Z",
    arrival_time: "2026-05-18T22:50:00Z",
    duration_text: "2h 40m",
    price_text: "GBP 184 pp",
    stop_count: 0,
    timing_quality: "Latest return",
    summary:
      "Maximizes Lisbon time, though the late home arrival may be less comfortable before work.",
    tradeoffs: ["Most final-day time", "Late home arrival", "Direct"],
    source_kind: "provider",
    recommended: false,
  },
];

const READY_FLIGHT_BOARD: TripSuggestionBoardState = {
  mode: "advanced_flights_workspace",
  title: "Flight options",
  subtitle: "London to Lisbon · 15 to 18 May · 2 travelers",
  cards: [],
  planning_mode_cards: [],
  advanced_anchor_cards: [],
  flight_strategy_cards: FLIGHT_STRATEGIES,
  outbound_flight_options: OUTBOUND_OPTIONS,
  return_flight_options: RETURN_OPTIONS,
  selected_flight_strategy: "best_timing",
  selected_outbound_flight_id: OUTBOUND_OPTIONS[0].id,
  selected_return_flight_id: RETURN_OPTIONS[0].id,
  selected_outbound_flight: OUTBOUND_OPTIONS[0],
  selected_return_flight: RETURN_OPTIONS[0],
  flight_selection_status: "selected",
  flight_results_status: "ready",
  flight_workspace_summary:
    "The route is ready to compare. Direct London to Lisbon options are strong enough to choose a working outbound and return pair.",
  flight_selection_summary:
    "The recommended pair protects both the first afternoon and the final day without adding a connection.",
  flight_downstream_notes: [
    "A late-morning arrival supports a gentle Alfama or Baixa first afternoon.",
    "An evening return means the final day can include lunch and one last neighborhood walk.",
  ],
  flight_arrival_day_impact_summary:
    "Arrival timing supports a light first afternoon rather than a recovery day.",
  flight_departure_day_impact_summary:
    "The return timing keeps the last day useful without making the home arrival extreme.",
  flight_timing_review_notes: [
    "Check baggage rules before locking a low-cost carrier option.",
  ],
  have_details: [
    { id: "route", label: "Route", status: "known", value: "London to Lisbon" },
    { id: "dates", label: "Dates", status: "known", value: "15 to 18 May" },
    { id: "travelers", label: "Travelers", status: "known", value: "2 adults" },
  ],
  need_details: [],
  visible_steps: [],
  required_steps: [],
  details_form: null,
  confirm_cta_label: null,
  own_choice_prompt: null,
};

const BLOCKED_FLIGHT_BOARD: TripSuggestionBoardState = {
  mode: "advanced_flights_workspace",
  title: "Flight options",
  subtitle: "Lisbon long weekend · route still incomplete",
  cards: [],
  planning_mode_cards: [],
  advanced_anchor_cards: [],
  flight_strategy_cards: FLIGHT_STRATEGIES,
  outbound_flight_options: [],
  return_flight_options: [],
  selected_flight_strategy: null,
  selected_outbound_flight_id: null,
  selected_return_flight_id: null,
  selected_outbound_flight: null,
  selected_return_flight: null,
  flight_selection_status: "none",
  flight_results_status: "blocked",
  flight_missing_requirements: ["origin", "travel dates"],
  flight_workspace_summary:
    "Wandrix needs a departure point and a usable date window before it can compare flight options cleanly.",
  flight_downstream_notes: [
    "The planner should ask for missing context before committing a flight shape.",
    "This state is useful for checking how the board behaves before provider results exist.",
  ],
  have_details: [
    { id: "destination", label: "Destination", status: "known", value: "Lisbon" },
    { id: "length", label: "Length", status: "known", value: "3 or 4 nights" },
  ],
  need_details: [
    { id: "origin", label: "Origin", status: "needed", value: null },
    { id: "dates", label: "Dates", status: "needed", value: "Late April or May" },
  ],
  visible_steps: [],
  required_steps: [],
  details_form: null,
  confirm_cta_label: null,
  own_choice_prompt: null,
};

export function FlightPreviewShell({
  active,
  title,
  subtitle,
  children,
}: FlightPreviewShellProps) {
  return (
    <main className="min-h-[calc(100vh-var(--nav-height))] bg-background px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto grid w-full max-w-[1500px] gap-5">
        <header className="grid gap-4 border-b border-shell-border pb-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div>
            <p className="font-label text-[11px] uppercase tracking-[0.18em] text-foreground/48">
              Flight module previews
            </p>
            <h1 className="mt-3 text-3xl font-semibold text-foreground md:text-4xl">
              {title}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-foreground/66">
              {subtitle}
            </p>
          </div>

          <nav aria-label="Flight preview pages" className="flex flex-wrap gap-2">
            {PREVIEW_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active === link.key ? "page" : undefined}
                className={[
                  "inline-flex min-h-10 items-center rounded-md border px-3 py-2 text-sm font-medium transition-colors",
                  active === link.key
                    ? "border-[color:var(--accent)] bg-accent-soft text-[color:var(--accent)]"
                    : "border-shell-border bg-panel text-foreground/72 hover:bg-panel-strong hover:text-foreground",
                ].join(" ")}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </header>

        {children}
      </div>
    </main>
  );
}

export function FlightPreviewHub() {
  return (
    <FlightPreviewShell
      active="overview"
      title="Flight board samples"
      subtitle="Sample-only pages for reviewing the flight UI surfaces without needing a saved trip or provider response."
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {PREVIEW_LINKS.filter((link) => link.key !== "overview").map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="group flex min-h-48 flex-col justify-between rounded-lg border border-shell-border bg-shell px-5 py-5 transition-colors hover:bg-panel-strong"
          >
            <div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-soft text-[color:var(--accent)]">
                {getPreviewIcon(link.key)}
              </div>
              <h2 className="mt-5 text-lg font-semibold text-foreground">
                {link.label}
              </h2>
              <p className="mt-2 text-sm leading-6 text-foreground/62">
                {getPreviewSummary(link.key)}
              </p>
            </div>
            <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[color:var(--accent)]">
              Open sample
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Link>
        ))}
      </section>
    </FlightPreviewShell>
  );
}

export function FlightLiveBoardPreview() {
  return (
    <FlightPreviewShell
      active="live-board"
      title="Live board flight card"
      subtitle="The compact working-flights panel that appears in the right-side trip board once flight data is available."
    >
      <section className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(360px,0.55fr)] xl:items-start">
        <div className="rounded-lg border border-shell-border bg-shell px-5 py-5">
          <div className="grid gap-5 lg:grid-cols-3">
            <PreviewStat label="Route" value="London to Lisbon" icon={<Route className="h-4 w-4" />} />
            <PreviewStat label="Window" value="15 to 18 May" icon={<CalendarRange className="h-4 w-4" />} />
            <PreviewStat label="Shape" value="Direct return pair" icon={<CheckCircle2 className="h-4 w-4" />} />
          </div>

          <div className="mt-6 rounded-lg border border-shell-border bg-panel px-5 py-5">
            <p className="text-sm font-semibold text-foreground">
              Arrival and departure impact
            </p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <ImpactNote
                title="Arrival day"
                body="The outbound lands before lunch, so the first day can carry a neighborhood walk without feeling overplanned."
              />
              <ImpactNote
                title="Final day"
                body="The return leaves after dinner-hour transfer time, keeping the last day useful for one final Lisbon stop."
              />
            </div>
          </div>
        </div>

        <div className="xl:sticky xl:top-[calc(var(--nav-height)+1.25rem)]">
          <FlightCard
            flight={SAMPLE_OUTBOUND_FLIGHT}
            returnFlight={SAMPLE_RETURN_FLIGHT}
          />
        </div>
      </section>
    </FlightPreviewShell>
  );
}

export function FlightReferenceBoardPreview() {
  return (
    <FlightPreviewShell
      active="reference"
      title="Saved-trip flight reference"
      subtitle="A sample of the supporting flight module page that inspects saved structured flights and matching timeline blocks."
    >
      <section className="grid gap-4 lg:grid-cols-[290px_minmax(0,1fr)]">
        <aside className="rounded-lg border border-shell-border bg-shell">
          <div className="border-b border-shell-border px-4 py-4">
            <p className="text-base font-semibold text-foreground">Flights</p>
            <p className="mt-1 text-sm leading-6 text-foreground/62">
              Lisbon spring long weekend
            </p>
          </div>
          <div className="grid gap-2 p-4">
            {[
              "Lisbon spring long weekend",
              "Kyoto autumn food week",
              "Barcelona family reset",
            ].map((trip, index) => (
              <button
                key={trip}
                type="button"
                className={[
                  "rounded-lg border px-3 py-3 text-left text-sm transition-colors",
                  index === 0
                    ? "border-[color:var(--accent)]/30 bg-accent-soft text-foreground"
                    : "border-shell-border bg-panel text-foreground/66 hover:bg-panel-strong",
                ].join(" ")}
              >
                <span className="block font-medium">{trip}</span>
                <span className="mt-1 block text-xs text-foreground/52">
                  {index === 0 ? "London to Lisbon" : "Sample trip"}
                </span>
              </button>
            ))}
          </div>
        </aside>

        <div className="grid gap-4">
          <section className="rounded-lg border border-shell-border bg-shell px-5 py-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold text-foreground">
                  Flight reference
                </h2>
                <p className="mt-2 max-w-3xl text-sm leading-7 text-foreground/66">
                  Saved structured flight data, provider status, and timeline movement for the selected trip.
                </p>
              </div>
              <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5 text-xs font-medium text-foreground/62">
                Sample draft
              </span>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <PreviewStat label="Travel window" value="15 to 18 May" icon={<CalendarRange className="h-4 w-4" />} />
              <PreviewStat label="Module status" value="Enabled" icon={<CheckCircle2 className="h-4 w-4" />} />
              <PreviewStat label="Flight items" value="2" icon={<Plane className="h-4 w-4" />} />
              <PreviewStat label="Timeline blocks" value="2" icon={<Clock className="h-4 w-4" />} />
            </div>
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <div className="rounded-lg border border-shell-border bg-shell px-5 py-5">
              <h3 className="text-base font-semibold text-foreground">
                Structured flight items
              </h3>
              <div className="mt-4 grid gap-3">
                {[SAMPLE_OUTBOUND_FLIGHT, SAMPLE_RETURN_FLIGHT].map((flight) => (
                  <FlightReferenceItem key={flight.id} flight={flight} />
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-shell-border bg-shell px-5 py-5">
              <h3 className="text-base font-semibold text-foreground">
                Timeline blocks
              </h3>
              <div className="mt-4 grid gap-3">
                {SAMPLE_TIMELINE_ITEMS.map((item) => (
                  <TimelineReferenceItem key={item.id} item={item} />
                ))}
              </div>
            </div>
          </section>
        </div>
      </section>
    </FlightPreviewShell>
  );
}

export function FlightAdvancedReadyPreview() {
  return (
    <FlightPreviewShell
      active="advanced-ready"
      title="Advanced flight selection"
      subtitle="The right-side board used when Advanced Planning has enough route and timing context to compare flight choices."
    >
      <div className="h-[calc(100vh-13rem)] min-h-[48rem] overflow-hidden rounded-lg border border-shell-border bg-shell">
        <TripSuggestionBoard
          board={READY_FLIGHT_BOARD}
          decisionCards={[]}
          disabled={false}
          onAction={noopBoardAction}
        />
      </div>
    </FlightPreviewShell>
  );
}

export function FlightAdvancedBlockedPreview() {
  return (
    <FlightPreviewShell
      active="advanced-blocked"
      title="Flight details missing"
      subtitle="The blocked Advanced Planning state shown before Wandrix has enough context to run a meaningful flight comparison."
    >
      <div className="h-[calc(100vh-13rem)] min-h-[40rem] overflow-hidden rounded-lg border border-shell-border bg-shell">
        <TripSuggestionBoard
          board={BLOCKED_FLIGHT_BOARD}
          decisionCards={[]}
          disabled={false}
          onAction={noopBoardAction}
        />
      </div>
    </FlightPreviewShell>
  );
}

function PreviewStat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-shell-border bg-panel px-4 py-4">
      <div className="flex items-center gap-2 text-[color:var(--accent)]">
        {icon}
        <p className="text-xs font-semibold uppercase tracking-[0.14em]">
          {label}
        </p>
      </div>
      <p className="mt-3 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}

function ImpactNote({ title, body }: { title: string; body: string }) {
  return (
    <article className="rounded-lg border border-shell-border bg-background px-4 py-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-6 text-foreground/64">{body}</p>
    </article>
  );
}

function FlightReferenceItem({ flight }: { flight: FlightDetail }) {
  return (
    <article className="rounded-lg border border-shell-border bg-panel px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">
            {flight.carrier}
            {flight.flight_number ? ` ${flight.flight_number}` : ""}
          </p>
          <p className="mt-1 text-sm text-foreground/62">
            {flight.departure_airport} to {flight.arrival_airport}
          </p>
        </div>
        <span className="rounded-md border border-shell-border bg-background px-2.5 py-1 text-xs text-foreground/60">
          {flight.direction}
        </span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
        <AirportBlock
          label={flight.departure_airport}
          time={formatFlightDateTime(flight.departure_time)}
        />
        <div className="hidden items-center gap-2 text-foreground/34 sm:flex">
          <div className="h-px w-10 border-t border-dashed border-shell-border" />
          <Plane className="h-4 w-4 text-[color:var(--accent)]" />
          <div className="h-px w-10 border-t border-dashed border-shell-border" />
        </div>
        <AirportBlock
          label={flight.arrival_airport}
          time={formatFlightDateTime(flight.arrival_time)}
          align="right"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {[flight.duration_text, flight.price_text, flight.timing_quality]
          .filter(Boolean)
          .map((fact) => (
            <span
              key={fact}
              className="rounded-md border border-shell-border bg-background px-2.5 py-1 text-xs font-medium text-foreground/62"
            >
              {fact}
            </span>
          ))}
      </div>
    </article>
  );
}

function TimelineReferenceItem({ item }: { item: TimelineItem }) {
  return (
    <article className="rounded-lg border border-shell-border bg-panel px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">{item.title}</p>
          <p className="mt-1 text-sm text-foreground/62">
            {[item.day_label, item.location_label].filter(Boolean).join(" · ")}
          </p>
        </div>
        <span className="rounded-md border border-shell-border bg-background px-2.5 py-1 text-xs text-foreground/60">
          {item.status}
        </span>
      </div>
      {item.summary ? (
        <p className="mt-3 text-sm leading-6 text-foreground/66">
          {item.summary}
        </p>
      ) : null}
    </article>
  );
}

function AirportBlock({
  label,
  time,
  align = "left",
}: {
  label: string;
  time: string;
  align?: "left" | "right";
}) {
  return (
    <div className={align === "right" ? "sm:text-right" : ""}>
      <p className="font-display text-2xl font-bold text-foreground">{label}</p>
      <p className="mt-1 text-xs leading-5 text-foreground/58">{time}</p>
    </div>
  );
}

function getPreviewIcon(key: FlightPreviewKey) {
  switch (key) {
    case "live-board":
      return <Plane className="h-5 w-5" />;
    case "reference":
      return <MapPin className="h-5 w-5" />;
    case "advanced-ready":
      return <CheckCircle2 className="h-5 w-5" />;
    case "advanced-blocked":
      return <Clock className="h-5 w-5" />;
    default:
      return <Route className="h-5 w-5" />;
  }
}

function getPreviewSummary(key: FlightPreviewKey) {
  switch (key) {
    case "live-board":
      return "Compact working-flights panel used inside the live trip board.";
    case "reference":
      return "Saved-trip flight inspection page with items and timeline blocks.";
    case "advanced-ready":
      return "Advanced Planning comparison board with selectable flight options.";
    case "advanced-blocked":
      return "Advanced Planning board before route and timing are ready.";
    default:
      return "Flight preview sample.";
  }
}

function formatFlightDateTime(value: string | null | undefined) {
  if (!value) {
    return "Time open";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function noopBoardAction() {}
