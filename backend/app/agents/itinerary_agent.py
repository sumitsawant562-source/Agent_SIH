"""
Itinerary Planning Agent (Stage 7).

Synthesizes completed TravelState requirements, Stage 5 destination recommendations,
and Stage 6 weather intelligence into a structured, day-by-day, weather-aware,
and budget-conscious travel itinerary using Gemini AI and deterministic fallback generators.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.graph.state import TravelState
from app.services.gemini import get_gemini_client

logger = logging.getLogger(__name__)


class ItineraryAgent:
    """Agent responsible for multi-day itinerary synthesis and schedule validation."""

    @classmethod
    def calculate_trip_dates(cls, state: TravelState) -> Tuple[List[str], int]:
        """
        Computes sequential calendar dates (YYYY-MM-DD) for the trip duration.
        """
        duration = state.get("duration_days") or 3
        if duration <= 0:
            duration = 3

        start_str = state.get("start_date")
        base_date: datetime

        if start_str:
            try:
                base_date = datetime.strptime(start_str.split("T")[0], "%Y-%m-%d")
            except (ValueError, TypeError):
                base_date = datetime.now(timezone.utc)
        else:
            base_date = datetime.now(timezone.utc) + timedelta(days=14)

        date_list = [
            (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(duration)
        ]
        return date_list, duration

    @classmethod
    def build_itinerary_prompt(cls, state: TravelState) -> str:
        """
        Constructs a comprehensive, context-rich prompt for Gemini AI synthesis.
        """
        destination = state.get("destination") or "Unknown"
        dates, duration = cls.calculate_trip_dates(state)
        budget = state.get("budget") or 0.0
        currency = state.get("currency") or "INR"
        travelers = state.get("travelers") or (state.get("adults") or 1) + (state.get("children") or 0)
        adults = state.get("adults") or 1
        children = state.get("children") or 0
        food_pref = state.get("food_preference") or "no preference"
        stay_pref = state.get("stay_preference") or "hotel"
        transport = state.get("transport_mode") or "flight/car"
        interests = ", ".join(state.get("interests") or ["sightseeing", "relaxation"])
        special = state.get("special_requirements") or "None"

        # Stage 5 Destination Recommendations
        recs = state.get("destination_recommendations") or []
        recs_summary_lines = []
        for r in recs[:12]:
            recs_summary_lines.append(
                f"- {r.get('name')} [{r.get('category')}]: {r.get('description', '')[:100]}... "
                f"(Cost: {r.get('estimated_cost', 0)} {currency}, Duration: {r.get('estimated_visit_duration', '2h')})"
            )
        recs_text = "\n".join(recs_summary_lines) if recs_summary_lines else "Curate popular local highlights."

        # Stage 6 Weather Information
        weather_curr = state.get("weather_current") or {}
        weather_forecast = state.get("weather_forecast") or []
        weather_insights = state.get("weather_insights") or []

        weather_lines = []
        if weather_curr:
            weather_lines.append(
                f"Current Condition: {weather_curr.get('temperature')}°C, "
                f"{weather_curr.get('weather_condition')} ({weather_curr.get('weather_description')}), "
                f"Rain Risk: {int(weather_curr.get('rain_probability', 0) * 100)}%, "
                f"Wind: {weather_curr.get('wind_speed')} m/s"
            )
        for f in weather_forecast[:6]:
            weather_lines.append(
                f"Forecast {f.get('date')} {f.get('time')}: {f.get('temperature')}°C, {f.get('weather_condition')} (Rain: {int(f.get('rain_probability', 0)*100)}%)"
            )
        for ins in weather_insights[:3]:
            weather_lines.append(f"Advisory: {ins.get('title')} - {ins.get('message')}")

        weather_text = "\n".join(weather_lines) if weather_lines else "Mild, pleasant travel weather."

        prompt = f"""
You are an expert, meticulous AI Travel Itinerary Planner.
Generate a realistic, seamless, day-by-day travel itinerary for {duration} days in {destination}.

TRIP PARAMETERS:
- Destination: {destination}
- Duration: {duration} Days ({dates[0]} to {dates[-1]})
- Travelers: {travelers} ({adults} Adults, {children} Children)
- Total Budget: {currency} {budget}
- Transport Mode: {transport}
- Dietary / Food Preference: {food_pref}
- Stay Style: {stay_pref}
- Interests: {interests}
- Special Notes: {special}

