"""
Live Gemini Test for Stage 10 Itinerary Agent.

Specs:
- Destination: Goa
- Duration: 4 days (2026-11-01 to 2026-11-04)
- Travelers: 2 adults (0 children)
- Budget: INR 30,000
- Food: Vegetarian
- Interests: beaches, culture, food, hidden gems
- Travel style: Budget/Moderate
"""

import json
import logging
import sys
from pprint import pprint

from app.agents.itinerary_agent import ItineraryAgent
from app.graph.state import create_initial_travel_state
from app.schemas.agent import ItineraryData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_live_test():
    print("=" * 80)
    print("STAGE 10: RUNNING LIVE GEMINI ITINERARY TEST")
    print("=" * 80)

    # Mock realistic Stage 5 Destination Recommendations
    destination_recs = [
        {
            "name": "Aguada Fort & Lighthouse",
            "category": "famous_place",
            "description": "17th-century Portuguese fortress with panoramic Arabian Sea views.",
            "why_recommended": "Iconic heritage landmark with coastal ramparts and scenic ocean photography.",
            "estimated_cost": 200.0,
            "estimated_visit_duration": "2.5 hours",
            "best_time_to_visit": "09:30 - 12:00",
            "distance_from_destination": "North Goa",
            "tags": ["heritage", "beaches", "views"],
        },
        {
            "name": "Fontainhas Latin Quarter",
            "category": "cultural_historical",
            "description": "Historic Portuguese quarter featuring pastel-colored heritage villas and galleries.",
            "why_recommended": "Authentic architectural charm and sheltered heritage walkways.",
            "estimated_cost": 0.0,
            "estimated_visit_duration": "2 hours",
            "best_time_to_visit": "15:00 - 17:00",
            "distance_from_destination": "Panaji Central",
            "tags": ["culture", "architecture", "photography"],
        },
        {
            "name": "Divar Island & Village",
            "category": "hidden_gem",
            "description": "Serene river island accessible by ferry, surrounded by lush paddy fields and old churches.",
            "why_recommended": "Off-beat tranquil island escape away from crowds.",
            "estimated_cost": 50.0,
            "estimated_visit_duration": "3 hours",
            "best_time_to_visit": "09:00 - 12:00",
            "distance_from_destination": "Mandovi River",
            "tags": ["hidden gems", "nature", "culture"],
        },
        {
            "name": "Anjuna Flea Market & Sunset Point",
            "category": "famous_place",
            "description": "Vibrant beachside marketplace with handicrafts, spices, and golden sunset views.",
            "why_recommended": "Classic Goa bohemian market experience and prime sunset views.",
            "estimated_cost": 100.0,
            "estimated_visit_duration": "2.5 hours",
            "best_time_to_visit": "16:30 - 19:00",
            "distance_from_destination": "North Goa",
            "tags": ["shopping", "beaches", "sunset"],
        },
        {
            "name": "Bhakti Kutir Organic Cafe",
            "category": "food_dining",
            "description": "Eco-friendly garden restaurant serving regional organic vegetarian dishes.",
            "why_recommended": "Top-rated vegetarian dining with fresh local produce.",
            "estimated_cost": 450.0,
            "distance_from_destination": "South Goa",
            "tags": ["food", "vegetarian", "organic"],
        },
    ]

    # Mock realistic Stage 6 Weather Data
    weather_curr = {
        "temperature": 29.5,
        "feels_like": 31.0,
        "weather_condition": "Sunny",
        "weather_description": "Clear skies with coastal breeze",
        "rain_probability": 0.05,
        "humidity": 65,
        "wind_speed": 3.8,
    }

    weather_forecast = [
        {"date": "2026-11-01", "time": "12:00", "temperature": 30.0, "weather_condition": "Sunny", "weather_description": "Clear", "rain_probability": 0.0},
        {"date": "2026-11-02", "time": "12:00", "temperature": 29.0, "weather_condition": "Partly Cloudy", "weather_description": "Scattered Clouds", "rain_probability": 0.1},
        {"date": "2026-11-03", "time": "12:00", "temperature": 28.5, "weather_condition": "Sunny", "weather_description": "Clear", "rain_probability": 0.05},
        {"date": "2026-11-04", "time": "12:00", "temperature": 29.0, "weather_condition": "Sunny", "weather_description": "Clear", "rain_probability": 0.0},
    ]

    weather_insights = [
        {"type": "heat_comfort", "title": "Midday Sun Caution", "message": "High UV index during 12:00-15:00; recommend indoor galleries or shaded rest."},
    ]

    state = create_initial_travel_state(
        trip_id="live-test-goa-4day",
        user_id="live-user-1",
        trip_data={
            "destination": "Goa",
            "start_location": "Mumbai",
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "duration_days": 4,
            "travelers": 2,
            "adults": 2,
            "children": 0,
            "budget": 30000.0,
            "currency": "INR",
            "transport_mode": "cab / auto / scooter",
            "food_preference": "Vegetarian",
            "stay_preference": "Boutique Hotel / Heritage Villa",
            "travel_style": "Budget/Moderate",
            "interests": ["beaches", "culture", "food", "hidden gems"],
            "special_requirements": "Vegetarian meals only; prefer scenic sunset views and unhurried pacing.",
            "destination_recommendations": destination_recs,
            "weather_current": weather_curr,
            "weather_forecast": weather_forecast,
            "weather_insights": weather_insights,
        },
    )

    result = ItineraryAgent.generate_itinerary(state)
    assert result["itinerary_status"] == "ready", f"Unexpected status: {result.get('itinerary_status')}"
    itin = result["itinerary"]

    # Validate against Pydantic model
    validated = ItineraryData(**itin)
    print(f"\n[OK] Pydantic Schema Validation Passed!")
    print(f"Destination: {validated.destination}")
    print(f"Duration: {validated.duration_days} Days ({validated.start_date} to {validated.end_date})")
    print(f"Total Estimated Cost: {validated.currency} {validated.total_estimated_cost:,.2f}")
    print(f"Cost Per Traveler: {validated.currency} {validated.cost_per_traveler:,.2f}")
    print(f"Budget Status: {validated.budget_status}")
    print(f"Weather Advisory: {validated.weather_advisory}")

    print("\n" + "=" * 80)
    print("DAY-BY-DAY ITINERARY DETAILS:")
    print("=" * 80)

    for day in validated.days:
        print(f"\n[*] DAY {day.day_number} ({day.date}): {day.theme}")
        print(f"   Summary: {day.summary}")
        print(f"   Weather Note: {day.weather_note or day.weather_summary}")
        if day.daily_budget:
            print(f"   Daily Budget: Stay={day.daily_budget.get('accommodation', 0)}, Food={day.daily_budget.get('food', 0)}, Transit={day.daily_budget.get('transport', 0)}, Activities={day.daily_budget.get('activities', 0)}, Total={day.daily_budget.get('total', 0)}")

        print("   --- Activities ---")
        for act in day.activities:
            print(f"   - [{act.time_slot.upper()}] {act.start_time}-{act.end_time}: {act.place_name} ({act.visit_duration})")
            print(f"     Why: {act.why_recommended}")
            print(f"     Transit: {act.travel_time_from_previous} via {act.transport_mode}")
            print(f"     Cost: {act.currency} {act.estimated_cost} | Weather: {act.weather_suitability}")
            if act.practical_tips:
                print(f"     Tips: {act.practical_tips}")

        print("   --- Meals ---")
        if day.meals:
            for m_type, meal in day.meals.items():
                if meal and isinstance(meal, dict):
                    print(f"   * {m_type.upper()}: {meal.get('name')} ({meal.get('suggested_time')}) - Specialty: {meal.get('local_specialty')} [{meal.get('dietary_fit')}]")

    print("\n" + "=" * 80)
    print("EXPERT PACKING SUGGESTIONS:")
    for p in validated.packing_suggestions:
        print(f"   + {p}")

    print("\nOVERALL LOGISTICS TIPS:")
    for t in validated.overall_tips:
        print(f"   * {t}")

    print("\n" + "=" * 80)
    print("LIVE GEMINI TEST VERIFIED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_live_test()
