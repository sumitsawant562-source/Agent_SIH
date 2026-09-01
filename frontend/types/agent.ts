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

// Stage 6: Weather Intelligence Interfaces
export interface CurrentWeather {
  location_name: string;
  latitude: number;
  longitude: number;
  temperature: number;
  feels_like: number;
  temperature_min?: number | null;
  temperature_max?: number | null;
  humidity: number;
  pressure?: number | null;
  wind_speed: number;
  wind_direction?: number | null;
  precipitation: number;
  rain_probability: number;
  weather_condition: string;
  weather_description: string;
  visibility: number;
  sunrise?: string | null;
  sunset?: string | null;
  observed_at: string;
  source: string;
}

export interface ForecastItem {
  date: string;
  time: string;
  temperature: number;
  feels_like: number;
  humidity: number;
  precipitation: number;
  rain_probability: number;
  wind_speed: number;
  weather_condition: string;
  weather_description: string;
}

export interface WeatherInsight {
  type: string;
  title: string;
  message: string;
  severity: "info" | "moderate" | "alert" | string;
}

export interface PlaceWeatherItem {
  place_name: string;
  category: string;
  latitude: number;
  longitude: number;
  temperature: number;
  weather_condition: string;
  weather_description: string;
  rain_probability: number;
}

export interface WeatherResponseData {
  trip_id: string;
  destination: string;
  current_weather?: CurrentWeather | null;
  forecast: ForecastItem[];
  insights: WeatherInsight[];
  place_weathers?: PlaceWeatherItem[];
  weather_status: "ready" | "unavailable" | "pending" | string;
  weather_errors: string[];
}

export interface WeatherResponse {
  success: boolean;
  data: WeatherResponseData;
}

// Stage 7: Itinerary Planning Interfaces
export interface ItineraryActivityItem {
  time_slot: "morning" | "afternoon" | "evening" | "night" | string;
  start_time: string;
  end_time: string;
  place_name: string;
  category: string;
  description: string;
  estimated_cost: number;
  currency: string;
  visit_duration_minutes: number;
  notes?: string | null;
}

export interface ItineraryFoodRecommendation {
  name: string;
  meal: "breakfast" | "lunch" | "dinner" | "snack" | string;
  cuisine_type?: string | null;
  estimated_cost: number;
  currency: string;
  dietary_fit?: string | null;
}

export interface ItineraryDay {
  day_number: number;
  date: string;
  theme: string;
  weather_summary?: string | null;
  activities: ItineraryActivityItem[];
  food_recommendations: ItineraryFoodRecommendation[];
  estimated_day_cost: number;
  notes?: string | null;
}

export interface ItineraryData {
  trip_id: string;
  destination: string;
  start_date?: string | null;
  end_date?: string | null;
  duration_days: number;
  total_estimated_cost: number;
  budget?: number | null;
  currency: string;
  budget_status: "within_budget" | "exceeds_budget" | "unspecified" | string;
  budget_warning?: string | null;
  weather_advisory?: string | null;
  days: ItineraryDay[];
}

export interface ItineraryResponseData {
  trip_id: string;
  destination: string;
  itinerary?: ItineraryData | null;
  itinerary_status: "ready" | "unavailable" | "pending" | string;
  itinerary_errors: string[];
}

export interface ItineraryResponse {
  success: boolean;
  data: ItineraryResponseData;
}



