"use client";

import { useEffect, useRef } from "react";

import { useThread, useThreadRuntime } from "@assistant-ui/react";

import type { ConversationBoardAction } from "@/types/conversation";
import type { PlannerBoardActionIntent } from "@/types/planner-board";

type TravelPlannerBoardActionsProps = {
  pendingBoardAction: PlannerBoardActionIntent | null;
  disabled: boolean;
  onHandled: (actionId: string) => void;
  onActionReadyForBackend: (action: ConversationBoardAction) => void;
};

export function TravelPlannerBoardActions({
  pendingBoardAction,
  disabled,
  onHandled,
  onActionReadyForBackend,
}: TravelPlannerBoardActionsProps) {
  const threadRuntime = useThreadRuntime();
  const isRunning = useThread((state) => state.isRunning);
  const handledActionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!pendingBoardAction) {
      return;
    }

    if (handledActionIdRef.current === pendingBoardAction.action_id) {
      return;
    }

    if (disabled || isRunning) {
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
      destination_name: pendingBoardAction.destination_name,
      country_or_region: pendingBoardAction.country_or_region,
      suggestion_id: pendingBoardAction.suggestion_id,
      selected_modules: pendingBoardAction.selected_modules,
      travel_window: pendingBoardAction.travel_window,
      trip_length: pendingBoardAction.trip_length,
      start_date: pendingBoardAction.start_date,
      end_date: pendingBoardAction.end_date,
      adults: pendingBoardAction.adults,
      children: pendingBoardAction.children,
      activity_styles: pendingBoardAction.activity_styles,
      budget_posture: pendingBoardAction.budget_posture,
      budget_gbp: pendingBoardAction.budget_gbp,
    };

    onActionReadyForBackend(backendAction);
    threadRuntime.append({
      role: "user",
      content: [
        {
          type: "text",
          text: buildBoardSelectionMessage(pendingBoardAction),
        },
      ],
      startRun: true,
    });
    handledActionIdRef.current = pendingBoardAction.action_id;
    onHandled(pendingBoardAction.action_id);
  }, [
    disabled,
    isRunning,
    onActionReadyForBackend,
    onHandled,
    pendingBoardAction,
    threadRuntime,
  ]);

  return null;
}

function buildBoardSelectionMessage(action: PlannerBoardActionIntent) {
  if (action.type === "confirm_trip_details") {
    return buildDetailsSummaryMessage(action);
  }

  if (action.type === "confirm_trip_brief") {
    return "Yes, this is the trip brief I want to move forward with. Please use it as the confirmed plan for the next step.";
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
  const route = [action.from_location, action.to_location]
    .filter(Boolean)
    .join(" to ");
  const activeModules = action.selected_modules
    ? Object.entries(action.selected_modules)
        .filter(([, enabled]) => enabled)
        .map(([moduleName]) => moduleName)
        .join(", ")
    : "full trip";
  const detailBits = [
    route ? `route ${route}` : null,
    action.travel_window ? `timing ${action.travel_window}` : null,
    action.trip_length ? `trip length ${action.trip_length}` : null,
    action.adults !== undefined && action.adults !== null
      ? `${action.adults} adult${action.adults === 1 ? "" : "s"}`
      : null,
    action.children !== undefined && action.children !== null
      ? `${action.children} child${action.children === 1 ? "" : "ren"}`
      : null,
    action.activity_styles?.length
      ? `style ${action.activity_styles.join(", ")}`
      : null,
    action.budget_posture
      ? `budget ${action.budget_posture.replace("_", "-")}`
      : null,
    action.budget_gbp ? `about GBP ${action.budget_gbp}` : null,
    activeModules ? `modules ${activeModules}` : null,
  ].filter(Boolean);

  return `Here are the trip details I want to use for now: ${detailBits.join(", ")}.`;
}
