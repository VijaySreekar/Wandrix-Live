"use client";

import { useMemo } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BedDouble,
  CalendarRange,
  Car,
  CheckCircle2,
  Clock,
  CloudSun,
  Compass,
  ExternalLink,
  MapPin,
  MapPinned,
  Plane,
  Sparkles,
  UtensilsCrossed,
  UsersRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/animate-ui/components/radix/dialog";
import {
  HotelSummary,
  WeatherCard,
  getLiveDestinationImage,
} from "@/components/package/trip-board-cards";
import { FlightCard } from "@/components/package/trip-board-flight-card";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  AdvancedActivityCandidateCard,
  AdvancedFlightOptionCard,
  PlannerConflictRecord,
  QuickPlanIntelligenceSummary,
} from "@/types/trip-conversation";
import type {
  FlightDetail,
  TimelineItem,
  TripBudgetEstimate,
} from "@/types/trip-draft";

type TripLiveBoardProps = {
  workspace: PlannerWorkspaceState;
  onAction: (action: PlannerBoardActionIntent) => void;
};

export function TripLiveBoard({ workspace, onAction }: TripLiveBoardProps) {
  const { tripDraft } = workspace;
  const { configuration, module_outputs: moduleOutputs, conversation } =
    tripDraft;
  const flightPlanning = conversation.flight_planning ?? null;
  const selectedOutboundFlight =
    flightPlanning?.selection_status === "completed"
      ? toFlightDetail(flightPlanning.selected_outbound_flight)
      : null;
  const selectedReturnFlight =
    flightPlanning?.selection_status === "completed"
      ? toFlightDetail(flightPlanning.selected_return_flight)
      : null;
  const hasSelectedFlights = flightPlanning?.selection_status === "completed";
  const outboundFlight =
    selectedOutboundFlight ??
    moduleOutputs.flights.find((flight) => flight.direction === "outbound");
  const returnFlight =
    selectedReturnFlight ??
    moduleOutputs.flights.find((flight) => flight.direction === "return");
  const stay =
    moduleOutputs.hotels.find(
      (hotel) =>
        hotel.id === conversation.stay_planning?.selected_hotel_id ||
        (!!conversation.stay_planning?.selected_hotel_name &&
          hotel.hotel_name === conversation.stay_planning.selected_hotel_name),
    ) ??
    moduleOutputs.hotels[0] ??
    null;
  const activityPlanning = conversation.activity_planning ?? {
    visible_candidates: [],
    schedule_summary: null,
    workspace_summary: null,
  };
  const tripStylePlanning = conversation.trip_style_planning ?? null;
  const tripStyleSummary =
    tripStylePlanning?.selection_status === "completed"
      ? tripStylePlanning.completion_summary ||
        tripStylePlanning.workspace_summary ||
        null
      : null;
  const flightPlanningSummary =
    flightPlanning?.completion_summary ||
    flightPlanning?.selection_summary ||
    flightPlanning?.workspace_summary ||
    null;
  const leadActivityCandidate =
    activityPlanning.visible_candidates.find(
      (candidate) => candidate.disposition === "essential",
    ) ??
    activityPlanning.visible_candidates.find(
      (candidate) => candidate.kind === "event" && Boolean(candidate.start_at),
    ) ??
    activityPlanning.visible_candidates[0] ??
    null;
  const tripDayCount = getTripDayCount(configuration.start_date, configuration.end_date);
  const weather = moduleOutputs.weather.slice(0, Math.min(Math.max(tripDayCount, 3), 7));
  const budgetEstimate =
    conversation.planning_mode === "quick" ? tripDraft.budget_estimate ?? null : null;
  const weatherPlanning = conversation.weather_planning ?? null;
  const plannerConflicts = (conversation.planner_conflicts ?? []).filter(
    (conflict) => (conflict.status ?? "open") !== "resolved",
  );
  const visibleTimeline = useMemo(
    () =>
      buildVisibleTimeline(tripDraft.timeline, {
        showQuickPlanLogistics: conversation.planning_mode === "quick",
        showProviderFlights: hasSelectedFlights,
      }),
    [tripDraft.timeline, conversation.planning_mode, hasSelectedFlights],
  );
  const quickPlanIntelligenceSummary =
    conversation.planning_mode === "quick" &&
    conversation.quick_plan_finalization?.accepted === true
      ? conversation.quick_plan_finalization.intelligence_summary
      : null;
  const dayArchitectureHighlights = useMemo(
    () => quickPlanIntelligenceSummary?.day_architecture_highlights ?? [],
    [quickPlanIntelligenceSummary],
  );
  const timelineSections = useMemo(
    () => buildTimelineSections(visibleTimeline, dayArchitectureHighlights),
    [visibleTimeline, dayArchitectureHighlights],
  );
  const leadTimelineHighlight = useMemo(
    () => findLeadTimelineHighlight(visibleTimeline),
    [visibleTimeline],
  );
  const isFinalized = tripDraft.status.confirmation_status === "finalized";
  const quickPlanBrochureEligible =
    conversation.quick_plan_finalization?.brochure_eligible === true;
  const canConfirmPlan =
    conversation.planning_mode === "quick" &&
    quickPlanBrochureEligible &&
    !isFinalized;

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-8 xl:px-8">
      <div className="space-y-12">
        <BoardHero
          destination={configuration.to_location}
          fromLocation={configuration.from_location}
          startDate={configuration.start_date}
          endDate={configuration.end_date}
          travelWindow={configuration.travel_window}
          tripLength={configuration.trip_length}
          adults={configuration.travelers.adults}
          childCount={configuration.travelers.children}
          summary={
            conversation.last_turn_summary ||
            "This is the first working draft of the trip. Keep refining it in chat and the board will tighten around the same plan."
          }
        />
        <PlanConfirmationPanel
          isFinalized={isFinalized}
          canConfirmPlan={canConfirmPlan}
          finalizedAt={tripDraft.status.finalized_at}
          onConfirm={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "finalize_quick_plan",
            })
          }
          onReopen={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "reopen_plan",
            })
          }
        />
        <QuickPlanExplainabilityPanel summary={quickPlanIntelligenceSummary} />

        <div className="space-y-6">
          {/* Itinerary header row */}
          <div className="flex items-end justify-between gap-4">
            <div>
              <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                Itinerary
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-foreground/55">
                {visibleTimeline.length > 0
                  ? `${timelineSections.length} day${timelineSections.length === 1 ? "" : "s"} · ${visibleTimeline.length} item${visibleTimeline.length === 1 ? "" : "s"} planned`
                  : "Keep refining in chat — the timeline fills in here automatically."}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <RouteChip from={configuration.from_location} to={configuration.to_location} />
            </div>
          </div>

          {/* Main two-column: timeline + sidebar */}
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(300px,340px)] xl:items-start">

            {/* Timeline column */}
            <section>
              {timelineSections.length > 0 ? (
                <div className="space-y-4">
                  {timelineSections.map((section, index) => (
                    <TimelineDaySection
                      key={section.id}
                      section={section}
                      dayIndex={index}
                      totalDays={timelineSections.length}
                    />
                  ))}
                </div>
              ) : (
                <ItineraryEmptyState />
              )}
            </section>

            {/* Sidebar column */}
            <div className="space-y-5 xl:sticky xl:top-6">
              {plannerConflicts.length ? (
                <InfoCard
                  icon={AlertTriangle}
                  title="Planning tensions"
                  subtitle="Worth resolving before this becomes brochure-ready"
                >
                  <LiveBoardConflictList conflicts={plannerConflicts} />
                </InfoCard>
              ) : null}
              <FlightCard
                flight={outboundFlight}
                returnFlight={returnFlight}
                mode={hasSelectedFlights ? "selected" : "candidate"}
              />
              {flightPlanningSummary ? (
                <InfoCard
                  icon={Plane}
                  title="Flight planning"
                  subtitle={
                    flightPlanning?.selection_status === "kept_open"
                      ? "Flights intentionally flexible"
                      : flightPlanning?.selection_status === "completed"
                        ? "Working flights selected"
                        : "Flight shape in progress"
                  }
                >
                  <p className="text-sm leading-7 text-foreground/66">
                    {flightPlanningSummary}
                  </p>
                  {flightPlanning?.arrival_day_impact_summary ? (
                    <p className="mt-2 text-sm leading-7 text-foreground/66">
                      {flightPlanning.arrival_day_impact_summary}
                    </p>
                  ) : null}
                  {flightPlanning?.departure_day_impact_summary ? (
                    <p className="mt-2 text-sm leading-7 text-foreground/66">
                      {flightPlanning.departure_day_impact_summary}
                    </p>
                  ) : null}
                </InfoCard>
              ) : null}
              <WeatherCard
                forecasts={weather}
                status={weatherPlanning?.results_status}
                summary={weatherPlanning?.workspace_summary}
                influenceNotes={weatherPlanning?.activity_influence_notes}
              />
              {budgetEstimate ? (
                <InfoCard
                  icon={Sparkles}
                  title="Estimated budget"
                  subtitle="Directional trip spend, separate from your stated budget"
                >
                  <BudgetEstimateSummary estimate={budgetEstimate} />
                </InfoCard>
              ) : null}
              <InfoCard
                icon={BedDouble}
                title="Stay details"
                subtitle={stay ? "Current stay direction" : "Hotel still open"}
              >
                {stay ? (
                  <HotelSummary
                    hotel={stay}
                    destination={configuration.to_location}
                    fallbackStayWindow={formatCompactDateRange(
                      configuration.start_date,
                      configuration.end_date,
                      configuration.travel_window,
                      configuration.trip_length,
                    )}
                  />
                ) : (
                  <EmptyPanel message="Hotel recommendations will settle here once Wandrix has enough destination and pacing context." />
                )}
              </InfoCard>

              <InfoCard
                icon={MapPinned}
                title="Highlights"
	                subtitle={
	                  leadActivityCandidate
	                    ? activityPlanning.schedule_summary || "Current standout recommendation"
	                    : leadTimelineHighlight
	                      ? "Pulled from the current draft itinerary"
	                      : "Destination highlights still forming"
	                }
              >
                {leadActivityCandidate ? (
                  <LiveBoardActivityHighlight
                    candidate={leadActivityCandidate}
                    workspaceSummary={activityPlanning.workspace_summary}
                    tripStyleSummary={tripStyleSummary}
                  />
                ) : leadTimelineHighlight ? (
                  <LiveBoardTimelineHighlight
                    item={leadTimelineHighlight}
                    tripStyleSummary={tripStyleSummary}
                  />
                ) : (
                  <EmptyPanel message="Local highlights will appear here as soon as activities are strong enough to elevate." />
                )}
              </InfoCard>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function toFlightDetail(
  option: AdvancedFlightOptionCard | null | undefined,
): FlightDetail | null {
  if (!option) {
    return null;
  }
  return {
    id: option.id,
    direction: option.direction,
    carrier: option.carrier,
    flight_number: option.flight_number ?? null,
    departure_airport: option.departure_airport,
    arrival_airport: option.arrival_airport,
    departure_time: option.departure_time ?? null,
    arrival_time: option.arrival_time ?? null,
    duration_text: option.duration_text ?? null,
    price_text: option.price_text ?? null,
    fare_amount: option.fare_amount ?? null,
    fare_currency: option.fare_currency ?? null,
    stop_count: option.stop_count ?? null,
    stop_details_available: option.stop_details_available ?? null,
    layover_summary: option.layover_summary ?? null,
    legs: option.legs ?? [],
    timing_quality: option.timing_quality ?? null,
    inventory_notice: option.inventory_notice ?? null,
    inventory_source: option.inventory_source ?? null,
    notes: [option.summary, ...option.tradeoffs].filter(Boolean),
  };
}

