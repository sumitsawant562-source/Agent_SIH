"""
Unit and Integration Tests for Stage 9: Crowd Monitoring & Overcrowding Agent.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.agents.crowd_agent import CrowdAgent
from app.core.config import settings
from app.graph.crowd_graph import run_crowd_graph
from app.graph.state import create_initial_travel_state
from app.main import app
from app.schemas.agent import CrowdData, CrowdResponse, CrowdStartRequest
from app.services.crowd import CrowdDetectionResult, CrowdService, CrowdServiceError

client = TestClient(app)


def generate_mock_jwt(user_id: str, email: str = "traveler@example.com") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "user_metadata": {"full_name": "Test Traveler"},
    }
    secret = settings.SUPABASE_JWT_SECRET or "dev-secret-key-for-testing_at_least_32_bytes"
    return jwt.encode(payload, secret, algorithm="HS256")


def test_1_crowd_agent_initialization():
    """Verify CrowdAgent input validation with valid parameters."""
    res = CrowdAgent.validate_inputs(
        destination_name="Baga Beach",
        people_count=45,
        capacity=100,
        latitude=15.5523,
        longitude=73.7517,
        confidence=0.92,
    )
    assert res["destination"] == "Baga Beach"
    assert res["people_count"] == 45
    assert res["capacity"] == 100
    assert res["latitude"] == 15.5523
    assert res["longitude"] == 73.7517
    assert res["confidence"] == 0.92


def test_2_low_crowd_classification():
    """Verify 0-30% capacity classifies as LOW with 'Visit'."""
    metrics = CrowdService.calculate_crowd_metrics(people_count=20, capacity=100)
    assert metrics["crowd_level"] == "LOW"
    assert metrics["crowd_percentage"] == 20.0
    assert metrics["base_recommendation"] == "Visit"
    assert metrics["is_overcrowded"] is False
    assert metrics["crowd_status"] == "Normal"


def test_3_moderate_crowd_classification():
    """Verify 31-60% capacity classifies as MODERATE with 'Visit with caution'."""
    metrics = CrowdService.calculate_crowd_metrics(people_count=50, capacity=100)
    assert metrics["crowd_level"] == "MODERATE"
    assert metrics["crowd_percentage"] == 50.0
    assert metrics["base_recommendation"] == "Visit with caution"
    assert metrics["is_overcrowded"] is False


def test_4_high_crowd_classification():
    """Verify 61-80% capacity classifies as HIGH."""
    metrics = CrowdService.calculate_crowd_metrics(people_count=75, capacity=100)
    assert metrics["crowd_level"] == "HIGH"
    assert metrics["crowd_percentage"] == 75.0
    assert metrics["base_recommendation"] == "Consider visiting during a less busy time"
    assert metrics["is_overcrowded"] is False
    assert metrics["crowd_status"] == "Busy"


def test_5_very_high_crowd_classification():
    """Verify 81-100% capacity classifies as VERY_HIGH and flags is_overcrowded=True."""
    metrics = CrowdService.calculate_crowd_metrics(people_count=90, capacity=100)
    assert metrics["crowd_level"] == "VERY_HIGH"
    assert metrics["crowd_percentage"] == 90.0
    assert metrics["base_recommendation"] == "Consider an alternative"
    assert metrics["is_overcrowded"] is True


def test_6_overcrowded_classification():
    """Verify >100% capacity classifies as OVER_CROWDED with 'Switch to an alternative destination'."""
    metrics = CrowdService.calculate_crowd_metrics(people_count=140, capacity=100)
    assert metrics["crowd_level"] == "OVER_CROWDED"
    assert metrics["crowd_percentage"] == 140.0
    assert metrics["base_recommendation"] == "Switch to an alternative destination"
    assert metrics["is_overcrowded"] is True
    assert metrics["crowd_status"] == "Overcrowded"


def test_7_invalid_people_count():
    """Verify negative or non-numeric people counts raise CrowdServiceError."""
    with pytest.raises(CrowdServiceError):
        CrowdService.validate_people_count(-5)

    with pytest.raises(CrowdServiceError):
        CrowdService.validate_people_count("invalid_number")


def test_8_invalid_capacity():
    """Verify zero, negative, or non-numeric capacities raise CrowdServiceError."""
    with pytest.raises(CrowdServiceError):
        CrowdService.validate_capacity(0)

    with pytest.raises(CrowdServiceError):
        CrowdService.validate_capacity(-50)

    with pytest.raises(CrowdServiceError):
        CrowdService.validate_capacity("not_a_num")


def test_9_coordinate_validation():
    """Verify latitude and longitude range validation."""
    lat, lon = CrowdService.validate_coordinates(15.4989, 73.8278)
    assert lat == 15.4989
    assert lon == 73.8278

    with pytest.raises(CrowdServiceError):
        CrowdService.validate_coordinates(95.0, 73.8278)

    with pytest.raises(CrowdServiceError):
        CrowdService.validate_coordinates(15.4989, 185.0)


def test_10_overcrowding_decision_logic():
    """Verify CrowdDetectionResult abstraction dataclass behavior."""
    det = CrowdDetectionResult(people_count=120, confidence=0.98, source="yolo_cv")
    assert det.people_count == 120
    assert det.confidence == 0.98
    assert det.source == "yolo_cv"
    assert det.timestamp is not None


def test_11_alternative_selection_and_ranking():
    """Verify alternative destination discovery and ranking based on distance & category."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={
            "destination": "Goa",
            "destination_recommendations": [
                {
                    "name": "Baga Beach",
                    "category": "famous_place",
                    "latitude": 15.5523,
                    "longitude": 73.7517,
                },
                {
                    "name": "Ashwem Beach",
                    "category": "hidden_gem",
                    "latitude": 15.6560,
                    "longitude": 73.7170,
                },
                {
                    "name": "Anjuna Flea Market",
                    "category": "nearby_place",
                    "latitude": 15.5780,
                    "longitude": 73.7420,
                },
            ],
        },
    )
    state["crowd_location"] = "Baga Beach"
    state["crowd_latitude"] = 15.5523
    state["crowd_longitude"] = 73.7517

    alternatives = CrowdAgent.find_alternative_places(state)
    assert len(alternatives) > 0
    # Baga Beach must NOT be in alternatives
    alt_names = [a["name"].lower() for a in alternatives]
    assert "baga beach" not in alt_names
    assert any("ashwem" in name for name in alt_names)


