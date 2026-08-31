"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabase/client";
import { Compass, Mail, Lock, AlertCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[70vh] items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-teal-500/20 border-t-teal-400" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialChecking, setInitialChecking] = useState(true);

  useEffect(() => {
    // If already logged in, redirect straight to dashboard
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session && session.user) {
        router.replace(redirectUrl);
      } else {
        setInitialChecking(false);
      }
    });
  }, [router, redirectUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation
    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }
    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);

    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (authError) {
        if (authError.message.toLowerCase().includes("invalid login credentials")) {
          setError("Invalid email or password. Please check your credentials.");
        } else if (authError.message.toLowerCase().includes("email not confirmed")) {
          setError("Please verify your email address before signing in.");
        } else {
          setError(authError.message || "Failed to sign in. Please try again.");
        }
        setLoading(false);
        return;
      }

      if (data.session) {
        router.replace(redirectUrl);
      }
    } catch (err: any) {
      setError("Unable to connect to the authentication server. Please check your network connection.");
      setLoading(false);
    }
  };

  if (initialChecking) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-teal-500/20 border-t-teal-400" />
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        {/* Brand Icon & Heading */}
        <div className="text-center mb-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-600 shadow-lg shadow-teal-500/20 mb-4">
            <Compass className="h-6 w-6 text-slate-950 font-bold" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Welcome Back
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-400">
            Sign in to access your intelligent travel plans
          </p>
        </div>

        <Card className="border-slate-800 bg-slate-900/80 shadow-2xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-lg">Account Login</CardTitle>
            <CardDescription>Enter your credentials below</CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 flex items-start gap-2.5">
                  <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <Input
                label="Email Address"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                icon={<Mail className="h-4 w-4" />}
                required
                autoComplete="email"
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock className="h-4 w-4" />}
                required
                autoComplete="current-password"
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full mt-2"
                isLoading={loading}
              >
                <span>Sign In</span>
                {!loading && <ArrowRight className="h-4 w-4" />}
              </Button>
            </form>
          </CardContent>

          <CardFooter className="justify-center text-xs text-slate-400">
            <span>Don&apos;t have an account?</span>{" "}
            <Link
              href="/signup"
              className="ml-1.5 font-semibold text-teal-400 hover:text-teal-300 transition-colors"
            >
              Create Account
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
