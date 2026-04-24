"use client";

import { useEffect, useRef } from "react";

import { useThreadRuntime } from "@assistant-ui/react";

import type { ConversationBoardAction } from "@/types/conversation";
import type { PlannerBoardActionIntent } from "@/types/planner-board";

type TravelPlannerBoardActionsProps = {
  pendingBoardAction: PlannerBoardActionIntent | null;
  disabled: boolean;
  onHandled: (actionId: string) => void;
  onDirectActionSubmit: (action: ConversationBoardAction) => Promise<string>;
};

export function TravelPlannerBoardActions({
  pendingBoardAction,
  disabled,
  onHandled,
  onDirectActionSubmit,
}: TravelPlannerBoardActionsProps) {
  const threadRuntime = useThreadRuntime();
  const handledActionIdRef = useRef<string | null>(null);
  const submittingActionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!pendingBoardAction) {
      return;
    }

    if (handledActionIdRef.current === pendingBoardAction.action_id) {
      return;
    }

    if (disabled) {
      return;
    }

    if (pendingBoardAction.type === "own_choice") {
      threadRuntime.composer.setText(
        pendingBoardAction.prompt_text ||
          "Tell me the destination you already have in mind.",
      );
      handledActionIdRef.current = pendingBoardAction.action_id;
      onHandled(pendingBoardAction.action_id);
      return;
    }

    const backendAction: ConversationBoardAction = {
      action_id: pendingBoardAction.action_id,
      type: pendingBoardAction.type,
      advanced_anchor: pendingBoardAction.advanced_anchor,
      destination_name: pendingBoardAction.destination_name,
      country_or_region: pendingBoardAction.country_or_region,
      suggestion_id: pendingBoardAction.suggestion_id,
      date_option_id: pendingBoardAction.date_option_id,
      flight_strategy: pendingBoardAction.flight_strategy,
      flight_option_id: pendingBoardAction.flight_option_id,
      stay_option_id: pendingBoardAction.stay_option_id,
      stay_segment_id: pendingBoardAction.stay_segment_id,
      stay_hotel_id: pendingBoardAction.stay_hotel_id,
      stay_hotel_name: pendingBoardAction.stay_hotel_name,
      activity_candidate_id: pendingBoardAction.activity_candidate_id,
      activity_candidate_title: pendingBoardAction.activity_candidate_title,
      activity_candidate_kind: pendingBoardAction.activity_candidate_kind,
      activity_candidate_disposition:
        pendingBoardAction.activity_candidate_disposition,
      activity_target_day_index: pendingBoardAction.activity_target_day_index,
      activity_target_daypart: pendingBoardAction.activity_target_daypart,
      trip_style_direction_primary:
        pendingBoardAction.trip_style_direction_primary,
      trip_style_direction_accent:
        pendingBoardAction.trip_style_direction_accent,
      trip_style_pace: pendingBoardAction.trip_style_pace,
      trip_style_tradeoff_axis: pendingBoardAction.trip_style_tradeoff_axis,
      trip_style_tradeoff_value: pendingBoardAction.trip_style_tradeoff_value,
      stay_hotel_max_nightly_rate:
        pendingBoardAction.stay_hotel_max_nightly_rate,
      stay_hotel_area_filter: pendingBoardAction.stay_hotel_area_filter,
      stay_hotel_style_filter: pendingBoardAction.stay_hotel_style_filter,
      stay_hotel_sort_order: pendingBoardAction.stay_hotel_sort_order,
      stay_hotel_page: pendingBoardAction.stay_hotel_page,
      from_location: pendingBoardAction.from_location,
      from_location_flexible: pendingBoardAction.from_location_flexible,
      to_location: pendingBoardAction.to_location,
      selected_modules: pendingBoardAction.selected_modules,
      travel_window: pendingBoardAction.travel_window,
      trip_length: pendingBoardAction.trip_length,
      weather_preference: pendingBoardAction.weather_preference,
      start_date: pendingBoardAction.start_date,
      end_date: pendingBoardAction.end_date,
      adults: pendingBoardAction.adults,
      children: pendingBoardAction.children,
      travelers_flexible: pendingBoardAction.travelers_flexible,
      activity_styles: pendingBoardAction.activity_styles,
      custom_style: pendingBoardAction.custom_style,
      budget_posture: pendingBoardAction.budget_posture,
      budget_gbp: pendingBoardAction.budget_gbp,
    };

    if (submittingActionIdRef.current === pendingBoardAction.action_id) {
      return;
    }

    submittingActionIdRef.current = pendingBoardAction.action_id;

    threadRuntime.append({
      role: "user",
      content: [
        {
          type: "text",
          text: buildBoardSelectionMessage(pendingBoardAction),
        },
      ],
      startRun: false,
    });

    void onDirectActionSubmit(backendAction)
      .then((assistantMessage) => {
        threadRuntime.append({
          role: "assistant",
          content: [{ type: "text", text: assistantMessage }],
          startRun: false,
        });
      })
      .catch((error: unknown) => {
        threadRuntime.append({
          role: "assistant",
          content: [
            {
              type: "text",
              text:
                error instanceof Error
                  ? error.message
                : "That board action could not be completed right now.",
            },
          ],
          startRun: false,
        });
      })
      .finally(() => {
        handledActionIdRef.current = pendingBoardAction.action_id;
        onHandled(pendingBoardAction.action_id);
        submittingActionIdRef.current = null;
      });
  }, [
    disabled,
    onDirectActionSubmit,
    onHandled,
    pendingBoardAction,
    threadRuntime,
  ]);

  return null;
}