def test_12_duplicate_and_self_alternative_removal():
    """Verify current destination and duplicate recommendations are removed."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={
            "destination_recommendations": [
                {"name": "Calangute Beach", "category": "famous_place"},
                {"name": "Calangute Beach", "category": "famous_place"},
                {"name": "Querim Cave", "category": "hidden_gem"},
            ],
        },
    )
    state["crowd_location"] = "Calangute Beach"
    alts = CrowdAgent.find_alternative_places(state)
    assert len(alts) == 1
    assert alts[0]["name"] == "Querim Cave"


def test_13_weather_aware_alternative_selection():
    """Verify alternatives attach weather suitability annotations."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={
            "weather_current": {
                "weather_condition": "Rain",
                "rain_probability": 0.85,
            },
            "destination_recommendations": [
                {"name": "Chorla Ghats", "category": "nature_adventure", "latitude": 15.6, "longitude": 74.1},
            ],
        },
    )
    state["crowd_location"] = "Baga Beach"
    alts = CrowdAgent.find_alternative_places(state)
    assert len(alts) == 1
    assert "Caution" in alts[0]["weather_suitability"] or "rain" in alts[0]["weather_suitability"].lower()


def test_14_gemini_successful_mock_response():
    """Verify Gemini AI explanation synthesis with mock generate_content."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={"destination": "Goa", "interests": ["beaches", "culture"]},
    )
    state["crowd_location"] = "Baga Beach"

    metrics = {
        "people_count": 130,
        "capacity": 100,
        "crowd_percentage": 130.0,
        "crowd_level": "OVER_CROWDED",
        "is_overcrowded": True,
        "base_recommendation": "Switch to an alternative destination",
    }
    alternatives = [{"name": "Ashwem Beach", "category": "hidden_gem"}]

    mock_resp = MagicMock()
    mock_resp.text = "Baga Beach is currently overcrowded. For a peaceful beach experience, we recommend Ashwem Beach."

    with patch("app.agents.crowd_agent.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp
        mock_get_client.return_value = mock_client

        explanation = CrowdAgent.generate_ai_explanation(state, metrics, alternatives)
        assert "Ashwem Beach" in explanation or "overcrowded" in explanation


def test_15_gemini_failure_deterministic_fallback():
    """Verify deterministic explanation fallback when Gemini errors out."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={"destination": "Goa"},
    )
    state["crowd_location"] = "Baga Beach"
    metrics = {
        "people_count": 120,
        "capacity": 100,
        "crowd_percentage": 120.0,
        "crowd_level": "OVER_CROWDED",
        "is_overcrowded": True,
        "base_recommendation": "Switch to an alternative destination",
    }
    alternatives = [{"name": "Anjuna Beach"}]

    with patch("app.agents.crowd_agent.get_gemini_client", return_value=None):
        explanation = CrowdAgent.generate_ai_explanation(state, metrics, alternatives)
        assert "120.0% capacity" in explanation
        assert "OVER CROWDED" in explanation or "Switch to an alternative" in explanation


