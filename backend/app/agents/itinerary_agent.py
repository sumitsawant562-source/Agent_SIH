"""
Itinerary Planning Agent (Stage 7).

Synthesizes completed TravelState requirements, Stage 5 destination recommendations,
and Stage 6 weather intelligence into a highly detailed, realistic, geographically sensible,
weather-aware, and budget-conscious travel itinerary using Gemini AI and robust deterministic fallback generators.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.graph.state import TravelState
from app.services.gemini import get_gemini_client

logger = logging.getLogger(__name__)


class ItineraryAgent:
    """Agent responsible for multi-day itinerary synthesis, schedule realism, and budget/weather alignment."""

    @classmethod
    def calculate_trip_dates(cls, state: TravelState) -> Tuple[List[str], int]:
        """
        Computes sequential calendar dates (YYYY-MM-DD) for the trip duration.
        """
        start_str = state.get("start_date")
        end_str = state.get("end_date")
        duration = state.get("duration_days")

        base_date: datetime
        if start_str:
            try:
                base_date = datetime.strptime(start_str.split("T")[0], "%Y-%m-%d")
            except (ValueError, TypeError):
                base_date = datetime.now(timezone.utc) + timedelta(days=14)
        else:
            base_date = datetime.now(timezone.utc) + timedelta(days=14)

        if duration is None or duration <= 0:
            if start_str and end_str:
                try:
                    s_dt = datetime.strptime(start_str.split("T")[0], "%Y-%m-%d")
                    e_dt = datetime.strptime(end_str.split("T")[0], "%Y-%m-%d")
                    calc_days = (e_dt - s_dt).days + 1
                    duration = max(1, calc_days)
                except (ValueError, TypeError):
                    duration = 3
            else:
                duration = 3

        date_list = [
            (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(duration)
        ]
        return date_list, duration

    @classmethod
    def build_itinerary_prompt(cls, state: TravelState) -> str:
        """
        Constructs a comprehensive, context-rich prompt for Gemini AI synthesis,
        incorporating Requirements, Destination Intelligence (Stage 5), and Weather Intelligence (Stage 6).
        """
        destination = state.get("destination") or "Unknown Destination"
        start_location = state.get("start_location") or "Origin City"
        dates, duration = cls.calculate_trip_dates(state)
        budget = float(state.get("budget") or 0.0)
        currency = state.get("currency") or "INR"
        travelers = int(state.get("travelers") or (state.get("adults") or 1) + (state.get("children") or 0))
        if travelers <= 0:
            travelers = 1
        adults = int(state.get("adults") or (travelers if state.get("children") is None else max(1, travelers - (state.get("children") or 0))))
        children = int(state.get("children") or 0)
        food_pref = state.get("food_preference") or "no preference"
        stay_pref = state.get("stay_preference") or "hotel"
        transport = state.get("transport_mode") or "flight/car"
        travel_style = state.get("travel_style") or "balanced pace"
        interests_list = state.get("interests") or ["sightseeing", "culture", "local cuisine"]
        if isinstance(interests_list, str):
            interests_list = [i.strip() for i in interests_list.split(",") if i.strip()]
        interests = ", ".join(interests_list)
        special = state.get("special_requirements") or "None"

        # Stage 5 Destination Recommendations Synthesis
        recs = state.get("destination_recommendations") or []
        recs_summary_lines = []
        for r in recs[:18]:
            cost_str = f"Cost: {r.get('estimated_cost', 0)} {currency}" if r.get("estimated_cost") is not None else "Free"
            dur_str = f"Duration: {r.get('estimated_visit_duration', '2h')}"
            best_t = f"Best Time: {r.get('best_time_to_visit', 'Flexible')}"
            dist = f"Location: {r.get('distance_from_destination', 'Central')}"
            recs_summary_lines.append(
                f"- **{r.get('name')}** [{r.get('category')}]: {r.get('description', '')[:120]} "
                f"(Why: {r.get('why_recommended', '')[:100]} | {cost_str} | {dur_str} | {best_t} | {dist})"
            )
        recs_text = "\n".join(recs_summary_lines) if recs_summary_lines else "Curate popular local highlights, heritage landmarks, and top culinary spots."

        # Stage 6 Weather Intelligence Synthesis
        weather_curr = state.get("weather_current") or {}
        weather_forecast = state.get("weather_forecast") or []
        weather_insights = state.get("weather_insights") or []

        weather_lines = []
        if weather_curr:
            weather_lines.append(
                f"- Current Conditions: {weather_curr.get('temperature')}°C (Feels like {weather_curr.get('feels_like')}°C), "
                f"{weather_curr.get('weather_condition')} ({weather_curr.get('weather_description')}), "
                f"Rain Risk: {int(weather_curr.get('rain_probability', 0) * 100)}%, "
                f"Humidity: {weather_curr.get('humidity')}%, Wind: {weather_curr.get('wind_speed')} m/s"
            )
        for f in weather_forecast[:8]:
            weather_lines.append(
                f"- Forecast {f.get('date')} {f.get('time')}: {f.get('temperature')}°C, {f.get('weather_condition')} "
                f"({f.get('weather_description')}, Rain Prob: {int(f.get('rain_probability', 0)*100)}%)"
            )
        for ins in weather_insights[:4]:
            if isinstance(ins, dict):
                weather_lines.append(f"- Advisory [{ins.get('type', 'notice')}]: {ins.get('title')} - {ins.get('message')}")
            elif isinstance(ins, str):
                weather_lines.append(f"- Advisory: {ins}")

        weather_text = "\n".join(weather_lines) if weather_lines else "Pleasant, mild travel weather expected across all travel dates."

        prompt = f"""You are an expert professional travel planner, destination researcher, itinerary optimizer, and local travel advisor.
Your job is to synthesize all upstream agent outputs into a highly detailed, realistic, practical, day-by-day travel itinerary that a real traveler can actually follow.
Do NOT generate a generic, rushed list of tourist attractions. Create an authentic, seamless travel experience.