function buildBoardSelectionMessage(action: PlannerBoardActionIntent) {
  if (action.type === "select_quick_plan") {
    return "Use Quick Plan and generate the first draft itinerary now.";
  }

  if (action.type === "select_advanced_plan") {
    return "Use Advanced Planning for this trip.";
  }

  if (action.type === "select_advanced_anchor") {
    const anchorLabel = action.advanced_anchor
      ? action.advanced_anchor.replace("_", " ")
      : "that focus";
    return `In Advanced Planning, start by shaping ${anchorLabel} first.`;
  }

  if (action.type === "select_flight_strategy") {
    const strategy = action.flight_strategy
      ? action.flight_strategy.replace(/_/g, " ")
      : "that flight strategy";
    return `Use ${strategy} as the working flight strategy.`;
  }

  if (action.type === "select_outbound_flight") {
    return "Use this outbound flight as the working planning option.";
  }

  if (action.type === "select_return_flight") {
    return "Use this return flight as the working planning option.";
  }

  if (action.type === "confirm_flight_selection") {
    return "Confirm these working flights for Advanced Planning.";
  }

  if (action.type === "keep_flights_open") {
    return "Keep flights flexible for now.";
  }

  if (action.type === "select_trip_style_direction_primary") {
    const primary = action.trip_style_direction_primary
      ? action.trip_style_direction_primary.replace(/_/g, " ")
      : "that direction";
    return `Set the trip direction to ${primary}.`;
  }

  if (action.type === "select_trip_style_direction_accent") {
    const accent = action.trip_style_direction_accent || "that accent";
    return `Add a ${accent} accent to the trip direction.`;
  }

  if (action.type === "clear_trip_style_direction_accent") {
    return "Clear the optional trip-style accent and keep the main direction only.";
  }

  if (action.type === "confirm_trip_style_direction") {
    return "Use this as the working trip direction and shape activities around it.";
  }

  if (action.type === "keep_current_trip_style_direction") {
    return "Keep the current trip direction anyway.";
  }

  if (action.type === "select_trip_style_pace") {
    const pace = action.trip_style_pace || "that pace";
    return `Set the trip pace to ${pace}.`;
  }

  if (action.type === "confirm_trip_style_pace") {
    return "Use this pace for the trip and shape activities around it.";
  }

  if (action.type === "keep_current_trip_style_pace") {
    return "Keep the current trip pace anyway.";
  }

  if (action.type === "set_trip_style_tradeoff") {
    const value = action.trip_style_tradeoff_value
      ? action.trip_style_tradeoff_value.replace(/_/g, " ")
      : "that tie-breaker";
    return `Set the Trip Style tie-breaker to ${value}.`;
  }

  if (action.type === "confirm_trip_style_tradeoffs") {
    return "Use these Trip Style tie-breakers and shape activities around them.";
  }

  if (action.type === "keep_current_trip_style_tradeoffs") {
    return "Keep the current Trip Style tie-breakers anyway.";
  }

  if (action.type === "select_date_option") {
    return "Use that date range as the working trip window.";
  }

  if (action.type === "pick_dates_for_me") {
    return "Pick the strongest date option for me.";
  }

  if (action.type === "confirm_working_dates") {
    return "Proceed with this trip window.";
  }

  if (action.type === "select_stay_option") {
    return "Use that stay direction as the current base for the trip.";
  }

  if (action.type === "select_stay_hotel") {
    return action.stay_hotel_name
      ? `I'd like to proceed with ${action.stay_hotel_name} as the working hotel for this trip.`
      : "I'd like to proceed with this hotel as the working hotel for this trip.";
  }

  if (action.type === "keep_current_stay_choice") {
    return "Keep the current base anyway, even if the way this trip is taking shape is putting it under some strain.";
  }

  if (action.type === "keep_current_hotel_choice") {
    return "Keep the current hotel anyway, even if the way this trip is taking shape is putting it under some strain.";
  }

  if (action.type === "set_activity_candidate_disposition") {
    const title = action.activity_candidate_title || "this pick";
    if (action.activity_candidate_disposition === "essential") {
      return `Let ${title} help shape the trip.`;
    }
    if (action.activity_candidate_disposition === "pass") {
      return `Leave ${title} out for this trip.`;
    }
    return `Keep ${title} in the mix for this trip.`;
  }

  if (action.type === "rebuild_activity_day_plan") {
    return "Refresh the draft days around the current shortlist.";
  }

  if (
    action.type === "move_activity_candidate_to_day" &&
    action.activity_target_day_index
  ) {
    const title = action.activity_candidate_title || "this pick";
    return `Move ${title} onto Day ${action.activity_target_day_index} and rebalance the rest lightly around it.`;
  }

  if (action.type === "move_activity_candidate_earlier") {
    const title = action.activity_candidate_title || "this pick";
    return `Move ${title} earlier in the day.`;
  }

  if (action.type === "move_activity_candidate_later") {
    const title = action.activity_candidate_title || "this pick";
    return `Move ${title} later in the day.`;
  }

  if (
    action.type === "pin_activity_candidate_daypart" &&
    action.activity_target_daypart
  ) {
    const title = action.activity_candidate_title || "this pick";
    return `Pin ${title} to the ${action.activity_target_daypart}.`;
  }

  if (action.type === "send_activity_candidate_to_reserve") {
    const title = action.activity_candidate_title || "this pick";
    return `Save ${title} for later instead of forcing it into the active day plan.`;
  }

  if (action.type === "restore_activity_candidate_from_reserve") {
    const title = action.activity_candidate_title || "this pick";
    return `Bring ${title} back into the active plan.`;
  }

  if (action.type === "set_stay_hotel_filters") {
    return "Update the hotel workspace filters with these choices.";
  }

  if (action.type === "set_stay_hotel_sort") {
    return "Reorder the hotel workspace with this sort preference.";
  }

  if (action.type === "set_stay_hotel_page") {
    return "Show the next hotel results page in the workspace.";
  }

  if (action.type === "reset_stay_hotel_filters") {
    return "Reset the hotel workspace filters to the default view.";
  }

  if (action.type === "revise_advanced_review_section") {
    const anchor = action.advanced_anchor
      ? action.advanced_anchor.replace(/_/g, " ")
      : "that part of the trip";
    return `Review ${anchor} again before finalizing the trip.`;
  }

  if (action.type === "apply_planner_conflict_safe_edit") {
    return "Apply the safe planner edit for this review tension.";
  }

  if (action.type === "defer_planner_conflict") {
    return "Keep this review tension as an intentional caution.";
  }

  if (action.type === "resolve_planner_conflict") {
    return "Mark this review tension as resolved.";
  }

  if (action.type === "finalize_quick_plan") {
    return "Finalize this quick plan from the board.";
  }

  if (action.type === "finalize_advanced_plan") {
    return "Finalize this reviewed Advanced plan from the board.";
  }

  if (action.type === "reopen_plan") {
    return "Reopen this finalized trip from the board.";
  }

  if (action.type === "confirm_trip_details") {
    return buildDetailsSummaryMessage(action);
  }

  const destination = [action.destination_name, action.country_or_region]
    .filter(Boolean)
    .join(", ");

  if (!destination) {
    return "That destination direction looks like the strongest fit so far.";
  }

  return `I’d like to explore ${destination} next. Keep it as the working destination for now while we fill in the rest.`;
}