function buildVisibleTimeline(
  timeline: TimelineItem[],
  {
    showQuickPlanLogistics,
    showProviderFlights,
  }: {
    showQuickPlanLogistics: boolean;
    showProviderFlights: boolean;
}) {
  return timeline
    .filter(
      (item) =>
        showQuickPlanLogistics ||
        !(item.source_module === "hotels" && item.type === "hotel"),
    )
    .filter((item) => !(item.source_module === "weather" || item.type === "weather"))
    .filter(
      (item) =>
        showQuickPlanLogistics ||
        showProviderFlights ||
        !(item.source_module === "flights" && item.type === "flight"),
    )
    .map(normalizeTimelineItemForBoard);
}

function normalizeTimelineItemForBoard(item: TimelineItem): TimelineItem {
  const details = sanitizeTimelineDetails(item.details);
  if (item.type === "flight" && item.source_module !== "flights") {
    return {
      ...item,
      type: "transfer",
      details:
        details.length > 0
          ? details
          : ["Flight option still needs selection before exact timings are final."],
    };
  }

  return {
    ...item,
    details,
  };
}

function findLeadTimelineHighlight(timeline: TimelineItem[]) {
  return (
    timeline.find((item) => item.type === "event" && Boolean(item.start_at)) ??
    timeline.find((item) => item.type === "activity") ??
    timeline.find((item) => item.type === "meal") ??
    null
  );
}

