import React from "react";
import Link from "next/link";
import {
  Compass,
  ArrowRight,
  Sparkles,
  Wallet,
  CloudSun,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  const features = [
    {
      icon: <Sparkles className="h-6 w-6 text-teal-400" />,
      title: "Personalized Itinerary",
      description:
        "Multi-agent reasoning designs bespoke daily schedules matching your exact pace, group size, and interests.",
      tag: "Agentic AI",
    },
    {
      icon: <Wallet className="h-6 w-6 text-emerald-400" />,
      title: "Budget-Aware Planning",
      description:
        "Smart cost allocation models optimize accommodation, transport, and dining to maximize value without compromise.",
      tag: "Optimization",
    },
    {
      icon: <CloudSun className="h-6 w-6 text-amber-400" />,
      title: "Weather-Aware Recommendations",
      description:
        "Real-time meteorological insights actively balance outdoor and indoor activities based on micro-climates.",
      tag: "Intelligence",
    },
    {
      icon: <MapPin className="h-6 w-6 text-rose-400" />,
      title: "Local Experiences",
      description:
        "Discover hidden gems, authentic regional cuisines, and verified cultural hubs vetted by travel intelligence.",
      tag: "Discovery",
    },
    {
      icon: <RefreshCw className="h-6 w-6 text-sky-400" />,
      title: "Adaptive Travel Planning",
      description:
        "Dynamic rescheduling engine recalculates routes and alternates instantly during transit disruptions or delays.",
      tag: "Real-Time",
    },
  ];

  return (
    <div className="relative isolate overflow-hidden">
      {/* Background Glow Orbs */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
      >
        <div
          style={{
            clipPath:
              "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)",
          }}
          className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-teal-500/30 to-emerald-600/20 opacity-40 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
        />
      </div>

      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-24 lg:pt-28 lg:pb-32 text-center">
        {/* Hackathon Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-teal-500/30 bg-teal-500/10 px-3.5 py-1 text-xs font-semibold text-teal-300 backdrop-blur-md mb-8">
          <Zap className="h-3.5 w-3.5 text-teal-400" />
          <span>Smart India Hackathon (SIH) Project</span>
        </div>

        {/* Hero Heading */}
        <h1 className="mx-auto max-w-4xl text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.1]">
          Plan Smarter. <br />
          <span className="bg-gradient-to-r from-teal-300 via-emerald-400 to-teal-500 bg-clip-text text-transparent">
            Travel Better.
          </span>
        </h1>

        {/* Supporting Copy */}
        <p className="mx-auto mt-6 max-w-2xl text-base sm:text-lg text-slate-300 leading-relaxed">
          An intelligent travel planning platform that creates personalized, budget-aware and adaptive travel itineraries.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/create-trip" className="w-full sm:w-auto">
            <Button size="lg" className="w-full sm:w-auto gap-2 group">
              <span>Plan My Trip</span>
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
          <Link href="/login" className="w-full sm:w-auto">
            <Button variant="secondary" size="lg" className="w-full sm:w-auto">
              Login
            </Button>
          </Link>
        </div>

        {/* Quick Highlights Strip */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-3 gap-4 max-w-3xl mx-auto border-t border-slate-800/80 pt-10 text-slate-400 text-xs sm:text-sm">
          <div className="flex items-center justify-center gap-2">
            <ShieldCheck className="h-4 w-4 text-teal-400" />
            <span>Row-Level Data Security</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <Compass className="h-4 w-4 text-teal-400" />
            <span>FastAPI & Next.js Core</span>
          </div>
          <div className="col-span-2 md:col-span-1 flex items-center justify-center gap-2">
            <Sparkles className="h-4 w-4 text-teal-400" />
            <span>Agentic Architecture Ready</span>
          </div>
        </div>
      </section>

      {/* Feature Section */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16 border-t border-slate-800/60">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-teal-400">
            Intelligent Core Capabilities
          </h2>
          <h3 className="mt-2 text-3xl font-extrabold text-white sm:text-4xl">
            Engineered for Precision & Convenience
          </h3>
          <p className="mt-4 text-sm sm:text-base text-slate-400">
            Designed to bridge the gap between fixed tourist templates and truly autonomous, context-aware itinerary generation.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="glass-card rounded-2xl p-7 flex flex-col justify-between relative group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="h-12 w-12 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform">
                    {feature.icon}
                  </div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-slate-800/60 px-2.5 py-1 rounded-full border border-slate-700/50">
                    {feature.tag}
                  </span>
                </div>
                <h4 className="text-lg font-bold text-white mb-2">{feature.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{feature.description}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center text-xs text-teal-400 font-medium">
                <span>Stage 1 Ready</span>
              </div>
            </div>
          ))}

          {/* Architecture Banner */}
          <div className="glass-card rounded-2xl p-7 flex flex-col justify-between bg-gradient-to-br from-slate-900 via-teal-950/40 to-slate-900 border-teal-500/30">
            <div>
              <div className="h-12 w-12 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center mb-4">
                <Compass className="h-6 w-6 text-teal-300" />
              </div>
              <h4 className="text-lg font-bold text-white mb-2">Stage 2 AI Expansion</h4>
              <p className="text-xs text-slate-300 leading-relaxed">
                Ready for LangGraph multi-agent orchestration, real-time weather APIs, Places telemetry, and interactive map visualizations.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60">
              <Link href="/create-trip">
                <span className="text-xs font-bold text-teal-300 hover:text-teal-200 flex items-center gap-1">
                  Start creating trips <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
