"use client";

import { useMemo, useState } from "react";

import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { useChatSidebarCollapsedState } from "@/components/chat/use-chat-sidebar-collapsed-state";
import { TripBoardPreview } from "@/components/package/trip-board-preview";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";

type SandboxScenarioKey = "kyoto" | "barcelona" | "lisbon";

const SANDBOX_SCENARIOS: Array<{
  key: SandboxScenarioKey;
  label: string;
  description: string;
}> = [
  {
    key: "kyoto",
    label: "Kyoto detail-rich trip",
    description:
      "A fuller board with flights, hotel, weather, and activity highlights.",
  },
  {
    key: "barcelona",
    label: "Barcelona family trip",
    description:
      "A more relaxed family trip with softer activity structure and open hotel choice.",
  },
  {
    key: "lisbon",
    label: "Lisbon decision-heavy",
    description:
      "A scenario with missing fields so the selections tab has something to work with.",
  },
];

export function TripBoardSandbox() {
  const [activeScenario, setActiveScenario] = useState<SandboxScenarioKey>("kyoto");
  const { isSidebarCollapsed, setIsSidebarCollapsed } =
    useChatSidebarCollapsedState();

  const workspace = useMemo(
    () => buildSandboxWorkspace(activeScenario),
    [activeScenario],
  );
  const recentTrips = useMemo(() => buildSandboxTrips(workspace), [workspace]);
  const activeScenarioDetails = useMemo(
    () =>
      SANDBOX_SCENARIOS.find((scenario) => scenario.key === activeScenario) ??
      SANDBOX_SCENARIOS[0],
    [activeScenario],
  );

  return (
    <main className="h-[calc(100vh-4.75rem)] overflow-hidden bg-background">
      <section
        className={[
          "grid h-full min-h-0 bg-background",
          isSidebarCollapsed
            ? "xl:grid-cols-[72px_minmax(0,0.72fr)_minmax(0,1.28fr)]"
            : "xl:grid-cols-[264px_minmax(0,0.8fr)_minmax(0,1.2fr)]",
        ].join(" ")}
      >
        <ChatSidebar
          collapsed={isSidebarCollapsed}
          onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
          workspace={workspace}
          recentTrips={recentTrips}
        />

        <section className="min-h-0 border-r border-[color:var(--chat-rail-border)] bg-[color:var(--chat-pane-bg)]">
          <div className="flex h-full min-h-0 flex-col">
            <div className="border-b border-[color:var(--chat-rail-border)] px-6 py-4">
              <div className="flex flex-wrap gap-2">
                {SANDBOX_SCENARIOS.map((scenario) => (
                  <button
                    key={scenario.key}
                    type="button"
                    onClick={() => setActiveScenario(scenario.key)}
                    className={[
                      "rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                      activeScenario === scenario.key
                        ? "border-[color:var(--accent)] bg-background text-foreground"
                        : "border-transparent bg-[color:var(--chat-rail-control-bg)] text-foreground/68 hover:bg-background hover:text-foreground",
                    ].join(" ")}
                  >
                    {scenario.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="chat-workspace-scroll min-h-0 flex-1 overflow-y-auto px-6 py-6">
              <div className="mx-auto flex w-full max-w-[46rem] flex-col gap-5 pb-10">
                <div className="max-w-[31rem] rounded-[1rem] border border-border/70 bg-background/92 px-5 py-4 shadow-[var(--chat-shadow-soft)]">
                  <p className="text-sm leading-7 text-foreground/74">
                    I&apos;m shaping the right-side board for this trip. Focus on
                    whether the hero, itinerary cards, and supporting panels feel
                    calm and readable at this width.
                  </p>
                </div>

                <div className="ml-auto max-w-[28rem] rounded-[1.1rem] rounded-br-md border border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,var(--color-background))] px-5 py-4 text-sm leading-7 text-foreground shadow-[var(--chat-shadow-card)]">
                  This feels crowded. I want to understand the board in a more
                  realistic shell.
                </div>

                <div className="max-w-[31rem] rounded-[1rem] border border-border/70 bg-background/92 px-5 py-4 shadow-[var(--chat-shadow-soft)]">
                  <p className="text-sm leading-7 text-foreground/74">
                    The middle column is intentionally quieter now so the board
                    reads like the main artifact, not a cramped side widget.
                  </p>
                </div>

                <div className="rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-5 py-4">
                  <p className="text-sm font-medium text-foreground">
                    {activeScenarioDetails.label}
                  </p>
                  <p className="mt-2 text-sm leading-7 text-foreground/62">
                    {activeScenarioDetails.description}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="min-h-0 bg-shell">
          <TripBoardPreview
            workspace={workspace}
            isBootstrapping={false}
          />
        </section>
      </section>
    </main>
  );
}

function buildSandboxTrips(
  currentWorkspace: PlannerWorkspaceState,
): TripListItemResponse[] {
  return [
    {
      trip_id: currentWorkspace.trip.trip_id,
      browser_session_id: currentWorkspace.trip.browser_session_id,
      thread_id: currentWorkspace.trip.thread_id,
      title: currentWorkspace.trip.title,
      trip_status: currentWorkspace.trip.trip_status,
      thread_status: currentWorkspace.trip.thread_status,
      created_at: currentWorkspace.trip.created_at,
      updated_at: "2026-04-19T09:00:00Z",
      phase: currentWorkspace.tripDraft.status.phase,
      brochure_ready: currentWorkspace.tripDraft.status.brochure_ready,
      from_location: currentWorkspace.tripDraft.configuration.from_location,
      to_location: currentWorkspace.tripDraft.configuration.to_location,
      start_date: currentWorkspace.tripDraft.configuration.start_date,
      end_date: currentWorkspace.tripDraft.configuration.end_date,
      selected_modules: Object.entries(
        currentWorkspace.tripDraft.configuration.selected_modules,
      )
        .filter(([, enabled]) => enabled)
        .map(([key]) => key),
      timeline_item_count: currentWorkspace.tripDraft.timeline.length,
    },
    {
      trip_id: "preview-trip-rome",
      browser_session_id: currentWorkspace.trip.browser_session_id,
      thread_id: "preview-thread-rome",
      title: "Rome spring long weekend",
      trip_status: "collecting_requirements",
      thread_status: "ready",
      created_at: "2026-04-17T09:00:00Z",
      updated_at: "2026-04-17T13:00:00Z",
      phase: "planning",
      brochure_ready: false,
      from_location: "London",
      to_location: "Rome",
      start_date: "2026-05-14",
      end_date: "2026-05-18",
      selected_modules: ["flights", "activities", "hotels"],
      timeline_item_count: 5,
    },
    {
      trip_id: "preview-trip-tokyo",
      browser_session_id: currentWorkspace.trip.browser_session_id,
      thread_id: "preview-thread-tokyo",
      title: "Tokyo food sprint",
      trip_status: "collecting_requirements",
      thread_status: "ready",
      created_at: "2026-04-14T09:00:00Z",
      updated_at: "2026-04-15T11:00:00Z",
      phase: "collecting_requirements",
      brochure_ready: false,
      from_location: "Heathrow",
      to_location: "Tokyo",
      start_date: null,
      end_date: null,
      selected_modules: ["flights", "activities"],
      timeline_item_count: 0,
    },
  ];
}

function buildSandboxWorkspace(
  scenario: SandboxScenarioKey,
): PlannerWorkspaceState {
  const commonBrowserSession = {
    browser_session_id: "browser-session-preview",
    user_id: null,
    timezone: "Europe/London",
    locale: "en-GB",
    status: "active" as const,
    created_at: "2026-04-19T09:00:00Z",
  };

  switch (scenario) {
    case "barcelona":
      return {
        browserSession: commonBrowserSession,
        trip: {
          trip_id: "preview-trip-barcelona",
          browser_session_id: commonBrowserSession.browser_session_id,
          thread_id: "preview-thread-barcelona",
          title: "Barcelona family reset",
          trip_status: "collecting_requirements",
          thread_status: "ready",
          created_at: "2026-04-19T09:00:00Z",
        },
        tripDraft: {
          trip_id: "preview-trip-barcelona",
          thread_id: "preview-thread-barcelona",
          title: "Barcelona family reset",
          configuration: {
            from_location: "Manchester",
            to_location: "Barcelona",
            start_date: "2026-08-12",
            end_date: "2026-08-17",
            travelers: {
              adults: 2,
              children: 2,
            },
            budget_gbp: 2900,
            selected_modules: {
              flights: true,
              weather: true,
              activities: true,
              hotels: false,
            },
            activity_styles: ["family", "relaxed", "outdoors"],
          },
          timeline: [
            {
              id: "timeline-barcelona-1",
              type: "flight",
              title: "Arrive in Barcelona",
              day_label: "Day 1",
              start_at: "2026-08-12T09:20:00Z",
              end_at: "2026-08-12T12:45:00Z",
              location_label: "Manchester to Barcelona",
              summary: "Morning arrival with an easy transfer into the city.",
              details: ["Target a midday hotel bag drop before lunch nearby."],
              source_module: "flights",
              status: "confirmed",
            },
            {
              id: "timeline-barcelona-2",
              type: "activity",
              title: "Parc de la Ciutadella afternoon",
              day_label: "Day 1",
              start_at: "2026-08-12T14:30:00Z",
              end_at: "2026-08-12T17:00:00Z",
              location_label: "Ciutat Vella",
              summary: "A low-pressure first stop for a family-friendly afternoon.",
              details: ["Keep the first day light after travel."],
              source_module: "activities",
              status: "draft",
            },
            {
              id: "timeline-barcelona-3",
              type: "activity",
              title: "Beach and aquarium split day",
              day_label: "Day 2",
              start_at: "2026-08-13T10:00:00Z",
              end_at: "2026-08-13T16:00:00Z",
              location_label: "Barceloneta",
              summary:
                "Keep weather-sensitive outdoor time in the morning and indoor time later.",
              details: ["Good option if temperatures peak in the afternoon."],
              source_module: "weather",
              status: "draft",
            },
          ],
          module_outputs: {
            flights: [
              {
                id: "flight-barcelona-outbound",
                direction: "outbound",
                carrier: "Vueling",
                flight_number: "VY8741",
                departure_airport: "MAN",
                arrival_airport: "BCN",
                departure_time: "2026-08-12T09:20:00Z",
                arrival_time: "2026-08-12T12:45:00Z",
                duration_text: "2h 25m direct",
                notes: ["Morning departure keeps the first day usable."],
              },
            ],
            hotels: [],
            weather: [
              {
                id: "weather-barcelona-1",
                day_label: "12 Aug",
                summary: "Warm and bright",
                high_c: 28,
                low_c: 22,
                notes: ["Good arrival-day weather for a light outdoor plan."],
              },
              {
                id: "weather-barcelona-2",
                day_label: "13 Aug",
                summary: "Hot afternoon",
                high_c: 31,
                low_c: 23,
                notes: [
                  "Best to split the day between outdoor and indoor stops.",
                ],
              },
            ],
            activities: [
              {
                id: "activity-barcelona-1",
                title: "Parc de la Ciutadella stroll",
                category: "outdoors",
                day_label: "Day 1",
                time_label: "Afternoon",
                notes: ["Easy first activity after arrival."],
              },
              {
                id: "activity-barcelona-2",
                title: "Barcelona Aquarium",
                category: "family",
                day_label: "Day 2",
                time_label: "Late afternoon",
                notes: ["Useful indoor option if the day gets too hot."],
              },
            ],
          },
          status: {
            phase: "planning",
            missing_fields: ["hotels"],
            confirmed_fields: ["from_location", "to_location", "start_date", "end_date"],
            inferred_fields: ["activity_styles"],
            open_questions: ["Do you want me to keep the hotel area family-friendly and walkable?"],
            decision_cards: [],
            brochure_ready: false,
            last_updated_at: "2026-04-19T09:00:00Z",
          },
        },
      };
    case "lisbon":
      return {
        browserSession: commonBrowserSession,
        trip: {
          trip_id: "preview-trip-lisbon",
          browser_session_id: commonBrowserSession.browser_session_id,
          thread_id: "preview-thread-lisbon",
          title: "Lisbon spring long weekend",
          trip_status: "collecting_requirements",
          thread_status: "ready",
          created_at: "2026-04-19T09:00:00Z",
        },
        tripDraft: {
          trip_id: "preview-trip-lisbon",
          thread_id: "preview-thread-lisbon",
          title: "Lisbon spring long weekend",
          configuration: {
            from_location: null,
            to_location: "Lisbon",
            start_date: null,
            end_date: null,
            travelers: {
              adults: 2,
              children: 0,
            },
            budget_gbp: 2200,
            selected_modules: {
              flights: true,
              weather: true,
              activities: true,
              hotels: true,
            },
            activity_styles: ["food", "culture", "relaxed"],
          },
          timeline: [],
          module_outputs: {
            flights: [],
            hotels: [],
            weather: [],
            activities: [],
          },
          status: {
            phase: "collecting_requirements",
            missing_fields: ["from_location", "start_date", "end_date"],
            confirmed_fields: ["to_location", "budget_gbp", "activity_styles"],
            inferred_fields: [],
            open_questions: [
              "Where would you be traveling from?",
              "What rough dates or month should I shape this around?",
            ],
            decision_cards: [
              {
                title: "Keep Lisbon or compare alternatives",
                description:
                  "The brief already points toward a relaxed, food-forward city break, so a quick direction choice would sharpen the board faster.",
                options: ["Keep Lisbon", "Compare Porto", "Compare Valencia"],
              },
              {
                title: "Set the timing",
                description:
                  "Even a rough month or weekend helps flights, weather, and hotel pacing feel more concrete.",
                options: ["Late April", "May bank holiday", "Keep the month flexible"],
              },
            ],
            brochure_ready: false,
            last_updated_at: "2026-04-19T09:00:00Z",
          },
        },
      };
    case "kyoto":
    default:
      return {
        browserSession: commonBrowserSession,
        trip: {
          trip_id: "preview-trip-kyoto",
          browser_session_id: commonBrowserSession.browser_session_id,
          thread_id: "preview-thread-kyoto",
          title: "Kyoto autumn food week",
          trip_status: "collecting_requirements",
          thread_status: "ready",
          created_at: "2026-04-19T09:00:00Z",
        },
        tripDraft: {
          trip_id: "preview-trip-kyoto",
          thread_id: "preview-thread-kyoto",
          title: "Kyoto autumn food week",
          configuration: {
            from_location: "Heathrow",
            to_location: "Kyoto",
            start_date: "2026-10-03",
            end_date: "2026-10-09",
            travelers: {
              adults: 2,
              children: 0,
            },
            budget_gbp: 4800,
            selected_modules: {
              flights: true,
              weather: true,
              activities: true,
              hotels: true,
            },
            activity_styles: ["food", "culture", "relaxed"],
          },
          timeline: [
            {
              id: "timeline-kyoto-1",
              type: "flight",
              title: "Overnight flight to Osaka",
              day_label: "Day 1",
              start_at: "2026-10-03T11:10:00Z",
              end_at: "2026-10-04T06:40:00Z",
              location_label: "Heathrow to Kansai",
              summary:
                "Direct overnight departure so the trip lands early enough to settle in.",
              details: ["Aim for a quiet first evening after check-in."],
              source_module: "flights",
              status: "confirmed",
            },
            {
              id: "timeline-kyoto-2",
              type: "hotel",
              title: "Hotel check-in near Gion",
              day_label: "Day 1",
              start_at: "2026-10-04T09:30:00Z",
              end_at: "2026-10-04T10:30:00Z",
              location_label: "Gion",
              summary:
                "Use a central east-Kyoto base to keep walks short in the first two days.",
              details: ["Early luggage drop is preferred."],
              source_module: "hotels",
              status: "draft",
            },
            {
              id: "timeline-kyoto-3",
              type: "activity",
              title: "Nishiki Market lunch walk",
              day_label: "Day 1",
              start_at: "2026-10-04T12:30:00Z",
              end_at: "2026-10-04T15:00:00Z",
              location_label: "Downtown Kyoto",
              summary:
                "A soft landing into the trip with food and low-pressure wandering.",
              details: ["Use this as the first mood-setting stop."],
              source_module: "activities",
              status: "confirmed",
            },
            {
              id: "timeline-kyoto-4",
              type: "activity",
              title: "Arashiyama morning",
              day_label: "Day 2",
              start_at: "2026-10-05T08:30:00Z",
              end_at: "2026-10-05T12:00:00Z",
              location_label: "Arashiyama",
              summary:
                "Front-load the bamboo grove and riverside walk before crowds build.",
              details: ["Keep the afternoon lighter with tea or shopping."],
              source_module: "activities",
              status: "draft",
            },
            {
              id: "timeline-kyoto-5",
              type: "meal",
              title: "Kaiseki dinner reservation",
              day_label: "Day 2",
              start_at: "2026-10-05T18:30:00Z",
              end_at: "2026-10-05T21:00:00Z",
              location_label: "Gion",
              summary:
                "A single anchor dinner to give the trip one polished evening.",
              details: ["Good fit for a food-forward but calm trip tone."],
              source_module: "activities",
              status: "draft",
            },
            {
              id: "timeline-kyoto-6",
              type: "weather",
              title: "Watch for light rain",
              day_label: "Day 3",
              start_at: "2026-10-06T09:00:00Z",
              end_at: "2026-10-06T17:00:00Z",
              location_label: "Kyoto",
              summary:
                "Shift the heaviest walking to the earlier days and keep museum options ready.",
              details: ["Use indoor stops if showers build after lunch."],
              source_module: "weather",
              status: "draft",
            },
            {
              id: "timeline-kyoto-7",
              type: "activity",
              title: "Tea house and craft shopping",
              day_label: "Day 3",
              start_at: "2026-10-06T11:00:00Z",
              end_at: "2026-10-06T16:00:00Z",
              location_label: "Higashiyama",
              summary:
                "A slower-paced day that still feels distinctly Kyoto.",
              details: ["Good weather backup structure."],
              source_module: "activities",
              status: "draft",
            },
            {
              id: "timeline-kyoto-8",
              type: "flight",
              title: "Return via Osaka",
              day_label: "Day 6",
              start_at: "2026-10-09T09:25:00Z",
              end_at: "2026-10-09T18:10:00Z",
              location_label: "Kansai to Heathrow",
              summary:
                "Mid-morning airport transfer keeps the final morning calm.",
              details: ["Leave room for a short breakfast stop before departure."],
              source_module: "flights",
              status: "confirmed",
            },
          ],
          module_outputs: {
            flights: [
              {
                id: "flight-kyoto-outbound",
                direction: "outbound",
                carrier: "Japan Airlines",
                flight_number: "JL44",
                departure_airport: "LHR",
                arrival_airport: "KIX",
                departure_time: "2026-10-03T11:10:00Z",
                arrival_time: "2026-10-04T06:40:00Z",
                duration_text: "13h 30m direct",
                notes: ["Direct routing keeps the first day cleaner."],
              },
              {
                id: "flight-kyoto-return",
                direction: "return",
                carrier: "Japan Airlines",
                flight_number: "JL43",
                departure_airport: "KIX",
                arrival_airport: "LHR",
                departure_time: "2026-10-09T09:25:00Z",
                arrival_time: "2026-10-09T18:10:00Z",
                duration_text: "14h 45m direct",
                notes: ["Return timing gives a quiet final morning."],
              },
            ],
            hotels: [
              {
                id: "hotel-kyoto-1",
                hotel_name: "Yasaka House Kyoto",
                area: "Gion / Higashiyama",
                check_in: "2026-10-04T09:30:00Z",
                check_out: "2026-10-09T02:00:00Z",
                notes: [
                  "Strong base for walkable evenings and food-heavy planning.",
                ],
              },
            ],
            weather: [
              {
                id: "weather-kyoto-1",
                day_label: "4 Oct",
                summary: "Cool, clear arrival day",
                high_c: 21,
                low_c: 14,
                notes: ["Best used for a gentle outdoor first afternoon."],
              },
              {
                id: "weather-kyoto-2",
                day_label: "5 Oct",
                summary: "Bright and dry",
                high_c: 23,
                low_c: 15,
                notes: ["Ideal for Arashiyama or temple-heavy walking."],
              },
              {
                id: "weather-kyoto-3",
                day_label: "6 Oct",
                summary: "Chance of light showers",
                high_c: 20,
                low_c: 13,
                notes: ["Keep museum or tea-house options nearby."],
              },
            ],
            activities: [
              {
                id: "activity-kyoto-1",
                title: "Nishiki Market grazing route",
                category: "food",
                day_label: "Day 1",
                time_label: "Lunch",
                notes: ["Good arrival-day energy without too much structure."],
              },
              {
                id: "activity-kyoto-2",
                title: "Early Arashiyama circuit",
                category: "culture",
                day_label: "Day 2",
                time_label: "Morning",
                notes: ["Start early to avoid the heaviest foot traffic."],
              },
              {
                id: "activity-kyoto-3",
                title: "Tea house reset in Higashiyama",
                category: "relaxed",
                day_label: "Day 3",
                time_label: "Afternoon",
                notes: ["Useful if rain softens the walking plan."],
              },
              {
                id: "activity-kyoto-4",
                title: "Craft shopping around Gion",
                category: "culture",
                day_label: "Day 3",
                time_label: "Late afternoon",
                notes: ["Pairs well with a calmer weather-adjusted day."],
              },
            ],
          },
          status: {
            phase: "planning",
            missing_fields: [],
            confirmed_fields: ["from_location", "to_location", "start_date", "end_date", "activity_styles"],
            inferred_fields: ["selected_modules"],
            open_questions: [],
            decision_cards: [],
            brochure_ready: true,
            last_updated_at: "2026-04-19T09:00:00Z",
          },
        },
      };
  }
}