================================================================================
TRIP REQUIREMENTS & CONSTRAINTS (Requirements Agent Output):
- Destination: {destination}
- Origin / Starting Location: {start_location}
- Dates: {dates[0]} to {dates[-1]} (EXACTLY {duration} Days)
- Date Schedule: {', '.join(dates)}
- Group Composition: {travelers} Travelers ({adults} Adults, {children} Children)
- Budget Constraint: {currency} {budget:,.2f} total ({currency} {budget/travelers:,.2f} per person)
- Primary Transport Mode: {transport}
- Dietary & Food Preference: {food_pref}
- Stay Preference: {stay_pref}
- Travel Style & Pace: {travel_style}
- Traveler Interests: {interests}
- Special Requirements / Accessibility: {special}

================================================================================
DESTINATION INTELLIGENCE & RECOMMENDED VENUES (Stage 5 Destination Agent Output):
{recs_text}

================================================================================
METEOROLOGICAL INTELLIGENCE & FORECAST (Stage 6 Weather Agent Output):
{weather_text}

================================================================================
MANDATORY PLANNING & LOGISTICAL RULES:

1. DURATION & DATES:
   - Generate EXACTLY {duration} day schedules, numbered sequentially from Day 1 to Day {duration}.
   - The dates MUST strictly match: {', '.join(dates)}.

2. GEOGRAPHIC CLUSTERING & ROUTING:
   - Schedule places that are in the same geographical area or neighborhood on the same day.
   - NEVER schedule places that are far apart on opposite sides of the city/region on the same day.
   - Account for realistic travel times between consecutive stops (e.g. "15 mins via taxi", "10 mins walk").
   - Day 1: Include arrival, check-in buffer, orientation, and relaxed nearby exploration.
   - Final Day: Include check-out, iconic final sightseeing/souvenir stop, and departure buffer.

3. TRAVEL PACING & REALISM:
   - Do NOT create impossible back-to-back schedules (e.g., 08:00->09:00->10:00).
   - Each major activity must have an adequate visit duration (typically 90 to 180 minutes) plus buffer time.
   - Allow comfortable meal breaks (45-75 minutes) and afternoon rest or shaded activities during hot hours.

4. ACTIVITY SPECIFICATIONS (For EVERY scheduled activity include):
   - `place_name`: Specific, real attraction or venue name (prioritize Stage 5 recommendations).
   - `category`: Category tag (famous_place, cultural_historical, nature_adventure, hidden_gem, food_dining, nearby_place).
   - `description`: Rich overview of the experience.
   - `what_to_do`: Actionable, specific things the traveler should do or see at this location.
   - `why_recommended`: Personalized reason why this place matches traveler interests and travel style.
   - `start_time` and `end_time`: In HH:MM 24-hour format (e.g. "09:30", "12:00").
   - `visit_duration_minutes`: Integer duration in minutes (e.g. 120, 150).
   - `visit_duration`: Human readable string (e.g. "2 hours", "2.5 hours").
   - `estimated_cost`: Realistic entry/activity cost per person in {currency}.
   - `travel_time_from_previous`: Realistic transit time from previous spot (e.g. "20 mins via cab").
   - `transport_mode`: Recommended transit mode (e.g. "taxi", "walking", "metro", "auto-rickshaw", "rental scooter").
   - `practical_tips`: Actionable tips (e.g. best photo angle, what to carry, advance booking advice).
   - `is_indoor`: Boolean (true if indoor/covered, false if outdoor).
   - `weather_suitability`: Weather fit note (e.g. "Optimal during cool morning breeze", "Air-conditioned indoor exhibit").
   - `notes`: Key precautions or entry requirements.

5. STRUCTURED MEAL RECOMMENDATIONS (For EVERY day provide Breakfast, Lunch, Evening Snack, Dinner):
   - Honor dietary requirement: "{food_pref}".
   - Prioritize food dining recommendations from Stage 5 data where available.
   - Include: `name`, `meal` ("breakfast", "lunch", "snack", "dinner"), `restaurant_type`, `cuisine_type`, `estimated_cost` (in {currency}), `suggested_time`, `local_specialty` (signature dish to try), `dietary_fit`.

6. WEATHER ADAPTATION:
   - If rain/storms are forecasted, schedule indoor museums, heritage galleries, or covered markets.
   - If hot (>30°C), schedule outdoor sightseeing during cooler morning/sunset hours and air-conditioned/shaded spots for midday.
   - Include a concise `weather_note` and `weather_summary` for each day.

7. BUDGET & FINANCIAL BREAKDOWN:
   - Provide a realistic `daily_budget` breakdown per day: `food`, `transport`, `activities`, `miscellaneous`, and `total`.
   - Calculate `total_estimated_cost` and evaluate `budget_status` ("within_budget", "near_budget", or "exceeds_budget").

8. OVERALL TRAVEL GUIDANCE:
   - Provide actionable `overall_tips` (transport, local etiquette, currency/tipping).
   - Provide tailored `packing_suggestions` (clothing, accessories, tech, weather gear).

================================================================================
REQUIRED JSON OUTPUT FORMAT:
Return ONLY valid JSON matching this exact structure. No markdown formatting outside JSON. No backticks.

