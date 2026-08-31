import pytest
from datetime import date
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.config import settings

client = TestClient(app)


def generate_mock_jwt(user_id: str, email: str = "test@example.com", full_name: str = "Test User") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "user_metadata": {
            "full_name": full_name
        }
    }
    secret = settings.SUPABASE_JWT_SECRET or "dev-secret-key-for-testing"
    return jwt.encode(payload, secret, algorithm="HS256")


def test_health_check():
    """Verify GET /api/health returns 200 OK with status and service identifier"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "travel-intelligence-backend"


def test_unauthenticated_request_rejected():
    """Verify endpoints requiring auth reject missing token with 401"""
    response = client.get("/api/trips")
    assert response.status_code == 401

    response = client.get("/api/auth/me")
    assert response.status_code == 401

    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_users_me_endpoint():
    """Verify /api/users/me returns authenticated user profile from token"""
    token = generate_mock_jwt("user-456", "developer@example.com", "Dev Traveler")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "user-456"
    assert data["email"] == "developer@example.com"
    assert data["full_name"] == "Dev Traveler"
    assert data["is_authenticated"] is True


def test_auth_me_endpoint():
    """Verify /api/auth/me returns current user profile from token"""
    token = generate_mock_jwt("user-123", "alice@example.com", "Alice Smith")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "user-123"
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Smith"
    assert data["is_authenticated"] is True


def test_trips_crud_and_validation():
    """Verify complete trip CRUD flow with strict validation, extended fields, and user ownership isolation"""
    user1_token = generate_mock_jwt("user-alice-1", "alice@example.com")
    user2_token = generate_mock_jwt("user-bob-2", "bob@example.com")

    headers1 = {"Authorization": f"Bearer {user1_token}"}
    headers2 = {"Authorization": f"Bearer {user2_token}"}

    # 1. Validation error tests
    invalid_trip_data = {
        "title": "Invalid Trip",
        "start_location": "",     # Empty -> should fail
        "destination": "Goa",
        "travel_date": "2026-10-01",
        "duration_days": 0,       # <= 0 -> should fail
        "adults": 0,              # < 1 -> should fail
        "budget": -100,           # <= 0 -> should fail
        "transport_mode": "flight",
    }
    resp = client.post("/api/trips", json=invalid_trip_data, headers=headers1)
    assert resp.status_code == 422

    # 2. Valid trip creation by User 1 with Stage 2 extended parameters
    valid_trip_data = {
        "title": "Himalayan Expedition",
        "start_location": "New Delhi",
        "start_latitude": 28.6139,
        "start_longitude": 77.2090,
        "destination": "Manali",
        "destination_latitude": 32.2432,
        "destination_longitude": 77.1892,
        "start_date": "2026-10-15",
        "end_date": "2026-10-20",
        "duration_days": 5,
        "travelers": 2,
        "adults": 2,
        "children": 0,
        "budget": 25000.00,
        "currency": "INR",
        "transport_mode": "car",
        "food_preference": "vegetarian",
        "stay_preference": "resort",
        "travel_style": "adventure",
        "interests": ["nature", "adventure", "photography"],
        "special_requirements": "Need heated rooms",
    }
    create_resp = client.post("/api/trips", json=valid_trip_data, headers=headers1)
    assert create_resp.status_code == 201
    created_trip = create_resp.json()
    assert created_trip["title"] == "Himalayan Expedition"
    assert created_trip["user_id"] == "user-alice-1"
    assert created_trip["duration_days"] == 5
    assert created_trip["currency"] == "INR"
    assert created_trip["start_latitude"] == 28.6139
    trip_id = created_trip["id"]

    # 3. User 1 can list own trips
    list_resp = client.get("/api/trips", headers=headers1)
    assert list_resp.status_code == 200
    trips = list_resp.json()["trips"]
    assert any(t["id"] == trip_id for t in trips)

    # 4. User 1 can get own trip by ID
    get_resp = client.get(f"/api/trips/{trip_id}", headers=headers1)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == trip_id

    # 5. User 2 (Bob) CANNOT access User 1's (Alice's) trip (Must return 403 Forbidden)
    unauth_get = client.get(f"/api/trips/{trip_id}", headers=headers2)
    assert unauth_get.status_code == 403

    # 6. User 2 CANNOT update User 1's trip
    unauth_update = client.put(f"/api/trips/{trip_id}", json={"title": "Hacked Title"}, headers=headers2)
    assert unauth_update.status_code == 403

    # 7. User 2 CANNOT delete User 1's trip
    unauth_delete = client.delete(f"/api/trips/{trip_id}", headers=headers2)
    assert unauth_delete.status_code == 403

    # 8. User 1 updates own trip
    update_resp = client.put(f"/api/trips/{trip_id}", json={"title": "Updated Himalayan Journey", "duration_days": 6}, headers=headers1)
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Himalayan Journey"
    assert update_resp.json()["duration_days"] == 6

    # 9. User 1 deletes own trip
    delete_resp = client.delete(f"/api/trips/{trip_id}", headers=headers1)
    assert delete_resp.status_code == 200

    # 10. Verify trip no longer exists
    get_after_delete = client.get(f"/api/trips/{trip_id}", headers=headers1)
    assert get_after_delete.status_code == 404


def test_gemini_status_endpoint():
    """Verify GET /api/ai/status returns provider and model info without exposing keys"""
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert data["provider"] == "gemini"
    assert "model" in data
    assert "status" in data


def test_gemini_test_endpoint():
    """Verify POST /api/ai/test executes gracefully with or without API key configured"""
    response = client.post("/api/ai/test", json={"prompt": "Ping"})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["provider"] == "gemini"
    assert "model" in data

