import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "TravelIQ | Agentic AI Personalized Travel Intelligence Platform",
  description:
    "An intelligent travel planning platform that creates personalized, budget-aware and adaptive travel itineraries for the Smart India Hackathon.",
  keywords: ["travel planning", "AI travel assistant", "itinerary planner", "SIH", "smart travel"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 flex min-h-screen flex-col antialiased selection:bg-teal-500/30 selection:text-teal-200">
        <Navbar />
        <main className="flex-1 w-full">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