function buildDetailsSummaryMessage(action: PlannerBoardActionIntent) {
  const route =
    action.from_location_flexible && action.to_location
      ? action.from_location
        ? `${action.from_location} (flexible) to ${action.to_location}`
        : `flexible departure to ${action.to_location}`
      : [action.from_location, action.to_location].filter(Boolean).join(" to ");
  const activeModules = action.selected_modules
    ? Object.entries(action.selected_modules)
        .filter(([, enabled]) => enabled)
        .map(([moduleName]) => moduleName)
        .join(", ")
    : "full trip";
  const detailBits = [
    route ? `route ${route}` : null,
    action.from_location_flexible && !action.from_location
      ? "departure still flexible"
      : null,
    action.travel_window ? `timing ${action.travel_window}` : null,
    action.trip_length ? `trip length ${action.trip_length}` : null,
    action.weather_preference
      ? `weather ${action.weather_preference}`
      : null,
    action.adults !== undefined && action.adults !== null
      ? `${action.adults} adult${action.adults === 1 ? "" : "s"}`
      : null,
    action.children !== undefined && action.children !== null
      ? `${action.children} child${action.children === 1 ? "" : "ren"}`
      : null,
    action.travelers_flexible ? "traveller count still flexible" : null,
    action.activity_styles?.length
      ? `style ${action.activity_styles.join(", ")}`
      : null,
    action.custom_style ? `custom style ${action.custom_style}` : null,
    action.budget_posture
      ? `budget ${action.budget_posture.replace("_", "-")}`
      : null,
    action.budget_gbp ? `about GBP ${action.budget_gbp}` : null,
    activeModules ? `modules ${activeModules}` : null,
  ].filter(Boolean);

  return `Please use these trip details as the current plan: ${detailBits.join(", ")}.`;
}
