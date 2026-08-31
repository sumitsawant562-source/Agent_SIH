"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase/client";
import { Compass, Mail, Lock, User, AlertCircle, ArrowRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";

export default function SignupPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialChecking, setInitialChecking] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session && session.user) {
        router.replace("/dashboard");
      } else {
        setInitialChecking(false);
      }
    });
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    // Form Validations
    if (!fullName.trim()) {
      setError("Please provide your full name.");
      return;
    }
    if (!email.trim()) {
      setError("Please provide a valid email address.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    setLoading(true);

    try {
      const { data, error: authError } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            full_name: fullName.trim(),
          },
        },
      });

      if (authError) {
        if (authError.message.toLowerCase().includes("user already registered")) {
          setError("An account with this email already exists. Please sign in instead.");
        } else if (authError.message.toLowerCase().includes("weak password")) {
          setError("Password is too weak. Please use a stronger combination.");
        } else {
          setError(authError.message || "Failed to create account. Please try again.");
        }
        setLoading(false);
        return;
      }

      if (data.session) {
        // Direct session established
        router.replace("/dashboard");
      } else if (data.user) {
        // User created (email confirmation might be enabled in Supabase)
        setSuccessMsg(
          "Account created successfully! If email confirmation is enabled on your Supabase project, please check your inbox."
        );
        setTimeout(() => {
          router.replace("/dashboard");
        }, 2000);
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
            Create Your Account
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-400">
            Join TravelIQ to experience intelligent travel planning
          </p>
        </div>

        <Card className="border-slate-800 bg-slate-900/80 shadow-2xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-lg">Get Started Free</CardTitle>
            <CardDescription>Fill in your details below</CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 flex items-start gap-2.5">
                  <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {successMsg && (
                <div className="rounded-xl border border-teal-500/30 bg-teal-500/10 p-3 text-xs text-teal-300 flex items-start gap-2.5">
                  <CheckCircle2 className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                  <span>{successMsg}</span>
                </div>
              )}

              <Input
                label="Full Name"
                type="text"
                placeholder="Alex Morgan"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                icon={<User className="h-4 w-4" />}
                required
                autoComplete="name"
              />

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
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock className="h-4 w-4" />}
                required
                autoComplete="new-password"
              />

              <Input
                label="Confirm Password"
                type="password"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                icon={<Lock className="h-4 w-4" />}
                required
                autoComplete="new-password"
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full mt-2"
                isLoading={loading}
              >
                <span>Create Account</span>
                {!loading && <ArrowRight className="h-4 w-4" />}
              </Button>
            </form>
          </CardContent>

          <CardFooter className="justify-center text-xs text-slate-400">
            <span>Already have an account?</span>{" "}
            <Link
              href="/login"
              className="ml-1.5 font-semibold text-teal-400 hover:text-teal-300 transition-colors"
            >
              Sign In
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
