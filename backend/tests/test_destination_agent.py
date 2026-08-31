"""
Unit and Integration Test Suite for Destination Intelligence Agent (Stage 5).

Tests:
1. Destination Agent initialization
2. Complete TravelState recommendation generation
3. Missing destination error detection
4. Gemini AI successful recommendation extraction (mocked)
5. Gemini malformed JSON response resilience
6. Gemini failure fallback to deterministic recommendations
7. Fallback generator quality and structure
8. Recommendation schema validation & field sanitization
9. Deduplication of duplicate place names
10. Destination LangGraph execution (async anyio)
11. API endpoint authentication enforcement (401 without Bearer)
12. Trip ownership enforcement (403 on other user's trip)
13. Invalid trip ID handling (404 for missing trip)
14. Realistic travel scenario evaluation (Goa, 2 adults, 4 days, budget 30000 INR)
15. OpenAPI schema compliance for destination endpoints
"""

import json
import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.config import settings
from app.agents.destination_agent import DestinationAgent, VALID_CATEGORIES
from app.graph.state import TravelState, create_initial_travel_state
from app.graph.destination_graph import (
    build_destination_graph,
    run_destination_graph,
)

client = TestClient(app)


def generate_mock_jwt(user_id: str, email: str = "traveler@example.com", full_name: str = "Test Traveler") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "user_metadata": {"full_name": full_name}
    }
    secret = settings.SUPABASE_JWT_SECRET or "dev-secret-key-for-testing"
    return jwt.encode(payload, secret, algorithm="HS256")


# ==============================================================================
# 1. UNIT TESTS: DestinationAgent Core Logic
# ==============================================================================


def test_1_destination_agent_initialization():
    """Verify DestinationAgent class is available and exports expected methods."""
    assert hasattr(DestinationAgent, "generate_recommendations")
    assert hasattr(DestinationAgent, "validate_and_deduplicate")
    assert hasattr(DestinationAgent, "_build_destination_prompt")
    assert hasattr(DestinationAgent, "_generate_fallback_recommendations")


def test_2_complete_travel_state_recommendations():
    """Verify DestinationAgent produces valid recommendations for complete state."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={
            "destination": "Goa",
            "starting_location": "Mumbai",
            "duration_days": 4,
            "adults": 2,
            "budget": 30000.0,
            "currency": "INR",
            "interests": ["beaches", "nature", "food"],
            "food_preference": "vegetarian",
            "stay_preference": "hotel",
        },
    )

    recs = DestinationAgent.generate_recommendations(state)
    assert isinstance(recs, list)
    assert len(recs) >= 5

    for item in recs:
        assert "name" in item and len(item["name"]) > 0
        assert "category" in item and item["category"] in VALID_CATEGORIES
        assert "description" in item and len(item["description"]) > 0
        assert "why_recommended" in item
        assert "confidence" in item and 0.0 <= item["confidence"] <= 1.0


def test_3_missing_destination_detection():
    """Verify DestinationAgent returns empty list when destination is missing."""
    empty_state = create_initial_travel_state(
        trip_id="trip-empty",
        user_id="user-123",
        trip_data={"destination": "", "starting_location": "Delhi"},
    )

    recs = DestinationAgent.generate_recommendations(empty_state)
    assert recs == []


def test_4_gemini_successful_mock_response():
    """Verify DestinationAgent correctly processes structured JSON from Gemini."""
    mock_gemini_data = [
        {
            "name": "Baga Beach Sunset Point",
            "category": "famous_place",
            "description": "Lively coastal stretch with golden sands.",
            "why_recommended": "Matches beach interest and sunset views.",
            "estimated_visit_duration": "2-3 hours",
            "estimated_cost": 200.0,
            "currency": "INR",
            "latitude": 15.5553,
            "longitude": 73.7517,
            "best_time_to_visit": "Late afternoon",
            "tags": ["beach", "sunset"],
            "confidence": 0.95,
        },
        {
            "name": "Spice Plantation Eco Tour",
            "category": "nature_adventure",
            "description": "Lush tropical farm offering guided organic spice walks.",
            "why_recommended": "Great for nature lovers with vegetarian buffet.",
            "estimated_visit_duration": "3 hours",
            "estimated_cost": 500.0,
            "currency": "INR",
            "latitude": 15.4200,
            "longitude": 74.0100,
            "best_time_to_visit": "Morning",
            "tags": ["nature", "eco", "vegetarian"],
            "confidence": 0.93,
        },
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(mock_gemini_data)}\n```"
    mock_client.models.generate_content.return_value = mock_response

    state = create_initial_travel_state(
        trip_id="trip-gemini",
        user_id="user-123",
        trip_data={"destination": "Goa", "budget": 20000},
    )

    with patch("app.agents.destination_agent.get_gemini_client", return_value=mock_client):
        recs = DestinationAgent.generate_recommendations(state)
        assert len(recs) == 2
        assert recs[0]["name"] == "Baga Beach Sunset Point"
        assert recs[0]["category"] == "famous_place"
        assert recs[1]["name"] == "Spice Plantation Eco Tour"
        assert recs[1]["category"] == "nature_adventure"


def test_5_gemini_malformed_json_resilience():
    """Verify DestinationAgent falls back cleanly when Gemini returns corrupted JSON."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Here are some places for you: {malformed json without brackets..."
    mock_client.models.generate_content.return_value = mock_response

    state = create_initial_travel_state(
        trip_id="trip-malformed",
        user_id="user-123",
        trip_data={"destination": "Jaipur", "budget": 15000},
    )

    with patch("app.agents.destination_agent.get_gemini_client", return_value=mock_client):
        recs = DestinationAgent.generate_recommendations(state)
        assert isinstance(recs, list)
        assert len(recs) > 0  # Fallback engaged gracefully
        assert all(r["category"] in VALID_CATEGORIES for r in recs)