function BudgetEstimateSummary({ estimate }: { estimate: TripBudgetEstimate }) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[color:var(--accent)]/16 bg-[color:color-mix(in_srgb,var(--accent)_7%,var(--background))] px-4 py-4">
        <p className="font-label text-[10px] font-bold uppercase tracking-[0.16em] text-foreground/45">
          Estimated total
        </p>
        <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
          {formatBudgetEstimateRange(
            estimate.total_low_amount,
            estimate.total_high_amount,
            estimate.currency,
          )}
        </p>
      </div>
      <div className="grid gap-2">
        {estimate.categories.map((category) => (
          <div
            key={category.category}
            className="flex items-center justify-between gap-3 rounded-lg border border-shell-border/70 bg-background px-3 py-2.5"
          >
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">{category.label}</p>
              <p className="mt-0.5 text-[11px] text-foreground/46">
                {formatBudgetEstimateSource(category.source)}
              </p>
            </div>
            <p className="shrink-0 text-sm font-semibold text-foreground/72">
              {formatBudgetEstimateRange(
                category.low_amount,
                category.high_amount,
                category.currency,
              )}
            </p>
          </div>
        ))}
      </div>
      <p className="text-[11px] leading-5 text-foreground/48">{estimate.caveat}</p>
    </div>
  );
}

