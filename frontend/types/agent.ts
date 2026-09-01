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
  what_to_do?: string | null;
  why_recommended?: string | null;
  estimated_cost: number;
  currency: string;
  visit_duration_minutes: number;
  visit_duration?: string | null;
  travel_time_from_previous?: string | null;
  transport_mode?: string | null;
  practical_tips?: string | null;
  is_indoor?: boolean | null;
  weather_suitability?: string | null;
  notes?: string | null;
}

export interface ItineraryFoodRecommendation {
  name: string;
  meal: "breakfast" | "lunch" | "dinner" | "snack" | string;
  restaurant_type?: string | null;
  cuisine_type?: string | null;
  estimated_cost: number;
  currency: string;
  suggested_time?: string | null;
  local_specialty?: string | null;
  dietary_fit?: string | null;
}

export interface ItineraryDay {
  day_number: number;
  date: string;
  theme: string;
  summary?: string | null;
  weather_summary?: string | null;
  weather_note?: string | null;
  morning?: { activities: ItineraryActivityItem[] } | null;
  afternoon?: { activities: ItineraryActivityItem[] } | null;
  evening?: { activities: ItineraryActivityItem[] } | null;
  night?: { activities: ItineraryActivityItem[] } | null;
  meals?: {
    breakfast?: ItineraryFoodRecommendation | null;
    lunch?: ItineraryFoodRecommendation | null;
    snack?: ItineraryFoodRecommendation | null;
    dinner?: ItineraryFoodRecommendation | null;
  } | null;
  activities: ItineraryActivityItem[];
  food_recommendations: ItineraryFoodRecommendation[];
  daily_budget?: {
    accommodation?: number;
    food: number;
    transport: number;
    activities: number;
    miscellaneous: number;
    total: number;
  } | null;
  travel_tips?: string[];
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
  cost_per_traveler?: number | null;
  budget?: number | null;
  currency: string;
  budget_status: "within_budget" | "near_budget" | "exceeds_budget" | "unspecified" | string;
  budget_warning?: string | null;
  weather_advisory?: string | null;
  trip_summary?: {
    destination: string;
    duration_days: number;
    travel_style?: string;
    estimated_total_cost?: number;
    budget_status?: string;
    cost_per_traveler?: number;
  } | null;
  overall_tips?: string[];
  packing_suggestions?: string[];
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

// Stage 8: Live Route & GPS Interfaces
export interface CoordinatePoint {
  latitude: number;
  longitude: number;
}

export interface RouteData {
  trip_id: string;
  origin: CoordinatePoint;
  destination: CoordinatePoint;
  distance_km: number;
  duration_minutes: number;
  transport_mode: "driving" | "walking" | "cycling" | string;
  geometry?: [number, number][] | any;
  source?: string;
  route_status: "ready" | "unavailable" | "error" | string;
  route_error?: string | null;
}

export interface RouteResponse {
  success: boolean;
  data: RouteData;
}

// Stage 9: Crowd Monitoring & Overcrowding Interfaces
export type CrowdLevel = "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH" | "OVER_CROWDED";

export interface AlternativePlaceItem {
  name: string;
  category: string;
  description?: string | null;
  why_recommended: string;
  estimated_visit_duration?: string | null;
  estimated_cost?: number | null;
  currency?: string;
  latitude?: number | null;
  longitude?: number | null;
  distance_km?: number | null;
  weather_suitability?: string | null;
  confidence?: number;
}

export interface CrowdData {
  trip_id: string;
  destination: string;
  people_count: number;
  capacity: number;
  crowd_percentage: number;
  crowd_level: CrowdLevel | string;
  crowd_score: number;
  crowd_status: "Normal" | "Busy" | "Overcrowded" | string;
  is_overcrowded: boolean;
  crowd_confidence: number;
  recommendation: string;
  ai_explanation?: string | null;
  alternative_places: AlternativePlaceItem[];
  latitude?: number | null;
  longitude?: number | null;
  source?: string | null;
  timestamp?: string | null;
}

export interface CrowdResponse {
  success: boolean;
  data: CrowdData;
}