def test_6_gemini_failure_fallback():
    """Verify DestinationAgent recovers gracefully when Gemini throws an exception."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API Quota Exceeded")

    state = create_initial_travel_state(
        trip_id="trip-err",
        user_id="user-123",
        trip_data={"destination": "Kerala", "budget": 25000},
    )

    with patch("app.agents.destination_agent.get_gemini_client", return_value=mock_client):
        recs = DestinationAgent.generate_recommendations(state)
        assert isinstance(recs, list)
        assert len(recs) > 0
        assert any(r["category"] == "famous_place" for r in recs)


def test_7_fallback_recommendations_quality():
    """Verify the deterministic fallback generator produces comprehensive structured data."""
    state = create_initial_travel_state(
        trip_id="trip-fb",
        user_id="user-123",
        trip_data={"destination": "Goa", "currency": "INR"},
    )

    fallback_recs = DestinationAgent._generate_fallback_recommendations(state)
    assert len(fallback_recs) >= 6

    categories_present = {r["category"] for r in fallback_recs}
    assert "famous_place" in categories_present
    assert "hidden_gem" in categories_present
    assert "food_dining" in categories_present
    assert "stay_area" in categories_present


def test_8_recommendation_validation_and_sanitization():
    """Verify category alias normalization, numeric casting, and boundary limits."""
    raw_dirty_items = [
        {
            "name": "  Historic Fort  ",
            "category": "tourist_spot",  # Alias for famous_place
            "description": "Great fort",
            "why_recommended": "Historic relevance",
            "estimated_cost": "500",
            "latitude": "15.4989",
            "longitude": "73.8278",
            "confidence": 1.5,  # Out of bounds -> capped to 1.0
        },
        {
            "name": "Night Food Street",
            "category": "dining",  # Alias for food_dining
            "description": "Tasty food stalls",
            "why_recommended": "Delicious snacks",
            "estimated_cost": "invalid_cost",
            "latitude": 999.0,  # Invalid lat -> None
            "confidence": -0.2,  # Negative -> floored to 0.0
        },
        {
            "name": "",  # Empty name -> should be skipped
            "category": "famous_place",
        },
    ]

    validated = DestinationAgent.validate_and_deduplicate(raw_dirty_items)
    assert len(validated) == 2

    assert validated[0]["name"] == "Historic Fort"
    assert validated[0]["category"] == "famous_place"
    assert validated[0]["estimated_cost"] == 500.0
    assert validated[0]["latitude"] == 15.4989
    assert validated[0]["confidence"] == 1.0

    assert validated[1]["name"] == "Night Food Street"
    assert validated[1]["category"] == "food_dining"
    assert validated[1]["estimated_cost"] is None
    assert validated[1]["latitude"] is None
    assert validated[1]["confidence"] == 0.0


def test_9_duplicate_removal():
    """Verify duplicate places with minor casing or spacing differences are deduplicated."""
    duplicates = [
        {"name": "Aguada Fort", "category": "famous_place", "description": "Version 1"},
        {"name": "aguada fort", "category": "famous_place", "description": "Version 2"},
        {"name": "  Aguada Fort  ", "category": "famous_place", "description": "Version 3"},
        {"name": "Chapora Fort", "category": "famous_place", "description": "Unique place"},
    ]

    deduped = DestinationAgent.validate_and_deduplicate(duplicates)
    assert len(deduped) == 2
    names = [d["name"] for d in deduped]
    assert "Aguada Fort" in names
    assert "Chapora Fort" in names


# ==============================================================================
# 2. INTEGRATION TESTS: LangGraph Destination Workflow
# ==============================================================================


@pytest.mark.anyio
async def test_10_destination_graph_execution():
    """Verify the 4-node destination LangGraph executes end-to-end and updates TravelState."""
    initial_state = create_initial_travel_state(
        trip_id="trip-graph-1",
        user_id="user-graph-1",
        trip_data={
            "destination": "Goa",
            "start_location": "Pune",
            "duration_days": 3,
            "budget": 20000,
        },
    )

    final_state = await run_destination_graph(initial_state)
    assert "destination_recommendations" in final_state
    recs = final_state["destination_recommendations"]
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert final_state["agent_status"] == "destination_recommendations_ready"


# ==============================================================================
# 3. END-TO-END API TESTS: POST /api/agent/destinations/start
# ==============================================================================


def test_11_api_authentication_enforcement():
    """Verify POST /api/agent/destinations/start rejects unauthenticated requests with 401."""
    res = client.post("/api/agent/destinations/start", json={"trip_id": str(uuid.uuid4())})
    assert res.status_code == 401


def test_12_api_trip_ownership_enforcement():
    """Verify User B cannot generate or access destination recommendations for User A's trip."""
    user_a_token = generate_mock_jwt("user-a-owner", "owner@example.com")
    user_b_token = generate_mock_jwt("user-b-intruder", "intruder@example.com")

    # Create trip for User A
    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "title": "Private Coastal Trip",
            "starting_location": "Mumbai",
            "destination": "Goa",
            "budget": 25000,
            "duration_days": 4,
            "transport_mode": "flight",
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    # User B attempts to access User A's trip recommendations
    unauth_res = client.post(
        "/api/agent/destinations/start",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={"trip_id": trip_id},
    )
    assert unauth_res.status_code == 403


