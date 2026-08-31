"""
Unit and Integration Tests for Stage 4: Requirement Agent and LangGraph Workflow.

Covers:
1. TravelState creation
2. Complete requirements evaluation
3. Missing destination detection
4. Missing travel dates detection
5. Missing traveler count detection
6. Question generation
7. User answer processing & parameter extraction
8. Requirement completion transition
9. Unauthorized trip access rejection (403)
10. Invalid trip ID handling (404)
11. Gemini failure graceful fallback
12. Invalid Gemini response JSON resilience
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.agents.requirement_agent import RequirementAgent
from app.core.config import settings
from app.graph.requirement_graph import build_requirement_graph, run_requirement_graph
from app.graph.state import TravelState, create_initial_travel_state
from app.main import app

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


# ---------------------------------------------------------------------------
# Unit Tests: TravelState Creation & Evaluator
# ---------------------------------------------------------------------------

def test_1_travel_state_creation():
    """Verify TravelState is properly initialized from a trip dictionary."""
    trip_data = {
        "title": "Goa Beach Holiday",
        "start_location": "Delhi",
        "destination": "Goa",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "duration_days": 4,
        "travelers": 2,
        "adults": 2,
        "children": 0,
        "budget": 35000.0,
        "currency": "INR",
        "food_preference": "vegetarian",
        "stay_preference": "resort",
        "interests": ["beaches", "nightlife"],
    }
    state = create_initial_travel_state("trip-123", "user-abc", trip_data)

    assert state["trip_id"] == "trip-123"
    assert state["user_id"] == "user-abc"
    assert state["start_location"] == "Delhi"
    assert state["destination"] == "Goa"
    assert state["start_date"] == "2026-11-01"
    assert state["end_date"] == "2026-11-05"
    assert state["duration_days"] == 4
    assert state["travelers"] == 2
    assert state["adults"] == 2
    assert state["budget"] == 35000.0
    assert state["food_preference"] == "vegetarian"
    assert state["stay_preference"] == "resort"
    assert state["interests"] == ["beaches", "nightlife"]
    assert state["requirements_complete"] is False


def test_2_complete_requirements():
    """Verify evaluator marks requirements_complete = True when all mandatory fields are present."""
    state = create_initial_travel_state(
        trip_id="trip-complete",
        user_id="user-1",
        trip_data={
            "start_location": "Mumbai",
            "destination": "Goa",
            "start_date": "2026-12-10",
            "end_date": "2026-12-15",
            "duration_days": 5,
            "travelers": 2,
            "budget": 20000.0,
        },
    )
    result = RequirementAgent.evaluate_state(state)
    assert result["requirements_complete"] is True
    assert result["missing_information"] == []
    assert result["questions"] == []
    assert result["agent_status"] == "requirements_collected"


def test_3_missing_destination():
    """Verify evaluator catches missing destination."""
    state = create_initial_travel_state(
        trip_id="trip-nodest",
        user_id="user-1",
        trip_data={
            "start_location": "Delhi",
            "destination": "",  # Missing
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
            "travelers": 2,
            "budget": 15000,
        },
    )
    result = RequirementAgent.evaluate_state(state)
    assert result["requirements_complete"] is False
    assert "destination" in result["missing_information"]
    assert any("Where would you like to travel to" in q for q in result["questions"])


def test_4_missing_travel_dates():
    """Verify evaluator catches missing start/end travel dates."""
    state = create_initial_travel_state(
        trip_id="trip-nodates",
        user_id="user-1",
        trip_data={
            "start_location": "Delhi",
            "destination": "Goa",
            "start_date": None,
            "end_date": None,
            "duration_days": None,
            "travelers": 2,
            "budget": 30000,
        },
    )
    result = RequirementAgent.evaluate_state(state)
    assert result["requirements_complete"] is False
    assert "travel_dates" in result["missing_information"]
    assert any("dates" in q.lower() for q in result["questions"])


def test_5_missing_traveler_count():
    """Verify evaluator catches missing or zero traveler count."""
    state = create_initial_travel_state(
        trip_id="trip-notravelers",
        user_id="user-1",
        trip_data={
            "start_location": "Delhi",
            "destination": "Manali",
            "start_date": "2026-11-01",
            "end_date": "2026-11-06",
            "travelers": 0,
            "adults": 0,
            "budget": 25000,
        },
    )
    result = RequirementAgent.evaluate_state(state)
    assert result["requirements_complete"] is False
    assert "travelers" in result["missing_information"]
    assert any("people" in q.lower() or "travelling" in q.lower() for q in result["questions"])


def test_6_question_generation():
    """Verify specific questions are generated for multiple missing fields (dates, travelers, budget)."""
    state = create_initial_travel_state(
        trip_id="trip-multi-missing",
        user_id="user-1",
        trip_data={
            "start_location": "Delhi",
            "destination": "Goa",
            "food_preference": "Vegetarian",
            "stay_preference": "Standard",
        },
    )
    result = RequirementAgent.evaluate_state(state)
    assert result["requirements_complete"] is False
    assert set(result["missing_information"]) == {"travel_dates", "travelers", "budget"}
    assert len(result["questions"]) == 3


def test_7_user_answer_processing():
    """Verify natural language answers are accurately extracted into structured values."""
    user_input = "I want to travel from 10 September to 14 September. Two adults. Budget 30000."
    extracted = RequirementAgent.extract_from_user_text(user_input)

    assert "start_date" in extracted
    assert "end_date" in extracted
    assert extracted["adults"] == 2
    assert extracted["travelers"] == 2
    assert extracted["budget"] == 30000.0


@pytest.mark.anyio
async def test_8_requirement_completion_flow():
    """Verify end-to-end LangGraph flow converts incomplete trip to complete state upon receiving user answers."""
    initial_state = create_initial_travel_state(
        trip_id="trip-flow",
        user_id="user-1",
        trip_data={
            "start_location": "Delhi",
            "destination": "Goa",
            "food_preference": "Vegetarian",
            "stay_preference": "Standard",
        },
        user_answers="I want to travel from 10 September to 14 September with 2 adults. Budget is 30000.",
    )

    final_state = await run_requirement_graph(initial_state)

    assert final_state["requirements_complete"] is True
    assert final_state["missing_information"] == []
    assert final_state["questions"] == []
    assert final_state["adults"] == 2
    assert final_state["budget"] == 30000.0
    assert final_state["agent_status"] == "requirements_collected"


# ---------------------------------------------------------------------------
# API Integration Tests: Auth, Ownership, Start, Respond
# ---------------------------------------------------------------------------

def test_9_unauthorized_trip_access():
    """Verify User 2 cannot access or run requirement agent on User 1's trip (403 Forbidden)."""
    user1_token = generate_mock_jwt("user-owner-1", "owner@example.com")
    user2_token = generate_mock_jwt("user-intruder-2", "intruder@example.com")

    # User 1 creates a trip
    create_resp = client.post(
        "/api/trips",
        json={"title": "Private Vacation", "start_location": "Bangalore", "destination": "Ooty"},
        headers={"Authorization": f"Bearer {user1_token}"},
    )
    assert create_resp.status_code == 201
    trip_id = create_resp.json()["id"]

    # User 2 attempts to start requirements on User 1's trip -> 403 Forbidden
    start_resp = client.post(
        "/api/agent/requirements/start",
        json={"trip_id": trip_id},
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert start_resp.status_code == 403

    # User 2 attempts to respond to User 1's trip -> 403 Forbidden
    respond_resp = client.post(
        "/api/agent/requirements/respond",
        json={"trip_id": trip_id, "answers": "Travelling tomorrow with 2 people, budget 50000"},
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert respond_resp.status_code == 403


def test_10_invalid_trip_id():
    """Verify 404 response when querying non-existent trip_id."""
    token = generate_mock_jwt("user-1", "user@example.com")
    resp = client.post(
        "/api/agent/requirements/start",
        json={"trip_id": "non-existent-uuid-99999"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_11_gemini_failure_fallback():
    """Verify requirement agent continues functioning seamlessly via fallback parser when Gemini raises an exception."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Gemini API rate limit or network failure")

    with patch("app.agents.requirement_agent.get_gemini_client", return_value=mock_client):
        user_input = "Travelling from 15 October to 20 October with two adults. Total budget is 45000."
        extracted = RequirementAgent.extract_from_user_text(user_input)

        # Fallback should parse successfully
        assert "start_date" in extracted
        assert "end_date" in extracted
        assert extracted["adults"] == 2
        assert extracted["budget"] == 45000.0


def test_12_invalid_gemini_response_resilience():
    """Verify agent handles malformed or non-JSON Gemini responses gracefully."""
    mock_response = MagicMock()
    mock_response.text = "I am an AI and I cannot output JSON right now: Error 500."
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.agents.requirement_agent.get_gemini_client", return_value=mock_client):
        user_input = "We are 3 adults travelling from 01 November to 05 November with budget 20000."
        extracted = RequirementAgent.extract_from_user_text(user_input)

        # Fallback handles the input cleanly
        assert extracted.get("adults") == 3
        assert extracted.get("budget") == 20000.0


def test_13_step_10_real_test_scenario():
    """
    Direct verification of Step 10 prompt example:
    1. Trip with:
       - Destination: Goa
       - Starting location: Delhi
       - Dates: missing
       - Travelers: missing
       - Budget: missing
       - Food: Vegetarian
       - Stay: Standard
       - Interests: Nature, Food
    2. POST /api/agent/requirements/start -> returns requirements_complete=false and missing-information questions
    3. User submits: "I want to travel from 10 September to 14 September. Two adults. Budget 30000."
    4. POST /api/agent/requirements/respond -> extracts start_date, end_date, adults, travelers, budget
       and re-evaluates requirements -> requirements_complete=true.
    """
    token = generate_mock_jwt("user-step10-traveler", "step10@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Create the trip with missing dates/travelers/budget
    create_payload = {
        "title": "Goa Getaway",
        "start_location": "Delhi",
        "destination": "Goa",
        "food_preference": "vegetarian",
        "stay_preference": "hotel",
        "interests": ["nature", "food"],
        # Leave dates, travelers, budget absent / empty
    }
    create_resp = client.post("/api/trips", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    trip_id = create_resp.json()["id"]

    # Step 2: POST /api/agent/requirements/start
    start_resp = client.post(
        "/api/agent/requirements/start",
        json={"trip_id": trip_id},
        headers=headers
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["success"] is True
    assert start_data["data"]["trip_id"] == trip_id
    assert start_data["data"]["requirements_complete"] is False
    assert "travel_dates" in start_data["data"]["missing_information"]
    assert "budget" in start_data["data"]["missing_information"]
    assert len(start_data["data"]["questions"]) > 0

    # Step 3 & 4: POST /api/agent/requirements/respond
    answer_text = "I want to travel from 10 September to 14 September. Two adults. Budget 30000."
    respond_resp = client.post(
        "/api/agent/requirements/respond",
        json={"trip_id": trip_id, "answers": answer_text},
        headers=headers
    )
    assert respond_resp.status_code == 200
    respond_data = respond_resp.json()
    assert respond_data["success"] is True
    assert respond_data["data"]["trip_id"] == trip_id
    assert respond_data["data"]["requirements_complete"] is True
    assert respond_data["data"]["missing_information"] == []
    assert respond_data["data"]["questions"] == []
    assert respond_data["data"]["adults"] == 2
    assert respond_data["data"]["travelers"] == 2
    assert respond_data["data"]["budget"] == 30000.0
    assert "09-10" in str(respond_data["data"]["start_date"])
    assert "09-14" in str(respond_data["data"]["end_date"])


def test_14_openapi_and_docs():
    """Verify OpenAPI schema includes all new agent routes."""
    resp = client.get("/api/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = schema.get("paths", {})
    assert "/api/agent/requirements/start" in paths
    assert "/api/agent/requirements/respond" in paths
    assert "/api/trips" in paths
    assert "/api/health" in paths

