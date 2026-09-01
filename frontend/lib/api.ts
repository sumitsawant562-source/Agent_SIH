import { supabase } from "@/lib/supabase/client";
import { Trip, TripCreateInput, TripUpdateInput } from "@/types/trip";
import {
  CoordinatePoint,
  CrowdResponse,
  DestinationResponse,
  ItineraryResponse,
  RequirementResponse,
  RouteResponse,
  WeatherResponse,
} from "@/types/agent";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface RequestOptions extends RequestInit {
  requireAuth?: boolean;
}

async function getAuthToken(): Promise<string | null> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  } catch (error) {
    console.warn("Failed to get auth token from Supabase session:", error);
    return null;
  }
}

async function apiFetch<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { requireAuth = true, headers = {}, ...restOptions } = options;
  const requestHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  };

  if (requireAuth) {
    const token = await getAuthToken();
    if (token) {
      requestHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const url = `${API_BASE_URL.replace(/\/$/, "")}/api${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
    });

    if (!response.ok) {
      let errorMessage = `API Error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === "string" 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to generic statusText
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error: any) {
    // If backend connection fails (e.g. backend offline), log and rethrow
    console.error(`[API Client Error] at ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Health
  async getHealth(): Promise<{ status: string }> {
    return apiFetch<{ status: string }>("/health", { requireAuth: false });
  },

  // Auth / Current User
  async getCurrentUser(): Promise<{ id: string; email: string; full_name?: string; is_authenticated: boolean }> {
    return apiFetch("/auth/me");
  },

  // Trips CRUD
  async getTrips(): Promise<{ total: number; trips: Trip[] }> {
    try {
      return await apiFetch<{ total: number; trips: Trip[] }>("/trips");
    } catch (err) {
      console.warn("FastAPI /trips endpoint unreachable, attempting direct Supabase query...", err);
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw err;
      
      const { data, error } = await (supabase.from("trips") as any)
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return { total: data?.length || 0, trips: (data as any) || [] };
    }
  },

  async getTrip(id: string): Promise<Trip> {
    try {
      return await apiFetch<Trip>(`/trips/${id}`);
    } catch (err) {
      console.warn(`FastAPI /trips/${id} unreachable, trying direct Supabase query...`, err);
      const { data, error } = await (supabase.from("trips") as any)
        .select("*")
        .eq("id", id)
        .single();
      if (error) throw error;
      return data as any;
    }
  },

  async createTrip(input: TripCreateInput): Promise<Trip> {
    try {
      return await apiFetch<Trip>("/trips", {
        method: "POST",
        body: JSON.stringify(input),
      });
    } catch (err) {
      console.warn("FastAPI trip creation failed, trying direct Supabase insert fallback...", err);
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw err;

      const { data, error } = await (supabase.from("trips") as any)
        .insert({
          ...input,
          user_id: user.id,
        })
        .select()
        .single();

      if (error) throw error;
      return data as any;
    }
  },

  async updateTrip(id: string, input: TripUpdateInput): Promise<Trip> {
    try {
      return await apiFetch<Trip>(`/trips/${id}`, {
        method: "PUT",
        body: JSON.stringify(input),
      });
    } catch (err) {
      console.warn(`FastAPI update failed for ${id}, trying direct Supabase update...`, err);
      const { data, error } = await (supabase.from("trips") as any)
        .update(input)
        .eq("id", id)
        .select()
        .single();

      if (error) throw error;
      return data as any;
    }
  },

  async deleteTrip(id: string): Promise<{ message: string; trip_id: string }> {
    try {
      return await apiFetch<{ message: string; trip_id: string }>(`/trips/${id}`, {
        method: "DELETE",
      });
    } catch (err) {
      console.warn(`FastAPI delete failed for ${id}, trying direct Supabase delete...`, err);
      const { error } = await (supabase.from("trips") as any)
        .delete()
        .eq("id", id);

      if (error) throw error;
      return { message: "Trip successfully deleted", trip_id: id };
    }
  },

  // AI Requirement Agent
  async startRequirementAnalysis(tripId: string): Promise<RequirementResponse> {
    return apiFetch<RequirementResponse>("/agent/requirements/start", {
      method: "POST",
      body: JSON.stringify({ trip_id: tripId }),
    });
  },

  async respondToRequirementAgent(tripId: string, answers: string): Promise<RequirementResponse> {
    return apiFetch<RequirementResponse>("/agent/requirements/respond", {
      method: "POST",
      body: JSON.stringify({ trip_id: tripId, answers }),
    });
  },

  // AI Destination Agent (Stage 5)
  async startDestinationAgent(tripId: string): Promise<DestinationResponse> {
    return apiFetch<DestinationResponse>("/agent/destinations/start", {
      method: "POST",
      body: JSON.stringify({ trip_id: tripId }),
    });
  },

  // AI Weather Agent (Stage 6)
  async startWeatherAgent(tripId: string): Promise<WeatherResponse> {
    return apiFetch<WeatherResponse>("/agent/weather/start", {
      method: "POST",
      body: JSON.stringify({ trip_id: tripId }),
    });
  },

  // AI Itinerary Planning Agent (Stage 7)
  async startItineraryAgent(tripId: string): Promise<ItineraryResponse> {
    return apiFetch<ItineraryResponse>("/agent/itinerary/start", {
      method: "POST",
      body: JSON.stringify({ trip_id: tripId }),
    });
  },

  // AI Live Route & GPS Agent (Stage 8)
  async calculateRoute(
    tripId: string,
    origin: CoordinatePoint,
    destination: CoordinatePoint,
    transportMode: string = "driving"
  ): Promise<RouteResponse> {
    return apiFetch<RouteResponse>("/agent/routes/calculate", {
      method: "POST",
      body: JSON.stringify({
        trip_id: tripId,
        origin,
        destination,
        transport_mode: transportMode,
      }),
    });
  },

  // AI Crowd Monitoring & Overcrowding Agent (Stage 9)
  async startCrowdAgent(
    tripId: string,
    params: {
      destination?: string;
      people_count: number;
      capacity?: number;
      latitude?: number | null;
      longitude?: number | null;
      confidence?: number;
      source?: string;
    }
  ): Promise<CrowdResponse> {
    return apiFetch<CrowdResponse>("/agent/crowd/start", {
      method: "POST",
      body: JSON.stringify({
        trip_id: tripId,
        destination: params.destination,
        people_count: params.people_count,
        capacity: params.capacity || 100,
        latitude: params.latitude,
        longitude: params.longitude,
        confidence: params.confidence || 0.95,
        source: params.source || "simulated_detector",
      }),
    });
  },
};

