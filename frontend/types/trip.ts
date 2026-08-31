export type TransportMode = "car" | "bike" | "bus" | "train" | "flight";

export type FoodPreference =
  | "vegetarian"
  | "non-vegetarian"
  | "vegan"
  | "no preference"
  | "any";

export type AccommodationPreference =
  | "hotel"
  | "homestay"
  | "hostel"
  | "resort"
  | "any";

export type TravelStyle =
  | "relaxed"
  | "balanced"
  | "adventure"
  | "budget"
  | "luxury"
  | "family";

export type TripStatus = "draft" | "planning" | "completed";

export interface Trip {
  id: string;
  user_id: string;
  title: string;
  starting_location: string;
  destination: string;
  travel_date: string;
  duration_days: number;
  adults: number;
  children: number;
  budget: number;
  transport_mode: TransportMode;
  interests: string[];
  food_preference: FoodPreference;
  accommodation_preference: AccommodationPreference;
  travel_style: TravelStyle;
  status: TripStatus;
  created_at: string;
  updated_at: string;
}

export interface TripCreateInput {
  title: string;
  starting_location: string;
  destination: string;
  travel_date: string;
  duration_days: number;
  adults: number;
  children: number;
  budget: number;
  transport_mode: TransportMode;
  interests: string[];
  food_preference: FoodPreference;
  accommodation_preference: AccommodationPreference;
  travel_style: TravelStyle;
  status?: TripStatus;
}

export interface TripUpdateInput {
  title?: string;
  starting_location?: string;
  destination?: string;
  travel_date?: string;
  duration_days?: number;
  adults?: number;
  children?: number;
  budget?: number;
  transport_mode?: TransportMode;
  interests?: string[];
  food_preference?: FoodPreference;
  accommodation_preference?: AccommodationPreference;
  travel_style?: TravelStyle;
  status?: TripStatus;
}

export const INTEREST_OPTIONS: { id: string; label: string; icon?: string }[] = [
  { id: "nature", label: "Nature & Outdoors" },
  { id: "museum", label: "Museums & History" },
  { id: "adventure", label: "Adventure & Sports" },
  { id: "culture", label: "Heritage & Culture" },
  { id: "shopping", label: "Shopping & Bazaars" },
  { id: "food", label: "Culinary & Food" },
  { id: "nightlife", label: "Nightlife & Social" },
  { id: "photography", label: "Photography & Scenic" },
  { id: "family", label: "Family Friendly" },
];

export const TRANSPORT_OPTIONS: { id: TransportMode; label: string; icon: string }[] = [
  { id: "car", label: "Car / Drive", icon: "Car" },
  { id: "bike", label: "Motorbike", icon: "Bike" },
  { id: "bus", label: "Bus / Coach", icon: "Bus" },
  { id: "train", label: "Train / Rail", icon: "Train" },
  { id: "flight", label: "Flight / Air", icon: "Plane" },
];

export const FOOD_OPTIONS: { id: FoodPreference; label: string }[] = [
  { id: "vegetarian", label: "Vegetarian" },
  { id: "non-vegetarian", label: "Non-Vegetarian" },
  { id: "vegan", label: "Vegan" },
  { id: "no preference", label: "No Preference" },
];

export const ACCOMMODATION_OPTIONS: { id: AccommodationPreference; label: string }[] = [
  { id: "hotel", label: "Hotel" },
  { id: "homestay", label: "Homestay / B&B" },
  { id: "hostel", label: "Hostel / Backpacker" },
  { id: "resort", label: "Resort & Spa" },
  { id: "any", label: "Any / Flexible" },
];

export const TRAVEL_STYLE_OPTIONS: { id: TravelStyle; label: string; desc: string }[] = [
  { id: "relaxed", label: "Relaxed", desc: "Easy-paced with ample downtime" },
  { id: "balanced", label: "Balanced", desc: "Standard blend of sightseeing & leisure" },
  { id: "adventure", label: "Adventure", desc: "Action-packed & active exploration" },
  { id: "budget", label: "Budget-Friendly", desc: "Cost-conscious and resourceful" },
  { id: "luxury", label: "Luxury", desc: "Premium comforts & curated experiences" },
  { id: "family", label: "Family Focused", desc: "Safe, comfortable, all-ages friendly" },
];
