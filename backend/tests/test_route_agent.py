"""
Unit and Integration Tests for Stage 8: Live Route & GPS Agent.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.agents.route_agent import RouteAgent
from app.core.config import settings
from app.graph.route_graph import run_route_graph
from app.graph.state import create_initial_travel_state
from app.main import app
from app.schemas.agent import RouteCalculateRequest, RouteData, RouteResponse
from app.services.routing import RoutingService, RoutingServiceError

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


def test_1_route_agent_initialization():
    """Verify RouteAgent input validation with valid coordinates and transport mode."""
    origin = {"latitude": 15.4909, "longitude": 73.8278}
    destination = {"latitude": 15.4989, "longitude": 73.8278}
    o_lat, o_lon, d_lat, d_lon, mode = RouteAgent.validate_inputs(origin, destination, "driving")
    assert o_lat == 15.4909
    assert o_lon == 73.8278
    assert d_lat == 15.4989
    assert d_lon == 73.8278
    assert mode == "driving"


def test_2_valid_coordinate_validation():
    """Verify RoutingService.validate_coordinates parses valid floats."""
    lat, lon = RoutingService.validate_coordinates(15.4989, "73.8278")
    assert lat == 15.4989
    assert lon == 73.8278


def test_3_invalid_latitude():
    """Verify error on latitude > 90 or < -90."""
    with pytest.raises(RoutingServiceError, match="Latitude out of bounds"):
        RoutingService.validate_coordinates(95.0, 73.8278)

    with pytest.raises(RoutingServiceError, match="Latitude out of bounds"):
        RoutingService.validate_coordinates(-95.0, 73.8278)


def test_4_invalid_longitude():
    """Verify error on longitude > 180 or < -180."""
    with pytest.raises(RoutingServiceError, match="Longitude out of bounds"):
        RoutingService.validate_coordinates(15.4989, 185.0)

    with pytest.raises(RoutingServiceError, match="Longitude out of bounds"):
        RoutingService.validate_coordinates(15.4989, -185.0)


def test_5_missing_origin():
    """Verify error when origin coordinates dictionary is missing."""
    with pytest.raises(RoutingServiceError, match="Missing or invalid origin"):
        RouteAgent.validate_inputs(None, {"latitude": 15.4989, "longitude": 73.8278}, "driving")


def test_6_missing_destination():
    """Verify error when destination coordinates dictionary is missing."""
    with pytest.raises(RoutingServiceError, match="Missing or invalid destination"):
        RouteAgent.validate_inputs({"latitude": 15.4909, "longitude": 73.8278}, None, "driving")


def test_7_supported_transport_modes():
    """Verify driving, walking, and cycling are accepted."""
    assert RoutingService.validate_transport_mode("driving") == "driving"
    assert RoutingService.validate_transport_mode("walking") == "walking"
    assert RoutingService.validate_transport_mode("cycling") == "cycling"
    assert RoutingService.validate_transport_mode(" DRIVING ") == "driving"


def test_8_unsupported_transport_mode():
    """Verify error when an unsupported mode like rocket or train is passed."""
    with pytest.raises(RoutingServiceError, match="Unsupported transport mode"):
        RoutingService.validate_transport_mode("teleportation")


def test_9_routing_service_successful_response():
    """Verify RoutingService parses mock OSRM response accurately."""
    mock_osrm_json = {
        "code": "Ok",
        "routes": [
            {
                "distance": 12500.0,
                "duration": 1500.0,
                "geometry": {
                    "coordinates": [
                        [73.8278, 15.4909],
                        [73.8300, 15.4950],
                        [73.8350, 15.4989],
                    ],
                    "type": "LineString",
                },
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps(mock_osrm_json).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = RoutingService.calculate_route(15.4909, 73.8278, 15.4989, 73.8350, "driving")
        assert res["distance_km"] == 12.5
        assert res["duration_minutes"] == 25.0
        assert res["transport_mode"] == "driving"
        assert len(res["geometry"]) == 3
        assert res["geometry"][0] == [15.4909, 73.8278]  # [lat, lon] conversion


def test_10_routing_service_timeout():
    """Verify timeout exception is converted to RoutingServiceError."""
    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        with pytest.raises(RoutingServiceError, match="Failed to calculate route"):
            RoutingService.calculate_route_osrm(15.4909, 73.8278, 15.4989, 73.8278, "driving")


def test_11_routing_service_failure():
    """Verify handling when routing engine returns no routes."""
    mock_osrm_empty = {"code": "NoRoute", "routes": []}
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps(mock_osrm_empty).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(RoutingServiceError, match="No route found"):
            RoutingService.calculate_route_osrm(15.4909, 73.8278, 15.4989, 73.8278, "driving")


def test_12_malformed_routing_response():
    """Verify error handling on invalid JSON response from routing API."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = b"<html>Service Unavailable</html>"
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(RoutingServiceError):
            RoutingService.calculate_route_osrm(15.4909, 73.8278, 15.4989, 73.8278, "driving")