def test_16_malformed_gemini_response_resilience():
    """Verify fallback when Gemini returns empty or whitespace response."""
    state = create_initial_travel_state(
        trip_id="trip-123",
        user_id="user-123",
        trip_data={"destination": "Goa"},
    )
    state["crowd_location"] = "Baga Beach"
    metrics = {
        "people_count": 25,
        "capacity": 100,
        "crowd_percentage": 25.0,
        "crowd_level": "LOW",
        "is_overcrowded": False,
        "base_recommendation": "Visit",
    }

    mock_resp = MagicMock()
    mock_resp.text = "   "

    with patch("app.agents.crowd_agent.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp
        mock_get_client.return_value = mock_client

        explanation = CrowdAgent.generate_ai_explanation(state, metrics, [])
        assert "25.0% capacity" in explanation
        assert "LOW crowd level" in explanation


def test_17_api_unauthorized_request():
    """Verify 401 when Authorization header is missing."""
    response = client.post(
        "/api/agent/crowd/start",
        json={
            "trip_id": "00000000-0000-0000-0000-000000000001",
            "destination": "Baga Beach",
            "people_count": 50,
        },
    )
    assert response.status_code == 401


def test_18_api_trip_ownership_violation():
    """Verify 404/403 when user attempts to access a trip they do not own."""
    user_token = generate_mock_jwt("user-unauthorized")

    with patch("app.services.trip_service.TripService.get_trip_by_id") as mock_get:
        from fastapi import HTTPException
        mock_get.side_effect = HTTPException(status_code=404, detail="Trip not found")

        response = client.post(
            "/api/agent/crowd/start",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "trip_id": "00000000-0000-0000-0000-000000000099",
                "destination": "Baga Beach",
                "people_count": 50,
            },
        )
        assert response.status_code == 404


def test_19_api_invalid_trip_id_not_found():
    """Verify 404 when trip does not exist."""
    user_token = generate_mock_jwt("user-123")
    with patch("app.services.trip_service.TripService.get_trip_by_id") as mock_get:
        from fastapi import HTTPException
        mock_get.side_effect = HTTPException(status_code=404, detail="Trip not found")

        response = client.post(
            "/api/agent/crowd/start",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "trip_id": "non-existent-trip",
                "destination": "Calangute",
                "people_count": 30,
            },
        )
        assert response.status_code == 404


def test_20_api_realistic_goa_crowd_scenario():
    """Verify full end-to-end API scenario for an overcrowded Goa destination."""
    user_id = "user-goa-crowd"
    token = generate_mock_jwt(user_id)
    trip_id = "trip-goa-crowd-999"

    mock_trip = {
        "id": trip_id,
        "user_id": user_id,
        "destination": "Goa",
        "destination_recommendations": [
            {
                "name": "Baga Beach",
                "category": "famous_place",
                "description": "Popular lively beach",
                "why_recommended": "Famous nightlife",
                "latitude": 15.5523,
                "longitude": 73.7517,
            },
            {
                "name": "Ashwem Beach",
                "category": "hidden_gem",
                "description": "Peaceful white sand beach",
                "why_recommended": "Serene and scenic atmosphere",
                "latitude": 15.6560,
                "longitude": 73.7170,
            },
        ],
    }

    with patch("app.services.trip_service.TripService.get_trip_by_id", return_value=mock_trip):
        response = client.post(
            "/api/agent/crowd/start",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trip_id": trip_id,
                "destination": "Baga Beach",
                "people_count": 135,
                "capacity": 100,
                "latitude": 15.5523,
                "longitude": 73.7517,
                "confidence": 0.96,
                "source": "simulated_detector",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["destination"] == "Baga Beach"
        assert data["people_count"] == 135
        assert data["capacity"] == 100
        assert data["crowd_percentage"] == 135.0
        assert data["crowd_level"] == "OVER_CROWDED"
        assert data["is_overcrowded"] is True
        assert len(data["alternative_places"]) >= 1
        assert data["alternative_places"][0]["name"] == "Ashwem Beach"
        assert data["recommendation"] == "Switch to an alternative destination"


def test_21_openapi_schema_contains_crowd_endpoint():
    """Verify the /api/agent/crowd/start endpoint is registered in OpenAPI schema."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert "/api/agent/crowd/start" in paths
    assert "post" in paths["/api/agent/crowd/start"]


@pytest.mark.anyio
async def test_22_full_crowd_langgraph_execution():
    """Verify 7-node LangGraph execution for TravelState."""
    initial_state = create_initial_travel_state(
        trip_id="trip-graph-123",
        user_id="user-graph-123",
        trip_data={
            "destination": "Goa",
            "destination_recommendations": [
                {"name": "Anjuna Beach", "category": "hidden_gem", "latitude": 15.57, "longitude": 73.74}
            ],
        },
    )
    initial_state["crowd_location"] = "Baga Beach"
    initial_state["crowd_count"] = 85
    initial_state["crowd_capacity"] = 100
    initial_state["crowd_latitude"] = 15.5523
    initial_state["crowd_longitude"] = 73.7517

    result = await run_crowd_graph(initial_state)
    assert result["crowd_level"] == "VERY_HIGH"
    assert result["crowd_percentage"] == 85.0
    assert result["is_overcrowded"] is True
    assert result["agent_status"] == "crowd_ready"
    assert result["crowd_timestamp"] is not None
    assert len(result["alternative_places"]) == 1