function PlanConfirmationPanel({
  isFinalized,
  canConfirmPlan,
  finalizedAt,
  onConfirm,
  onReopen,
}: {
  isFinalized: boolean;
  canConfirmPlan: boolean;
  finalizedAt: string | null;
  onConfirm: () => void;
  onReopen: () => void;
}) {
  if (!isFinalized && !canConfirmPlan) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-[color:var(--accent)]/16 bg-[color:color-mix(in_srgb,var(--accent)_7%,var(--background))] shadow-[0_1px_8px_rgba(0,0,0,0.03)]">
      <div className="flex flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[color:var(--accent)]/10 text-[color:var(--accent)]">
            <CheckCircle2 className="h-4.5 w-4.5" />
          </div>
          <div className="min-w-0 space-y-1">
          <p className="text-sm font-semibold text-foreground">
            {isFinalized ? "Trip plan finalized" : "Ready to save this quick plan?"}
          </p>
          <p className="text-sm leading-6 text-foreground/62">
            {isFinalized
              ? `This version is saved as the brochure-ready trip${finalizedAt ? ` since ${formatBoardDate(finalizedAt)}` : ""}. Reopen planning here in chat if you want to make changes.`
              : "Confirming this will lock the current draft, save the brochure-ready version, and open the saved trip view for a calmer review."}
          </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {isFinalized ? (
            <Button type="button" variant="outline" onClick={onReopen}>
              Reopen planning
            </Button>
          ) : (
            <Dialog>
              <DialogTrigger asChild>
                <Button
                  type="button"
                  className="bg-[color:var(--accent)] text-white hover:bg-[color:var(--accent)]/90"
                >
                  Confirm and view
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Save this quick plan?</DialogTitle>
                  <DialogDescription>
                    This will finalize the current trip plan, generate the brochure-ready version, and open the saved trip view. You can return to this chat history and reopen planning here later.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button type="button" variant="outline">
                      Keep editing
                    </Button>
                  </DialogClose>
                  <DialogClose asChild>
                    <Button type="button" onClick={onConfirm}>
                      Confirm and save
                    </Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>
    </section>
  );
}

function QuickPlanExplainabilityPanel({
  summary,
}: {
  summary: QuickPlanIntelligenceSummary | null | undefined;
}) {
  if (!summary) {
    return null;
  }

  const planFitChips = [
    ...(summary.plan_fit?.user_intent ?? []),
    ...(summary.plan_fit?.pacing_rules ?? []).slice(0, 2),
  ].slice(0, 5);
  const acceptedModules = summary.accepted_module_scope ?? [];
  const excludedModules = summary.excluded_modules ?? [];
  const dayHighlights = summary.day_architecture_highlights ?? [];
  const providerNotes = summary.provider_confidence_notes ?? [];
  const assumptionNotes = summary.assumption_notes ?? [];
  const timingConfidence = summary.timing_confidence;
  const reviewOutcome = summary.review_outcome;

  return (
    <section className="overflow-hidden rounded-2xl border border-[color:var(--accent)]/14 bg-[color:color-mix(in_srgb,var(--accent)_5%,var(--background))] shadow-[0_1px_8px_rgba(0,0,0,0.03)]">
      <div className="grid gap-0 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="border-b border-[color:var(--accent)]/10 px-5 py-5 lg:border-b-0 lg:border-r">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[color:var(--accent)]/10 text-[color:var(--accent)]">
              <Sparkles className="h-4.5 w-4.5" />
            </div>
            <div>
              <p className="font-label text-[10px] font-bold uppercase tracking-[0.18em] text-[color:var(--accent)]/75">
                Why this plan works
              </p>
              <p className="mt-2 text-sm font-semibold leading-6 text-foreground">
                {summary.plan_rationale ||
                  "This Quick Plan passed private completeness and quality review before it reached the board."}
              </p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {planFitChips.map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-[color:var(--accent)]/14 bg-background px-3 py-1 text-[11px] font-semibold text-foreground/62"
              >
                {chip}
              </span>
            ))}
            {acceptedModules.map((module) => (
              <span
                key={module}
                className="rounded-full bg-[color:var(--accent)] px-3 py-1 text-[11px] font-bold text-white"
              >
                {formatModuleLabel(module)}
              </span>
            ))}
          </div>
        </div>

        <div className="grid gap-3 px-5 py-5 md:grid-cols-2">
          <QuickPlanInsightBlock
            title="Logistics confidence"
            rows={[
              ...providerNotes.slice(0, 3),
              formatTimingConfidence(timingConfidence),
            ].filter(Boolean)}
          />
          <QuickPlanInsightBlock
            title="Assumptions"
            rows={[
              ...assumptionNotes.slice(0, 3),
              ...excludedModules
                .slice(0, 3)
                .map((item) => `${formatModuleLabel(item.module)}: ${item.reason}`),
            ]}
            emptyText="No major assumptions are exposed for this accepted plan."
          />
          <QuickPlanInsightBlock
            title="Day architecture"
            rows={dayHighlights
              .slice(0, 3)
              .map((day) =>
                [day.day_label, day.theme, day.geography_focus]
                  .filter(Boolean)
                  .join(" · "),
              )}
            emptyText="Day themes are not available on this older draft."
          />
          <QuickPlanInsightBlock
            title="Review outcome"
            rows={[
              `Completeness: ${formatReviewStatus(reviewOutcome?.completeness_status)}`,
              `Quality: ${formatReviewStatus(reviewOutcome?.quality_status)}`,
            ]}
          />
        </div>
      </div>
    </section>
  );
}

function QuickPlanInsightBlock({
  title,
  rows,
  emptyText = "No notes available.",
}: {
  title: string;
  rows: string[];
  emptyText?: string;
}) {
  const visibleRows = rows.filter(Boolean);
  return (
    <div className="rounded-xl border border-shell-border/70 bg-background px-4 py-3.5">
      <p className="font-label text-[10px] font-bold uppercase tracking-[0.16em] text-foreground/42">
        {title}
      </p>
      <div className="mt-2 space-y-1.5">
        {(visibleRows.length ? visibleRows : [emptyText]).map((row) => (
          <p key={row} className="text-xs leading-5 text-foreground/60">
            {row}
          </p>
        ))}
      </div>
    </div>
  );
}

function BoardHero({
  destination,
  fromLocation,
  startDate,
  endDate,
  travelWindow,
  tripLength,
  adults,
  childCount,
  summary,
}: {
  destination: string | null;
  fromLocation: string | null;
  startDate: string | null;
  endDate: string | null;
  travelWindow: string | null;
  tripLength: string | null;
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

        <div className="flex flex-col justify-between gap-6 px-6 py-6 md:px-7 md:py-7">
          <div>
            <p className="font-label text-[10px] uppercase tracking-[0.2em] text-foreground/48">
              Upcoming trip - {formatTripLength(startDate, endDate, tripLength)}
            </p>
            <h2 className="mt-4 text-[2rem] font-semibold tracking-tight text-foreground md:text-[2.35rem]">
              {destination || "Your next destination"}
            </h2>
          </div>

          <div className="space-y-5">
            <div className="rounded-xl border border-border/60 bg-background px-5 py-5">
              <div className="flex items-start gap-4">
                <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_12%,white)] text-[color:var(--accent)]">
                  <MapPinned className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/44">
                    Route
                  </p>
                  <p className="mt-2.5 text-base font-semibold leading-tight text-foreground">
                    {formatRouteSummary(fromLocation, destination)}
                  </p>
                  <p className="mt-3 text-sm leading-relaxed text-foreground/60">
                    {summary}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <HeroInlineDetail
                icon={CalendarRange}
                label="Travel window"
	                value={formatCompactDateRange(
	                  startDate,
	                  endDate,
	                  travelWindow,
	                  tripLength,
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
    <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-background px-4 py-3.5 text-foreground">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] text-[color:var(--accent)]">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/44">
          {label}
        </p>
        <p className="mt-1.5 text-sm font-semibold leading-5 text-foreground">
          {value}
        </p>
      </div>
    </div>
  );
}

