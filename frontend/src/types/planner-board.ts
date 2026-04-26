import type { ConversationBoardAction } from "@/types/conversation";

export type PlannerBackendBoardActionIntent = ConversationBoardAction & {
  prompt_text?: string | null;
};

export type PlannerChatPromptIntent = {
  action_id: string;
  type: "chat_prompt";
  prompt_text: string;
};

export type PlannerBoardActionIntent =
  | PlannerBackendBoardActionIntent
  | PlannerChatPromptIntent;
