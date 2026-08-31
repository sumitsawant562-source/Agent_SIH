"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { supabase } from "@/lib/supabase/client";
import { Compass, LogOut, Menu, X, PlusCircle, LayoutDashboard, User } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Check initial auth state
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user || null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
      router.push("/login");
    } catch (err) {
      console.error("Sign out error:", err);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600 shadow-md shadow-teal-500/20 group-hover:scale-105 transition-transform duration-200">
            <Compass className="h-5 w-5 text-slate-950 font-bold" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-extrabold tracking-tight text-white group-hover:text-teal-300 transition-colors">
              Travel<span className="text-teal-400">IQ</span>
            </span>
            <span className="text-[10px] tracking-wider uppercase font-semibold text-slate-400 -mt-1">
              AI Intelligence
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          <Link
            href="/"
            className={`text-sm font-medium transition-colors ${
              pathname === "/" ? "text-teal-400" : "text-slate-300 hover:text-white"
            }`}
          >
            Overview
          </Link>
          {user && (
            <>
              <Link
                href="/dashboard"
                className={`text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === "/dashboard" ? "text-teal-400" : "text-slate-300 hover:text-white"
                }`}
              >
                <LayoutDashboard className="h-4 w-4" />
                Dashboard
              </Link>
              <Link
                href="/create-trip"
                className={`text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  pathname === "/create-trip" ? "text-teal-400" : "text-slate-300 hover:text-white"
                }`}
              >
                <PlusCircle className="h-4 w-4" />
                Create Trip
              </Link>
            </>
          )}
        </nav>

        {/* Auth CTA Actions */}
        <div className="hidden md:flex items-center gap-3">
          {!loading && (
            <>
              {user ? (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-full py-1.5 px-3">
                    <div className="h-6 w-6 rounded-full bg-teal-500/20 text-teal-300 flex items-center justify-center text-xs font-semibold">
                      <User className="h-3.5 w-3.5" />
                    </div>
                    <span className="text-xs font-medium text-slate-300 max-w-[140px] truncate">
                      {user.user_metadata?.full_name || user.email}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleSignOut}
                    className="text-slate-400 hover:text-rose-400 hover:bg-rose-500/10"
                    title="Sign Out"
                  >
                    <LogOut className="h-4 w-4" />
                    <span className="sr-only">Sign Out</span>
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2.5">
                  <Link href="/login">
                    <Button variant="ghost" size="sm">
                      Log In
                    </Button>
                  </Link>
                  <Link href="/signup">
                    <Button variant="primary" size="sm">
                      Get Started
                    </Button>
                  </Link>
                </div>
              )}
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-400 hover:text-white rounded-lg bg-slate-900 border border-slate-800"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-slate-950 px-4 pt-3 pb-5 space-y-3">
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-300 hover:text-white py-2"
          >
            Overview
          </Link>
          {user ? (
            <>
              <Link
                href="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-sm font-medium text-slate-300 hover:text-white py-2"
              >
                Dashboard
              </Link>
              <Link
                href="/create-trip"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-sm font-medium text-slate-300 hover:text-white py-2"
              >
                Create Trip
              </Link>
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400 truncate max-w-[200px]">{user.email}</span>
                <Button variant="danger" size="sm" onClick={handleSignOut}>
                  Sign Out
                </Button>
              </div>
            </>
          ) : (
            <div className="pt-3 border-t border-slate-800 flex flex-col gap-2">
              <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="outline" className="w-full">
                  Log In
                </Button>
              </Link>
              <Link href="/signup" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="primary" className="w-full">
                  Get Started
                </Button>
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
