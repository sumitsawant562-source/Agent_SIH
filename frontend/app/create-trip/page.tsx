"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import {
  TripCreateInput,
  TransportMode,
  FoodPreference,
  AccommodationPreference,
  TravelStyle,
  INTEREST_OPTIONS,
  TRANSPORT_OPTIONS,
  FOOD_OPTIONS,
  ACCOMMODATION_OPTIONS,
  TRAVEL_STYLE_OPTIONS,
} from "@/types/trip";
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
  AlertCircle,
  ArrowRight,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function CreateTripPage() {
  return (
    <ProtectedRoute>
      <CreateTripForm />
    </ProtectedRoute>
  );
}

function CreateTripForm() {
  const router = useRouter();

  // Form State
  const [startingLocation, setStartingLocation] = useState("");
  const [destination, setDestination] = useState("");
  const [tripTitle, setTripTitle] = useState("");
  const [travelDate, setTravelDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 7);
    return tomorrow.toISOString().split("T")[0];
  });
  const [durationDays, setDurationDays] = useState(3);
  const [adults, setAdults] = useState(1);
  const [childrenCount, setChildrenCount] = useState(0);
  const [budget, setBudget] = useState(1500);
  const [transportMode, setTransportMode] = useState<TransportMode>("flight");
  const [selectedInterests, setSelectedInterests] = useState<string[]>([
    "nature",
    "food",
    "culture",
  ]);
  const [foodPreference, setFoodPreference] = useState<FoodPreference>("no preference");
  const [accommodationPreference, setAccommodationPreference] =
    useState<AccommodationPreference>("hotel");
  const [travelStyle, setTravelStyle] = useState<TravelStyle>("balanced");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleInterest = (id: string) => {
    setSelectedInterests((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const getTransportLucide = (iconName: string) => {
    switch (iconName) {
      case "Car":
        return <Car className="h-5 w-5" />;
      case "Bike":
        return <Bike className="h-5 w-5" />;
      case "Bus":
        return <Bus className="h-5 w-5" />;
      case "Train":
        return <Train className="h-5 w-5" />;
      case "Plane":
      default:
        return <Plane className="h-5 w-5" />;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!startingLocation.trim()) {
      setError("Please specify a starting location.");
      return;
    }
    if (!destination.trim()) {
      setError("Please specify a travel destination.");
      return;
    }
    if (!travelDate) {
      setError("Please select a valid travel date.");
      return;
    }
    if (durationDays < 1) {
      setError("Duration must be at least 1 day.");
      return;
    }
    if (adults < 1) {
      setError("At least 1 adult traveler is required.");
      return;
    }
    if (childrenCount < 0) {
      setError("Children count cannot be negative.");
      return;
    }
    if (budget <= 0) {
      setError("Please enter a realistic travel budget greater than 0.");
      return;
    }

    setLoading(true);

    const generatedTitle = tripTitle.trim() || `Journey to ${destination.trim()}`;

    const tripPayload: TripCreateInput = {
      title: generatedTitle,
      starting_location: startingLocation.trim(),
      destination: destination.trim(),
      travel_date: travelDate,
      duration_days: Number(durationDays),
      adults: Number(adults),
      children: Number(childrenCount),
      budget: Number(budget),
      transport_mode: transportMode,
      interests: selectedInterests,
      food_preference: foodPreference,
      accommodation_preference: accommodationPreference,
      travel_style: travelStyle,
      status: "draft",
    };

    try {
      await api.createTrip(tripPayload);
      router.push("/dashboard");
    } catch (err: any) {
      console.error("Create trip error:", err);
      setError(
        err.message || "Failed to save trip draft. Please check your connection or database setup."
      );
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-10">
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-teal-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20 mb-3">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Stage 1 Trip Form</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Create New Travel Journey
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Configure your travel parameters below to save a draft itinerary.
        </p>
      </div>

      {error && (
        <div className="mb-8 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs sm:text-sm text-rose-300 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Route & Timing */}
        <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <MapPin className="h-5 w-5 text-teal-400" />
              <span>1. Route & Schedule</span>
            </CardTitle>
            <CardDescription>Where are you departing from and heading to?</CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Starting Location"
                placeholder="e.g., New Delhi, India"
                value={startingLocation}
                onChange={(e) => setStartingLocation(e.target.value)}
                icon={<MapPin className="h-4 w-4" />}
                required
              />

              <Input
                label="Destination"
                placeholder="e.g., Leh-Ladakh, India"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                icon={<MapPin className="h-4 w-4" />}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Travel Start Date"
                type="date"
                value={travelDate}
                onChange={(e) => setTravelDate(e.target.value)}
                icon={<Calendar className="h-4 w-4" />}
                required
              />

              <Input
                label="Duration (Number of Days)"
                type="number"
                min={1}
                max={365}
                value={durationDays}
                onChange={(e) => setDurationDays(Math.max(1, parseInt(e.target.value) || 1))}
                icon={<Clock className="h-4 w-4" />}
                required
              />
            </div>

            <Input
              label="Trip Title (Optional)"
              placeholder="e.g., Scenic Himalayan Expedition"
              value={tripTitle}
              onChange={(e) => setTripTitle(e.target.value)}
              helperText="Leave empty to automatically name based on destination"
            />
          </CardContent>
        </Card>

        {/* Section 2: Travelers & Budget */}
        <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <Users className="h-5 w-5 text-emerald-400" />
              <span>2. Travelers & Budget</span>
            </CardTitle>
            <CardDescription>Specify group demographics and estimated financial budget</CardDescription>
          </CardHeader>

          <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Adults (Age 12+)"
              type="number"
              min={1}
              value={adults}
              onChange={(e) => setAdults(Math.max(1, parseInt(e.target.value) || 1))}
              icon={<Users className="h-4 w-4" />}
              required
            />

            <Input
              label="Children (Under 12)"
              type="number"
              min={0}
              value={childrenCount}
              onChange={(e) => setChildrenCount(Math.max(0, parseInt(e.target.value) || 0))}
              icon={<Users className="h-4 w-4" />}
            />

            <Input
              label="Total Budget ($ or ₹)"
              type="number"
              min={1}
              step="1"
              value={budget}
              onChange={(e) => setBudget(Math.max(1, parseFloat(e.target.value) || 0))}
              icon={<Wallet className="h-4 w-4" />}
              required
            />
          </CardContent>
        </Card>

        {/* Section 3: Travel Medium */}
        <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <Plane className="h-5 w-5 text-amber-400" />
              <span>3. Travel Medium</span>
            </CardTitle>
            <CardDescription>Select primary mode of transit</CardDescription>
          </CardHeader>

          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {TRANSPORT_OPTIONS.map((opt) => {
                const isSelected = transportMode === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setTransportMode(opt.id)}
                    className={`flex flex-col items-center justify-center p-4 rounded-xl border text-center transition-all ${
                      isSelected
                        ? "border-teal-500 bg-teal-500/10 text-teal-300 ring-2 ring-teal-500/20"
                        : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    <div className="mb-2 text-current">{getTransportLucide(opt.icon)}</div>
                    <span className="text-xs font-semibold">{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Section 4: Travel Interests (Multi-select) */}
        <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-rose-400" />
              <span>4. Travel Interests</span>
            </CardTitle>
            <CardDescription>Select all activities and vibes that apply (Multiple selection)</CardDescription>
          </CardHeader>

          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {INTEREST_OPTIONS.map((interest) => {
                const isChecked = selectedInterests.includes(interest.id);
                return (
                  <button
                    key={interest.id}
                    type="button"
                    onClick={() => toggleInterest(interest.id)}
                    className={`flex items-center justify-between p-3.5 rounded-xl border text-left transition-all ${
                      isChecked
                        ? "border-teal-500 bg-teal-500/15 text-white ring-1 ring-teal-500/40"
                        : "border-slate-800 bg-slate-900/50 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    <span className="text-xs font-medium">{interest.label}</span>
                    <div
                      className={`h-5 w-5 rounded-md flex items-center justify-center border text-xs transition-colors ${
                        isChecked
                          ? "bg-teal-500 border-teal-400 text-slate-950 font-bold"
                          : "border-slate-700 bg-slate-800 text-transparent"
                      }`}
                    >
                      <Check className="h-3.5 w-3.5" />
                    </div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Section 5: Preferences (Food, Accommodation, Style) */}
        <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-sky-400" />
              <span>5. Preferences & Travel Style</span>
            </CardTitle>
            <CardDescription>Fine-tune dining, lodging, and expedition style</CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Food Preference */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Food Preference
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {FOOD_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setFoodPreference(opt.id)}
                    className={`p-3 rounded-xl border text-xs font-medium transition-all ${
                      foodPreference === opt.id
                        ? "border-teal-500 bg-teal-500/10 text-teal-300 ring-1 ring-teal-500/30"
                        : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Accommodation Preference */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Accommodation Preference
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                {ACCOMMODATION_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setAccommodationPreference(opt.id)}
                    className={`p-3 rounded-xl border text-xs font-medium transition-all ${
                      accommodationPreference === opt.id
                        ? "border-teal-500 bg-teal-500/10 text-teal-300 ring-1 ring-teal-500/30"
                        : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Travel Style */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Travel Style & Pace
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {TRAVEL_STYLE_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setTravelStyle(opt.id)}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      travelStyle === opt.id
                        ? "border-teal-500 bg-teal-500/10 text-white ring-1 ring-teal-500/30"
                        : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    <div className="font-semibold text-xs text-white mb-0.5">{opt.label}</div>
                    <div className="text-[11px] text-slate-400">{opt.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Submit Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-4">
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.back()}
            disabled={loading}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={loading}
            className="w-full sm:w-auto gap-2"
          >
            <span>Continue (Save Draft Trip)</span>
            {!loading && <ArrowRight className="h-4 w-4" />}
          </Button>
        </div>
      </form>
    </div>
  );
}
