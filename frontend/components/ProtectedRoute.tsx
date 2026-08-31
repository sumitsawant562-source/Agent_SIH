"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { supabase } from "@/lib/supabase/client";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!isMounted) return;

        if (session && session.user) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
        }
      } catch (err) {
        if (isMounted) {
          setIsAuthenticated(false);
          router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
        }
      }
    }

    checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!isMounted) return;
      if (session && session.user) {
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
        router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
      }
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [router, pathname]);

  if (isAuthenticated === null) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-4">
        <div className="relative">
          <div className="h-12 w-12 rounded-full border-2 border-teal-500/20 border-t-teal-400 animate-spin" />
        </div>
        <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold animate-pulse">
          Verifying Authenticated Session...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