function RouteChip({
  from,
  to,
}: {
  from: string | null;
  to: string | null;
}) {
  if (!from && !to) return null;
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-[color:var(--accent)]/20 bg-[color:var(--accent)]/6 px-3.5 py-1.5">
      {from ? (
        <span className="text-xs font-semibold text-[color:var(--accent)]">{from}</span>
      ) : null}
      {from && to ? (
        <ArrowRight className="h-3 w-3 shrink-0 text-[color:var(--accent)]/60" />
      ) : null}
      {to ? (
        <span className="text-xs font-semibold text-[color:var(--accent)]">{to}</span>
      ) : null}
    </div>
  );
}

function ItineraryEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[color:var(--planner-board-border)] bg-[color:var(--planner-board-soft)] px-8 py-14 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[color:var(--accent)]/10">
        <Compass className="h-7 w-7 text-[color:var(--accent)]" />
      </div>
      <p className="mt-5 text-base font-semibold text-foreground">No itinerary yet</p>
      <p className="mt-2 max-w-xs text-sm leading-relaxed text-foreground/55">
        Wandrix hasn&apos;t saved a full itinerary yet. Keep pushing the trip forward in chat and the timeline will fill in automatically.
      </p>
    </div>
  );
}

function TimelineDaySection({
  section,
  dayIndex,
  totalDays,
}: {
  section: {
    id: string;
    dayLabel: string;
    summary: string;
    items: TimelineItem[];
  };
  dayIndex: number;
  totalDays: number;
}) {
  const isFirst = dayIndex === 0;
  const isLast = dayIndex === totalDays - 1;

  return (
    <article className="overflow-hidden rounded-2xl border border-[color:var(--planner-board-border)] bg-white shadow-[0_1px_4px_rgba(0,0,0,0.04)]">
      {/* Day header */}
      <div
        className="flex items-center gap-4 px-5 py-4"
        style={{
          background: isFirst
            ? "linear-gradient(135deg, color-mix(in srgb, var(--accent) 12%, white), color-mix(in srgb, var(--accent) 5%, white))"
            : "color-mix(in srgb, var(--planner-board-soft) 60%, white)",
        }}
      >
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold"
          style={
            isFirst
              ? { background: "var(--accent)", color: "white" }
              : {
                  background: "color-mix(in srgb, var(--accent) 12%, white)",
                  color: "var(--accent)",
                }
          }
        >
          {dayIndex + 1}
        </div>
        <div className="min-w-0 flex-1">
          <p
            className="text-sm font-bold tracking-tight"
            style={{ color: isFirst ? "var(--accent)" : "var(--planner-board-text)" }}
          >
            {section.dayLabel}
          </p>
          <p className="mt-0.5 truncate text-xs text-foreground/55">
            {section.summary}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {isFirst && (
            <span className="rounded-full bg-[color:var(--accent)] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-white">
              Start
            </span>
          )}
          {isLast && totalDays > 1 && (
            <span className="rounded-full bg-[color:var(--planner-board-accent-soft)] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-[color:var(--planner-board-accent-text)]">
              Final day
            </span>
          )}
          <span className="text-xs text-foreground/40">
            {section.items.length} item{section.items.length === 1 ? "" : "s"}
          </span>
        </div>
      </div>

      {/* Events list */}
      <div className="divide-y divide-[color:var(--planner-board-border)]/60">
        {section.items.map((item, itemIndex) => (
          <TimelineEventRow
            key={item.id}
            item={item}
            itemIndex={itemIndex}
            dayIndex={dayIndex}
            isLastInDay={itemIndex === section.items.length - 1}
          />
        ))}
      </div>
    </article>
  );
}

