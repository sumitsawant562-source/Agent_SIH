"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import { Trip } from "@/types/trip";
import {
  AlternativePlaceItem,
  CoordinatePoint,
  CrowdData,
  DestinationRecommendationItem,
  ItineraryData,
  ItineraryDay,
  RouteData,
  WeatherResponseData,
} from "@/types/agent";
import { TripMap } from "@/components/TripMap";
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
  Navigation,
  Locate,
  LocateFixed,
  Radio,
  Footprints,
  Compass as CompassIcon,
  Activity,
  Gauge,
  ShieldAlert,
  Sliders,
  UserCheck,
  Hotel,
  Building2,
  ShieldCheck,
  CheckCircle,
  Info,
  X,
  ExternalLink,
  Layers,
  CircleDot,
  Check,
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

  // Stage 8 Live Route & GPS State
  const [gpsStatus, setGpsStatus] = useState<
    "GPS_IDLE" | "GPS_LOADING" | "GPS_ACTIVE" | "GPS_PERMISSION_DENIED" | "GPS_UNAVAILABLE" | "GPS_ERROR"
  >("GPS_IDLE");
  const [userLocation, setUserLocation] = useState<{
    latitude: number;
    longitude: number;
    accuracy?: number;
  } | null>(null);
  const [selectedDestination, setSelectedDestination] = useState<{
    latitude: number;
    longitude: number;
    name: string;
  } | null>(null);
  const [transportMode, setTransportMode] = useState<"driving" | "walking" | "cycling">("driving");
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [routeNotification, setRouteNotification] = useState<string | null>(null);

  // Stage 9 Crowd Monitoring State
  const [crowdData, setCrowdData] = useState<CrowdData | null>(null);
  const [crowdLoading, setCrowdLoading] = useState(false);
  const [crowdError, setCrowdError] = useState<string | null>(null);
  const [crowdPlaceInput, setCrowdPlaceInput] = useState<string>("");
  const [crowdCountInput, setCrowdCountInput] = useState<number>(45);
  const [crowdCapacityInput, setCrowdCapacityInput] = useState<number>(100);

  // Prototype Presentation & Booking State
  const [bookingModal, setBookingModal] = useState<{
    open: boolean;
    type: "railway" | "hotel";
    title: string;
    subtitle?: string;
    details?: any;
  } | null>(null);
  const [trainSearchOpen, setTrainSearchOpen] = useState(false);
  const [trainSearchLoading, setTrainSearchLoading] = useState(false);
  const [selectedHotelModal, setSelectedHotelModal] = useState<any | null>(null);

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

  // Stage 8 Geolocation & Route Handlers
  const handleEnableGPS = () => {
    if (typeof window === "undefined" || !("geolocation" in navigator)) {
      setGpsStatus("GPS_UNAVAILABLE");
      setRouteError("Geolocation is not supported by your current browser.");
      return;
    }

    setGpsStatus("GPS_LOADING");
    setRouteError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setGpsStatus("GPS_ACTIVE");
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          setGpsStatus("GPS_PERMISSION_DENIED");
          setRouteError("GPS Permission Denied. Please enable location access in browser settings.");
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          setGpsStatus("GPS_UNAVAILABLE");
          setRouteError("GPS position currently unavailable.");
        } else {
          setGpsStatus("GPS_ERROR");
          setRouteError(`GPS Error: ${err.message}`);
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  };

  const handleCalculateRoute = async (
    targetDestination?: { latitude: number; longitude: number; name: string },
    modeOverride?: "driving" | "walking" | "cycling"
  ) => {
    if (!tripId) return;

    if (!userLocation) {
      setRouteError("Please enable Live GPS first to calculate route from your current location.");
      handleEnableGPS();
      return;
    }

    const dest = targetDestination || selectedDestination;
    if (!dest || typeof dest.latitude !== "number" || typeof dest.longitude !== "number") {
      setRouteError("Please select a destination place with valid coordinates.");
      return;
    }

    const activeMode = modeOverride || transportMode;

    setRouteLoading(true);
    setRouteError(null);

    try {
      const res = await api.calculateRoute(
        tripId,
        { latitude: userLocation.latitude, longitude: userLocation.longitude },
        { latitude: dest.latitude, longitude: dest.longitude },
        activeMode
      );

      if (res && res.data) {
        setRouteData(res.data);
        if (res.data.route_status === "unavailable" && res.data.route_error) {
          setRouteError(res.data.route_error);
        }
      }
    } catch (err: any) {
      console.error("Failed to calculate route:", err);
      setRouteError(err.message || "Failed to calculate live transit route.");
    } finally {
      setRouteLoading(false);
    }
  };

  const handleNavigateToPlace = (place: { name: string; latitude?: number | null; longitude?: number | null }) => {
    if (typeof place.latitude !== "number" || typeof place.longitude !== "number") {
      setRouteNotification(`Route unavailable: '${place.name}' does not have geographic coordinates.`);
      setTimeout(() => setRouteNotification(null), 4000);
      return;
    }

    const destObj = {
      latitude: place.latitude,
      longitude: place.longitude,
      name: place.name,
    };

    setSelectedDestination(destObj);

    if (userLocation) {
      handleCalculateRoute(destObj);
    } else {
      handleEnableGPS();
    }

    const mapSection = document.getElementById("live-navigation-section");
    if (mapSection) {
      mapSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleEvaluateCrowd = async (
    overridePlace?: string,
    overrideCount?: number,
    overrideCapacity?: number
  ) => {
    if (!tripId) return;

    const targetPlace = (overridePlace || crowdPlaceInput || selectedDestination?.name || trip?.destination || "").trim();
    if (!targetPlace) {
      setCrowdError("Please enter or select a place/destination to monitor.");
      return;
    }

    const count = typeof overrideCount === "number" ? overrideCount : crowdCountInput;
    const capacity = typeof overrideCapacity === "number" ? overrideCapacity : crowdCapacityInput;

    // Determine target coordinates from selected place, recommendations, or trip
    let targetLat: number | null = null;
    let targetLon: number | null = null;

    if (selectedDestination && selectedDestination.name.toLowerCase() === targetPlace.toLowerCase()) {
      targetLat = selectedDestination.latitude;
      targetLon = selectedDestination.longitude;
    } else {
      const match = recommendations.find((r) => r.name.toLowerCase() === targetPlace.toLowerCase());
      if (match && typeof match.latitude === "number" && typeof match.longitude === "number") {
        targetLat = match.latitude;
        targetLon = match.longitude;
      } else if ((trip as any)?.destination_latitude && (trip as any)?.destination_longitude) {
        targetLat = (trip as any).destination_latitude;
        targetLon = (trip as any).destination_longitude;
      }
    }

    setCrowdLoading(true);
    setCrowdError(null);

    try {
      const res = await api.startCrowdAgent(tripId, {
        destination: targetPlace,
        people_count: count,
        capacity: capacity,
        latitude: targetLat,
        longitude: targetLon,
        confidence: 0.95,
        source: "simulated_detector",
      });

      if (res && res.data) {
        setCrowdData(res.data);
      }
    } catch (err: any) {
      console.error("Failed to evaluate crowd metrics:", err);
      setCrowdError(err.message || "Failed to evaluate crowd levels.");
    } finally {
      setCrowdLoading(false);
    }
  };

  const handleSearchTrains = () => {
    setTrainSearchLoading(true);
    setTimeout(() => {
      setTrainSearchLoading(false);
      setTrainSearchOpen(true);
    }, 400);
  };

  const handleOpenRailwayBooking = (trainInfo?: any) => {
    const fromCity = trip?.starting_location || "Mumbai";
    const toCity = trip?.destination || "Goa";
    setBookingModal({
      open: true,
      type: "railway",
      title: "Railway Booking Integration",
      subtitle: "Real-time railway availability and confirmed ticket booking will be provided through an authorized railway booking/API partner in the production version.",
      details: trainInfo || {
        name: "Vande Bharat Express (22229)",
        route: `${fromCity} → ${toCity}`,
        departure: "06:10 AM",
        arrival: "01:30 PM",
        duration: "7h 20m",
        fare: 1850,
        classType: "Executive Chair Car (EC)",
      },
    });
  };

  const handleOpenHotelBooking = (hotelInfo?: any) => {
    setBookingModal({
      open: true,
      type: "hotel",
      title: "Hotel Booking Integration",
      subtitle: "Real-time availability and booking will be connected through an authorized booking provider in the production version.",
      details: hotelInfo || {
        name: "Heritage Seaside Boutique Resort",
        location: trip?.destination || "Goa",
        price: 3400,
        type: "Boutique Resort & Spa",
        rating: 4.8,
      },
    });
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

                  {/* Distance & Navigate Button */}
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                    {item.distance_from_destination ? (
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                        <MapPin className="h-3.5 w-3.5 text-teal-400 flex-shrink-0" />
                        <span>{item.distance_from_destination}</span>
                      </div>
                    ) : (
                      <div />
                    )}

                    <Button
                      size="sm"
                      onClick={() => handleNavigateToPlace({
                        name: item.name,
                        latitude: item.latitude,
                        longitude: item.longitude,
                      })}
                      className="h-7 text-[11px] px-2.5 bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 gap-1 rounded-lg"
                    >
                      <Navigation className="h-3 w-3" />
                      <span>Navigate</span>
                    </Button>
                  </div>

                  {/* Tags */}
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
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
                    <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-violet-400 uppercase tracking-wider">
                            Day {day.day_number} • {day.date}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-white mt-1">{day.theme}</h3>
                        {day.summary && (
                          <p className="text-xs text-slate-300 mt-1 leading-relaxed max-w-2xl">{day.summary}</p>
                        )}
                        {(day.weather_summary || day.weather_note) && (
                          <p className="text-xs text-cyan-300/90 mt-2 flex items-center gap-1.5">
                            <CloudSun className="h-3.5 w-3.5 text-cyan-400 flex-shrink-0" />
                            <span>{day.weather_summary || day.weather_note}</span>
                          </p>
                        )}
                      </div>

                      <div className="text-right flex-shrink-0">
                        <div className="text-[11px] text-slate-400">Day Estimated Budget</div>
                        <div className="text-lg font-bold text-emerald-400 mt-0.5">
                          {itineraryData.currency} {Math.round(day.estimated_day_cost).toLocaleString()}
                        </div>
                        {itineraryData.cost_per_traveler && (
                          <div className="text-[10px] text-slate-500">
                            ~{itineraryData.currency} {Math.round(itineraryData.cost_per_traveler / (itineraryData.duration_days || 1)).toLocaleString()} / person
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Daily Budget Breakdown Pill Bar if present */}
                    {day.daily_budget && (
                      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-3.5">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                          <Wallet className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Daily Budget Allocation Breakdown</span>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                            <span className="text-[10px] text-slate-500 block">Food & Dining</span>
                            <span className="font-bold text-amber-300">
                              {itineraryData.currency} {Math.round(day.daily_budget.food || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                            <span className="text-[10px] text-slate-500 block">Local Transit</span>
                            <span className="font-bold text-blue-300">
                              {itineraryData.currency} {Math.round(day.daily_budget.transport || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                            <span className="text-[10px] text-slate-500 block">Activities & Entry</span>
                            <span className="font-bold text-violet-300">
                              {itineraryData.currency} {Math.round(day.daily_budget.activities || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                            <span className="text-[10px] text-slate-500 block">Miscellaneous</span>
                            <span className="font-bold text-slate-300">
                              {itineraryData.currency} {Math.round(day.daily_budget.miscellaneous || 0).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Activities Timeline */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <Clock className="h-3.5 w-3.5 text-violet-400" />
                        <span>Scheduled Activities & Excursions</span>
                      </h4>

                      <div className="grid grid-cols-1 gap-3.5">
                        {day.activities.map((act, actIdx) => (
                          <div
                            key={actIdx}
                            className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-4 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-start justify-between gap-4 shadow-sm"
                          >
                            <div className="space-y-2 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge className="bg-violet-500/20 text-violet-300 border-violet-500/30 text-[10px] uppercase font-bold">
                                  {act.time_slot}
                                </Badge>
                                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                                  <Clock className="h-3 w-3 text-slate-500" />
                                  {act.start_time} - {act.end_time}
                                </span>
                                <Badge variant="outline" className="border-slate-700 text-slate-400 text-[10px]">
                                  {act.visit_duration || `${act.visit_duration_minutes} min`}
                                </Badge>
                                {act.is_indoor !== undefined && act.is_indoor !== null && (
                                  <Badge variant="outline" className="border-slate-800 bg-slate-950/60 text-[10px] text-slate-400">
                                    {act.is_indoor ? "🏛️ Indoor" : "🌲 Outdoor"}
                                  </Badge>
                                )}
                                {act.transport_mode && act.travel_time_from_previous && (
                                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-teal-300 font-mono flex items-center gap-1">
                                    🚗 {act.travel_time_from_previous}
                                  </span>
                                )}
                              </div>

                              <div>
                                <h5 className="text-sm font-bold text-white">{act.place_name}</h5>
                                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                  {act.what_to_do || act.description}
                                </p>
                              </div>

                              {act.why_recommended && (
                                <div className="p-2.5 rounded-xl bg-violet-500/5 border border-violet-500/15 text-[11px] text-violet-200 leading-relaxed flex items-start gap-2">
                                  <Sparkles className="h-3.5 w-3.5 text-violet-400 flex-shrink-0 mt-0.5" />
                                  <div>
                                    <strong className="text-violet-300">Why Recommended:</strong> {act.why_recommended}
                                  </div>
                                </div>
                              )}

                              <div className="flex flex-wrap gap-2 pt-1 text-[11px] text-slate-400">
                                {act.weather_suitability && (
                                  <span className="flex items-center gap-1 text-cyan-300/90 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-md">
                                    <Sun className="h-3 w-3 text-amber-400" />
                                    {act.weather_suitability}
                                  </span>
                                )}
                                {act.practical_tips && (
                                  <span className="flex items-center gap-1 text-slate-300 bg-slate-950/60 border border-slate-800 px-2 py-0.5 rounded-md">
                                    💡 {act.practical_tips}
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="md:text-right flex-shrink-0 flex md:flex-col items-center md:items-end justify-between gap-2">
                              <div>
                                <div className="text-[11px] text-slate-400">Estimated Cost</div>
                                <div className="text-sm font-bold text-slate-200">
                                  {act.estimated_cost > 0
                                    ? `${act.currency} ${Math.round(act.estimated_cost)}`
                                    : "Free Entry"}
                                </div>
                              </div>

                              <Button
                                size="sm"
                                onClick={() => {
                                  // Look up matching recommendation with coordinates
                                  const match = recommendations.find(
                                    (r) => r.name.toLowerCase().includes(act.place_name.toLowerCase()) ||
                                           act.place_name.toLowerCase().includes(r.name.toLowerCase())
                                  );
                                  handleNavigateToPlace({
                                    name: act.place_name,
                                    latitude: match?.latitude,
                                    longitude: match?.longitude,
                                  });
                                }}
                                className="h-7 text-[11px] px-2.5 bg-violet-600/20 hover:bg-violet-600 text-violet-300 hover:text-white border border-violet-500/30 gap-1 rounded-lg"
                              >
                                <Navigation className="h-3 w-3" />
                                <span>Navigate</span>
                              </Button>
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
                              className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-3.5 flex flex-col justify-between gap-2"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <div className="flex flex-wrap items-center gap-2">
                                    <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px] uppercase font-bold">
                                      {food.meal}
                                    </Badge>
                                    {food.dietary_fit && (
                                      <span className="text-[10px] text-emerald-400 font-semibold">
                                        🌱 {food.dietary_fit}
                                      </span>
                                    )}
                                    {food.suggested_time && (
                                      <span className="text-[10px] text-slate-500 font-mono">
                                        ⏰ {food.suggested_time}
                                      </span>
                                    )}
                                  </div>
                                  <div className="text-xs font-bold text-white mt-1.5">{food.name}</div>
                                  {food.restaurant_type && (
                                    <div className="text-[10px] text-slate-400">{food.restaurant_type}</div>
                                  )}
                                  {food.cuisine_type && (
                                    <div className="text-[11px] text-slate-300 mt-0.5">{food.cuisine_type}</div>
                                  )}
                                </div>

                                <div className="text-right flex-shrink-0">
                                  <div className="text-[10px] text-slate-400">Est. Cost</div>
                                  <div className="text-xs font-bold text-amber-300">
                                    {food.currency} {Math.round(food.estimated_cost)}
                                  </div>
                                </div>
                              </div>

                              {food.local_specialty && (
                                <div className="pt-2 border-t border-slate-800/60 text-[11px] text-amber-200/90 flex items-center gap-1.5">
                                  <Utensils className="h-3 w-3 text-amber-400 flex-shrink-0" />
                                  <span><strong>Must Try:</strong> {food.local_specialty}</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Day Logistics Tips */}
                    {day.travel_tips && day.travel_tips.length > 0 && (
                      <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-3.5 space-y-1.5">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-teal-400 flex items-center gap-1.5">
                          <Compass className="h-3.5 w-3.5 text-teal-400" />
                          <span>Day Logistics & Transit Advice</span>
                        </div>
                        <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                          {day.travel_tips.map((tip, tIdx) => (
                            <li key={tIdx}>{tip}</li>
                          ))}
                        </ul>
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

              {/* OVERALL TIPS & PACKING SUGGESTIONS */}
              {((itineraryData.overall_tips && itineraryData.overall_tips.length > 0) ||
                (itineraryData.packing_suggestions && itineraryData.packing_suggestions.length > 0)) && (
                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                  {itineraryData.overall_tips && itineraryData.overall_tips.length > 0 && (
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                      <h4 className="text-xs font-bold text-violet-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>Expert Trip Tips & Advice</span>
                      </h4>
                      <ul className="list-disc list-inside text-xs text-slate-300 space-y-1.5">
                        {itineraryData.overall_tips.map((tip, idx) => (
                          <li key={idx} className="leading-relaxed">{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {itineraryData.packing_suggestions && itineraryData.packing_suggestions.length > 0 && (
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                      <h4 className="text-xs font-bold text-teal-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <CheckCircle className="h-3.5 w-3.5" />
                        <span>Personalized Packing Checklist</span>
                      </h4>
                      <ul className="list-disc list-inside text-xs text-slate-300 space-y-1.5">
                        {itineraryData.packing_suggestions.map((item, idx) => (
                          <li key={idx} className="leading-relaxed">{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* PART 7: AGENTIC AI TRAVEL DECISION SYNTHESIS CENTER */}
        <div id="ai-travel-decision-section" className="rounded-3xl border border-violet-500/30 bg-gradient-to-br from-slate-900/90 via-violet-950/20 to-slate-900/90 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5 mb-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>AI Travel Decision Center</span>
                  <Badge variant="outline" className="border-violet-500/40 text-violet-300 bg-violet-500/10 text-xs">
                    Multi-Agent Synthesis
                  </Badge>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Autonomous coordination across Requirement, Destination, Weather, Itinerary, GPS, and Crowd Agents
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-xs text-violet-200">
              <CircleDot className="h-3 w-3 text-violet-400 animate-pulse" />
              <span className="font-semibold">Autonomous Coordination</span>
            </div>
          </div>

          {/* Active Agents Status Checklist */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 mb-5">
            <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
              <div className="truncate">
                <div className="text-[10px] uppercase font-bold text-slate-400">Requirements</div>
                <div className="text-xs font-semibold text-white truncate">Profile Ready</div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <CheckCircle className={`h-3.5 w-3.5 ${recommendations.length > 0 ? "text-emerald-400" : "text-slate-600"} flex-shrink-0`} />
              <div className="truncate">
                <div className="text-[10px] uppercase font-bold text-slate-400">Destinations</div>
                <div className="text-xs font-semibold text-white truncate">
                  {recommendations.length > 0 ? `${recommendations.length} Evaluated` : "Not evaluated yet"}
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <CheckCircle className={`h-3.5 w-3.5 ${weatherData?.current_weather ? "text-emerald-400" : "text-slate-600"} flex-shrink-0`} />
              <div className="truncate">
                <div className="text-[10px] uppercase font-bold text-slate-400">Weather</div>
                <div className="text-xs font-semibold text-white truncate">
                  {weatherData?.current_weather ? `${weatherData.current_weather.temperature}°C · ${weatherData.current_weather.weather_condition}` : "Not evaluated yet"}
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <CheckCircle className={`h-3.5 w-3.5 ${itineraryData?.days?.length ? "text-emerald-400" : "text-slate-600"} flex-shrink-0`} />
              <div className="truncate">
                <div className="text-[10px] uppercase font-bold text-slate-400">Itinerary</div>
                <div className="text-xs font-semibold text-white truncate">
                  {itineraryData?.days?.length ? `${itineraryData.days.length} Days Planned` : "Not evaluated yet"}
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <CheckCircle className={`h-3.5 w-3.5 ${userLocation ? "text-emerald-400" : "text-slate-600"} flex-shrink-0`} />
              <div className="truncate">
                <div className="text-[10px] uppercase font-bold text-slate-400">Live GPS</div>
                <div className="text-xs font-semibold text-white truncate">
                  {userLocation ? "Active Tracking" : "Standby"}
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <CheckCircle className={`h-3.5 w-3.5 ${crowdData ? "text-emerald-400" : "text-slate-600"} flex-shrink-0`} />
              <div className="truncate">
                <div className="text-[10px] uppercase font-bold text-slate-400">Crowd Agent</div>
                <div className="text-xs font-semibold text-white truncate">
                  {crowdData ? `${crowdData.crowd_level.replace(/_/g, " ")} (${crowdData.crowd_percentage}%)` : "Not evaluated yet"}
                </div>
              </div>
            </div>
          </div>

          {/* Unified AI Decision Callout */}
          <div className="rounded-2xl border border-violet-500/40 bg-violet-950/30 p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-violet-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="text-[11px] font-bold text-violet-300 uppercase tracking-wider">Current AI Travel Decision</span>
                <p className="text-xs text-slate-200 mt-1 leading-relaxed">
                  {crowdData?.is_overcrowded ? (
                    <>
                      Selected destination <strong className="text-white">{crowdData.destination}</strong> is currently crowded ({crowdData.crowd_percentage}% occupancy). A nearby alternative with lower crowd density {crowdData.alternative_places?.[0] ? <strong className="text-cyan-300">"{crowdData.alternative_places[0].name}"</strong> : "nearby"} and suitable weather has been recommended.
                    </>
                  ) : crowdData ? (
                    <>
                      Venue <strong className="text-white">{crowdData.destination}</strong> is operating within normal safety thresholds ({crowdData.crowd_percentage}% occupancy). Proceeding with scheduled itinerary.
                    </>
                  ) : (
                    <>
                      Multi-agent coordination active. Run Crowd Intelligence or Route calculation below to evaluate destination density and calculate optimal navigation paths.
                    </>
                  )}
                </p>
              </div>
            </div>

            {crowdData?.is_overcrowded && crowdData.alternative_places?.[0] && (
              <Button
                size="sm"
                onClick={() => handleNavigateToPlace(crowdData.alternative_places[0])}
                className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-xs font-semibold whitespace-nowrap shadow-md shadow-violet-600/20"
              >
                <Navigation className="h-3.5 w-3.5 mr-1.5" />
                Navigate to Alternative
              </Button>
            )}
          </div>
        </div>

        {/* STAGE 9: CROWD MONITORING & OVERCROWDING AGENT SECTION (PARTS 4 & 5 & 9) */}
        <div id="crowd-monitoring-section" className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 mb-6">
            <div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center shadow-lg shadow-rose-500/20">
                  <Activity className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>Crowd Intelligence & Overcrowding Agent</span>
                    <Badge variant="outline" className="border-rose-500/30 text-rose-400 bg-rose-500/10 text-xs">
                      Stage 9 Agent
                    </Badge>
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Deterministic capacity calculations, safety thresholds, and intelligent alternative rerouting
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Status Pill */}
            {crowdData && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-800 bg-slate-950/70 text-xs">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    crowdData.is_overcrowded
                      ? "bg-rose-500 animate-ping"
                      : crowdData.crowd_level === "HIGH"
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                  }`}
                />
                <span className="text-slate-300 font-semibold">
                  {crowdData.destination}: {crowdData.crowd_level.replace(/_/g, " ")} ({crowdData.crowd_percentage}%)
                </span>
              </div>
            )}
          </div>

          {/* Transparent Source Architecture Label (Part 4 & 5) */}
          <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3.5 mb-5 flex items-start gap-2.5 text-xs text-slate-400">
            <Info className="h-4 w-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong className="text-slate-300">Crowd data source:</strong> Prototype/sensor-ready input. Production version can integrate authorized camera feeds, public crowd data, venue occupancy data, anonymous density signals, or user reports.
            </p>
          </div>

          {/* Crowd Error Callout */}
          {crowdError && (
            <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 mb-5 flex items-start gap-3 text-xs">
              <AlertCircle className="h-4 w-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-rose-200">Crowd Monitoring Notice:</strong>
                <p className="text-rose-300 mt-0.5">{crowdError}</p>
              </div>
            </div>
          )}

          {/* Controls Bar: Place selector & Detection Simulator */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
            {/* Target Place Input */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-400">Target Venue / Place</span>
                <input
                  type="text"
                  placeholder={selectedDestination?.name || trip?.destination || "Enter place name (e.g. Baga Beach)"}
                  value={crowdPlaceInput}
                  onChange={(e) => setCrowdPlaceInput(e.target.value)}
                  className="w-full mt-2 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
                />
              </div>
              <div className="flex items-center gap-1.5 mt-2 overflow-x-auto pb-1 text-[10px] text-slate-400">
                <span>Quick pick:</span>
                {recommendations.slice(0, 3).map((r, rIdx) => (
                  <button
                    key={rIdx}
                    onClick={() => setCrowdPlaceInput(r.name)}
                    className="truncate max-w-[110px] px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    {r.name}
                  </button>
                ))}
              </div>
            </div>

            {/* People Count & Presets (Part 9 Demo Crowd Input) */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-semibold text-slate-400">Demo Crowd Input</span>
                  <Badge className="bg-slate-800 border-slate-700 text-[9px] text-slate-400">Simulated / Sensor</Badge>
                </div>
                <span className="text-xs font-bold text-white">{crowdCountInput} people</span>
              </div>
              <div className="grid grid-cols-4 gap-1.5 mt-2">
                <button
                  onClick={() => setCrowdCountInput(25)}
                  className={`py-1 rounded-lg text-[10px] font-semibold border transition-all ${
                    crowdCountInput === 25
                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Low (25)
                </button>
                <button
                  onClick={() => setCrowdCountInput(55)}
                  className={`py-1 rounded-lg text-[10px] font-semibold border transition-all ${
                    crowdCountInput === 55
                      ? "bg-blue-500/20 border-blue-500 text-blue-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Med (55)
                </button>
                <button
                  onClick={() => setCrowdCountInput(78)}
                  className={`py-1 rounded-lg text-[10px] font-semibold border transition-all ${
                    crowdCountInput === 78
                      ? "bg-amber-500/20 border-amber-500 text-amber-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  High (78)
                </button>
                <button
                  onClick={() => setCrowdCountInput(135)}
                  className={`py-1 rounded-lg text-[10px] font-semibold border transition-all ${
                    crowdCountInput === 135
                      ? "bg-rose-500/20 border-rose-500 text-rose-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Over (135)
                </button>
              </div>
            </div>

            {/* Action Trigger */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-400">Venue Capacity Limit</span>
                <div className="text-xs text-slate-300 mt-1 font-semibold">{crowdCapacityInput} Persons</div>
              </div>
              <Button
                onClick={() => handleEvaluateCrowd()}
                disabled={crowdLoading}
                className="w-full bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white text-xs font-semibold gap-1.5 shadow-md shadow-rose-600/20 mt-2"
              >
                {crowdLoading ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Evaluating Crowd...</span>
                  </>
                ) : (
                  <>
                    <Gauge className="h-3.5 w-3.5" />
                    <span>Evaluate Crowd Level</span>
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Crowd Results Section */}
          {crowdData && (
            <div className="space-y-5">
              {/* Metrics Header Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Crowd Level</span>
                  <div className="mt-1">
                    <Badge
                      className={`text-xs font-bold ${
                        crowdData.crowd_level === "LOW"
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                          : crowdData.crowd_level === "MODERATE"
                          ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                          : crowdData.crowd_level === "HIGH"
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                          : "bg-rose-500/20 text-rose-300 border-rose-500/30"
                      }`}
                    >
                      {crowdData.crowd_level.replace(/_/g, " ")}
                    </Badge>
                  </div>
                </div>

                <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Occupancy</span>
                  <div className="text-lg font-bold text-white mt-0.5">
                    {crowdData.people_count} / {crowdData.capacity}
                  </div>
                  <div className="text-[10px] text-slate-400">({crowdData.crowd_percentage}%)</div>
                </div>

                <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Safety Status</span>
                  <div className="text-base font-bold text-white mt-0.5 flex items-center gap-1.5">
                    {crowdData.is_overcrowded ? (
                      <span className="text-rose-400 flex items-center gap-1">
                        <ShieldAlert className="h-4 w-4" /> Overcrowded
                      </span>
                    ) : (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <UserCheck className="h-4 w-4" /> {crowdData.crowd_status}
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/60">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Confidence</span>
                  <div className="text-base font-bold text-white mt-0.5">
                    {Math.round(crowdData.crowd_confidence * 100)}%
                  </div>
                  <div className="text-[10px] text-slate-500 capitalize">{crowdData.source?.replace(/_/g, " ")}</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="p-4 rounded-2xl border border-slate-800/80 bg-slate-950/60">
                <div className="flex justify-between items-center text-xs mb-1.5">
                  <span className="text-slate-400 font-medium">Capacity Utilization</span>
                  <span
                    className={`font-bold ${
                      crowdData.crowd_percentage > 100
                        ? "text-rose-400"
                        : crowdData.crowd_percentage > 70
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {crowdData.crowd_percentage}%
                  </span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      crowdData.crowd_percentage > 100
                        ? "bg-rose-500"
                        : crowdData.crowd_percentage > 70
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(crowdData.crowd_percentage, 100)}%` }}
                  />
                </div>
              </div>

              {/* Overcrowding Recommendation Banner */}
              <div
                className={`p-5 rounded-2xl border ${
                  crowdData.is_overcrowded
                    ? "border-rose-500/40 bg-rose-950/20 text-rose-200"
                    : "border-emerald-500/30 bg-emerald-950/20 text-emerald-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  {crowdData.is_overcrowded ? (
                    <AlertTriangle className="h-5 w-5 text-rose-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h3 className="font-bold text-sm text-white flex items-center gap-2">
                      <span>Recommendation: {crowdData.recommendation}</span>
                      {crowdData.is_overcrowded && (
                        <Badge className="bg-rose-500 text-white font-bold text-[10px]">Overcrowding Alert</Badge>
                      )}
                    </h3>
                    <p className="text-xs mt-1 leading-relaxed text-slate-300">
                      {crowdData.ai_explanation ||
                        `${crowdData.destination} is at ${crowdData.crowd_percentage}% capacity. ${crowdData.recommendation}.`}
                    </p>
                  </div>
                </div>
              </div>

              {/* Recommended Alternatives Carousel / Cards */}
              {crowdData.alternative_places && crowdData.alternative_places.length > 0 && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-amber-400" />
                      <span>Recommended Alternative Destinations</span>
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      Lower density alternatives nearby
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {crowdData.alternative_places.map((alt, aIdx) => (
                      <div
                        key={aIdx}
                        className="rounded-2xl border border-slate-800/90 bg-slate-950/70 p-4 flex flex-col justify-between gap-3 hover:border-slate-700 transition-all shadow-md"
                      >
                        <div>
                          <div className="flex items-center justify-between gap-2">
                            <h5 className="text-xs font-bold text-white truncate">{alt.name}</h5>
                            <Badge className={getCategoryBadgeClass(alt.category) + " text-[10px]"}>
                              {getCategoryLabel(alt.category)}
                            </Badge>
                          </div>

                          <p className="text-[11px] text-slate-300 mt-2 line-clamp-2 leading-relaxed">
                            {alt.why_recommended || alt.description}
                          </p>

                          <div className="flex flex-wrap items-center gap-2 mt-3 text-[10px] text-slate-400">
                            {alt.distance_km !== null && alt.distance_km !== undefined && (
                              <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-300 font-medium">
                                📍 {alt.distance_km} km away
                              </span>
                            )}
                            {alt.estimated_visit_duration && (
                              <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                                ⏱️ {alt.estimated_visit_duration}
                              </span>
                            )}
                            {alt.weather_suitability && (
                              <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-emerald-300 font-medium">
                                ⛅ {alt.weather_suitability}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end">
                          <Button
                            size="sm"
                            onClick={() => handleNavigateToPlace(alt)}
                            className="bg-blue-600 hover:bg-blue-500 text-white text-[11px] py-1 px-3 gap-1.5 shadow-sm"
                          >
                            <Navigation className="h-3 w-3" />
                            <span>Navigate Here</span>
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* STAGE 8: LIVE ROUTE & GPS AGENT SECTION */}
        <div id="live-navigation-section" className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 mb-6">
            <div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <Navigation className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>Live Route & GPS Navigation</span>
                    <Badge variant="outline" className="border-blue-500/30 text-blue-400 bg-blue-500/10 text-xs">
                      Stage 8 Agent
                    </Badge>
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Real-time browser GPS tracking and turn-by-turn routing to your itinerary destinations
                  </p>
                </div>
              </div>
            </div>

            {/* GPS Status & Actions */}
            <div className="flex flex-wrap items-center gap-3">
              {/* GPS Status Pill */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-800 bg-slate-950/70 text-xs">
                <Radio
                  className={`h-3.5 w-3.5 ${
                    gpsStatus === "GPS_ACTIVE"
                      ? "text-emerald-400 animate-pulse"
                      : gpsStatus === "GPS_LOADING"
                      ? "text-amber-400 animate-spin"
                      : "text-slate-500"
                  }`}
                />
                <span className="text-slate-300 font-medium">
                  {gpsStatus === "GPS_ACTIVE"
                    ? `GPS Active (${userLocation?.latitude.toFixed(3)}, ${userLocation?.longitude.toFixed(3)})`
                    : gpsStatus === "GPS_LOADING"
                    ? "Acquiring GPS Signal..."
                    : gpsStatus === "GPS_PERMISSION_DENIED"
                    ? "GPS Permission Denied"
                    : "GPS Standby"}
                </span>
              </div>

              <Button
                onClick={handleEnableGPS}
                variant="outline"
                className="border-slate-700 text-slate-300 hover:bg-slate-800 text-xs gap-1.5"
              >
                <LocateFixed className="h-3.5 w-3.5 text-blue-400" />
                <span>{gpsStatus === "GPS_ACTIVE" ? "Refresh GPS" : "Enable Live GPS"}</span>
              </Button>
            </div>
          </div>

          {/* Route Notification / Error Callouts */}
          {routeNotification && (
            <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-3.5 mb-5 flex items-center gap-2.5 text-xs text-amber-200">
              <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0" />
              <span>{routeNotification}</span>
            </div>
          )}

          {routeError && (
            <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 mb-5 flex items-start gap-3 text-xs">
              <AlertCircle className="h-4 w-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-rose-200">Routing / GPS Notice:</strong>
                <p className="text-rose-300 mt-0.5">{routeError}</p>
              </div>
            </div>
          )}

          {/* Controls Bar: Transport Mode & Destination Selector */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Mode Selector */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-3.5 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-400">Transport Mode</span>
              <div className="flex gap-1.5 mt-2">
                <button
                  onClick={() => {
                    setTransportMode("driving");
                    if (selectedDestination) handleCalculateRoute(selectedDestination, "driving");
                  }}
                  className={`flex-1 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    transportMode === "driving"
                      ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                      : "bg-slate-900 text-slate-400 hover:text-white"
                  }`}
                >
                  <Car className="h-3.5 w-3.5" />
                  <span>Drive</span>
                </button>

                <button
                  onClick={() => {
                    setTransportMode("walking");
                    if (selectedDestination) handleCalculateRoute(selectedDestination, "walking");
                  }}
                  className={`flex-1 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    transportMode === "walking"
                      ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                      : "bg-slate-900 text-slate-400 hover:text-white"
                  }`}
                >
                  <Footprints className="h-3.5 w-3.5" />
                  <span>Walk</span>
                </button>

                <button
                  onClick={() => {
                    setTransportMode("cycling");
                    if (selectedDestination) handleCalculateRoute(selectedDestination, "cycling");
                  }}
                  className={`flex-1 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    transportMode === "cycling"
                      ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                      : "bg-slate-900 text-slate-400 hover:text-white"
                  }`}
                >
                  <Bike className="h-3.5 w-3.5" />
                  <span>Cycle</span>
                </button>
              </div>
            </div>

            {/* Target Destination Pill */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-3.5 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-400">Target Destination</span>
              <div className="flex items-center justify-between gap-2 mt-1">
                <div className="truncate">
                  <div className="text-xs font-bold text-white truncate">
                    {selectedDestination?.name || "No Destination Selected"}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {selectedDestination
                      ? `${selectedDestination.latitude.toFixed(4)}, ${selectedDestination.longitude.toFixed(4)}`
                      : "Click 'Navigate' on any place card"}
                  </div>
                </div>
                {selectedDestination && (
                  <Badge className="bg-violet-500/20 text-violet-300 border-violet-500/30 text-[10px]">
                    Selected
                  </Badge>
                )}
              </div>
            </div>

            {/* Route Trigger Action */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-3.5 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-400">Live Navigation</span>
                <div className="text-xs text-slate-300 mt-0.5">Calculate shortest path</div>
              </div>
              <Button
                onClick={() => handleCalculateRoute()}
                disabled={routeLoading || !selectedDestination}
                className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium gap-1.5 shadow-md shadow-blue-600/20"
              >
                {routeLoading ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Routing...</span>
                  </>
                ) : (
                  <>
                    <Navigation className="h-3.5 w-3.5" />
                    <span>Calculate Route</span>
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Active Route Summary Metrics */}
          {routeData && routeData.route_status === "ready" && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6 p-4 rounded-2xl border border-blue-500/30 bg-blue-500/10">
              <div>
                <div className="text-[10px] uppercase font-bold text-blue-300">Route Distance</div>
                <div className="text-lg font-bold text-white mt-0.5">{routeData.distance_km} km</div>
              </div>
              <div>
                <div className="text-[10px] uppercase font-bold text-blue-300">Estimated Duration</div>
                <div className="text-lg font-bold text-white mt-0.5">{routeData.duration_minutes} mins</div>
              </div>
              <div className="sm:text-right">
                <div className="text-[10px] uppercase font-bold text-blue-300">Transit Mode</div>
                <Badge className="mt-1 bg-blue-600 text-white font-semibold text-xs uppercase">
                  {routeData.transport_mode}
                </Badge>
              </div>
            </div>
          )}

          {/* Interactive Map Component */}
          <TripMap
            userLocation={userLocation}
            destinationLocation={selectedDestination}
            routeGeometry={routeData?.geometry}
            places={recommendations.filter(
              (r) => typeof r.latitude === "number" && typeof r.longitude === "number"
            ).map((r) => ({
              name: r.name,
              latitude: r.latitude!,
              longitude: r.longitude!,
              category: r.category,
            }))}
            onSelectDestination={(p) => {
              setSelectedDestination(p);
              if (userLocation) {
                handleCalculateRoute(p);
              }
            }}
            className="h-[420px] w-full rounded-2xl border border-slate-800 shadow-inner"
          />
        </div>

        {/* SMART TRAIN BOOKING SECTION (PART 1 & PART 2) */}
        <div id="smart-train-booking-section" className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 mb-6">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Train className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>Smart Train Booking</span>
                  <Badge variant="outline" className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10 text-xs">
                    Integration Ready · Prototype UI
                  </Badge>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Route transit intelligence and railway booking partner integration interface
                </p>
              </div>
            </div>

            <Badge className="bg-slate-800 text-slate-300 border-slate-700 text-xs">
              Prototype / Demo Data
            </Badge>
          </div>

          {/* Route & Passenger Context Header */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6 p-4 rounded-2xl border border-slate-800/80 bg-slate-950/60">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">From</span>
              <div className="text-xs font-bold text-white mt-0.5">{trip.starting_location || "Mumbai (CSMT)"}</div>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">To</span>
              <div className="text-xs font-bold text-white mt-0.5">{trip.destination || "Goa (MAO)"}</div>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Travel Date</span>
              <div className="text-xs font-bold text-white mt-0.5">
                {trip.travel_date ? new Date(trip.travel_date).toLocaleDateString() : "Flexible / Scheduled"}
              </div>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Passengers</span>
              <div className="text-xs font-bold text-white mt-0.5">
                {trip.adults} Adults{trip.children ? `, ${trip.children} Child` : ""}
              </div>
            </div>
          </div>

          {/* Recommended Train Showcase Card */}
          <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-slate-950/60 to-blue-950/20 p-5 mb-6">
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30 text-[10px] uppercase font-bold">
                  Recommended Express
                </Badge>
                <span className="text-xs font-bold text-white">Vande Bharat Express (22229)</span>
              </div>
              <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 text-[10px]">
                🟢 Available · Demo Availability
              </Badge>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-3 border-y border-slate-800/80">
              <div>
                <span className="text-[10px] text-slate-400">Departure</span>
                <div className="text-sm font-bold text-white mt-0.5">06:10 AM</div>
                <div className="text-[10px] text-slate-500">{trip.starting_location || "Origin Station"}</div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">Arrival</span>
                <div className="text-sm font-bold text-white mt-0.5">01:30 PM</div>
                <div className="text-[10px] text-slate-500">{trip.destination || "Madgaon Jn"}</div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">Duration</span>
                <div className="text-sm font-bold text-white mt-0.5">7h 20m</div>
                <div className="text-[10px] text-slate-500">Direct Superfast</div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">Estimated Fare</span>
                <div className="text-sm font-bold text-cyan-300 mt-0.5">₹1,850 / person</div>
                <div className="text-[10px] text-slate-500">Executive / CC</div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 mt-4">
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 text-cyan-400" />
                <span>Fastest direct rail transit to destination. Punctuality score: 98%</span>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSearchTrains}
                  disabled={trainSearchLoading}
                  className="border-slate-700 text-slate-300 hover:text-white text-xs gap-1.5"
                >
                  {trainSearchLoading ? (
                    <RefreshCw className="h-3 w-3 animate-spin" />
                  ) : (
                    <Search className="h-3 w-3" />
                  )}
                  <span>{trainSearchOpen ? "Refresh Trains" : "Search Trains"}</span>
                </Button>

                <Button
                  size="sm"
                  onClick={() => handleOpenRailwayBooking()}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold gap-1.5 shadow-md shadow-cyan-600/20"
                >
                  <span>Continue to Booking</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>

          {/* Prototype Train Search Results (Part 2) */}
          {trainSearchOpen && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Train className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Available Train Options ({trip.starting_location || "Mumbai"} → {trip.destination || "Goa"})</span>
                </h4>
                <Badge className="bg-slate-800 text-amber-300 border-amber-500/30 text-[10px]">
                  Prototype / Demo Data
                </Badge>
              </div>

              <div className="space-y-2.5">
                {[
                  {
                    name: "Vande Bharat Express",
                    number: "22229",
                    dep: "06:10 AM",
                    arr: "01:30 PM",
                    dur: "7h 20m",
                    status: "🟢 Available (AVL 34)",
                    fare: 1850,
                    class: "Executive Chair Car",
                  },
                  {
                    name: "Tejas Superfast Express",
                    number: "22119",
                    dep: "05:50 AM",
                    arr: "02:40 PM",
                    dur: "8h 50m",
                    status: "🟢 Available (AVL 18)",
                    fare: 1420,
                    class: "AC Chair Car (CC)",
                  },
                  {
                    name: "Mandovi Express",
                    number: "10103",
                    dep: "07:10 AM",
                    arr: "07:00 PM",
                    dur: "11h 50m",
                    status: "🟡 RAC 8",
                    fare: 760,
                    class: "3-Tier AC (3A)",
                  },
                ].map((train, tIdx) => (
                  <div
                    key={tIdx}
                    className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{train.name}</span>
                        <span className="text-[10px] text-slate-500 font-mono">#{train.number}</span>
                        <Badge className="bg-slate-900 border-slate-700 text-slate-300 text-[10px]">
                          {train.class}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-1.5 text-xs text-slate-300">
                        <span><strong>{train.dep}</strong> → <strong>{train.arr}</strong></span>
                        <span className="text-slate-500">⏱️ {train.dur}</span>
                        <span className="text-[11px] font-semibold">{train.status}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-3 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
                      <div className="text-left sm:text-right">
                        <div className="text-xs font-bold text-cyan-300">₹{train.fare}</div>
                        <div className="text-[10px] text-slate-500">per passenger</div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenRailwayBooking(train)}
                        className="border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 text-xs"
                      >
                        Book Train
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* SMART STAY & HOTEL BOOKING SECTION (PART 3) */}
        <div id="smart-stay-booking-section" className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 mb-6">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Hotel className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>Smart Stay & Hotel Booking</span>
                  <Badge variant="outline" className="border-indigo-500/30 text-indigo-400 bg-indigo-500/10 text-xs">
                    Integration Ready · Smart Accommodations
                  </Badge>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Curated stay recommendations matched with your itinerary pace and budget
                </p>
              </div>
            </div>

            <Badge className="bg-slate-800 text-slate-300 border-slate-700 text-xs">
              Personalized Recommendations
            </Badge>
          </div>

          {/* Stay Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                name: `${trip.destination || "Destination"} Seaside Heritage Resort`,
                type: "Boutique Beach Resort",
                location: "North Coast Beachfront",
                rating: 4.8,
                price: 3800,
                distance: "0.8 km from beach",
                amenities: ["Ocean View", "Free Breakfast", "Pool & Spa"],
              },
              {
                name: "Coconut Grove Villa & Homestay",
                type: "Eco Homestay / Villa",
                location: "Quiet Palm Enclave",
                rating: 4.9,
                price: 2400,
                distance: "2.2 km from market",
                amenities: ["Private Garden", "Local Cuisine", "WiFi"],
              },
              {
                name: "The Grand Horizon Luxury Suites",
                type: "Premium City Hotel",
                location: "Central Historic District",
                rating: 4.7,
                price: 4900,
                distance: "1.1 km from center",
                amenities: ["Rooftop Lounge", "Airport Shuttle", "Gym"],
              },
            ].map((stay, sIdx) => (
              <div
                key={sIdx}
                className="p-5 rounded-2xl border border-slate-800 bg-slate-950/70 hover:border-slate-700 transition-all flex flex-col justify-between shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <Badge className="bg-indigo-500/20 text-indigo-300 border-indigo-500/30 text-[10px]">
                      {stay.type}
                    </Badge>
                    <span className="text-xs font-bold text-amber-300">⭐ {stay.rating}</span>
                  </div>

                  <h4 className="text-sm font-bold text-white">{stay.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-1">📍 {stay.location} · {stay.distance}</p>

                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {stay.amenities.map((am, aIdx) => (
                      <span key={aIdx} className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                        {am}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-indigo-300">₹{stay.price}</div>
                    <div className="text-[10px] text-slate-500">per night</div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Button
                      size="sm"
                      onClick={() => handleOpenHotelBooking(stay)}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm"
                    >
                      Book Stay
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PLATFORM CAPABILITIES & FUTURE INTEGRATION STATUS (PART 8) */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden mt-8">
          <div className="flex items-center gap-3 border-b border-slate-800/80 pb-5 mb-5">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>Platform Capabilities & Integration Architecture</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Transparent overview of verified live prototype modules and upcoming production integration partners
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Live / Implemented Features */}
            <div className="p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/10">
              <div className="flex items-center gap-2 mb-3">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <h3 className="text-sm font-bold text-emerald-300 uppercase tracking-wider">LIVE & IMPLEMENTED</h3>
              </div>
              <ul className="space-y-2 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>AI Travel Requirement Evaluator (LangGraph TravelState)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Destination Intelligence & Hidden Gems Generator (Gemini)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Live Weather Intelligence & Advisory Engine (OpenWeather API)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Personalized Multi-Day Itinerary Planner</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Live Browser GPS Tracking & Interactive Leaflet Map</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>OSRM Turn-by-Turn Route Engine (Driving, Walking, Cycling)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Crowd Intelligence & Deterministic Overcrowding Rerouting</span>
                </li>
              </ul>
            </div>

            {/* Integration Ready / Planned */}
            <div className="p-5 rounded-2xl border border-blue-500/30 bg-blue-950/10">
              <div className="flex items-center gap-2 mb-3">
                <CircleDot className="h-2.5 w-2.5 text-blue-400" />
                <h3 className="text-sm font-bold text-blue-300 uppercase tracking-wider">INTEGRATION READY</h3>
              </div>
              <ul className="space-y-2 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  <span>Authorized Railway Booking API Partner (IRCTC GDS Integration)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  <span>Direct Hotel & Stay Booking API Provider</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  <span>Computer Vision Camera Feed Ingestion (YOLO / OpenCV)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  <span>Multi-Source Public & Venue Occupancy Signals</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* PROFESSIONAL BOOKING INTEGRATION MODAL (PARTS 1, 3, 10) */}
      {bookingModal && bookingModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-3xl border border-slate-800 bg-slate-950 p-6 md:p-7 shadow-2xl space-y-5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                  {bookingModal.type === "railway" ? (
                    <Train className="h-5 w-5 text-white" />
                  ) : (
                    <Hotel className="h-5 w-5 text-white" />
                  )}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{bookingModal.title}</h3>
                  <Badge variant="outline" className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10 text-[10px] mt-0.5">
                    Production Integration Point
                  </Badge>
                </div>
              </div>

              <button
                onClick={() => setBookingModal(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Details Summary Card */}
            {bookingModal.details && (
              <div className="p-4 rounded-2xl border border-slate-800/80 bg-slate-900/60 text-xs space-y-1.5">
                <div className="font-bold text-white text-sm">{bookingModal.details.name}</div>
                {bookingModal.details.route && (
                  <div className="text-slate-300">Route: <strong>{bookingModal.details.route}</strong></div>
                )}
                {bookingModal.details.departure && (
                  <div className="text-slate-400">Timing: {bookingModal.details.departure} - {bookingModal.details.arrival} ({bookingModal.details.duration})</div>
                )}
                {bookingModal.details.location && (
                  <div className="text-slate-300">Location: {bookingModal.details.location} ({bookingModal.details.type})</div>
                )}
                {bookingModal.details.fare && (
                  <div className="text-cyan-300 font-bold mt-1">Estimated Fare: ₹{bookingModal.details.fare} / passenger</div>
                )}
                {bookingModal.details.price && (
                  <div className="text-indigo-300 font-bold mt-1">Estimated Tariff: ₹{bookingModal.details.price} / night</div>
                )}
              </div>
            )}

            {/* Official Integration Message */}
            <div className="p-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 text-xs text-amber-200 leading-relaxed flex items-start gap-2.5">
              <Info className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-amber-100 font-semibold block mb-0.5">Production Architecture Notice:</strong>
                <span>{bookingModal.subtitle}</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                onClick={() => setBookingModal(null)}
                className="w-full bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold py-2.5 rounded-xl shadow-md"
              >
                Back to Trip
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}