DESTINATION PLACES (Stage 5 Data):
{recs_text}

METEOROLOGICAL OUTLOOK (Stage 6 Weather Data):
{weather_text}

PLANNING RULES:
1. Generate EXACTLY {duration} days. Number them 1 to {duration}.
2. Use the exact calendar dates: {', '.join(dates)}.
3. For EACH day, schedule:
   - Morning Activity (09:00 - 11:30)
   - Afternoon Activity (14:00 - 16:30)
   - Evening Activity (18:00 - 20:30)
   - 2-3 Food recommendations (Breakfast, Lunch, Dinner) strictly honoring "{food_pref}" diet.
4. WEATHER ADAPTATION:
   - If rainy periods are forecasted, schedule indoor cultural sites/museums or covered markets.
   - Schedule outdoor beaches/nature in dry/mild weather windows.
   - If hot (>32°C), prioritize morning/evening outdoor exploration and indoor midday rests.
5. BUDGET ADAPTATION:
   - Keep total estimated cost across activities and food realistic relative to the {currency} {budget} budget.
   - Assign reasonable estimated costs per activity and meal in {currency}.
6. NO DUPLICATE PLACES across days unless justified.

REQUIRED JSON OUTPUT FORMAT (Return ONLY valid JSON):
{{
  "days": [
    {{
      "day_number": 1,
      "date": "{dates[0]}",
      "theme": "Heritage Landmarks & Coastal Sunset",
      "weather_summary": "Sunny with mild coastal breeze",
      "activities": [
        {{
          "time_slot": "morning",
          "start_time": "09:00",
          "end_time": "11:30",
          "place_name": "Historic Fort Aguada",
          "category": "famous_place",
          "description": "Explore the 17th-century Portuguese coastal fortification and lighthouse.",
          "estimated_cost": 200.0,
          "currency": "{currency}",
          "visit_duration_minutes": 150,
          "notes": "Carry sunscreen and water"
        }},
        {{
          "time_slot": "afternoon",
          "start_time": "14:00",
          "end_time": "16:30",
          "place_name": "Museum of Goa",
          "category": "cultural_historical",
          "description": "Contemporary art space showcasing Goan history and culture indoors.",
          "estimated_cost": 300.0,
          "currency": "{currency}",
          "visit_duration_minutes": 150,
          "notes": "Air-conditioned indoor exhibit"
        }},
        {{
          "time_slot": "evening",
          "start_time": "18:00",
          "end_time": "20:00",
          "place_name": "Calangute Beach Walk",
          "category": "famous_place",
          "description": "Stroll along the golden sands as the sun sets over the Arabian Sea.",
          "estimated_cost": 0.0,
          "currency": "{currency}",
          "visit_duration_minutes": 120,
          "notes": "Great sunset photography"
        }}
      ],
      "food_recommendations": [
        {{
          "name": "Bhojan Pure Veg Restaurant",
          "meal": "lunch",
          "cuisine_type": "Goan & Gujarati Thali",
          "estimated_cost": 400.0,
          "currency": "{currency}",
          "dietary_fit": "100% Vegetarian"
        }},
        {{
          "name": "Zest Plant Cafe",
          "meal": "dinner",
          "cuisine_type": "Organic Vegetarian & Bowls",
          "estimated_cost": 600.0,
          "currency": "{currency}",
          "dietary_fit": "Vegetarian / Vegan"
        }}
      ],
      "estimated_day_cost": 1500.0,
      "notes": "Comfortable walking day with car transfer"
    }}
  ]
}}
"""
        return prompt

    @classmethod
    def validate_and_sanitize_itinerary(
        cls,
        raw_data: Dict[str, Any],
        state: TravelState,
    ) -> Dict[str, Any]:
        """
        Validates structure, ensures day count and dates align, sanitizes costs,
        and deduplicates places.
        """
        dates, expected_duration = cls.calculate_trip_dates(state)
        currency = state.get("currency") or "INR"
        budget = float(state.get("budget") or 0.0)

        raw_days = raw_data.get("days") if isinstance(raw_data, dict) else []
        if not isinstance(raw_days, list) or len(raw_days) == 0:
            raise ValueError("Itinerary response missing valid 'days' list.")

        sanitized_days: List[Dict[str, Any]] = []
        visited_places: set = set()
        total_trip_cost = 0.0

        for idx in range(expected_duration):
            # Take matching day from raw_days or create padded day
            raw_day = raw_days[idx] if idx < len(raw_days) and isinstance(raw_days[idx], dict) else {}
            day_num = idx + 1
            day_date = dates[idx]
            day_theme = raw_day.get("theme") or f"Day {day_num}: {state.get('destination')} Discovery"
            weather_sum = raw_day.get("weather_summary") or "Pleasant conditions suitable for sightseeing"

            # Parse and sanitize activities
            raw_activities = raw_day.get("activities") or []
            sanitized_activities: List[Dict[str, Any]] = []
            day_activity_cost = 0.0

            slots = ["morning", "afternoon", "evening"]
            default_times = [("09:00", "11:30"), ("14:00", "16:30"), ("18:00", "20:30")]

            for a_idx, a in enumerate(raw_activities):
                if not isinstance(a, dict):
                    continue
                p_name = (a.get("place_name") or a.get("name") or "").strip()
                if not p_name:
                    continue

                # Remove direct repetition
                clean_name_key = p_name.lower()
                if clean_name_key in visited_places and len(visited_places) < 15:
                    p_name = f"{p_name} Area Exploration"

                visited_places.add(clean_name_key)

                slot = a.get("time_slot") or (slots[a_idx] if a_idx < len(slots) else "evening")
                start_t = a.get("start_time") or (default_times[a_idx][0] if a_idx < len(default_times) else "18:00")
                end_t = a.get("end_time") or (default_times[a_idx][1] if a_idx < len(default_times) else "20:00")

                cost = 0.0
                if a.get("estimated_cost") is not None:
                    try:
                        cost = max(0.0, float(a.get("estimated_cost")))
                    except (ValueError, TypeError):
                        cost = 0.0

                dur_min = 120
                if a.get("visit_duration_minutes"):
                    try:
                        dur_min = max(30, int(a.get("visit_duration_minutes")))
                    except (ValueError, TypeError):
                        dur_min = 120

                sanitized_activities.append({
                    "time_slot": slot,
                    "start_time": start_t,
                    "end_time": end_t,
                    "place_name": p_name,
                    "category": a.get("category") or "famous_place",
                    "description": a.get("description") or f"Explore {p_name}.",
                    "estimated_cost": round(cost, 2),
                    "currency": currency,
                    "visit_duration_minutes": dur_min,
                    "notes": a.get("notes"),
                })
                day_activity_cost += cost

            # Parse and sanitize food recommendations
            raw_foods = raw_day.get("food_recommendations") or []
            sanitized_foods: List[Dict[str, Any]] = []
            day_food_cost = 0.0

            for f in raw_foods:
                if not isinstance(f, dict):
                    continue
                f_name = (f.get("name") or "").strip()
                if not f_name:
                    continue

                f_cost = 400.0
                if f.get("estimated_cost") is not None:
                    try:
                        f_cost = max(0.0, float(f.get("estimated_cost")))
                    except (ValueError, TypeError):
                        f_cost = 400.0

                sanitized_foods.append({
                    "name": f_name,
                    "meal": f.get("meal") or "lunch",
                    "cuisine_type": f.get("cuisine_type") or "Local Cuisine",
                    "estimated_cost": round(f_cost, 2),
                    "currency": currency,
                    "dietary_fit": f.get("dietary_fit") or state.get("food_preference") or "Standard",
                })
                day_food_cost += f_cost

            # If no food recommendations in response, add defaults
            if not sanitized_foods:
                pref = state.get("food_preference") or "Local"
                sanitized_foods = [
                    {
                        "name": f"Local {pref.title()} Lunch Spot",
                        "meal": "lunch",
                        "cuisine_type": f"{pref.title()} Flavors",
                        "estimated_cost": 450.0,
                        "currency": currency,
                        "dietary_fit": pref.title(),
                    },
                    {
                        "name": f"Authentic {pref.title()} Dining",
                        "meal": "dinner",
                        "cuisine_type": f"{pref.title()} Specialties",
                        "estimated_cost": 650.0,
                        "currency": currency,
                        "dietary_fit": pref.title(),
                    },
                ]
                day_food_cost = 1100.0

            day_total = day_activity_cost + day_food_cost
            total_trip_cost += day_total

            sanitized_days.append({
                "day_number": day_num,
                "date": day_date,
                "theme": day_theme,
                "weather_summary": weather_sum,
                "activities": sanitized_activities,
                "food_recommendations": sanitized_foods,
                "estimated_day_cost": round(day_total, 2),
                "notes": raw_day.get("notes"),
            })

        # Budget check & status
        budget_status = "within_budget"
        budget_warning = None
        if budget > 0:
            if total_trip_cost > budget:
                budget_status = "exceeds_budget"
                diff = total_trip_cost - budget
                budget_warning = (
                    f"Estimated itinerary cost ({currency} {int(total_trip_cost):,}) exceeds your budget "
                    f"({currency} {int(budget):,}) by approximately {currency} {int(diff):,}."
                )
        else:
            budget_status = "unspecified"

        destination_name = state.get("destination") or "Unknown"

        return {
            "trip_id": state.get("trip_id") or "",
            "destination": destination_name,
            "start_date": dates[0],
            "end_date": dates[-1],
            "duration_days": expected_duration,
            "total_estimated_cost": round(total_trip_cost, 2),
            "budget": budget if budget > 0 else None,
            "currency": currency,
            "budget_status": budget_status,
            "budget_warning": budget_warning,
            "days": sanitized_days,
        }

    @classmethod
    def generate_fallback_itinerary(cls, state: TravelState) -> Dict[str, Any]:
        """
        Creates a high-quality deterministic itinerary by grouping available
        Stage 5 destination recommendations, factoring in Stage 6 weather.
        """
        dates, duration = cls.calculate_trip_dates(state)
        destination = state.get("destination") or "Trip"
        currency = state.get("currency") or "INR"
        budget = float(state.get("budget") or 0.0)
        food_pref = (state.get("food_preference") or "Local Cuisine").title()
        recs = state.get("destination_recommendations") or []
        weather_insights = state.get("weather_insights") or []

        weather_summary_default = (
            weather_insights[0].get("message")
            if weather_insights
            else "Favorable conditions for day tours."
        )

        # Categorized buckets
        famous = [r for r in recs if r.get("category") == "famous_place"]
        nature = [r for r in recs if r.get("category") in ("nature_adventure", "nearby_place")]
        cultural = [r for r in recs if r.get("category") == "cultural_historical"]
        gems = [r for r in recs if r.get("category") == "hidden_gem"]
        foods = [r for r in recs if r.get("category") == "food_dining"]

        fallback_themes = [
            f"Iconic Landmarks & Coastal Vistas of {destination}",
            f"Heritage, Architecture & Cultural Trail",
            f"Nature, Hidden Gems & Scenic Countryside",
            f"Local Markets, Culinary Delights & Sunset Promenade",
            f"Relaxed Discovery & Leisure Exploration",
        ]

        days: List[Dict[str, Any]] = []
        total_cost = 0.0

        for i in range(duration):
            day_num = i + 1
            day_date = dates[i]
            theme = fallback_themes[i % len(fallback_themes)]

            # Select 3 activities
            p1 = famous[i % len(famous)] if famous else {"name": f"{destination} Central Promenade", "category": "famous_place"}
            p2 = (cultural[i % len(cultural)] if cultural else (nature[i % len(nature)] if nature else {"name": f"{destination} Museum & Heritage Hall", "category": "cultural_historical"}))
            p3 = gems[i % len(gems)] if gems else (nature[i % len(nature)] if nature else {"name": f"{destination} Scenic Sunset Viewpoint", "category": "nature_adventure"})

            act1_cost = float(p1.get("estimated_cost") or 250.0)
            act2_cost = float(p2.get("estimated_cost") or 350.0)
            act3_cost = float(p3.get("estimated_cost") or 100.0)

            activities = [
                {
                    "time_slot": "morning",
                    "start_time": "09:00",
                    "end_time": "11:30",
                    "place_name": p1.get("name"),
                    "category": p1.get("category") or "famous_place",
                    "description": p1.get("description") or f"Morning exploration of {p1.get('name')}.",
                    "estimated_cost": act1_cost,
                    "currency": currency,
                    "visit_duration_minutes": 150,
                    "notes": "Best experienced in early morning light.",
                },
                {
                    "time_slot": "afternoon",
                    "start_time": "14:00",
                    "end_time": "16:30",
                    "place_name": p2.get("name"),
                    "category": p2.get("category") or "cultural_historical",
                    "description": p2.get("description") or f"Afternoon cultural visit to {p2.get('name')}.",
                    "estimated_cost": act2_cost,
                    "currency": currency,
                    "visit_duration_minutes": 150,
                    "notes": "Indoor or shaded sightseeing during midday.",
                },
                {
                    "time_slot": "evening",
                    "start_time": "18:00",
                    "end_time": "20:30",
                    "place_name": p3.get("name"),
                    "category": p3.get("category") or "nature_adventure",
                    "description": p3.get("description") or f"Sunset relaxation at {p3.get('name')}.",
                    "estimated_cost": act3_cost,
                    "currency": currency,
                    "visit_duration_minutes": 150,
                    "notes": "Scenic viewpoint for sunset relaxation.",
                },
            ]

            # Food recommendations
            f_spot = foods[i % len(foods)] if foods else {}
            f_name = f_spot.get("name") or f"Authentic {food_pref} Bistro"
            food_recs = [
                {
                    "name": f_name,
                    "meal": "lunch",
                    "cuisine_type": f"{food_pref} Specialties",
                    "estimated_cost": 450.0,
                    "currency": currency,
                    "dietary_fit": food_pref,
                },
                {
                    "name": f"{destination} Coastal {food_pref} Dining",
                    "meal": "dinner",
                    "cuisine_type": f"{food_pref} Gourmet",
                    "estimated_cost": 650.0,
                    "currency": currency,
                    "dietary_fit": food_pref,
                },
            ]

            day_cost = act1_cost + act2_cost + act3_cost + 450.0 + 650.0
            total_cost += day_cost

            days.append({
                "day_number": day_num,
                "date": day_date,
                "theme": theme,
                "weather_summary": weather_summary_default,
                "activities": activities,
                "food_recommendations": food_recs,
                "estimated_day_cost": round(day_cost, 2),
                "notes": "Coordinated itinerary with clustered transit.",
            })

        budget_status = "within_budget"
        budget_warning = None
        if budget > 0 and total_cost > budget:
            budget_status = "exceeds_budget"
            diff = total_cost - budget
            budget_warning = (
                f"Estimated itinerary cost ({currency} {int(total_cost):,}) exceeds budget "
                f"({currency} {int(budget):,}) by {currency} {int(diff):,}."
            )

        return {
            "trip_id": state.get("trip_id") or "",
            "destination": destination,
            "start_date": dates[0],
            "end_date": dates[-1],
            "duration_days": duration,
            "total_estimated_cost": round(total_cost, 2),
            "budget": budget if budget > 0 else None,
            "currency": currency,
            "budget_status": budget_status,
            "budget_warning": budget_warning,
            "days": days,
        }

    @classmethod
    def generate_itinerary(cls, state: TravelState) -> Dict[str, Any]:
        """
        Main entry point for generating structured itinerary with Gemini AI
        and automatic fallback protection.
        """
        destination = state.get("destination")
        if not destination or not destination.strip():
            return {
                "itinerary": None,
                "itinerary_status": "unavailable",
                "itinerary_errors": ["Missing trip destination in travel state."],
            }

        client = get_gemini_client()
        prompt = cls.build_itinerary_prompt(state)

        try:
            if not client:
                logger.warning("Gemini client unavailable; engaging deterministic fallback itinerary.")
                fallback = cls.generate_fallback_itinerary(state)
                return {
                    "itinerary": fallback,
                    "itinerary_status": "ready",
                    "itinerary_errors": [],
                }

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            raw_text = response.text or ""
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
            clean_json = json_match.group(1) if json_match else raw_text.strip()

            parsed = json.loads(clean_json)
            sanitized = cls.validate_and_sanitize_itinerary(parsed, state)

            return {
                "itinerary": sanitized,
                "itinerary_status": "ready",
                "itinerary_errors": [],
            }
        except Exception as e:
            logger.warning(f"Gemini itinerary generation failed: {e}; engaging fallback.")
            fallback = cls.generate_fallback_itinerary(state)
            return {
                "itinerary": fallback,
                "itinerary_status": "ready",
                "itinerary_errors": [],
            }
