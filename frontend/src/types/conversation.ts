export type TripConversationMessageRequest = {
  message: string;
};

export type TripConversationMessageResponse = {
  trip_id: string;
  thread_id: string;
  draft_phase:
    | "collecting_requirements"
    | "planning"
    | "ready_for_review"
    | "finalized";
  message: string;
};
