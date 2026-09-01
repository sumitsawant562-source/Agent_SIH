"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import { Trip } from "@/types/trip";
import { DestinationRecommendationItem, ItineraryData, ItineraryDay, WeatherResponseData } from "@/types/agent";
import {
  MapPin,
  Calendar,
  Clock,
  Users,
  Wallet,
  Car,
  Bike,
  Bus,
  Train,
  Plane,
  Sparkles,
  ArrowLeft,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Utensils,
  Home,
  Compass,
  Tag,
  Search,
  ChevronRight,
  Landmark,
  TreePine,
  Coffee,
  Gem,
  BedDouble,
  CloudSun,
  CloudRain,
  Sun,
  Wind,
  Droplets,
  Thermometer,
  Eye,
  Sunrise,
  Sunset,
  RefreshCw,
  Route,
  CalendarDays,
  UtensilsCrossed,
  AlertTriangle,
  Compass as CompassIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function TripDetailsPage() {
  return (
    <ProtectedRoute>
      <TripDetailsContent />
    </ProtectedRoute>
  );
}

function TripDetailsContent() {
  const params = useParams();
  const router = useRouter();
  const tripId = params?.id as string;

  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Stage 5 Destination Recommendations State
  const [recommendations, setRecommendations] = useState<DestinationRecommendationItem[]>([]);
  const [destLoading, setDestLoading] = useState(false);
  const [destError, setDestError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // Stage 6 Weather Intelligence State
  const [weatherData, setWeatherData] = useState<WeatherResponseData | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);

  // Stage 7 Itinerary Planning State
  const [itineraryData, setItineraryData] = useState<ItineraryData | null>(null);
  const [itineraryLoading, setItineraryLoading] = useState(false);
  const [itineraryError, setItineraryError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<number>(1);

  useEffect(() => {
    if (!tripId) return;

    async function loadTrip() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getTrip(tripId);
        setTrip(data);
      } catch (err: any) {
        console.error("Failed to fetch trip details:", err);
        setError(err.message || "Failed to load trip details.");
      } finally {
        setLoading(false);
      }
    }

    loadTrip();
  }, [tripId]);

  const handleFetchRecommendations = async () => {
    if (!tripId) return;
    setDestLoading(true);
    setDestError(null);
    try {
      const res = await api.startDestinationAgent(tripId);
      if (res && res.data && res.data.recommendations) {
        setRecommendations(res.data.recommendations);
      }
    } catch (err: any) {
      console.error("Failed to fetch destination recommendations:", err);
      setDestError(err.message || "Failed to generate destination recommendations.");
    } finally {
      setDestLoading(false);
    }
  };

  const handleFetchWeather = async () => {
    if (!tripId) return;
    setWeatherLoading(true);
    setWeatherError(null);
    try {
      const res = await api.startWeatherAgent(tripId);
      if (res && res.data) {
        setWeatherData(res.data);
        if (res.data.weather_status === "unavailable" && res.data.weather_errors.length > 0) {
          setWeatherError(res.data.weather_errors[0]);
        }
      }
    } catch (err: any) {
      console.error("Failed to fetch weather intelligence:", err);
      setWeatherError(err.message || "Failed to fetch live weather information.");
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleFetchItinerary = async () => {
    if (!tripId) return;
    setItineraryLoading(true);
    setItineraryError(null);
    try {
      const res = await api.startItineraryAgent(tripId);
      if (res && res.data && res.data.itinerary) {
        setItineraryData(res.data.itinerary);
        setSelectedDay(1);
      } else if (res && res.data && res.data.itinerary_errors.length > 0) {
        setItineraryError(res.data.itinerary_errors[0]);
      }
    } catch (err: any) {
      console.error("Failed to fetch itinerary:", err);
      setItineraryError(err.message || "Failed to synthesize day-by-day itinerary.");
    } finally {
      setItineraryLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!tripId) return;
    if (!confirm("Are you sure you want to delete this trip?")) return;

    setDeleting(true);
    try {
      await api.deleteTrip(tripId);
      router.push("/dashboard");
    } catch (err: any) {
      alert("Failed to delete trip: " + (err.message || "Unknown error"));
      setDeleting(false);
    }
  };

  const getTransportIcon = (mode: string) => {
    switch (mode) {
      case "flight":
        return <Plane className="h-4 w-4" />;
      case "train":
        return <Train className="h-4 w-4" />;
      case "bus":
        return <Bus className="h-4 w-4" />;
      case "bike":
        return <Bike className="h-4 w-4" />;
      case "car":
      default:
        return <Car className="h-4 w-4" />;
    }
  };

  const getCategoryBadgeClass = (category: string) => {
    switch (category) {
      case "famous_place":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      case "hidden_gem":
        return "bg-rose-500/10 text-rose-300 border-rose-500/20";
      case "nearby_place":
        return "bg-amber-500/10 text-amber-300 border-amber-500/20";
      case "food_dining":
        return "bg-orange-500/10 text-orange-300 border-orange-500/20";
      case "stay_area":
        return "bg-indigo-500/10 text-indigo-300 border-indigo-500/20";
      case "nature_adventure":
        return "bg-emerald-500/10 text-emerald-300 border-emerald-500/20";
      case "cultural_historical":
        return "bg-purple-500/10 text-purple-300 border-purple-500/20";
      case "family_friendly":
        return "bg-teal-500/10 text-teal-300 border-teal-500/20";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  const getCategoryLabel = (cat: string) => {
    switch (cat) {
      case "famous_place":
        return "Famous Landmark";
      case "hidden_gem":
        return "Hidden Gem";
      case "nearby_place":
        return "Nearby Excursion";
      case "food_dining":
        return "Food & Dining";
      case "stay_area":
        return "Stay Neighborhood";
      case "nature_adventure":
        return "Nature & Adventure";
      case "cultural_historical":
        return "Culture & Heritage";
      case "family_friendly":
        return "Family Friendly";
      default:
        return cat.replace(/_/g, " ");
    }
  };

  const filteredRecommendations = selectedCategory === "all"
    ? recommendations
    : recommendations.filter((r) => r.category === selectedCategory);

  const categories = [
    { id: "all", label: "All Categories" },
    { id: "famous_place", label: "Famous Places" },
    { id: "hidden_gem", label: "Hidden Gems" },
    { id: "nearby_place", label: "Nearby Getaways" },
    { id: "food_dining", label: "Food & Dining" },
    { id: "stay_area", label: "Stay Areas" },
    { id: "nature_adventure", label: "Nature & Adventure" },
    { id: "cultural_historical", label: "Culture & Heritage" },
    { id: "family_friendly", label: "Family Friendly" },
  ];

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex min-h-[50vh] flex-col items-center justify-center space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-teal-500/20 border-t-teal-400" />
          <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold animate-pulse">
            Loading Trip Details...
          </p>
        </div>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-16">
        <Card className="border-rose-500/30 bg-rose-500/10 text-center py-10 px-6">
          <AlertCircle className="mx-auto h-12 w-12 text-rose-400 mb-3" />
          <h2 className="text-xl font-bold text-white">Trip Not Found</h2>
          <p className="mt-2 text-sm text-rose-200/80">
            {error || "The requested trip does not exist or you do not have permission to view it."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/dashboard">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Dashboard
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <Link href="/dashboard">
          <Button variant="ghost" size="sm" className="gap-2 text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Dashboard</span>
          </Button>
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="danger"
            size="sm"
            onClick={handleDelete}
            isLoading={deleting}
            className="gap-2"
          >
            <Trash2 className="h-4 w-4" />
            <span>Delete Trip</span>
          </Button>
        </div>
      </div>

      {/* Header Title Section */}
      <div className="mt-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <Badge variant={trip.status as any}>
              {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
            </Badge>
            <span className="text-xs text-slate-500">
              Created {new Date(trip.created_at).toLocaleDateString()}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            {trip.title}
          </h1>
        </div>
      </div>

      {/* Route Highlight Banner */}
      <div className="mt-6 rounded-2xl border border-teal-500/20 bg-gradient-to-r from-teal-500/10 via-slate-900 to-emerald-500/10 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 text-white font-semibold text-lg">
          <div className="flex items-center gap-2 text-slate-300">
            <MapPin className="h-5 w-5 text-teal-400" />
            <span>{trip.starting_location}</span>
          </div>
          <span className="text-teal-400">→</span>
          <div className="flex items-center gap-2 text-teal-300">
            <MapPin className="h-5 w-5 text-emerald-400" />
            <span>{trip.destination}</span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs sm:text-sm text-slate-300">
          <div className="flex items-center gap-1.5 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <Calendar className="h-4 w-4 text-teal-400" />
            <span>{trip.travel_date}</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <Clock className="h-4 w-4 text-teal-400" />
            <span>{trip.duration_days} {trip.duration_days === 1 ? "Day" : "Days"}</span>
          </div>
        </div>
      </div>

      {/* Trip Details Grid */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Travel Party & Budget */}
        <Card className="border-slate-800 bg-slate-900/80">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-teal-400">
              <Users className="h-5 w-5" />
              <span>Travelers & Budget</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Adults</span>
              <span className="font-semibold text-white">{trip.adults || 1}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Children</span>
              <span className="font-semibold text-white">{trip.children || 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Total Budget</span>
              <span className="font-bold text-emerald-400">
                ${Number(trip.budget).toLocaleString()}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Transit & Preferences */}
        <Card className="border-slate-800 bg-slate-900/80">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-teal-400">
              <Compass className="h-5 w-5" />
              <span>Transit & Logistics</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Transport Mode</span>
              <span className="font-semibold text-white capitalize flex items-center gap-1.5">
                {getTransportIcon(trip.transport_mode)}
                {trip.transport_mode}
              </span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Food Preference</span>
              <span className="font-semibold text-white capitalize flex items-center gap-1.5">
                <Utensils className="h-3.5 w-3.5 text-slate-400" />
                {trip.food_preference}
              </span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Stay Type</span>
              <span className="font-semibold text-white capitalize flex items-center gap-1.5">
                <Home className="h-3.5 w-3.5 text-slate-400" />
                {trip.accommodation_preference}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Travel Style & Interests */}
        <Card className="border-slate-800 bg-slate-900/80">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-teal-400">
              <Sparkles className="h-5 w-5" />
              <span>Style & Interests</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Travel Pace</span>
              <span className="font-semibold text-white capitalize">{trip.travel_style}</span>
            </div>
            <div className="pt-1">
              <span className="text-slate-400 block mb-2 text-xs uppercase tracking-wider font-semibold">
                Interests & Themes
              </span>
              <div className="flex flex-wrap gap-1.5">
                {trip.interests && trip.interests.length > 0 ? (
                  trip.interests.map((interest, idx) => (
                    <span
                      key={idx}
                      className="text-xs font-medium text-teal-300 bg-teal-500/10 border border-teal-500/20 px-2.5 py-0.5 rounded-lg capitalize"
                    >
                      {interest}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500">General Leisure</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ========================================================================= */}
      {/* STAGE 5: DESTINATION INTELLIGENCE AGENT SECTION */}
      {/* ========================================================================= */}
      <div className="mt-12">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Sparkles className="h-3 w-3" />
                Stage 5 Agent
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Destination Intelligence & Recommendations
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              AI-curated places, hidden gems, culinary hotspots, and stay areas tailored for {trip.destination}.
            </p>
          </div>

          <Button
            onClick={handleFetchRecommendations}
            isLoading={destLoading}
            className="gap-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-slate-950 font-semibold shadow-lg shadow-teal-500/20"
          >
            <Sparkles className="h-4 w-4" />
            <span>{recommendations.length > 0 ? "Regenerate Recommendations" : "Analyze Destination"}</span>
          </Button>
        </div>

        {/* Error Alert */}
        {destError && (
          <div className="mt-4 p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-rose-400 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-rose-200">{destError}</div>
          </div>
        )}

        {/* Category Filter Pills */}
        {recommendations.length > 0 && (
          <div className="mt-6 flex flex-wrap gap-2">
            {categories.map((cat) => {
              const count = cat.id === "all"
                ? recommendations.length
                : recommendations.filter((r) => r.category === cat.id).length;
              if (count === 0 && cat.id !== "all") return null;

              const isSelected = selectedCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`text-xs px-3 py-1.5 rounded-xl font-medium transition-all flex items-center gap-1.5 border ${
                    isSelected
                      ? "bg-teal-500 text-slate-950 border-teal-400 shadow-md font-semibold"
                      : "bg-slate-900/80 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-white"
                  }`}
                >
                  <span>{cat.label}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? "bg-slate-950/20 text-slate-950" : "bg-slate-800 text-slate-400"}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Loading Spinner State */}
        {destLoading && (
          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-12 flex flex-col items-center justify-center space-y-4">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-teal-500/20 border-t-teal-400" />
            <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold animate-pulse">
              Destination Agent is analyzing {trip.destination}...
            </p>
          </div>
        )}

        {/* Empty State before Analysis */}
        {!destLoading && recommendations.length === 0 && !destError && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-10 text-center">
            <Compass className="mx-auto h-10 w-10 text-slate-600 mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">No Destination Recommendations Yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
              Click &quot;Analyze Destination&quot; above to run the Destination Intelligence Agent with Gemini AI and generate personalized recommendations.
            </p>
            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handleFetchRecommendations}
                className="gap-2 text-teal-400 border-teal-500/30 hover:bg-teal-500/10"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Start Destination Agent</span>
              </Button>
            </div>
          </div>
        )}

        {/* Recommendations Cards Grid */}
        {!destLoading && filteredRecommendations.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredRecommendations.map((item, idx) => (
              <Card
                key={idx}
                className="border-slate-800/80 bg-slate-900/90 hover:border-slate-700/80 transition-all shadow-lg flex flex-col justify-between"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-md border uppercase tracking-wider ${getCategoryBadgeClass(item.category)}`}>
                        {getCategoryLabel(item.category)}
                      </span>
                      <CardTitle className="text-lg font-bold text-white mt-2 leading-snug">
                        {item.name}
                      </CardTitle>
                    </div>
                    {item.confidence && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-teal-300 border border-slate-700 flex-shrink-0" title="Recommendation Confidence">
                        {Math.round(item.confidence * 100)}% match
                      </span>
                    )}
                  </div>
                  <CardDescription className="text-xs text-slate-300/90 mt-2 leading-relaxed">
                    {item.description}
                  </CardDescription>
                </CardHeader>

                <CardContent className="pt-0 space-y-3.5 text-xs">
                  {/* Why Recommended Reason */}
                  {item.why_recommended && (
                    <div className="rounded-xl bg-teal-500/5 border border-teal-500/15 p-2.5">
                      <div className="text-[10px] uppercase font-bold text-teal-400 tracking-wider mb-1 flex items-center gap-1">
                        <Sparkles className="h-3 w-3" />
                        Why Recommended
                      </div>
                      <p className="text-slate-300 leading-relaxed text-[11px]">
                        {item.why_recommended}
                      </p>
                    </div>
                  )}

                  {/* Metadata Chips (Cost, Duration, Best Time) */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-400">
                    {item.estimated_visit_duration && (
                      <div className="flex items-center gap-1.5 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
                        <Clock className="h-3.5 w-3.5 text-teal-400 flex-shrink-0" />
                        <span className="truncate">{item.estimated_visit_duration}</span>
                      </div>
                    )}
                    {item.estimated_cost !== null && item.estimated_cost !== undefined && (
                      <div className="flex items-center gap-1.5 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
                        <Wallet className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                        <span className="truncate font-semibold text-slate-200">
                          {item.estimated_cost === 0 ? "Free Entry" : `${item.currency || "₹"} ${item.estimated_cost}`}
                        </span>
                      </div>
                    )}
                    {item.best_time_to_visit && (
                      <div className="flex items-center gap-1.5 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80 col-span-2 sm:col-span-1">
                        <Calendar className="h-3.5 w-3.5 text-amber-400 flex-shrink-0" />
                        <span className="truncate">{item.best_time_to_visit}</span>
                      </div>
                    )}
                  </div>

                  {/* Distance info */}
                  {item.distance_from_destination && (
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                      <MapPin className="h-3.5 w-3.5 text-teal-400 flex-shrink-0" />
                      <span>{item.distance_from_destination}</span>
                    </div>
                  )}

                  {/* Tags */}
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/60">
                      {item.tags.map((tag, tIdx) => (
                        <span
                          key={tIdx}
                          className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-400 border border-slate-700/60"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* STAGE 6: WEATHER INTELLIGENCE AGENT SECTION */}
      {/* ========================================================================= */}
      <div className="mt-14">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <CloudSun className="h-3 w-3" />
                Stage 6 Agent
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Weather Intelligence & Climate Advisory
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Live meteorological observations, 5-day forecasts, and actionable itinerary insights powered by OpenWeatherMap.
            </p>
          </div>

          <Button
            onClick={handleFetchWeather}
            isLoading={weatherLoading}
            className="gap-2 bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-400 hover:to-teal-500 text-slate-950 font-semibold shadow-lg shadow-cyan-500/20"
          >
            <CloudSun className="h-4 w-4" />
            <span>{weatherData?.current_weather ? "Refresh Weather" : "Analyze Live Weather"}</span>
          </Button>
        </div>

        {/* Error Alert */}
        {weatherError && (
          <div className="mt-4 p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-rose-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-rose-200">
                <span className="font-semibold block mb-0.5">Weather Service Notice</span>
                {weatherError}
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleFetchWeather}
              className="text-xs text-rose-300 border-rose-500/30 hover:bg-rose-500/10"
            >
              Retry
            </Button>
          </div>
        )}

        {/* Loading Spinner */}
        {weatherLoading && (
          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-12 flex flex-col items-center justify-center space-y-4">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-cyan-500/20 border-t-cyan-400" />
            <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold animate-pulse">
              Fetching real-time atmospheric data for {trip.destination}...
            </p>
          </div>
        )}

        {/* Empty State before Analysis */}
        {!weatherLoading && !weatherData?.current_weather && !weatherError && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-10 text-center">
            <CloudSun className="mx-auto h-10 w-10 text-slate-600 mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">Live Weather Not Analyzed Yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
              Click &quot;Analyze Live Weather&quot; to fetch real-time weather metrics, multi-day forecasts, and climate precautions for {trip.destination}.
            </p>
            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handleFetchWeather}
                className="gap-2 text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/10"
              >
                <CloudSun className="h-3.5 w-3.5" />
                <span>Start Weather Agent</span>
              </Button>
            </div>
          </div>
        )}

        {/* Live Weather Content Display */}
        {!weatherLoading && weatherData?.current_weather && (
          <div className="mt-6 space-y-6">
            {/* Top Grid: Current Conditions Card + Key Atmosphere Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Primary Current Weather Card */}
              <Card className="lg:col-span-1 border-cyan-500/30 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 p-6 flex flex-col justify-between shadow-xl">
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-400 pb-3 border-b border-slate-800">
                    <span className="flex items-center gap-1.5 font-medium text-cyan-300">
                      <MapPin className="h-3.5 w-3.5" />
                      {weatherData.current_weather.location_name}
                    </span>
                    <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
                      {weatherData.current_weather.source}
                    </span>
                  </div>

                  <div className="mt-5 flex items-center justify-between">
                    <div>
                      <div className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
                        {Math.round(weatherData.current_weather.temperature)}°C
                      </div>
                      <p className="text-xs text-slate-400 mt-1">
                        Feels like {Math.round(weatherData.current_weather.feels_like)}°C
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-semibold">
                        <Sun className="h-4 w-4 text-amber-400" />
                        <span>{weatherData.current_weather.weather_condition}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1.5">
                        {weatherData.current_weather.weather_description}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <Droplets className="h-3.5 w-3.5 text-cyan-400" />
                    <span>Humidity: {weatherData.current_weather.humidity}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Wind className="h-3.5 w-3.5 text-teal-400" />
                    <span>Wind: {weatherData.current_weather.wind_speed} m/s</span>
                  </div>
                </div>
              </Card>

              {/* Atmospheric Metrics & Sun Times */}
              <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Rain Risk</span>
                    <CloudRain className="h-4 w-4 text-cyan-400" />
                  </div>
                  <div className="mt-3">
                    <div className="text-2xl font-bold text-white">
                      {Math.round(weatherData.current_weather.rain_probability * 100)}%
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {weatherData.current_weather.precipitation > 0 ? `${weatherData.current_weather.precipitation} mm recent` : "No current rain"}
                    </p>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Visibility</span>
                    <Eye className="h-4 w-4 text-teal-400" />
                  </div>
                  <div className="mt-3">
                    <div className="text-2xl font-bold text-white">
                      {(weatherData.current_weather.visibility / 1000).toFixed(1)} km
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {weatherData.current_weather.visibility >= 8000 ? "Clear Sightlines" : "Moderate Visibility"}
                    </p>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Sunrise</span>
                    <Sunrise className="h-4 w-4 text-amber-400" />
                  </div>
                  <div className="mt-3">
                    <div className="text-xl font-bold text-amber-200">
                      {weatherData.current_weather.sunrise || "--:--"}
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">Dawn Window</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Sunset</span>
                    <Sunset className="h-4 w-4 text-rose-400" />
                  </div>
                  <div className="mt-3">
                    <div className="text-xl font-bold text-rose-200">
                      {weatherData.current_weather.sunset || "--:--"}
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">Golden Hour</p>
                  </div>
                </div>

                {/* Weather Insights Highlights Banner */}
                {weatherData.insights && weatherData.insights.length > 0 && (
                  <div className="col-span-2 sm:col-span-4 rounded-2xl border border-teal-500/20 bg-teal-500/5 p-4 space-y-2.5">
                    <div className="text-xs uppercase font-bold text-teal-400 tracking-wider flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5" />
                      Meteorological Travel Advisories
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {weatherData.insights.map((insight, iIdx) => {
                        const alertStyle = insight.severity === "alert"
                          ? "border-rose-500/30 bg-rose-500/10 text-rose-200"
                          : insight.severity === "moderate"
                          ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                          : "border-teal-500/30 bg-slate-950/60 text-slate-300";
                        return (
                          <div key={iIdx} className={`p-3 rounded-xl border text-xs ${alertStyle}`}>
                            <div className="font-semibold text-white mb-1 flex items-center gap-1.5">
                              <span>{insight.title}</span>
                            </div>
                            <p className="text-[11px] leading-relaxed opacity-90">{insight.message}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Multi-Day Forecast Timeline */}
            {weatherData.forecast && weatherData.forecast.length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-cyan-400" />
                  <span>5-Day Weather Forecast Timeline</span>
                </h3>
                <div className="flex gap-3 overflow-x-auto pb-3 pt-1 scrollbar-thin scrollbar-thumb-slate-800">
                  {weatherData.forecast.map((f, fIdx) => (
                    <div
                      key={fIdx}
                      className="flex-shrink-0 w-36 rounded-2xl border border-slate-800/80 bg-slate-900/90 p-3.5 flex flex-col justify-between hover:border-slate-700 transition-all text-center"
                    >
                      <div>
                        <div className="text-[10px] font-semibold text-slate-400">
                          {f.date.slice(5)} {f.time ? `• ${f.time}` : ""}
                        </div>
                        <div className="text-lg font-bold text-white mt-1">
                          {Math.round(f.temperature)}°C
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                          {f.weather_description}
                        </div>
                      </div>

                      <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Droplets className="h-3 w-3 text-cyan-400" />
                          {f.humidity}%
                        </span>
                        {f.rain_probability > 0 ? (
                          <span className="text-cyan-300 font-semibold">
                            {Math.round(f.rain_probability * 100)}% rain
                          </span>
                        ) : (
                          <span className="text-emerald-400 font-medium">Dry</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* STAGE 7: ITINERARY PLANNING AGENT SECTION */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 mb-6">
            <div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-violet-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                  <Route className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>Day-by-Day Itinerary & Schedule</span>
                    <Badge variant="outline" className="border-violet-500/30 text-violet-400 bg-violet-500/10 text-xs">
                      Stage 7 AI Agent
                    </Badge>
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Personalized multi-day schedule adapted to real weather, budget, transit mode, and diet
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                onClick={handleFetchItinerary}
                disabled={itineraryLoading}
                className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium shadow-lg shadow-violet-600/20 transition-all gap-2"
              >
                {itineraryLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-white" />
                    <span>Synthesizing Itinerary...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 text-violet-200" />
                    <span>{itineraryData ? "Regenerate Itinerary" : "Generate Itinerary"}</span>
                  </>
                )}
              </Button>
            </div>
          </div>

          {itineraryError && (
            <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-rose-200">Itinerary Generation Notice</h4>
                <p className="text-xs text-rose-300 mt-0.5">{itineraryError}</p>
              </div>
            </div>
          )}

          {itineraryLoading && (
            <div className="py-12 flex flex-col items-center justify-center gap-4 text-center">
              <div className="h-12 w-12 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
              <div>
                <p className="text-sm font-semibold text-white">Synthesizing personalized daily schedules...</p>
                <p className="text-xs text-slate-400 mt-1">Cross-referencing attractions, weather forecast, and budget constraints</p>
              </div>
            </div>
          )}

          {!itineraryLoading && !itineraryData && !itineraryError && (
            <div className="py-12 flex flex-col items-center justify-center text-center max-w-md mx-auto">
              <div className="h-14 w-14 rounded-3xl bg-slate-800/60 border border-slate-700 flex items-center justify-center mb-4">
                <CalendarDays className="h-7 w-7 text-slate-400" />
              </div>
              <h3 className="text-base font-semibold text-white">Ready for Multi-Day Schedule Planning</h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Click <strong className="text-violet-300">&quot;Generate Itinerary&quot;</strong> to synthesize an intelligent day-by-day plan combining your travel preferences, Stage 5 recommendations, and Stage 6 live weather conditions.
              </p>
              <Button
                onClick={handleFetchItinerary}
                className="mt-5 bg-violet-600 hover:bg-violet-500 text-white text-xs gap-2 font-medium"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Generate Itinerary</span>
              </Button>
            </div>
          )}

          {!itineraryLoading && itineraryData && (
            <div className="space-y-6">
              {/* ITINERARY SUMMARY HEADER & BUDGET BAR */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
                  <div className="text-xs text-slate-400">Total Duration</div>
                  <div className="text-lg font-bold text-white mt-1">
                    {itineraryData.duration_days} Days
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {itineraryData.start_date} → {itineraryData.end_date}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
                  <div className="text-xs text-slate-400">Total Estimated Cost</div>
                  <div className="text-lg font-bold text-violet-400 mt-1">
                    {itineraryData.currency} {Math.round(itineraryData.total_estimated_cost).toLocaleString()}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Budget: {itineraryData.budget ? `${itineraryData.currency} ${Math.round(itineraryData.budget).toLocaleString()}` : "Not specified"}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between">
                  <div>
                    <div className="text-xs text-slate-400">Budget Status</div>
                    <div className="mt-1 flex items-center gap-2">
                      {itineraryData.budget_status === "within_budget" ? (
                        <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 text-xs">
                          Within Target Budget
                        </Badge>
                      ) : itineraryData.budget_status === "exceeds_budget" ? (
                        <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-xs">
                          Exceeds Stated Budget
                        </Badge>
                      ) : (
                        <Badge className="bg-slate-800 text-slate-300 text-xs">Budget Flexible</Badge>
                      )}
                    </div>
                  </div>
                  {itineraryData.budget_warning && (
                    <p className="text-[10px] text-amber-300/80 mt-1">{itineraryData.budget_warning}</p>
                  )}
                </div>
              </div>

              {itineraryData.weather_advisory && (
                <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-3.5 flex items-center gap-3 text-xs text-sky-200">
                  <CloudSun className="h-5 w-5 text-sky-400 flex-shrink-0" />
                  <span><strong>Meteorological Advisory:</strong> {itineraryData.weather_advisory}</span>
                </div>
              )}

              {/* DAY TABS */}
              <div className="flex gap-2 border-b border-slate-800 pb-3 overflow-x-auto scrollbar-thin scrollbar-thumb-slate-800">
                {itineraryData.days.map((day) => {
                  const isActive = selectedDay === day.day_number;
                  return (
                    <button
                      key={day.day_number}
                      onClick={() => setSelectedDay(day.day_number)}
                      className={`px-4 py-2.5 rounded-2xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                        isActive
                          ? "bg-violet-600 text-white shadow-lg shadow-violet-600/25"
                          : "bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800/80"
                      }`}
                    >
                      <Calendar className="h-3.5 w-3.5" />
                      <span>Day {day.day_number}</span>
                      <span className="text-[10px] opacity-75">({day.date.slice(5)})</span>
                    </button>
                  );
                })}
              </div>

              {/* ACTIVE DAY DETAILS */}
              {(() => {
                const day = itineraryData.days.find((d) => d.day_number === selectedDay) || itineraryData.days[0];
                if (!day) return null;

                return (
                  <div className="space-y-6 pt-2">
                    {/* Day Banner */}
                    <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-violet-400 uppercase tracking-wider">Day {day.day_number} • {day.date}</span>
                        </div>
                        <h3 className="text-base font-bold text-white mt-0.5">{day.theme}</h3>
                        {day.weather_summary && (
                          <p className="text-xs text-cyan-300/90 mt-1 flex items-center gap-1.5">
                            <CloudSun className="h-3.5 w-3.5 text-cyan-400" />
                            <span>{day.weather_summary}</span>
                          </p>
                        )}
                      </div>

                      <div className="text-right">
                        <div className="text-[11px] text-slate-400">Day Estimated Cost</div>
                        <div className="text-base font-bold text-emerald-400">
                          {itineraryData.currency} {Math.round(day.estimated_day_cost).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* Activities Timeline */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <Clock className="h-3.5 w-3.5 text-violet-400" />
                        <span>Scheduled Activities & Excursions</span>
                      </h4>

                      <div className="grid grid-cols-1 gap-3">
                        {day.activities.map((act, actIdx) => (
                          <div
                            key={actIdx}
                            className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-4 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-start justify-between gap-4"
                          >
                            <div className="space-y-1.5 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge className="bg-violet-500/20 text-violet-300 border-violet-500/30 text-[10px] uppercase font-bold">
                                  {act.time_slot}
                                </Badge>
                                <span className="text-xs font-semibold text-slate-300">
                                  {act.start_time} - {act.end_time}
                                </span>
                                <Badge variant="outline" className="border-slate-700 text-slate-400 text-[10px]">
                                  {act.visit_duration_minutes} min
                                </Badge>
                              </div>

                              <h5 className="text-sm font-bold text-white pt-1">{act.place_name}</h5>
                              <p className="text-xs text-slate-400 leading-relaxed">{act.description}</p>

                              {act.notes && (
                                <p className="text-[11px] text-violet-300/80 italic pt-1">
                                  💡 {act.notes}
                                </p>
                              )}
                            </div>

                            <div className="md:text-right flex-shrink-0">
                              <div className="text-[11px] text-slate-400">Estimated Cost</div>
                              <div className="text-sm font-bold text-slate-200">
                                {act.estimated_cost > 0
                                  ? `${act.currency} ${Math.round(act.estimated_cost)}`
                                  : "Free Entry"}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Food Recommendations */}
                    {day.food_recommendations && day.food_recommendations.length > 0 && (
                      <div className="space-y-3 pt-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                          <UtensilsCrossed className="h-3.5 w-3.5 text-amber-400" />
                          <span>Curated Dining & Food Recommendations</span>
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {day.food_recommendations.map((food, fIdx) => (
                            <div
                              key={fIdx}
                              className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-3.5 flex items-center justify-between gap-3"
                            >
                              <div>
                                <div className="flex items-center gap-2">
                                  <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px] uppercase font-bold">
                                    {food.meal}
                                  </Badge>
                                  {food.dietary_fit && (
                                    <span className="text-[10px] text-emerald-400 font-semibold">
                                      🌱 {food.dietary_fit}
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs font-bold text-white mt-1">{food.name}</div>
                                {food.cuisine_type && (
                                  <div className="text-[11px] text-slate-400">{food.cuisine_type}</div>
                                )}
                              </div>

                              <div className="text-right">
                                <div className="text-[10px] text-slate-400">Est. Meal Cost</div>
                                <div className="text-xs font-bold text-amber-300">
                                  {food.currency} {Math.round(food.estimated_cost)}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Day Notes */}
                    {day.notes && (
                      <div className="rounded-2xl border border-slate-800/60 bg-slate-950/40 p-3.5 text-xs text-slate-400 flex items-start gap-2.5">
                        <Compass className="h-4 w-4 text-violet-400 flex-shrink-0 mt-0.5" />
                        <span><strong>Day Advisory:</strong> {day.notes}</span>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}



