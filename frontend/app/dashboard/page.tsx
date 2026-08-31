"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabase/client";
import { Trip } from "@/types/trip";
import {
  PlusCircle,
  Calendar,
  Clock,
  Wallet,
  MapPin,
  Trash2,
  AlertCircle,
  Compass,
  Car,
  Bike,
  Bus,
  Train,
  Plane,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}

function DashboardContent() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchUserDataAndTrips();
  }, []);

  const fetchUserDataAndTrips = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get current user info
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        setUserName(user.user_metadata?.full_name || user.email?.split("@")[0] || "Explorer");
      }

      // Fetch trips from API client (with direct Supabase fallback)
      const data = await api.getTrips();
      setTrips(data.trips || []);
    } catch (err: any) {
      console.error("Dashboard fetch error:", err);
      setError("Unable to load your trips. Please check your connection or database setup.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTrip = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this trip?")) return;

    setDeletingId(id);
    try {
      await api.deleteTrip(id);
      setTrips((prev) => prev.filter((t) => t.id !== id));
    } catch (err: any) {
      alert("Failed to delete trip: " + (err.message || "Unknown error"));
    } finally {
      setDeletingId(null);
    }
  };

  const getTransportIcon = (mode: string) => {
    switch (mode) {
      case "flight":
        return <Plane className="h-3.5 w-3.5" />;
      case "train":
        return <Train className="h-3.5 w-3.5" />;
      case "bus":
        return <Bus className="h-3.5 w-3.5" />;
      case "bike":
        return <Bike className="h-3.5 w-3.5" />;
      case "car":
      default:
        return <Car className="h-3.5 w-3.5" />;
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-teal-400 bg-teal-500/10 px-2.5 py-0.5 rounded-full border border-teal-500/20">
              <Sparkles className="h-3 w-3" />
              Traveler Dashboard
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Welcome back{userName ? `, ${userName}` : ""}!
          </h1>
          <p className="mt-1.5 text-sm text-slate-400">
            Plan your next journey with intelligent travel planning.
          </p>
        </div>

        <Link href="/create-trip">
          <Button size="lg" className="w-full sm:w-auto shadow-lg shadow-teal-500/20 gap-2">
            <PlusCircle className="h-5 w-5" />
            <span>+ Create New Trip</span>
          </Button>
        </Link>
      </div>

      {/* Main Content Area */}
      <div className="mt-8 space-y-6">
        {/* Error Alert */}
        {error && (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs sm:text-sm text-rose-300 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold">Notice</p>
              <p className="mt-0.5 text-rose-300/80">{error}</p>
            </div>
            <Button variant="outline" size="sm" onClick={fetchUserDataAndTrips}>
              Retry
            </Button>
          </div>
        )}

        {/* Trips Grid Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>Saved Trips</span>
            {!loading && (
              <span className="text-xs font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full border border-slate-700">
                {trips.length}
              </span>
            )}
          </h2>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-56 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse p-6 space-y-4"
              >
                <div className="h-6 bg-slate-800 rounded-md w-3/4" />
                <div className="h-4 bg-slate-800/60 rounded-md w-1/2" />
                <div className="pt-4 grid grid-cols-2 gap-3">
                  <div className="h-4 bg-slate-800/60 rounded-md" />
                  <div className="h-4 bg-slate-800/60 rounded-md" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && trips.length === 0 && (
          <Card className="border-slate-800/80 bg-slate-900/40 text-center py-16 px-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800/80 border border-slate-700/80 text-teal-400 mb-4">
              <Compass className="h-8 w-8 animate-spin-slow" />
            </div>
            <h3 className="text-xl font-bold text-white">No trips planned yet</h3>
            <p className="mt-2 text-sm text-slate-400 max-w-md mx-auto">
              Create your first personalized travel itinerary with custom dates, budgets, and travel preferences.
            </p>
            <div className="mt-6">
              <Link href="/create-trip">
                <Button variant="primary" size="md" className="gap-2">
                  <PlusCircle className="h-4 w-4" />
                  <span>+ Create New Trip</span>
                </Button>
              </Link>
            </div>
          </Card>
        )}

        {/* Trips Cards Grid */}
        {!loading && trips.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((trip) => (
              <div
                key={trip.id}
                className="glass-card rounded-2xl p-6 flex flex-col justify-between group border border-slate-800 bg-slate-900/70"
              >
                <div>
                  {/* Status & Actions Bar */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <Badge variant={trip.status as any}>
                      {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
                    </Badge>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => handleDeleteTrip(trip.id, e)}
                        disabled={deletingId === trip.id}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                        title="Delete Trip"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Trip Title & Route */}
                  <Link href={`/trips/${trip.id}`} className="block group-hover:underline">
                    <h3 className="text-lg font-bold text-white group-hover:text-teal-300 transition-colors line-clamp-1">
                      {trip.title}
                    </h3>
                  </Link>

                  <div className="mt-2 flex items-center gap-1.5 text-xs text-teal-400 font-medium">
                    <MapPin className="h-3.5 w-3.5 shrink-0 text-teal-400" />
                    <span className="truncate">
                      {trip.starting_location} → {trip.destination}
                    </span>
                  </div>

                  {/* Trip Attributes */}
                  <div className="mt-5 grid grid-cols-2 gap-3 text-xs text-slate-300 border-t border-slate-800/80 pt-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-slate-400" />
                      <span>{trip.travel_date}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-slate-400" />
                      <span>
                        {trip.duration_days} {trip.duration_days === 1 ? "Day" : "Days"}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Wallet className="h-4 w-4 text-slate-400" />
                      <span className="font-semibold text-emerald-400">
                        ${Number(trip.budget).toLocaleString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 capitalize">
                      {getTransportIcon(trip.transport_mode)}
                      <span>{trip.transport_mode}</span>
                    </div>
                  </div>

                  {/* Interests Chips */}
                  {trip.interests && trip.interests.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {trip.interests.slice(0, 3).map((interest, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-medium text-slate-400 bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 rounded-md capitalize"
                        >
                          {interest}
                        </span>
                      ))}
                      {trip.interests.length > 3 && (
                        <span className="text-[10px] text-slate-500 px-1 py-0.5">
                          +{trip.interests.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Card Footer */}
                <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-500">
                  <span className="capitalize text-[11px]">
                    Style: <strong className="text-slate-300 font-medium">{trip.travel_style}</strong>
                  </span>
                  <span className="text-[10px]">
                    {new Date(trip.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
