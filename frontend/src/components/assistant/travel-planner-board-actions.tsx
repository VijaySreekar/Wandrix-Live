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
  const destination = [action.destination_name, action.country_or_region]
    .filter(Boolean)
    .join(", ");

  if (!destination) {
    return "That destination direction looks like the strongest fit so far.";
  }

  return `That ${destination} option looks like the strongest fit so far. Can we explore it next without locking it in yet?`;
}
