export type PlannerLocationSuggestionKind = "origin" | "destination";

export type PlannerLocationSuggestion = {
  id: string;
  label: string;
  detail: string | null;
};

export type PlannerLocationSuggestionResponse = {
  items: PlannerLocationSuggestion[];
};
