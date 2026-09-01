"""
Unit and Integration Tests for Stage 7: Itinerary Planning Agent.
"""

import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import jwt

from fastapi.testclient import TestClient

from app.agents.itinerary_agent import ItineraryAgent
from app.core.config import settings
from app.graph.itinerary_graph import run_itinerary_graph
from app.graph.state import create_initial_travel_state
from app.main import app
from app.schemas.agent import (
    ItineraryActivityItem,
    ItineraryData,
    ItineraryDay,
    ItineraryFoodRecommendation,
    ItineraryResponse,
)

client = TestClient(app)


def generate_mock_jwt(user_id: str, email: str = "test@example.com") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "user_metadata": {"full_name": "Test Traveler"},
    }
    secret = settings.SUPABASE_JWT_SECRET or "dev-secret-key-for-testing_at_least_32_bytes"
    return jwt.encode(payload, secret, algorithm="HS256")


def test_1_itinerary_agent_initialization():
    """Verify ItineraryAgent class and calculate_trip_dates."""
    state = create_initial_travel_state(
        trip_id="trip-1",
        user_id="user-1",
        trip_data={
            "destination": "Goa",
            "start_date": "2026-11-01",
            "duration_days": 4,
        },
    )
    dates, duration = ItineraryAgent.calculate_trip_dates(state)
    assert duration == 4
    assert len(dates) == 4
    assert dates[0] == "2026-11-01"
    assert dates[3] == "2026-11-04"