{{
  "trip_summary": {{
    "destination": "{destination}",
    "duration_days": {duration},
    "travel_style": "{travel_style}",
    "estimated_total_cost": 21500.0,
    "budget_status": "within_budget",
    "cost_per_traveler": 10750.0
  }},
  "days": [
    {{
      "day_number": 1,
      "date": "{dates[0]}",
      "theme": "Arrival, Coastal Heritage & Sunset Walk",
      "summary": "Arrive in {destination}, check in, explore the iconic heritage fortress, and unwind at the beach for sunset.",
      "weather_summary": "Sunny with mild coastal breeze (27°C - 30°C)",
      "weather_note": "Pleasant morning and late afternoon; warm at midday.",
      "morning": {{
        "activities": [
          {{
            "time_slot": "morning",
            "start_time": "09:30",
            "end_time": "12:00",
            "place_name": "Historic Coastal Fortress",
            "category": "cultural_historical",
            "description": "Explore the 17th-century fortification overlooking the sea.",
            "what_to_do": "Tour the upper ramparts, visit the lighthouse, and capture panoramic ocean vistas.",
            "why_recommended": "Iconic landmark providing historical context and breathtaking coastal views.",
            "estimated_cost": 200.0,
            "currency": "{currency}",
            "visit_duration_minutes": 150,
            "visit_duration": "2.5 hours",
            "travel_time_from_previous": "25 mins from hotel via cab",
            "transport_mode": "cab",
            "practical_tips": "Wear comfortable walking shoes and carry sunscreen; best photo spot at upper battlement.",
            "is_indoor": false,
            "weather_suitability": "Optimal during cool morning breeze",
            "notes": "Carry drinking water and sun protection"
          }}
        ]
      }},
      "afternoon": {{
        "activities": [
          {{
            "time_slot": "afternoon",
            "start_time": "14:30",
            "end_time": "16:45",
            "place_name": "State Cultural Art Museum",
            "category": "cultural_historical",
            "description": "Contemporary art space showcasing regional history and installations.",
            "what_to_do": "Browse contemporary art galleries, sculpture exhibits, and cultural displays.",
            "why_recommended": "Rich indoor cultural immersion during the warmest afternoon hours.",
            "estimated_cost": 300.0,
            "currency": "{currency}",
            "visit_duration_minutes": 135,
            "visit_duration": "2 hours 15 mins",
            "travel_time_from_previous": "15 mins via auto / taxi",
            "transport_mode": "auto",
            "practical_tips": "Air-conditioned indoors with quiet cafe on site.",
            "is_indoor": true,
            "weather_suitability": "All-weather indoor cultural haven",
            "notes": "Photography permitted without flash"
          }}
        ]
      }},
      "evening": {{
        "activities": [
          {{
            "time_slot": "evening",
            "start_time": "17:30",
            "end_time": "19:45",
            "place_name": "Scenic Sunset Promenade & Beach",
            "category": "famous_place",
            "description": "Golden sand shoreline with panoramic sunset views.",
            "what_to_do": "Stroll along the shoreline, watch the sunset, and enjoy fresh refreshments.",
            "why_recommended": "Vibrant coastal atmosphere with scenic golden-hour photography.",
            "estimated_cost": 0.0,
            "currency": "{currency}",
            "visit_duration_minutes": 135,
            "visit_duration": "2 hours 15 mins",
            "travel_time_from_previous": "12 mins via auto",
            "transport_mode": "auto",
            "practical_tips": "Arrive by 17:30 for prime golden-hour lighting.",
            "is_indoor": false,
            "weather_suitability": "Pleasant open-air evening conditions",
            "notes": "Great sunset photography spot"
          }}
        ]
      }},
      "night": {{
        "activities": []
      }},
      "activities": [
        /* Combined list of all morning, afternoon, evening, night activities */
      ],
      "meals": {{
        "breakfast": {{
          "name": "Heritage Cafe & Bakery",
          "meal": "breakfast",
          "restaurant_type": "Artisanal Cafe & Bakery",
          "cuisine_type": "Regional & Continental Breakfast",
          "estimated_cost": 350.0,
          "currency": "{currency}",
          "suggested_time": "08:00 - 09:00",
          "local_specialty": "Traditional Poi bread with preserves / Masala Omelette",
          "dietary_fit": "{food_pref}"
        }},
        "lunch": {{
          "name": "Local Cuisine Thali House",
          "meal": "lunch",
          "restaurant_type": "Authentic Thali Dining",
          "cuisine_type": "Regional Vegetarian & Traditional Thali",
          "estimated_cost": 450.0,
          "currency": "{currency}",
          "suggested_time": "12:30 - 13:45",
          "local_specialty": "Traditional Multi-Curry Thali with local breads",
          "dietary_fit": "{food_pref}"
        }},
        "snack": {{
          "name": "Garden Tea Lounge",
          "meal": "snack",
          "restaurant_type": "Garden Tearoom",
          "cuisine_type": "Artisanal Teas & Pastries",
          "estimated_cost": 250.0,
          "currency": "{currency}",
          "suggested_time": "16:45 - 17:15",
          "local_specialty": "Iced lemongrass tea & warm savoury scones",
          "dietary_fit": "{food_pref}"
        }},
        "dinner": {{
          "name": "Waterfront Regional Restaurant",
          "meal": "dinner",
          "restaurant_type": "Waterfront Dining",
          "cuisine_type": "Local Coastal & Regional Specialties",
          "estimated_cost": 750.0,
          "currency": "{currency}",
          "suggested_time": "20:00 - 21:30",
          "local_specialty": "Signature regional curry with aromatic rice",
          "dietary_fit": "{food_pref}"
        }}
      }},
      "food_recommendations": [
        /* Combined list of breakfast, lunch, snack, dinner objects */
      ],
      "daily_budget": {{
        "food": 1800.0,
        "transport": 800.0,
        "activities": 500.0,
        "miscellaneous": 300.0,
        "total": 3400.0
      }},
      "travel_tips": [
        "Pre-book local cabs or hire a vehicle for seamless point-to-point transit.",
        "Keep cash handy for local beach shacks and entry tickets."
      ],
      "estimated_day_cost": 3400.0,
      "notes": "Comfortable exploration clustered in northern coastal district to minimize transit fatigue."
    }}
  ],
  "overall_tips": [
    "Hire a private car or reliable taxi package for multi-point sightseeing days.",
    "Stay hydrated and carry high-SPF sunscreen during midday excursions."
  ],
  "packing_suggestions": [
    "Lightweight breathable cotton clothing",
    "Comfortable walking shoes & slip-on beach sandals",
    "Sun hat, UV sunglasses, and sunscreen",
    "Power bank and portable umbrella"
  ],
  "total_estimated_cost": 21500.0,
  "cost_per_traveler": 10750.0,
  "budget": {budget if budget > 0 else 25000.0},
  "currency": "{currency}",
  "budget_status": "within_budget",
  "budget_warning": null,
  "weather_advisory": "Favorable dry conditions expected throughout the trip."
}}
"""
        return prompt

    @classmethod
    def _sanitize_activity_item(
        cls,
        raw_act: Dict[str, Any],
        default_slot: str,
        default_start: str,
        default_end: str,
        currency: str,
        visited_places: set,
    ) -> Optional[Dict[str, Any]]:
        """Sanitizes a single activity item with full metadata."""
        if not isinstance(raw_act, dict):
            return None

        p_name = (raw_act.get("place_name") or raw_act.get("name") or "").strip()
        if not p_name:
            return None

        # Deduplication / area differentiation
        clean_key = p_name.lower()
        if clean_key in visited_places and len(visited_places) < 25:
            p_name = f"{p_name} Exploration & Surroundings"
        visited_places.add(clean_key)

        slot = raw_act.get("time_slot") or default_slot
        start_t = raw_act.get("start_time") or default_start
        end_t = raw_act.get("end_time") or default_end

        cost = 0.0
        if raw_act.get("estimated_cost") is not None:
            try:
                cost = max(0.0, float(raw_act.get("estimated_cost")))
            except (ValueError, TypeError):
                cost = 0.0

        dur_min = 120
        if raw_act.get("visit_duration_minutes"):
            try:
                dur_min = max(30, int(raw_act.get("visit_duration_minutes")))
            except (ValueError, TypeError):
                dur_min = 120

        dur_str = raw_act.get("visit_duration") or (f"{dur_min // 60}h {dur_min % 60}m" if dur_min % 60 else f"{dur_min // 60} hours")
        desc = raw_act.get("description") or f"Explore and experience {p_name}."
        what_to_do = raw_act.get("what_to_do") or desc
        why_rec = raw_act.get("why_recommended") or raw_act.get("why_it_is_recommended") or "Top recommended highlight offering authentic regional character."
        travel_time = raw_act.get("travel_time_from_previous") or "15-20 mins via local transit"
        transport_mode = raw_act.get("transport_mode") or raw_act.get("recommended_transport_mode") or "cab / taxi"
        practical_tips = raw_act.get("practical_tips") or raw_act.get("notes") or "Wear comfortable footwear and carry water."
        is_indoor = raw_act.get("is_indoor")
        if is_indoor is None:
            cat = str(raw_act.get("category", "")).lower()
            is_indoor = cat in ("cultural_historical", "museum", "art_gallery", "stay_area")
        weather_suit = raw_act.get("weather_suitability") or ("All-weather indoor attraction" if is_indoor else "Optimal for fair weather conditions")

        return {
            "time_slot": slot,
            "start_time": start_t,
            "end_time": end_t,
            "place_name": p_name,
            "category": raw_act.get("category") or "famous_place",
            "description": desc,
            "what_to_do": what_to_do,
            "why_recommended": why_rec,
            "estimated_cost": round(cost, 2),
            "currency": currency,
            "visit_duration_minutes": dur_min,
            "visit_duration": dur_str,
            "travel_time_from_previous": travel_time,
            "transport_mode": transport_mode,
            "practical_tips": practical_tips,
            "is_indoor": bool(is_indoor),
            "weather_suitability": weather_suit,
            "notes": raw_act.get("notes") or practical_tips,
        }

    @classmethod
    def _sanitize_meal_item(
        cls,
        raw_meal: Dict[str, Any],
        meal_type: str,
        currency: str,
        default_cost: float,
        default_time: str,
        dietary_pref: str,
    ) -> Dict[str, Any]:
        """Sanitizes a single meal item with full metadata."""
        if not isinstance(raw_meal, dict):
            raw_meal = {}

        name = (raw_meal.get("name") or raw_meal.get("place_name") or raw_meal.get("recommended_place") or f"Local {dietary_pref} {meal_type.title()} Spot").strip()
        cuisine = raw_meal.get("cuisine_type") or raw_meal.get("cuisine") or f"{dietary_pref} Regional Specialties"
        rest_type = raw_meal.get("restaurant_type") or ("Artisanal Cafe" if meal_type in ("breakfast", "snack") else "Traditional Regional Dining")

        cost = default_cost
        if raw_meal.get("estimated_cost") is not None:
            try:
                cost = max(0.0, float(raw_meal.get("estimated_cost")))
            except (ValueError, TypeError):
                cost = default_cost

        time_val = raw_meal.get("suggested_time") or raw_meal.get("time") or default_time
        specialty = raw_meal.get("local_specialty") or f"Chef's special {dietary_pref} delicacy"
        dietary_fit = raw_meal.get("dietary_fit") or dietary_pref

        return {
            "name": name,
            "meal": meal_type,
            "restaurant_type": rest_type,
            "cuisine_type": cuisine,
            "estimated_cost": round(cost, 2),
            "currency": currency,
            "suggested_time": time_val,
            "local_specialty": specialty,
            "dietary_fit": dietary_fit,
        }

    @classmethod
    def validate_and_sanitize_itinerary(
        cls,
        raw_data: Dict[str, Any],
        state: TravelState,
    ) -> Dict[str, Any]:
        """
        Validates structure, ensures day count and dates align, sanitizes costs,
        harmonizes time slots and meals, computes daily budgets, and deduplicates places.
        """
        dates, expected_duration = cls.calculate_trip_dates(state)
        currency = state.get("currency") or "INR"
        budget = float(state.get("budget") or 0.0)
        travelers = int(state.get("travelers") or (state.get("adults") or 1) + (state.get("children") or 0))
        if travelers <= 0:
            travelers = 1
        food_pref = (state.get("food_preference") or "Local Cuisine").title()
        travel_style = state.get("travel_style") or "balanced pace"
        destination = state.get("destination") or "Unknown Destination"

        raw_days = raw_data.get("days") if isinstance(raw_data, dict) else []
        if not isinstance(raw_days, list) or len(raw_days) == 0:
            raise ValueError("Itinerary response missing valid 'days' list.")

        sanitized_days: List[Dict[str, Any]] = []
        visited_places: set = set()
        total_trip_cost = 0.0

        for idx in range(expected_duration):
            raw_day = raw_days[idx] if idx < len(raw_days) and isinstance(raw_days[idx], dict) else {}
            day_num = idx + 1
            day_date = dates[idx]

            day_theme = (
                raw_day.get("theme")
                or raw_day.get("title")
                or f"Day {day_num}: {destination} Exploration & Culture"
            )
            day_summary = (
                raw_day.get("summary")
                or f"Experience the key highlights, culture, and cuisine of {destination} on Day {day_num}."
            )
            weather_sum = (
                raw_day.get("weather_summary")
                or raw_day.get("weather_note")
                or "Pleasant conditions suitable for sightseeing and exploration."
            )
            weather_note = raw_day.get("weather_note") or weather_sum

            # Collect activities from both slot containers and flat list
            morning_acts_raw = []
            afternoon_acts_raw = []
            evening_acts_raw = []
            night_acts_raw = []

            # Check structured slots first
            if isinstance(raw_day.get("morning"), dict) and isinstance(raw_day["morning"].get("activities"), list):
                morning_acts_raw.extend(raw_day["morning"]["activities"])
            if isinstance(raw_day.get("afternoon"), dict) and isinstance(raw_day["afternoon"].get("activities"), list):
                afternoon_acts_raw.extend(raw_day["afternoon"]["activities"])
            if isinstance(raw_day.get("evening"), dict) and isinstance(raw_day["evening"].get("activities"), list):
                evening_acts_raw.extend(raw_day["evening"]["activities"])
            if isinstance(raw_day.get("night"), dict) and isinstance(raw_day["night"].get("activities"), list):
                night_acts_raw.extend(raw_day["night"]["activities"])

            # Check flat activities list
            flat_activities = raw_day.get("activities") or []
            for act in flat_activities:
                if not isinstance(act, dict):
                    continue
                slot = str(act.get("time_slot", "")).lower()
                if slot == "morning" and act not in morning_acts_raw:
                    morning_acts_raw.append(act)
                elif slot == "afternoon" and act not in afternoon_acts_raw:
                    afternoon_acts_raw.append(act)
                elif slot == "evening" and act not in evening_acts_raw:
                    evening_acts_raw.append(act)
                elif slot == "night" and act not in night_acts_raw:
                    night_acts_raw.append(act)
                elif act not in morning_acts_raw and act not in afternoon_acts_raw and act not in evening_acts_raw and act not in night_acts_raw:
                    if len(morning_acts_raw) == 0:
                        morning_acts_raw.append(act)
                    elif len(afternoon_acts_raw) == 0:
                        afternoon_acts_raw.append(act)
                    elif len(evening_acts_raw) == 0:
                        evening_acts_raw.append(act)
                    else:
                        night_acts_raw.append(act)

            # Sanitize each slot's activities
            sanitized_morning = []
            for m_act in morning_acts_raw:
                san = cls._sanitize_activity_item(m_act, "morning", "09:30", "12:00", currency, visited_places)
                if san:
                    sanitized_morning.append(san)

            sanitized_afternoon = []
            for a_act in afternoon_acts_raw:
                san = cls._sanitize_activity_item(a_act, "afternoon", "14:30", "16:45", currency, visited_places)
                if san:
                    sanitized_afternoon.append(san)

            sanitized_evening = []
            for e_act in evening_acts_raw:
                san = cls._sanitize_activity_item(e_act, "evening", "17:30", "19:45", currency, visited_places)
                if san:
                    sanitized_evening.append(san)

            sanitized_night = []
            for n_act in night_acts_raw:
                san = cls._sanitize_activity_item(n_act, "night", "20:30", "22:00", currency, visited_places)
                if san:
                    sanitized_night.append(san)

            # Ensure every day has at least morning, afternoon, and evening activities
            if not sanitized_morning:
                sanitized_morning.append({
                    "time_slot": "morning",
                    "start_time": "09:30",
                    "end_time": "12:00",
                    "place_name": f"{destination} Heritage Walk & Landmarks",
                    "category": "famous_place",
                    "description": f"Morning discovery walk exploring iconic landmarks of {destination}.",
                    "what_to_do": f"Visit the landmark heritage precinct and take photographs.",
                    "why_recommended": "Essential sightseeing spot for first-time and returning visitors.",
                    "estimated_cost": 200.0,
                    "currency": currency,
                    "visit_duration_minutes": 150,
                    "visit_duration": "2.5 hours",
                    "travel_time_from_previous": "15 mins via local transit",
                    "transport_mode": "cab",
                    "practical_tips": "Start early to avoid heat and queues.",
                    "is_indoor": False,
                    "weather_suitability": "Optimal during cool morning hours",
                    "notes": "Carry sunscreen and water",
                })

            if not sanitized_afternoon:
                sanitized_afternoon.append({
                    "time_slot": "afternoon",
                    "start_time": "14:30",
                    "end_time": "16:45",
                    "place_name": f"{destination} Art Gallery & Cultural Museum",
                    "category": "cultural_historical",
                    "description": f"Indoor cultural exploration showcasing regional history and art.",
                    "what_to_do": f"Tour exhibits, galleries, and artifact collections.",
                    "why_recommended": "Pleasant indoor cultural experience during the midday hours.",
                    "estimated_cost": 250.0,
                    "currency": currency,
                    "visit_duration_minutes": 135,
                    "visit_duration": "2 hours 15 mins",
                    "travel_time_from_previous": "15 mins via auto / taxi",
                    "transport_mode": "auto",
                    "practical_tips": "Air-conditioned indoor exhibit space.",
                    "is_indoor": True,
                    "weather_suitability": "All-weather indoor facility",
                    "notes": "Photography permitted in main halls",
                })

            if not sanitized_evening:
                sanitized_evening.append({
                    "time_slot": "evening",
                    "start_time": "17:30",
                    "end_time": "19:45",
                    "place_name": f"{destination} Scenic Sunset Promenade",
                    "category": "nature_adventure",
                    "description": f"Relaxed evening stroll along the scenic promenade as the sun sets.",
                    "what_to_do": f"Enjoy sunset vistas, coastal breeze, and local street delicacies.",
                    "why_recommended": "Prime golden-hour spot with refreshing open-air ambience.",
                    "estimated_cost": 0.0,
                    "currency": currency,
                    "visit_duration_minutes": 135,
                    "visit_duration": "2 hours 15 mins",
                    "travel_time_from_previous": "15 mins via auto",
                    "transport_mode": "auto",
                    "practical_tips": "Arrive before sunset for prime lighting.",
                    "is_indoor": False,
                    "weather_suitability": "Pleasant open-air evening breeze",
                    "notes": "Great sunset photography spot",
                })

            all_day_activities = sanitized_morning + sanitized_afternoon + sanitized_evening + sanitized_night

            # Parse Meals (both structured dict and list)
            raw_meals_dict = raw_day.get("meals") if isinstance(raw_day.get("meals"), dict) else {}
            raw_foods_list = raw_day.get("food_recommendations") or []

            b_raw = raw_meals_dict.get("breakfast") or next((f for f in raw_foods_list if str(f.get("meal", "")).lower() == "breakfast"), {})
            l_raw = raw_meals_dict.get("lunch") or next((f for f in raw_foods_list if str(f.get("meal", "")).lower() == "lunch"), {})
            s_raw = raw_meals_dict.get("snack") or next((f for f in raw_foods_list if str(f.get("meal", "")).lower() == "snack"), {})
            d_raw = raw_meals_dict.get("dinner") or next((f for f in raw_foods_list if str(f.get("meal", "")).lower() == "dinner"), {})

            breakfast_item = cls._sanitize_meal_item(b_raw, "breakfast", currency, 300.0, "08:00 - 09:00", food_pref)
            lunch_item = cls._sanitize_meal_item(l_raw, "lunch", currency, 450.0, "12:30 - 13:45", food_pref)
            snack_item = cls._sanitize_meal_item(s_raw, "snack", currency, 200.0, "16:45 - 17:15", food_pref)
            dinner_item = cls._sanitize_meal_item(d_raw, "dinner", currency, 650.0, "20:00 - 21:30", food_pref)

            structured_meals = {
                "breakfast": breakfast_item,
                "lunch": lunch_item,
                "snack": snack_item,
                "dinner": dinner_item,
            }
            food_recommendations_list = [breakfast_item, lunch_item, snack_item, dinner_item]

            # Daily budget calculation
            day_act_cost = sum(a["estimated_cost"] for a in all_day_activities)
            day_food_cost = sum(f["estimated_cost"] for f in food_recommendations_list)
            
            raw_daily_budget = raw_day.get("daily_budget") or {}
            transport_budget = float(raw_daily_budget.get("transport") or 600.0)
            misc_budget = float(raw_daily_budget.get("miscellaneous") or 250.0)

            day_total_cost = round(day_act_cost + day_food_cost + transport_budget + misc_budget, 2)
            total_trip_cost += day_total_cost

            daily_budget_breakdown = {
                "food": round(day_food_cost, 2),
                "transport": round(transport_budget, 2),
                "activities": round(day_act_cost, 2),
                "miscellaneous": round(misc_budget, 2),
                "total": day_total_cost,
            }

            travel_tips = raw_day.get("travel_tips") or [
                f"Cluster stops in the {destination} core area to avoid peak transit congestion.",
                "Carry local currency cash for entry tickets and small vendors.",
            ]

            sanitized_days.append({
                "day_number": day_num,
                "date": day_date,
                "theme": day_theme,
                "summary": day_summary,
                "weather_summary": weather_sum,
                "weather_note": weather_note,
                "morning": {"activities": sanitized_morning},
                "afternoon": {"activities": sanitized_afternoon},
                "evening": {"activities": sanitized_evening},
                "night": {"activities": sanitized_night},
                "activities": all_day_activities,
                "meals": structured_meals,
                "food_recommendations": food_recommendations_list,
                "daily_budget": daily_budget_breakdown,
                "travel_tips": travel_tips,
                "estimated_day_cost": day_total_cost,
                "notes": raw_day.get("notes") or f"Day {day_num} curated for balanced sightseeing and culinary discovery.",
            })

        # Overall trip summary & budget status
        cost_per_person = round(total_trip_cost / travelers, 2)
        budget_status = "within_budget"
        budget_warning = None

        if budget > 0:
            if total_trip_cost <= budget * 1.05:
                budget_status = "within_budget"
            elif budget * 1.05 < total_trip_cost <= budget * 1.25:
                budget_status = "near_budget"
                diff = total_trip_cost - budget
                budget_warning = (
                    f"Estimated trip cost ({currency} {int(total_trip_cost):,}) is slightly above budget "
                    f"({currency} {int(budget):,}) by ~{currency} {int(diff):,}."
                )
            else:
                budget_status = "exceeds_budget"
                diff = total_trip_cost - budget
                budget_warning = (
                    f"Estimated trip cost ({currency} {int(total_trip_cost):,}) exceeds your budget "
                    f"({currency} {int(budget):,}) by {currency} {int(diff):,}."
                )
        else:
            budget_status = "unspecified"

        overall_tips = raw_data.get("overall_tips") or [
            "Use pre-booked local cabs or trusted ride-hailing for seamless travel between clusters.",
            "Stay well hydrated and take shaded breaks during the hottest midday hours.",
            "Keep emergency contact numbers and local digital maps accessible offline.",
        ]

        packing_suggestions = raw_data.get("packing_suggestions") or [
            "Breathable lightweight cotton clothing & sun hat",
            "Comfortable walking shoes & sandals",
            "High SPF sunscreen & UV protective sunglasses",
            "Universal charging adapter & portable power bank",
        ]

        trip_summary = raw_data.get("trip_summary") or {
            "destination": destination,
            "duration_days": expected_duration,
            "travel_style": travel_style,
            "estimated_total_cost": round(total_trip_cost, 2),
            "budget_status": budget_status,
            "cost_per_traveler": cost_per_person,
        }

        return {
            "trip_id": state.get("trip_id") or "",
            "destination": destination,
            "start_date": dates[0],
            "end_date": dates[-1],
            "duration_days": expected_duration,
            "total_estimated_cost": round(total_trip_cost, 2),
            "cost_per_traveler": cost_per_person,
            "budget": budget if budget > 0 else None,
            "currency": currency,
            "budget_status": budget_status,
            "budget_warning": budget_warning,
            "weather_advisory": raw_data.get("weather_advisory") or "Favorable travel conditions expected.",
            "trip_summary": trip_summary,
            "overall_tips": overall_tips,
            "packing_suggestions": packing_suggestions,
            "days": sanitized_days,
        }

    @classmethod
    def generate_fallback_itinerary(cls, state: TravelState) -> Dict[str, Any]:
        """
        Creates a high-quality, comprehensive deterministic itinerary by synthesizing
        available Stage 5 destination recommendations and Stage 6 weather data.
        """
        dates, duration = cls.calculate_trip_dates(state)
        destination = state.get("destination") or "Trip"
        currency = state.get("currency") or "INR"
        budget = float(state.get("budget") or 0.0)
        travelers = int(state.get("travelers") or (state.get("adults") or 1) + (state.get("children") or 0))
        if travelers <= 0:
            travelers = 1
        food_pref = (state.get("food_preference") or "Local Cuisine").title()
        travel_style = state.get("travel_style") or "balanced pace"

        recs = state.get("destination_recommendations") or []
        weather_insights = state.get("weather_insights") or []
        weather_summary_default = (
            weather_insights[0].get("message")
            if weather_insights and isinstance(weather_insights[0], dict)
            else "Favorable conditions for day tours and outdoor sightseeing."
        )

        # Categorized buckets
        famous = [r for r in recs if r.get("category") == "famous_place"]
        nature = [r for r in recs if r.get("category") in ("nature_adventure", "nearby_place")]
        cultural = [r for r in recs if r.get("category") == "cultural_historical"]
        gems = [r for r in recs if r.get("category") == "hidden_gem"]
        foods = [r for r in recs if r.get("category") == "food_dining"]

        fallback_themes = [
            f"Iconic Landmarks & Coastal Heritage of {destination}",
            f"Cultural Trail, Architecture & Artisanal Traditions",
            f"Nature Excursions, Hidden Gems & Scenic Countryside",
            f"Local Markets, Culinary Delights & Sunset Promenade",
            f"Relaxed Discovery, Leisure Exploration & Local Flavors",
        ]

        days: List[Dict[str, Any]] = []
        total_trip_cost = 0.0

        for i in range(duration):
            day_num = i + 1
            day_date = dates[i]
            theme = fallback_themes[i % len(fallback_themes)]

            # Select 3 activities
            p1 = famous[i % len(famous)] if famous else {"name": f"{destination} Historic Central Landmark", "category": "famous_place", "description": f"Explore the premier historic monument and iconic center of {destination}."}
            p2 = (cultural[i % len(cultural)] if cultural else (nature[i % len(nature)] if nature else {"name": f"{destination} Heritage Museum & Art Gallery", "category": "cultural_historical", "description": f"Indoor museum displaying cultural treasures and heritage of {destination}."}))
            p3 = gems[i % len(gems)] if gems else (nature[i % len(nature)] if nature else {"name": f"{destination} Sunset Viewpoint & Promenade", "category": "nature_adventure", "description": f"Scenic coastal viewpoint offering panoramic golden-hour sunset vistas."})

            act1_cost = float(p1.get("estimated_cost") or 200.0)
            act2_cost = float(p2.get("estimated_cost") or 250.0)
            act3_cost = float(p3.get("estimated_cost") or 0.0)

            act1 = {
                "time_slot": "morning",
                "start_time": "09:30",
                "end_time": "12:00",
                "place_name": p1.get("name"),
                "category": p1.get("category") or "famous_place",
                "description": p1.get("description") or f"Morning exploration of {p1.get('name')}.",
                "what_to_do": f"Tour the main grounds of {p1.get('name')}, explore the architectural exhibits, and take photos.",
                "why_recommended": p1.get("why_recommended") or f"Top-rated landmark showcasing the historical identity of {destination}.",
                "estimated_cost": act1_cost,
                "currency": currency,
                "visit_duration_minutes": 150,
                "visit_duration": "2.5 hours",
                "travel_time_from_previous": "20 mins from hotel via cab",
                "transport_mode": "cab",
                "practical_tips": "Start early to enjoy comfortable morning light.",
                "is_indoor": False,
                "weather_suitability": "Optimal during cool morning hours",
                "notes": "Best experienced in early morning light.",
            }

            act2 = {
                "time_slot": "afternoon",
                "start_time": "14:30",
                "end_time": "16:45",
                "place_name": p2.get("name"),
                "category": p2.get("category") or "cultural_historical",
                "description": p2.get("description") or f"Afternoon cultural visit to {p2.get('name')}.",
                "what_to_do": f"Browse regional galleries, historical artifacts, and artisan exhibits at {p2.get('name')}.",
                "why_recommended": p2.get("why_recommended") or "Provides deep cultural perspective and comfortable indoor pacing.",
                "estimated_cost": act2_cost,
                "currency": currency,
                "visit_duration_minutes": 135,
                "visit_duration": "2 hours 15 mins",
                "travel_time_from_previous": "15 mins via auto / taxi",
                "transport_mode": "auto",
                "practical_tips": "Air-conditioned indoor exhibit; audio guides available.",
                "is_indoor": True,
                "weather_suitability": "All-weather indoor cultural haven",
                "notes": "Indoor or shaded sightseeing during midday.",
            }

            act3 = {
                "time_slot": "evening",
                "start_time": "17:30",
                "end_time": "19:45",
                "place_name": p3.get("name"),
                "category": p3.get("category") or "nature_adventure",
                "description": p3.get("description") or f"Sunset relaxation at {p3.get('name')}.",
                "what_to_do": f"Stroll around the viewpoint, watch the sunset, and take evening photographs.",
                "why_recommended": p3.get("why_recommended") or "Scenic open-air viewpoint for golden-hour relaxation.",
                "estimated_cost": act3_cost,
                "currency": currency,
                "visit_duration_minutes": 135,
                "visit_duration": "2 hours 15 mins",
                "travel_time_from_previous": "15 mins via auto",
                "transport_mode": "auto",
                "practical_tips": "Arrive by 17:30 for prime golden-hour lighting.",
                "is_indoor": False,
                "weather_suitability": "Pleasant open-air evening breeze",
                "notes": "Scenic viewpoint for sunset relaxation.",
            }

            day_activities = [act1, act2, act3]

            # Food recommendations
            f_spot = foods[i % len(foods)] if foods else {}
            f_name = f_spot.get("name") or f"{destination} Authentic {food_pref} Bistro"

            breakfast = {
                "name": f"{destination} Heritage Cafe",
                "meal": "breakfast",
                "restaurant_type": "Artisanal Cafe",
                "cuisine_type": f"{food_pref} Breakfast & Pastries",
                "estimated_cost": 300.0,
                "currency": currency,
                "suggested_time": "08:00 - 09:00",
                "local_specialty": "Fresh baked local breads with artisan tea/coffee",
                "dietary_fit": food_pref,
            }
            lunch = {
                "name": f_name,
                "meal": "lunch",
                "restaurant_type": "Traditional Dining House",
                "cuisine_type": f"{food_pref} Regional Specialties",
                "estimated_cost": 450.0,
                "currency": currency,
                "suggested_time": "12:30 - 13:45",
                "local_specialty": f"Signature {destination} {food_pref} Thali",
                "dietary_fit": food_pref,
            }
            snack = {
                "name": f"{destination} Garden Tearoom",
                "meal": "snack",
                "restaurant_type": "Tea Lounge",
                "cuisine_type": "Artisanal Teas & Savouries",
                "estimated_cost": 200.0,
                "currency": currency,
                "suggested_time": "16:45 - 17:15",
                "local_specialty": "Iced herbal tea with savoury bites",
                "dietary_fit": food_pref,
            }
            dinner = {
                "name": f"{destination} Coastal View Dining",
                "meal": "dinner",
                "restaurant_type": "Waterfront Dining",
                "cuisine_type": f"{food_pref} Gourmet",
                "estimated_cost": 650.0,
                "currency": currency,
                "suggested_time": "20:00 - 21:30",
                "local_specialty": f"Chef's special {food_pref} dinner curry & rice",
                "dietary_fit": food_pref,
            }

            structured_meals = {
                "breakfast": breakfast,
                "lunch": lunch,
                "snack": snack,
                "dinner": dinner,
            }
            food_recs = [breakfast, lunch, snack, dinner]

            transport_cost = 600.0
            misc_cost = 250.0
            day_act_total = act1_cost + act2_cost + act3_cost
            day_food_total = 300.0 + 450.0 + 200.0 + 650.0
            day_cost = round(day_act_total + day_food_total + transport_cost + misc_cost, 2)
            total_trip_cost += day_cost

            daily_budget = {
                "food": day_food_total,
                "transport": transport_cost,
                "activities": day_act_total,
                "miscellaneous": misc_cost,
                "total": day_cost,
            }

            days.append({
                "day_number": day_num,
                "date": day_date,
                "theme": theme,
                "summary": f"Day {day_num} in {destination} featuring {act1['place_name']}, {act2['place_name']}, and {act3['place_name']}.",
                "weather_summary": weather_summary_default,
                "weather_note": weather_summary_default,
                "morning": {"activities": [act1]},
                "afternoon": {"activities": [act2]},
                "evening": {"activities": [act3]},
                "night": {"activities": []},
                "activities": day_activities,
                "meals": structured_meals,
                "food_recommendations": food_recs,
                "daily_budget": daily_budget,
                "travel_tips": [
                    f"Cluster stops in the {destination} core to reduce transit overhead.",
                    "Keep local currency cash on hand for entry fees and local vendors.",
                ],
                "estimated_day_cost": day_cost,
                "notes": "Coordinated itinerary with clustered transit and balanced pacing.",
            })

        cost_per_person = round(total_trip_cost / travelers, 2)
        budget_status = "within_budget"
        budget_warning = None
        if budget > 0:
            if total_trip_cost <= budget * 1.05:
                budget_status = "within_budget"
            elif budget * 1.05 < total_trip_cost <= budget * 1.25:
                budget_status = "near_budget"
                diff = total_trip_cost - budget
                budget_warning = (
                    f"Estimated itinerary cost ({currency} {int(total_trip_cost):,}) is near budget "
                    f"({currency} {int(budget):,}) by ~{currency} {int(diff):,}."
                )
            else:
                budget_status = "exceeds_budget"
                diff = total_trip_cost - budget
                budget_warning = (
                    f"Estimated itinerary cost ({currency} {int(total_trip_cost):,}) exceeds budget "
                    f"({currency} {int(budget):,}) by {currency} {int(diff):,}."
                )

        trip_summary = {
            "destination": destination,
            "duration_days": duration,
            "travel_style": travel_style,
            "estimated_total_cost": round(total_trip_cost, 2),
            "budget_status": budget_status,
            "cost_per_traveler": cost_per_person,
        }

        return {
            "trip_id": state.get("trip_id") or "",
            "destination": destination,
            "start_date": dates[0],
            "end_date": dates[-1],
            "duration_days": duration,
            "total_estimated_cost": round(total_trip_cost, 2),
            "cost_per_traveler": cost_per_person,
            "budget": budget if budget > 0 else None,
            "currency": currency,
            "budget_status": budget_status,
            "budget_warning": budget_warning,
            "weather_advisory": "Weather conditions are favorable across your trip.",
            "trip_summary": trip_summary,
            "overall_tips": [
                "Use pre-arranged local taxis or rental cars for smooth transit between districts.",
                "Stay well hydrated during midday exploration.",
                "Keep cash handy for entry tickets and small dining spots.",
            ],
            "packing_suggestions": [
                "Light breathable clothing & comfortable footwear",
                "Sun protection: hat, sunglasses, sunscreen",
                "Universal power adapter and power bank",
            ],
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
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")

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
                model=model_name,
                contents=prompt,
            )

            raw_text = getattr(response, "text", "") or ""
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
