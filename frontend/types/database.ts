export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          full_name?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          full_name?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      trips: {
        Row: {
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
          transport_mode: "car" | "bike" | "bus" | "train" | "flight";
          interests: string[];
          food_preference: "vegetarian" | "non-vegetarian" | "vegan" | "no preference" | "any";
          accommodation_preference: "hotel" | "homestay" | "hostel" | "resort" | "any";
          travel_style: "relaxed" | "balanced" | "adventure" | "budget" | "luxury" | "family";
          status: "draft" | "planning" | "completed";
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          title: string;
          starting_location: string;
          destination: string;
          travel_date: string;
          duration_days: number;
          adults?: number;
          children?: number;
          budget: number;
          transport_mode: "car" | "bike" | "bus" | "train" | "flight";
          interests?: string[];
          food_preference?: "vegetarian" | "non-vegetarian" | "vegan" | "no preference" | "any";
          accommodation_preference?: "hotel" | "homestay" | "hostel" | "resort" | "any";
          travel_style?: "relaxed" | "balanced" | "adventure" | "budget" | "luxury" | "family";
          status?: "draft" | "planning" | "completed";
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          title?: string;
          starting_location?: string;
          destination?: string;
          travel_date?: string;
          duration_days?: number;
          adults?: number;
          children?: number;
          budget?: number;
          transport_mode?: "car" | "bike" | "bus" | "train" | "flight";
          interests?: string[];
          food_preference?: "vegetarian" | "non-vegetarian" | "vegan" | "no preference" | "any";
          accommodation_preference?: "hotel" | "homestay" | "hostel" | "resort" | "any";
          travel_style?: "relaxed" | "balanced" | "adventure" | "budget" | "luxury" | "family";
          status?: "draft" | "planning" | "completed";
          created_at?: string;
          updated_at?: string;
        };
      };
    };
  };
}
