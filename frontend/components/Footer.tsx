import React from "react";
import Link from "next/link";
import { Compass, Sparkles, Shield, Cpu } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-800/80 bg-slate-950/60 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-500 text-slate-950">
                <Compass className="h-4 w-4 font-bold" />
              </div>
              <span className="text-base font-bold text-white">
                Travel<span className="text-teal-400">IQ</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-md leading-relaxed">
              An agentic AI personalized travel intelligence platform designed for the Smart India Hackathon (SIH). Delivers hyper-personalized, budget-aware, and adaptive itineraries.
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-500 pt-2">
              <span className="flex items-center gap-1">
                <Shield className="h-3.5 w-3.5 text-teal-400" />
                Row-Level Security
              </span>
              <span className="flex items-center gap-1">
                <Cpu className="h-3.5 w-3.5 text-teal-400" />
                FastAPI & Next.js
              </span>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">Platform</h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <Link href="/" className="hover:text-teal-400 transition-colors">
                  Overview & Features
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="hover:text-teal-400 transition-colors">
                  Travel Dashboard
                </Link>
              </li>
              <li>
                <Link href="/create-trip" className="hover:text-teal-400 transition-colors">
                  Plan New Journey
                </Link>
              </li>
            </ul>
          </div>

          {/* Stage Info */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">Hackathon Stage</h4>
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-teal-400 font-semibold">
                <Sparkles className="h-3.5 w-3.5" />
                Stage 1: Production Foundation
              </div>
              <p className="text-[11px] text-slate-500">
                Core DB schemas, RLS, Supabase Auth & FastAPI CRUD architecture active.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} TravelIQ Intelligence Platform. Built for SIH.</p>
          <p className="text-[11px]">Designed with Next.js, FastAPI & Supabase</p>
        </div>
      </div>
    </footer>
  );
}
