"use client";

import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripCreateResponse } from "@/types/trip";
import type { TripDraft } from "@/types/trip-draft";


export function buildStarterTripDraft(trip: TripCreateResponse): TripDraft {
  return {
    trip_id: trip.trip_id,
    thread_id: trip.thread_id,
    title: trip.title,
    configuration: {
      from_location: null,
      to_location: null,
      start_date: null,
      end_date: null,
      travel_window: null,
      trip_length: null,
      travelers: {
        adults: null,
        children: null,
      },
      budget_posture: null,
      budget_gbp: null,
      selected_modules: {
        flights: true,
        weather: true,
        activities: true,
        hotels: true,
      },
      activity_styles: [],
    },
    timeline: [],
    module_outputs: {
      flights: [],
      hotels: [],
      weather: [],
      activities: [],
    },
    status: {
      phase: "opening",
      confirmation_status: "unconfirmed",
      finalized_at: null,
      finalized_via: null,
      missing_fields: [],
      confirmed_fields: [],
      inferred_fields: [],
      brochure_ready: false,
      last_updated_at: null,
    },
    conversation: {
      phase: "opening",
      planning_mode: null,
      planning_mode_status: "not_selected",
      confirmation_status: "unconfirmed",
      finalized_at: null,
      finalized_via: null,
      open_questions: [],
      decision_cards: [],
      last_turn_summary: null,
      active_goals: [],
      suggestion_board: {
        mode: "helper",
        cards: [],
        planning_mode_cards: [],
        have_details: [],
        need_details: [],
        visible_steps: [],
        required_steps: [],
        details_form: null,
        confirm_cta_label: null,
        own_choice_prompt: null,
        source_context: null,
        title: null,
        subtitle: null,
      },
      memory: {
        field_memory: {},
        mentioned_options: [],
        rejected_options: [],
        decision_history: [],
        turn_summaries: [],
      },
    },
  };
}


export function buildEphemeralWorkspace(
  existingBrowserSessionId: string | null,
): PlannerWorkspaceState {
  const suffix = crypto.randomUUID().replace(/-/g, "");
  const trip: TripCreateResponse = {
    trip_id: `draft_trip_${suffix}`,
    browser_session_id:
      existingBrowserSessionId ?? `draft_browser_session_${suffix}`,
    thread_id: `draft_thread_${suffix}`,
    title: `Trip ${suffix.slice(-6)}`,
    trip_status: "collecting_requirements",
    thread_status: "ready",
    created_at: new Date().toISOString(),
  };

  const browserSession: BrowserSessionCreateResponse = {
    browser_session_id: trip.browser_session_id,
    user_id: null,
    timezone: null,
    locale: null,
    status: "active",
    created_at: trip.created_at,
  };

  return {
    isEphemeral: true,
    browserSession,
    trip,
    tripDraft: buildStarterTripDraft(trip),
  };
}


export function isEphemeralTripId(tripId: string | null | undefined) {
  return typeof tripId === "string" && tripId.startsWith("draft_trip_");
}