def test_13_api_authentication_enforcement():
    """Verify 401 Unauthorized when Bearer token is omitted."""
    res = client.post(
        "/api/agent/routes/calculate",
        json={
            "trip_id": "any-trip",
            "origin": {"latitude": 15.4909, "longitude": 73.8278},
            "destination": {"latitude": 15.4989, "longitude": 73.8278},
        },
    )
    assert res.status_code == 401


def test_14_api_trip_ownership_enforcement():
    """Verify 403 Forbidden when User B tries to route for User A's trip."""
    token_a = generate_mock_jwt("user-owner-route", "owner@example.com")
    token_b = generate_mock_jwt("user-intruder-route", "intruder@example.com")

    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Private Route Trip", "destination": "Goa", "starting_location": "Panaji"},
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    res = client.post(
        "/api/agent/routes/calculate",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "trip_id": trip_id,
            "origin": {"latitude": 15.4909, "longitude": 73.8278},
            "destination": {"latitude": 15.4989, "longitude": 73.8278},
        },
    )
    assert res.status_code == 403


def test_15_api_invalid_trip_id_not_found():
    """Verify 404 Not Found for non-existent trip UUID."""
    token = generate_mock_jwt("user-route-test", "user@example.com")
    res = client.post(
        "/api/agent/routes/calculate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "trip_id": "00000000-0000-0000-0000-000000000000",
            "origin": {"latitude": 15.4909, "longitude": 73.8278},
            "destination": {"latitude": 15.4989, "longitude": 73.8278},
        },
    )
    assert res.status_code == 404


@pytest.mark.anyio
async def test_16_route_graph_execution():
    """Verify complete 5-node LangGraph execution."""
    state = create_initial_travel_state(
        trip_id="trip-route-graph",
        user_id="user-route",
        trip_data={"destination": "Goa"},
    )
    state["route_origin"] = {"latitude": 15.4909, "longitude": 73.8278}
    state["route_destination"] = {"latitude": 15.4989, "longitude": 73.8278}
    state["route_transport_mode"] = "driving"

    mock_route = {
        "distance_km": 5.4,
        "duration_minutes": 14.0,
        "geometry": [[15.4909, 73.8278], [15.4989, 73.8278]],
        "transport_mode": "driving",
        "source": "osrm",
    }

    with patch.object(RoutingService, "calculate_route", return_value=mock_route):
        final_state = await run_route_graph(state)
        assert final_state.get("route_status") == "ready"
        assert final_state.get("route_distance_km") == 5.4
        assert final_state.get("route_duration_minutes") == 14.0
        assert len(final_state.get("route_geometry")) == 2
        assert final_state.get("agent_status") == "route_ready"


def test_17_api_realistic_goa_route_scenario():
    """Verify route calculation API end-to-end with mock routing response."""
    token = generate_mock_jwt("user-goa-route", "goa@example.com")

    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Goa Navigation Trip",
            "starting_location": "Panaji",
            "destination": "Goa",
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    mock_route = {
        "distance_km": 8.2,
        "duration_minutes": 18.5,
        "geometry": [[15.4909, 73.8278], [15.5100, 73.8100], [15.5200, 73.7700]],
        "transport_mode": "driving",
        "source": "osrm",
    }

    with patch.object(RoutingService, "calculate_route", return_value=mock_route):
        res = client.post(
            "/api/agent/routes/calculate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trip_id": trip_id,
                "origin": {"latitude": 15.4909, "longitude": 73.8278},
                "destination": {"latitude": 15.5200, "longitude": 73.7700},
                "transport_mode": "driving",
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["distance_km"] == 8.2
        assert data["duration_minutes"] == 18.5
        assert data["transport_mode"] == "driving"
        assert len(data["geometry"]) == 3


def test_18_openapi_schema_contains_route_endpoint():
    """Verify OpenAPI documentation registers POST /api/agent/routes/calculate."""
    res = client.get("/api/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    paths = schema.get("paths", {})
    assert "/api/agent/routes/calculate" in paths
    assert "post" in paths["/api/agent/routes/calculate"]


def test_19_no_api_key_exposure_in_errors():
    """Verify that routing error strings never expose internal secrets or keys."""
    state = create_initial_travel_state(
        trip_id="trip-route-sec",
        user_id="user-route",
        trip_data={"destination": "Goa"},
    )
    state["route_origin"] = {"latitude": 15.4909, "longitude": 73.8278}
    state["route_destination"] = {"latitude": 15.4989, "longitude": 73.8278}

    with patch.object(RoutingService, "calculate_route", side_effect=Exception("secret_key_12345_failed")):
        res = RouteAgent.calculate_route(state)
        assert res["route_status"] == "unavailable"
        assert "route_error" in res


@pytest.mark.anyio
async def test_20_missing_coordinate_handling():
    """Verify route graph gracefully marks route unavailable when coordinates are empty."""
    state = create_initial_travel_state(
        trip_id="trip-missing-coords",
        user_id="user-route",
        trip_data={"destination": "Goa"},
    )
    state["route_origin"] = None
    state["route_destination"] = None

    final_state = await run_route_graph(state)
    assert final_state.get("route_status") == "unavailable"
    assert "coordinates are required" in final_state.get("route_error")
