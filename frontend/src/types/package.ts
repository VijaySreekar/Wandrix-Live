export type TravelPace = "relaxed" | "balanced" | "packed";

export type TravelerDetails = {
  adults: number;
  children: number;
};

export type TravelPackageRequest = {
  origin: string;
  destination: string;
  start_date: string;
  end_date: string;
  travelers: TravelerDetails;
  budget_gbp?: number;
  interests: string[];
  pace: TravelPace;
  include_flights: boolean;
  include_hotel: boolean;
};

export type DailyPlan = {
  day: number;
  date: string;
  morning: string;
  afternoon: string;
  evening: string;
};

export type TravelPackageResponse = {
  title: string;
  summary: string;
  origin: string;
  destination: string;
  duration_nights: number;
  travelers: TravelerDetails;
  estimated_total_gbp: number | null;
  inclusions: string[];
  recommendations: string[];
  itinerary: DailyPlan[];
};
