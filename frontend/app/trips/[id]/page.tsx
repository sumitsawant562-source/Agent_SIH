"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import { Trip } from "@/types/trip";
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

      {/* Stage 4 AI Agent Readiness Notice */}
      <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-400">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Trip Draft Configured</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Trip parameters are saved. Multi-agent itinerary synthesis will execute in Stage 4.
            </p>
          </div>
        </div>
        <Link href="/dashboard">
          <Button variant="outline" size="sm">
            Return to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}