function TimelineEventRow({
  item,
  itemIndex,
  dayIndex,
}: {
  item: TimelineItem;
  itemIndex: number;
  dayIndex: number;
  isLastInDay: boolean;
}) {
  const { bg, text, label } = getItemTypeStyle(item.type);
  const details = sanitizeTimelineDetails(item.details);
  const displayTime = getTimelineDisplayTime(item, itemIndex, dayIndex);
  const timingChip = formatTimelineTimingChip(item);
  const timingNote =
    item.timing_source === "planner_estimate" && item.timing_note
      ? item.timing_note
      : null;

  return (
    <div className="group flex items-start gap-0 transition-colors hover:bg-[color:var(--planner-board-soft)]/60">
      {/* Time column */}
      <div className="flex w-20 shrink-0 flex-col items-end px-4 py-4 pt-[1.125rem]">
        {displayTime.start ? (
          <>
            <span className="text-xs font-bold tabular-nums text-[color:var(--accent)]">
              {displayTime.start}
            </span>
            {displayTime.end ? (
              <span className="mt-0.5 text-[10px] tabular-nums text-foreground/40">
                {displayTime.end}
              </span>
            ) : null}
          </>
        ) : (
          <span className="flex items-center gap-1 text-[10px] text-foreground/35">
            <Clock className="h-2.5 w-2.5" />
            Needs timing
          </span>
        )}
      </div>

      {/* Connector */}
      <div className="flex shrink-0 flex-col items-center pt-[1.1rem]">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{ background: bg }}
        >
          <TimelineItemIcon itemType={item.type} color={text} />
        </div>
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1 px-4 py-4">
        <div className="flex items-start gap-2">
          <p className="flex-1 text-sm font-semibold leading-snug text-[color:var(--planner-board-text)]">
            {item.title}
          </p>
          <span
            className="mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.1em]"
            style={{ background: bg, color: text }}
          >
            {label}
          </span>
          {timingChip ? (
            <span className="mt-0.5 shrink-0 rounded-full bg-[color:var(--planner-board-soft)] px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-foreground/45">
              {timingChip}
            </span>
          ) : null}
        </div>

        {item.type === "event" && item.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={item.image_url}
            alt={item.title}
            className="mt-3 h-24 w-full max-w-[13rem] rounded-lg object-cover"
          />
        ) : null}

        {item.location_label ? (
          <div className="mt-1.5 flex items-center gap-1 text-xs text-foreground/50">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="truncate">
              {item.venue_name && item.type === "event"
                ? `${item.venue_name} · ${item.location_label}`
                : item.location_label}
            </span>
          </div>
        ) : null}

        {details[0] ? (
          <p className="mt-1.5 text-xs leading-relaxed text-foreground/55">
            {details[0]}
          </p>
        ) : null}

        {timingNote ? (
          <p className="mt-1.5 text-[11px] leading-relaxed text-foreground/42">
            {timingNote}
          </p>
        ) : null}

        {(item.status_text || item.price_text || item.availability_text) ? (
          <div className="mt-2 flex flex-wrap gap-2">
            {[item.status_text, item.price_text, item.availability_text]
              .filter(Boolean)
              .map((detail) => (
                <span
                  key={detail}
                  className="rounded-full bg-[color:var(--planner-board-soft)] px-2 py-0.5 text-[10px] font-medium text-foreground/60"
                >
                  {detail}
                </span>
              ))}
          </div>
        ) : null}

        {details.length > 1 ? (
          <ul className="mt-2 space-y-1">
            {details.slice(1, 3).map((detail) => (
              <li
                key={detail}
                className="flex items-start gap-1.5 text-xs leading-relaxed text-foreground/45"
              >
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-foreground/25" />
                <span>{detail}</span>
              </li>
            ))}
          </ul>
        ) : null}

        {item.type === "event" && item.source_url ? (
          <a
            href={item.source_url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[color:var(--accent)] hover:underline"
          >
            {item.source_label ? `View on ${item.source_label}` : "View event"}
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </div>
    </div>
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
    <section className="rounded-xl border border-shell-border/70 bg-[color:color-mix(in_srgb,var(--background)_82%,var(--panel))] px-6 py-6">
      <div className="flex items-center gap-2 text-[color:var(--accent)]">
        <Icon className="h-4 w-4" />
        <p className="font-label text-[11px] font-bold uppercase tracking-[0.16em]">
          {title}
        </p>
      </div>
      <p className="mt-3.5 text-sm leading-relaxed text-foreground/56">{subtitle}</p>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function LiveBoardConflictList({
  conflicts,
}: {
  conflicts: PlannerConflictRecord[];
}) {
  return (
    <div className="space-y-3">
      {conflicts.slice(0, 3).map((conflict) => (
        <div
          key={conflict.id}
          className="rounded-lg bg-background px-4 py-3 text-sm leading-relaxed"
        >
          <p className="font-semibold text-foreground/82">{conflict.summary}</p>
          <p className="mt-1 text-xs leading-5 text-foreground/58">
            {conflict.recommended_repair || conflict.suggested_repair}
          </p>
          {conflict.why_it_matters ? (
            <p className="mt-1 text-xs leading-5 text-foreground/48">
              {conflict.why_it_matters}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="rounded-xl bg-background px-5 py-4 text-sm leading-relaxed text-foreground/66">
      {message}
    </div>
  );
}

function LiveBoardActivityHighlight({
  candidate,
  workspaceSummary,
  tripStyleSummary,
}: {
  candidate: AdvancedActivityCandidateCard;
  workspaceSummary?: string | null;
  tripStyleSummary?: string | null;
}) {
  const placementLabel = candidate.start_at
    ? new Date(candidate.start_at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })
    : candidate.time_label || "Needs timing";

  return (
    <div className="overflow-hidden rounded-xl bg-background">
      <div className="border-b border-shell-border/70 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_16%,white),color-mix(in_srgb,var(--accent2)_10%,white))] px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-lg font-semibold text-foreground">{candidate.title}</p>
            <p className="mt-1 text-sm text-foreground/58">
              {[candidate.kind === "event" ? "Timed moment" : "Planned stop", placementLabel]
                .filter(Boolean)
                .join(" • ")}
            </p>
          </div>
          <span className="rounded-md border border-shell-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground/62">
            {candidate.disposition === "essential" ? "Leading pick" : "In the mix"}
          </span>
        </div>
      </div>
      <div className="grid gap-3 px-4 py-4">
        {candidate.location_label ? (
          <div className="flex items-center gap-2 text-sm text-foreground/58">
            <MapPin className="h-4 w-4 shrink-0 text-[color:var(--accent)]" />
            <span>{candidate.location_label}</span>
          </div>
        ) : null}
        {candidate.summary ? (
          <p className="text-sm leading-7 text-foreground/66">{candidate.summary}</p>
        ) : null}
        {workspaceSummary ? (
          <p className="rounded-lg border border-shell-border/70 bg-panel px-3 py-3 text-sm leading-6 text-foreground/60">
            {workspaceSummary}
          </p>
        ) : null}
        {tripStyleSummary ? (
          <p className="rounded-lg border border-shell-border/70 bg-panel px-3 py-3 text-sm leading-6 text-foreground/60">
            {tripStyleSummary}
          </p>
        ) : null}
        {(candidate.price_text || candidate.availability_text || candidate.status_text) ? (
          <div className="flex flex-wrap gap-2">
            {[candidate.status_text, candidate.price_text, candidate.availability_text]
              .filter(Boolean)
              .map((detail) => (
                <span
                  key={detail}
                  className="rounded-full bg-[color:var(--planner-board-soft)] px-2 py-0.5 text-[10px] font-medium text-foreground/60"
                >
                  {detail}
                </span>
              ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function LiveBoardTimelineHighlight({
  item,
  tripStyleSummary,
}: {
  item: TimelineItem;
  tripStyleSummary?: string | null;
}) {
  const details = sanitizeTimelineDetails(item.details);
  const placementLabel =
    item.start_at ? formatBoardDate(item.start_at) : item.day_label || "Needs timing";

  return (
    <div className="overflow-hidden rounded-xl bg-background">
      <div className="border-b border-shell-border/70 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_16%,white),color-mix(in_srgb,var(--accent2)_10%,white))] px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-lg font-semibold text-foreground">{item.title}</p>
            <p className="mt-1 text-sm text-foreground/58">
              {[getItemTypeStyle(item.type).label, placementLabel].filter(Boolean).join(" • ")}
            </p>
          </div>
          <span className="rounded-md border border-shell-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground/62">
            Draft pick
          </span>
        </div>
      </div>
      <div className="grid gap-3 px-4 py-4">
        {item.location_label ? (
          <div className="flex items-center gap-2 text-sm text-foreground/58">
            <MapPin className="h-4 w-4 shrink-0 text-[color:var(--accent)]" />
            <span>{item.location_label}</span>
          </div>
        ) : null}
        {item.summary || details[0] ? (
          <p className="text-sm leading-7 text-foreground/66">{item.summary || details[0]}</p>
        ) : null}
        {tripStyleSummary ? (
          <p className="rounded-lg border border-shell-border/70 bg-panel px-3 py-3 text-sm leading-6 text-foreground/60">
            {tripStyleSummary}
          </p>
        ) : null}
      </div>
    </div>
  );
}

type TimelineItemType = TimelineItem["type"];

function getItemTypeStyle(type: TimelineItemType): {
  bg: string;
  text: string;
  label: string;
} {
  switch (type) {
    case "flight":
      return { bg: "rgba(29,78,216,0.1)", text: "#1d4ed8", label: "Flight" };
    case "hotel":
      return { bg: "rgba(5,150,105,0.1)", text: "#059669", label: "Stay" };
    case "meal":
      return { bg: "rgba(217,119,6,0.1)", text: "#d97706", label: "Meal" };
    case "weather":
      return { bg: "rgba(14,165,233,0.1)", text: "#0ea5e9", label: "Weather" };
    case "transfer":
      return { bg: "rgba(99,102,241,0.1)", text: "#6366f1", label: "Travel" };
    case "activity":
      return { bg: "rgba(236,72,153,0.1)", text: "#ec4899", label: "Activity" };
    case "note":
      return { bg: "rgba(100,116,139,0.1)", text: "#64748b", label: "Note" };
    default:
      return { bg: "rgba(100,116,139,0.1)", text: "#64748b", label: "Event" };
  }
}

function TimelineItemIcon({
  itemType,
  color,
}: {
  itemType: TimelineItemType;
  color?: string;
}) {
  const Icon =
    itemType === "flight"
      ? Plane
      : itemType === "hotel"
        ? BedDouble
        : itemType === "meal"
          ? UtensilsCrossed
          : itemType === "weather"
            ? CloudSun
            : itemType === "transfer"
              ? Car
              : itemType === "activity"
                ? MapPinned
                : Sparkles;

  return <Icon className="h-4 w-4" style={{ color: color ?? "var(--accent)" }} />;
}

function sanitizeTimelineDetails(details: string[]) {
  return details
    .filter((detail) => !isProviderSourceDetail(detail))
    .map(cleanTimelineDetail)
    .filter(Boolean);
}

function isProviderSourceDetail(detail: string) {
  const normalized = detail.trim().toLowerCase();
  return (
    normalized.startsWith("tripadvisor:")
    || normalized.startsWith("source:")
    || normalized.includes("rapidapi")
    || normalized.includes("cached hotel search result")
    || normalized.includes("cached inventory snapshot")
  );
}

function cleanTimelineDetail(detail: string) {
  const trimmed = detail.trim();
  const prefixes = ["Cached fare snapshot:", "Live fare snapshot:"];
  for (const prefix of prefixes) {
    if (trimmed.startsWith(prefix)) {
      return `Estimated fare: ${trimmed.slice(prefix.length).trim()}.`;
    }
  }
  return trimmed;
}

function shouldShowTimelineEndTime(item: TimelineItem) {
  if (!item.start_at || !item.end_at || item.type === "hotel") {
    return false;
  }

  const start = new Date(item.start_at);
  const end = new Date(item.end_at);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return true;
  }

  return start.toDateString() === end.toDateString();
}

function getTimelineDisplayTime(
  item: TimelineItem,
  itemIndex: number,
  dayIndex: number,
) {
  if (item.start_at) {
    return {
      start: formatTime(item.start_at),
      end:
        item.end_at && shouldShowTimelineEndTime(item)
          ? formatTime(item.end_at)
          : null,
    };
  }

  if (item.timing_source !== "planner_estimate") {
    return { start: null, end: null };
  }

  const fallback = getFallbackTimelineClock(item, itemIndex, dayIndex);
  return fallback
    ? {
        start: fallback.start,
        end: fallback.end,
      }
    : { start: null, end: null };
}

function getFallbackTimelineClock(
  item: TimelineItem,
  itemIndex: number,
  dayIndex: number,
) {
  const slots =
    item.type === "meal"
      ? [
          ["08:30", "09:30"],
          ["12:30", "13:30"],
          ["19:30", "21:00"],
        ]
      : item.type === "transfer"
        ? [
            ["09:15", "09:45"],
            ["13:45", "14:15"],
            ["18:00", "18:30"],
            ["21:00", "21:25"],
          ]
        : item.type === "hotel"
          ? [["15:30", "16:15"]]
          : item.type === "event"
            ? [
                ["09:30", "12:30"],
                ["14:00", "17:00"],
                ["19:00", "21:00"],
              ]
            : item.type === "note"
              ? [
                  ["09:00", "09:30"],
                  ["16:30", "17:00"],
                  ["20:30", "21:00"],
                ]
              : dayIndex === 0
                ? [
                    ["17:00", "19:00"],
                    ["19:30", "21:00"],
                  ]
                : [
                    ["09:30", "12:30"],
                    ["13:30", "16:00"],
                    ["16:30", "18:30"],
                    ["19:30", "21:00"],
                  ];

  return {
    start: slots[Math.min(itemIndex, slots.length - 1)][0],
    end: slots[Math.min(itemIndex, slots.length - 1)][1],
  };
}

function formatTimelineTimingChip(item: TimelineItem) {
  if (item.timing_source === "planner_estimate") {
    return "estimated";
  }
  if (item.timing_source === "user_confirmed") {
    return "confirmed";
  }
  return null;
}

function formatBudgetEstimateRange(
  lowAmount: number | null,
  highAmount: number | null,
  currency: string | null,
) {
  if (lowAmount === null || highAmount === null || !currency) {
    return "Not priced";
  }

  if (Math.round(lowAmount) === Math.round(highAmount)) {
    return formatBudgetEstimateAmount(lowAmount, currency);
  }

  return `${formatBudgetEstimateAmount(lowAmount, currency)} - ${formatBudgetEstimateAmount(
    highAmount,
    currency,
  )}`;
}

function formatBudgetEstimateAmount(amount: number, currency: string) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatBudgetEstimateSource(source: TripBudgetEstimate["categories"][number]["source"]) {
  if (source === "provider_price") {
    return "Provider price";
  }
  if (source === "planner_estimate") {
    return "Planner estimate";
  }
  return "Unavailable";
}

function formatModuleLabel(module: string) {
  if (module === "hotels") {
    return "Stays";
  }
  return module.charAt(0).toUpperCase() + module.slice(1);
}

function formatReviewStatus(status: string | null | undefined) {
  if (!status) {
    return "Not available";
  }
  return status.replace(/_/g, " ");
}

function formatTimingConfidence(
  timingConfidence: QuickPlanIntelligenceSummary["timing_confidence"] | undefined,
) {
  if (!timingConfidence) {
    return "";
  }
  const providerExactCount = timingConfidence.provider_exact_count ?? 0;
  const plannerEstimateCount = timingConfidence.planner_estimate_count ?? 0;
  if (providerExactCount && plannerEstimateCount) {
    return `${providerExactCount} provider-timed rows, ${plannerEstimateCount} planner-estimated rows.`;
  }
  if (providerExactCount) {
    return `${providerExactCount} rows use exact provider timing.`;
  }
  if (plannerEstimateCount) {
    return `${plannerEstimateCount} rows use planner-estimated timing.`;
  }
  return "";
}

function buildTimelineSections(
  timeline: TimelineItem[],
  dayArchitectureHighlights: NonNullable<
    QuickPlanIntelligenceSummary["day_architecture_highlights"]
  > = [],
) {
  const dayHighlightByLabel = new Map(
    dayArchitectureHighlights
      .filter((day) => day.day_label)
      .map((day) => [day.day_label as string, day]),
  );
  const orderedTimeline = [...timeline].sort(compareTimelineItems);
  const sections = new Map<
    string,
    {
      id: string;
      dayLabel: string;
      summary: string;
      items: TimelineItem[];
    }
  >();

  orderedTimeline.forEach((item, index) => {
    const dayLabel = item.day_label || `Day ${index + 1}`;
    const existingSection = sections.get(dayLabel);

    if (existingSection) {
      existingSection.items.push(item);
      return;
    }

    sections.set(dayLabel, {
      id: `${dayLabel}-${index}`,
      dayLabel,
      summary:
        dayHighlightByLabel.get(dayLabel)?.theme ||
        item.summary ||
        item.location_label ||
        item.title,
      items: [item],
    });
  });

  return Array.from(sections.values()).sort((first, second) =>
    compareDayLabels(first.dayLabel, second.dayLabel),
  );
}

function compareTimelineItems(first: TimelineItem, second: TimelineItem) {
  return (
    compareDayLabels(first.day_label, second.day_label)
    || compareTimelineTime(first.start_at, second.start_at)
    || first.title.localeCompare(second.title)
  );
}

function compareDayLabels(first: string | null, second: string | null) {
  return getDayLabelIndex(first) - getDayLabelIndex(second);
}

function getDayLabelIndex(dayLabel: string | null) {
  if (!dayLabel) {
    return 999;
  }

  const match = dayLabel.match(/\bday\s*(\d+)\b/i);
  if (!match) {
    return 999;
  }

  const parsed = Number(match[1]);
  return Number.isFinite(parsed) ? parsed : 999;
}

function compareTimelineTime(first: string | null, second: string | null) {
  return parseTimelineTime(first) - parseTimelineTime(second);
}

function parseTimelineTime(value: string | null) {
  if (!value) {
    return Number.POSITIVE_INFINITY;
  }

  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? Number.POSITIVE_INFINITY : parsed;
}

function formatTripLength(
  startDate: string | null,
  endDate: string | null,
  tripLength?: string | null,
) {
  if (!startDate || !endDate) {
    return tripLength || "open timing";
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

function getTripDayCount(startDate: string | null, endDate: string | null) {
  if (!startDate || !endDate) {
    return 3;
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return 3;
  }

  return Math.max(
    1,
    Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1,
  );
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
    return [travelWindow, tripLength].filter(Boolean).join(" - ") || "Timing open";
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
    return "Timing open";
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
    return value || "Needs timing";
  }

  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function formatBoardDate(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(parsed);
}
