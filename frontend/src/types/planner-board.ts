import type { ConversationBoardAction } from "@/types/conversation";

export type PlannerBoardActionIntent = ConversationBoardAction & {
  prompt_text?: string | null;
};
