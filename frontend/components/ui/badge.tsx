import * as React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "draft" | "planning" | "completed" | "outline" | "accent";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "bg-slate-800 text-slate-200 border-slate-700",
    draft: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    planning: "bg-teal-500/10 text-teal-400 border-teal-500/30",
    completed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    outline: "border-slate-700 text-slate-300 bg-transparent",
    accent: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}
