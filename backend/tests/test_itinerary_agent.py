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