def test_2_complete_travel_state():
    """Verify fallback itinerary with complete TravelState parameters."""
    state = create_initial_travel_state(
        trip_id="trip-2",
        user_id="user-2",
        trip_data={
            "destination": "Goa",
            "start_date": "2026-10-15",
            "duration_days": 3,
            "budget": 25000.0,
            "currency": "INR",
            "food_preference": "vegetarian",
            "interests": ["beaches", "culture"],
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    assert fallback["destination"] == "Goa"
    assert fallback["duration_days"] == 3
    assert len(fallback["days"]) == 3
    assert fallback["total_estimated_cost"] > 0
    assert fallback["budget_status"] == "within_budget"


def test_3_missing_destination():
    """Verify agent returns unavailable error when destination is missing."""
    state = create_initial_travel_state(
        trip_id="trip-3",
        user_id="user-3",
        trip_data={"destination": ""},
    )
    res = ItineraryAgent.generate_itinerary(state)
    assert res["itinerary_status"] == "unavailable"
    assert len(res["itinerary_errors"]) > 0


def test_4_missing_dates():
    """Verify default dates calculation when start_date is omitted."""
    state = create_initial_travel_state(
        trip_id="trip-4",
        user_id="user-4",
        trip_data={"destination": "Manali", "duration_days": 3},
    )
    dates, duration = ItineraryAgent.calculate_trip_dates(state)
    assert duration == 3
    assert len(dates) == 3
    assert len(dates[0].split("-")) == 3


def test_5_invalid_duration():
    """Verify duration normalization when given 0 or negative days."""
    state = create_initial_travel_state(
        trip_id="trip-5",
        user_id="user-5",
        trip_data={"destination": "Jaipur", "duration_days": 0},
    )
    dates, duration = ItineraryAgent.calculate_trip_dates(state)
    assert duration == 3  # normalized default
    assert len(dates) == 3


def test_6_destination_recommendations_integration():
    """Verify that Stage 5 places populate activities in fallback itinerary."""
    state = create_initial_travel_state(
        trip_id="trip-6",
        user_id="user-6",
        trip_data={
            "destination": "Goa",
            "duration_days": 2,
            "destination_recommendations": [
                {
                    "name": "Baga Beach",
                    "category": "famous_place",
                    "description": "Lively coastal beach.",
                    "estimated_cost": 0.0,
                },
                {
                    "name": "Basilica of Bom Jesus",
                    "category": "cultural_historical",
                    "description": "UNESCO world heritage church.",
                    "estimated_cost": 50.0,
                },
            ],
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    names = [act["place_name"] for d in fallback["days"] for act in d["activities"]]
    assert "Baga Beach" in names or "Basilica of Bom Jesus" in names


def test_7_weather_integration():
    """Verify that Stage 6 weather insights inform daily weather summaries."""
    state = create_initial_travel_state(
        trip_id="trip-7",
        user_id="user-7",
        trip_data={
            "destination": "Goa",
            "duration_days": 2,
            "weather_insights": [
                {"title": "Coastal Rain Alert", "message": "Scattered afternoon showers expected.", "type": "rain_alert"}
            ],
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    assert "showers" in fallback["days"][0]["weather_summary"].lower()


def test_8_gemini_successful_mock_response():
    """Verify proper parsing when Gemini returns structured JSON."""
    state = create_initial_travel_state(
        trip_id="trip-8",
        user_id="user-8",
        trip_data={"destination": "Goa", "duration_days": 2, "start_date": "2026-10-01"},
    )
    mock_payload = {
        "days": [
            {
                "day_number": 1,
                "date": "2026-10-01",
                "theme": "Historic Forts & Sunset",
                "weather_summary": "Sunny with light breeze",
                "activities": [
                    {
                        "time_slot": "morning",
                        "start_time": "09:00",
                        "end_time": "11:30",
                        "place_name": "Fort Aguada",
                        "category": "famous_place",
                        "description": "Historic coastal fort.",
                        "estimated_cost": 200.0,
                        "currency": "INR",
                        "visit_duration_minutes": 150,
                    }
                ],
                "food_recommendations": [
                    {
                        "name": "Fisherman's Wharf",
                        "meal": "lunch",
                        "cuisine_type": "Goan",
                        "estimated_cost": 600.0,
                        "currency": "INR",
                    }
                ],
            },
            {
                "day_number": 2,
                "date": "2026-10-02",
                "theme": "Old Goa Churches",
                "weather_summary": "Partly cloudy",
                "activities": [
                    {
                        "time_slot": "morning",
                        "start_time": "09:00",
                        "end_time": "11:30",
                        "place_name": "Se Cathedral",
                        "category": "cultural_historical",
                        "description": "Magnificent cathedral.",
                        "estimated_cost": 0.0,
                        "currency": "INR",
                        "visit_duration_minutes": 120,
                    }
                ],
                "food_recommendations": [],
            },
        ]
    }

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = f"```json\n{json.dumps(mock_payload)}\n```"
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.agents.itinerary_agent.get_gemini_client", return_value=mock_client):
        res = ItineraryAgent.generate_itinerary(state)
        assert res["itinerary_status"] == "ready"
        itin = res["itinerary"]
        assert itin["duration_days"] == 2
        assert len(itin["days"]) == 2
        assert itin["days"][0]["theme"] == "Historic Forts & Sunset"


def test_9_gemini_malformed_json_resilience():
    """Verify graceful fallback when Gemini returns invalid JSON string."""
    state = create_initial_travel_state(
        trip_id="trip-9",
        user_id="user-9",
        trip_data={"destination": "Goa", "duration_days": 2},
    )
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "This is NOT valid JSON output"
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.agents.itinerary_agent.get_gemini_client", return_value=mock_client):
        res = ItineraryAgent.generate_itinerary(state)
        assert res["itinerary_status"] == "ready"
        assert res["itinerary"] is not None
        assert len(res["itinerary"]["days"]) == 2


def test_10_gemini_failure_fallback():
    """Verify deterministic fallback when Gemini API raises an exception."""
    state = create_initial_travel_state(
        trip_id="trip-10",
        user_id="user-10",
        trip_data={"destination": "Goa", "duration_days": 3},
    )
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("API quota exceeded")

    with patch("app.agents.itinerary_agent.get_gemini_client", return_value=mock_client):
        res = ItineraryAgent.generate_itinerary(state)
        assert res["itinerary_status"] == "ready"
        assert res["itinerary"]["duration_days"] == 3


def test_11_fallback_itinerary_structure():
    """Verify that fallback itinerary contains all required schema fields."""
    state = create_initial_travel_state(
        trip_id="trip-11",
        user_id="user-11",
        trip_data={"destination": "Shimla", "duration_days": 2, "budget": 15000.0},
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    validated = ItineraryData(**fallback)
    assert validated.destination == "Shimla"
    assert len(validated.days) == 2
    assert validated.days[0].estimated_day_cost > 0


def test_12_duplicate_place_removal():
    """Verify that duplicate place names are sanitized or suffixed."""
    state = create_initial_travel_state(
        trip_id="trip-12",
        user_id="user-12",
        trip_data={"destination": "Goa", "duration_days": 2},
    )
    raw = {
        "days": [
            {
                "day_number": 1,
                "activities": [{"place_name": "Calangute Beach", "estimated_cost": 0}],
            },
            {
                "day_number": 2,
                "activities": [{"place_name": "Calangute Beach", "estimated_cost": 0}],
            },
        ]
    }
    sanitized = ItineraryAgent.validate_and_sanitize_itinerary(raw, state)
    d1_place = sanitized["days"][0]["activities"][0]["place_name"]
    d2_place = sanitized["days"][1]["activities"][0]["place_name"]
    assert d1_place == "Calangute Beach"
    assert "Area" in d2_place or d2_place != d1_place


def test_13_date_validation():
    """Verify that daily schedule dates strictly match computed sequential dates."""
    state = create_initial_travel_state(
        trip_id="trip-13",
        user_id="user-13",
        trip_data={"destination": "Ooty", "start_date": "2026-12-20", "duration_days": 3},
    )
    dates, duration = ItineraryAgent.calculate_trip_dates(state)
    assert dates == ["2026-12-20", "2026-12-21", "2026-12-22"]


def test_14_day_count_validation():
    """Verify that sanitized itinerary always produces exactly duration_days count."""
    state = create_initial_travel_state(
        trip_id="trip-14",
        user_id="user-14",
        trip_data={"destination": "Delhi", "duration_days": 4},
    )
    raw = {"days": [{"day_number": 1, "activities": []}]}  # only 1 day provided
    sanitized = ItineraryAgent.validate_and_sanitize_itinerary(raw, state)
    assert len(sanitized["days"]) == 4


def test_15_budget_validation():
    """Verify budget warning when estimated cost exceeds stated budget."""
    state = create_initial_travel_state(
        trip_id="trip-15",
        user_id="user-15",
        trip_data={"destination": "Paris", "duration_days": 3, "budget": 1000.0},  # unrealistically low budget
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    assert fallback["budget_status"] == "exceeds_budget"
    assert fallback["budget_warning"] is not None


def test_16_weather_consistency_validation():
    """Verify weather advisory attachment in itinerary when rain alerts exist."""
    state = create_initial_travel_state(
        trip_id="trip-16",
        user_id="user-16",
        trip_data={
            "destination": "Goa",
            "duration_days": 2,
            "weather_insights": [
                {"title": "Monsoon Alert", "message": "Heavy rainfall expected in the coastal belt.", "type": "rain_alert"}
            ],
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    assert fallback["days"][0]["weather_summary"] is not None


@pytest.mark.anyio
async def test_17_itinerary_graph_execution():
    """Verify complete 8-node LangGraph execution."""
    state = create_initial_travel_state(
        trip_id="trip-17",
        user_id="user-17",
        trip_data={
            "destination": "Goa",
            "duration_days": 3,
            "budget": 30000.0,
            "food_preference": "vegetarian",
        },
    )
    final_state = await run_itinerary_graph(state)
    assert final_state.get("itinerary_status") == "ready"
    assert final_state.get("itinerary") is not None
    assert len(final_state["itinerary"]["days"]) == 3
    assert final_state["agent_status"] == "itinerary_synthesis_ready"


def test_18_api_authentication_enforcement():
    """Verify 401 Unauthorized when Bearer token is missing."""
    res = client.post("/api/agent/itinerary/start", json={"trip_id": "any-trip"})
    assert res.status_code == 401


def test_19_api_trip_ownership_enforcement():
    """Verify 403 Forbidden when User B attempts to access User A's trip."""
    token_a = generate_mock_jwt("user-owner", "owner@example.com")
    token_b = generate_mock_jwt("user-intruder", "intruder@example.com")

    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Private Trip", "destination": "Goa", "starting_location": "Mumbai"},
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    res = client.post(
        "/api/agent/itinerary/start",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"trip_id": trip_id},
    )
    assert res.status_code == 403


def test_20_api_invalid_trip_id_not_found():
    """Verify 404 Not Found for non-existent trip."""
    token = generate_mock_jwt("user-test", "user@example.com")
    res = client.post(
        "/api/agent/itinerary/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"trip_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert res.status_code == 404


def test_21_api_realistic_goa_scenario():
    """Verify realistic Goa itinerary generation via API."""
    token = generate_mock_jwt("user-goa", "goa@example.com")

    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Goa 4-Day Holiday",
            "starting_location": "Bangalore",
            "destination": "Goa",
            "start_date": "2026-11-10",
            "duration_days": 4,
            "budget": 35000.0,
            "currency": "INR",
            "food_preference": "vegetarian",
            "interests": ["beaches", "culture", "nature"],
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    res = client.post(
        "/api/agent/itinerary/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"trip_id": trip_id},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["destination"] == "Goa"
    assert data["itinerary_status"] == "ready"
    itin = data["itinerary"]
    assert itin["duration_days"] == 4
    assert len(itin["days"]) == 4


def test_22_openapi_schema_contains_itinerary_endpoint():
    """Verify that OpenAPI documentation includes POST /api/agent/itinerary/start."""
    res = client.get("/api/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    paths = schema.get("paths", {})
    assert "/api/agent/itinerary/start" in paths
    assert "post" in paths["/api/agent/itinerary/start"]


def test_23_single_day_trip():
    """Verify 1-day itinerary synthesis with complete morning, afternoon, evening, meals, and budget."""
    state = create_initial_travel_state(
        trip_id="trip-23",
        user_id="user-23",
        trip_data={
            "destination": "Agra",
            "start_date": "2026-11-15",
            "duration_days": 1,
            "budget": 8000.0,
            "currency": "INR",
            "food_preference": "vegetarian",
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    assert fallback["duration_days"] == 1
    assert len(fallback["days"]) == 1
    day1 = fallback["days"][0]
    assert day1["day_number"] == 1
    assert day1["date"] == "2026-11-15"
    assert len(day1["activities"]) >= 3
    assert len(day1["food_recommendations"]) == 4
    assert "breakfast" in day1["meals"]
    assert "lunch" in day1["meals"]
    assert "snack" in day1["meals"]
    assert "dinner" in day1["meals"]
    assert day1["daily_budget"]["total"] > 0


def test_24_multi_day_trip():
    """Verify 5-day itinerary synthesis with sequential calendar dates and day indexing."""
    state = create_initial_travel_state(
        trip_id="trip-24",
        user_id="user-24",
        trip_data={
            "destination": "Kerala",
            "start_date": "2026-12-01",
            "duration_days": 5,
            "budget": 60000.0,
            "currency": "INR",
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    assert fallback["duration_days"] == 5
    assert len(fallback["days"]) == 5
    for i, d in enumerate(fallback["days"]):
        assert d["day_number"] == i + 1
        assert d["estimated_day_cost"] > 0
    assert fallback["days"][0]["date"] == "2026-12-01"
    assert fallback["days"][4]["date"] == "2026-12-05"


def test_25_rich_gemini_structured_output_parsing():
    """Verify parsing when Gemini returns full structured JSON with morning/afternoon/evening blocks and meals."""
    state = create_initial_travel_state(
        trip_id="trip-25",
        user_id="user-25",
        trip_data={"destination": "Jaipur", "duration_days": 2, "start_date": "2026-11-20", "travelers": 2},
    )
    mock_payload = {
        "trip_summary": {
            "destination": "Jaipur",
            "duration_days": 2,
            "travel_style": "cultural",
            "estimated_total_cost": 18000.0,
            "budget_status": "within_budget",
            "cost_per_traveler": 9000.0,
        },
        "days": [
            {
                "day_number": 1,
                "date": "2026-11-20",
                "theme": "Royal Forts & Palaces",
                "summary": "Explore Amber Fort and City Palace with traditional Rajasthani dinner.",
                "weather_summary": "Sunny with clear skies (24°C)",
                "weather_note": "Cool morning and pleasant afternoon.",
                "morning": {
                    "activities": [
                        {
                            "time_slot": "morning",
                            "start_time": "09:00",
                            "end_time": "12:00",
                            "place_name": "Amber Palace & Fort",
                            "category": "famous_place",
                            "description": "Magnificent hilltop fort complex with mirror mosaics.",
                            "what_to_do": "Tour Sheesh Mahal, courtyard ramparts, and panoramic hills.",
                            "why_recommended": "Iconic UNESCO heritage landmark showcasing Rajput architecture.",
                            "estimated_cost": 500.0,
                            "currency": "INR",
                            "visit_duration_minutes": 180,
                            "visit_duration": "3 hours",
                            "travel_time_from_previous": "30 mins via taxi",
                            "transport_mode": "taxi",
                            "practical_tips": "Hire an official audio guide at the main gate.",
                            "is_indoor": False,
                            "weather_suitability": "Optimal during cool morning hours",
                            "notes": "Stair climbing involved; wear sports shoes",
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "time_slot": "afternoon",
                            "start_time": "14:30",
                            "end_time": "16:30",
                            "place_name": "City Palace Museum",
                            "category": "cultural_historical",
                            "description": "Royal residence with weapon armories and royal textile galleries.",
                            "what_to_do": "Visit the textile gallery, armor museum, and Chandra Mahal courtyard.",
                            "why_recommended": "Indoor historical collections sheltered from midday sun.",
                            "estimated_cost": 350.0,
                            "currency": "INR",
                            "visit_duration_minutes": 120,
                            "is_indoor": True,
                        }
                    ]
                },
                "evening": {
                    "activities": [
                        {
                            "time_slot": "evening",
                            "start_time": "17:30",
                            "end_time": "19:30",
                            "place_name": "Hawa Mahal & Johari Bazaar Walk",
                            "category": "famous_place",
                            "description": "Wind Palace facade and traditional jewelry bazaar.",
                            "what_to_do": "Photograph the palace facade and explore local craft stores.",
                            "why_recommended": "Golden hour lighting on pink sandstone.",
                            "estimated_cost": 50.0,
                            "currency": "INR",
                            "visit_duration_minutes": 120,
                            "is_indoor": False,
                        }
                    ]
                },
                "meals": {
                    "breakfast": {
                        "name": "Tapri Central Tea House",
                        "meal": "breakfast",
                        "restaurant_type": "Heritage Rooftop Tearoom",
                        "cuisine_type": "Rajasthani & Indian Breakfast",
                        "estimated_cost": 300.0,
                        "currency": "INR",
                        "suggested_time": "08:00 - 08:45",
                        "local_specialty": "Masala Chai with Dal Pakwan",
                        "dietary_fit": "Vegetarian",
                    },
                    "lunch": {
                        "name": "Laxmi Misthan Bhandar (LMB)",
                        "meal": "lunch",
                        "restaurant_type": "Iconic Heritage Restaurant",
                        "cuisine_type": "Rajasthani Vegetarian Thali",
                        "estimated_cost": 550.0,
                        "currency": "INR",
                        "suggested_time": "12:45 - 14:00",
                        "local_specialty": "Dal Baati Churma & Gatte ki Sabzi",
                        "dietary_fit": "Pure Vegetarian",
                    },
                    "snack": {
                        "name": "Samrat Kachori House",
                        "meal": "snack",
                        "restaurant_type": "Street Delicacy Spot",
                        "cuisine_type": "Rajasthani Savouries",
                        "estimated_cost": 100.0,
                        "currency": "INR",
                        "suggested_time": "16:45 - 17:15",
                        "local_specialty": "Crisp Pyaaz Kachori with tamarind chutney",
                        "dietary_fit": "Vegetarian",
                    },
                    "dinner": {
                        "name": "Handi Restaurant",
                        "meal": "dinner",
                        "restaurant_type": "Traditional Mughlai & North Indian",
                        "cuisine_type": "North Indian Specialties",
                        "estimated_cost": 750.0,
                        "currency": "INR",
                        "suggested_time": "20:00 - 21:30",
                        "local_specialty": "Handi Paneer & Butter Naan",
                        "dietary_fit": "Vegetarian options",
                    },
                },
                "daily_budget": {
                    "food": 1700.0,
                    "transport": 800.0,
                    "activities": 900.0,
                    "miscellaneous": 300.0,
                    "total": 3700.0,
                },
                "travel_tips": [
                    "Buy a composite entry ticket to cover multiple monuments at a discount.",
                ],
            }
        ],
        "overall_tips": [
            "Use e-rickshaws for short intra-bazaar transit.",
        ],
        "packing_suggestions": [
            "Cotton scarf and sunglasses for fort exploration.",
        ],
    }

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(mock_payload)
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.agents.itinerary_agent.get_gemini_client", return_value=mock_client):
        res = ItineraryAgent.generate_itinerary(state)
        assert res["itinerary_status"] == "ready"
        itin = res["itinerary"]
        assert itin["duration_days"] == 2
        d1 = itin["days"][0]
        assert d1["theme"] == "Royal Forts & Palaces"
        assert len(d1["activities"]) >= 3
        assert d1["activities"][0]["place_name"] == "Amber Palace & Fort"
        assert d1["activities"][0]["what_to_do"] is not None
        assert d1["activities"][0]["why_recommended"] is not None
        assert d1["meals"]["lunch"]["local_specialty"] == "Dal Baati Churma & Gatte ki Sabzi"
        assert d1["daily_budget"]["food"] == 1700.0
        assert itin["cost_per_traveler"] > 0


def test_26_budget_constraint_adaptation():
    """Verify budget status evaluation for tight, moderate, and generous budgets."""
    # Exceeds budget
    state_tight = create_initial_travel_state(
        trip_id="trip-26a",
        user_id="user-26a",
        trip_data={"destination": "Manali", "duration_days": 3, "budget": 2000.0},
    )
    itin_tight = ItineraryAgent.generate_fallback_itinerary(state_tight)
    assert itin_tight["budget_status"] == "exceeds_budget"
    assert itin_tight["budget_warning"] is not None

    # Within budget
    state_generous = create_initial_travel_state(
        trip_id="trip-26b",
        user_id="user-26b",
        trip_data={"destination": "Manali", "duration_days": 3, "budget": 50000.0},
    )
    itin_generous = ItineraryAgent.generate_fallback_itinerary(state_generous)
    assert itin_generous["budget_status"] == "within_budget"
    assert itin_generous["budget_warning"] is None


def test_27_weather_rain_alert_integration():
    """Verify weather advisory integration when rain alerts are present."""
    state = create_initial_travel_state(
        trip_id="trip-27",
        user_id="user-27",
        trip_data={
            "destination": "Mumbai",
            "duration_days": 2,
            "weather_insights": [
                {"type": "rain_alert", "title": "Heavy Monsoon Downpour", "message": "Expect heavy rain in the coastal belt."}
            ],
        },
    )
    itin = ItineraryAgent.generate_fallback_itinerary(state)
    assert "heavy rain" in itin["days"][0]["weather_summary"].lower() or "monsoon" in itin["days"][0]["weather_summary"].lower()


def test_28_traveler_personalization():
    """Verify dietary preference reflection in meals."""
    state = create_initial_travel_state(
        trip_id="trip-28",
        user_id="user-28",
        trip_data={
            "destination": "Varanasi",
            "duration_days": 2,
            "food_preference": "Pure Vegetarian",
            "interests": ["spirituality", "ghats", "temples"],
        },
    )
    itin = ItineraryAgent.generate_fallback_itinerary(state)
    assert itin["days"][0]["meals"]["lunch"]["dietary_fit"] == "Pure Vegetarian"


def test_29_date_range_calculation_with_end_date():
    """Verify duration calculation from start_date and end_date."""
    state = create_initial_travel_state(
        trip_id="trip-29",
        user_id="user-29",
        trip_data={
            "destination": "Udaipur",
            "start_date": "2026-11-10",
            "end_date": "2026-11-13",
        },
    )
    dates, duration = ItineraryAgent.calculate_trip_dates(state)
    assert duration == 4
    assert dates[0] == "2026-11-10"
    assert dates[3] == "2026-11-13"


def test_30_invalid_dates_resilience():
    """Verify resilience when start_date is malformed."""
    state = create_initial_travel_state(
        trip_id="trip-30",
        user_id="user-30",
        trip_data={
            "destination": "Mysore",
            "start_date": "invalid-date-string",
            "duration_days": 2,
        },
    )
    dates, duration = ItineraryAgent.calculate_trip_dates(state)
    assert duration == 2
    assert len(dates) == 2
    assert len(dates[0].split("-")) == 3


def test_31_cost_per_traveler_calculation():
    """Verify cost per traveler calculation across group travelers."""
    state = create_initial_travel_state(
        trip_id="trip-31",
        user_id="user-31",
        trip_data={
            "destination": "Goa",
            "duration_days": 3,
            "travelers": 4,
            "adults": 4,
            "children": 0,
            "budget": 40000.0,
        },
    )
    itin = ItineraryAgent.generate_fallback_itinerary(state)
    assert itin["cost_per_traveler"] == round(itin["total_estimated_cost"] / 4, 2)


def test_32_pydantic_schema_validation_of_enriched_itinerary():
    """Verify that enriched itinerary data passes strict Pydantic validation."""
    state = create_initial_travel_state(
        trip_id="trip-32",
        user_id="user-32",
        trip_data={
            "destination": "Darjeeling",
            "duration_days": 3,
            "budget": 30000.0,
            "interests": ["tea gardens", "mountains", "toy train"],
        },
    )
    fallback = ItineraryAgent.generate_fallback_itinerary(state)
    model = ItineraryData(**fallback)
    assert model.destination == "Darjeeling"
    assert len(model.days) == 3
    assert model.days[0].daily_budget is not None
    assert model.days[0].meals is not None
    assert len(model.days[0].activities) >= 3


