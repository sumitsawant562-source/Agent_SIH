export interface RequirementData {
  trip_id: string;
  requirements_complete: boolean;
  missing_information: string[];
  questions: string[];
  start_location?: string | null;
  destination?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  duration_days?: number | null;
  travelers?: number | null;
  adults?: number | null;
  children?: number | null;
  budget?: number | null;
  currency?: string | null;
  transport_mode?: string | null;
  food_preference?: string | null;
  stay_preference?: string | null;
  interests?: string[] | null;
  special_requirements?: string | null;
}

export interface RequirementResponse {
  success: boolean;
  data: RequirementData;
}

export type DestinationCategory =
  | "famous_place"
  | "hidden_gem"
  | "nearby_place"
  | "food_dining"
  | "stay_area"
  | "nature_adventure"
  | "cultural_historical"
  | "family_friendly";

export interface DestinationRecommendationItem {
  name: string;
  category: DestinationCategory | string;
  description: string;
  why_recommended: string;
  estimated_visit_duration?: string | null;
  estimated_cost?: number | null;
  currency?: string;
  latitude?: number | null;
  longitude?: number | null;
  best_time_to_visit?: string | null;
  distance_from_destination?: string | null;
  distance_from_previous_location?: string | null;
  tags?: string[];
  confidence: number;
}

export interface DestinationResponseData {
  trip_id: string;
  destination: string;
  recommendations: DestinationRecommendationItem[];
  categories_summary?: Record<string, number>;
  total_recommendations: number;
}

export interface DestinationResponse {
  success: boolean;
  data: DestinationResponseData;
}