def test_13_api_invalid_trip_id_not_found():
    """Verify POST /api/agent/destinations/start returns 404 for nonexistent trip ID."""
    token = generate_mock_jwt("user-valid", "valid@example.com")
    fake_id = str(uuid.uuid4())
    res = client.post(
        "/api/agent/destinations/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"trip_id": fake_id},
    )
    assert res.status_code == 404


def test_14_api_realistic_destination_scenario():
    """Verify complete API flow: create trip -> run destination agent -> receive categorized recommendations."""
    token = generate_mock_jwt("user-traveler", "traveler@example.com")

    # 1. Create realistic trip
    create_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Goa Holiday Adventure",
            "starting_location": "Bangalore",
            "destination": "Goa",
            "travel_date": "2026-10-15",
            "duration_days": 4,
            "adults": 2,
            "children": 0,
            "budget": 30000.0,
            "currency": "INR",
            "transport_mode": "flight",
            "food_preference": "vegetarian",
            "stay_preference": "hotel",
            "interests": ["nature", "beaches", "food", "culture"],
        },
    )
    assert create_res.status_code == 201
    trip_id = create_res.json()["id"]

    # 2. Call Destination Agent
    dest_res = client.post(
        "/api/agent/destinations/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"trip_id": trip_id},
    )
    assert dest_res.status_code == 200
    body = dest_res.json()

    assert body["success"] is True
    data = body["data"]
    assert data["trip_id"] == trip_id
    assert data["destination"] == "Goa"
    assert data["total_recommendations"] > 0
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["categories_summary"], dict)

    # Check category distribution
    cats = {r["category"] for r in data["recommendations"]}
    assert len(cats) >= 3  # Diverse categories


def test_15_openapi_schema_contains_destination_endpoint():
    """Verify OpenAPI documentation registers POST /api/agent/destinations/start."""
    openapi_res = client.get("/api/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()

    paths = schema.get("paths", {})
    assert "/api/agent/destinations/start" in paths
    assert "post" in paths["/api/agent/destinations/start"]
