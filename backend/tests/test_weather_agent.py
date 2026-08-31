"""
Unit and Integration Test Suite for Weather Intelligence Agent (Stage 6).

Tests:
1. Weather service initialization
2. Current weather parsing & normalization (mocked)
3. Forecast parsing & normalization (mocked)
4. Valid coordinates validation
5. Invalid coordinates validation (out of bounds & invalid types)
6. Missing weather API key handling
7. Weather API timeout handling
8. Weather API HTTP error handling (401, 404, 429, 500)
9. Malformed weather API response resilience
10. Weather Agent initialization & method export
11. Weather Graph 6-node execution (async anyio)
12. Weather analysis & deterministic insight generation
13. Top recommended places weather extraction
14. API endpoint authentication enforcement (401)
15. Trip ownership enforcement (403)
16. Invalid trip ID handling (404)
17. Realistic travel scenario evaluation
18. OpenAPI schema contains /api/agent/weather/start
19. No fake weather generated on API failure
"""

import json
import urllib.error
import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.config import settings
from app.agents.weather_agent import WeatherAgent
from app.graph.state import TravelState, create_initial_travel_state
from app.graph.weather_graph import run_weather_graph
from app.services.weather import WeatherService, WeatherServiceError

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
# 1. UNIT TESTS: WeatherService
# ==============================================================================


def test_1_weather_service_initialization():
    """Verify WeatherService methods exist and are callable."""
    assert hasattr(WeatherService, "get_current_weather")
    assert hasattr(WeatherService, "get_forecast")
    assert hasattr(WeatherService, "geocode_location")
    assert hasattr(WeatherService, "validate_coordinates")


def test_2_current_weather_parsing():
    """Verify WeatherService correctly normalizes raw OpenWeatherMap current weather JSON."""
    mock_raw_data = {
        "coord": {"lon": 73.8278, "lat": 15.4989},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
        "main": {
            "temp": 28.5,
            "feels_like": 31.2,
            "temp_min": 26.0,
            "temp_max": 30.0,
            "pressure": 1012,
            "humidity": 68,
        },
        "visibility": 10000,
        "wind": {"speed": 4.2, "deg": 240},
        "sys": {"sunrise": 1727743200, "sunset": 1727786400},
        "name": "Panaji",
        "dt": 1727764800,
    }

    with patch.object(WeatherService, "_make_api_request", return_value=mock_raw_data):
        result = WeatherService.get_current_weather(15.4989, 73.8278, location_name="Goa")

        assert result["location_name"] == "Goa"
        assert result["temperature"] == 28.5
        assert result["feels_like"] == 31.2
        assert result["humidity"] == 68
        assert result["wind_speed"] == 4.2
        assert result["weather_condition"] == "Clear"
        assert result["weather_description"] == "Clear Sky"
        assert result["visibility"] == 10000
        assert result["source"] == "OpenWeatherMap"


def test_3_forecast_parsing():
    """Verify WeatherService correctly normalizes raw OpenWeatherMap 5-day forecast JSON."""
    mock_raw_forecast = {
        "list": [
            {
                "dt": 1727764800,
                "dt_txt": "2026-10-01 12:00:00",
                "main": {"temp": 29.0, "feels_like": 32.0, "humidity": 70},
                "weather": [{"main": "Clouds", "description": "few clouds"}],
                "wind": {"speed": 3.5},
                "pop": 0.15,
            },
            {
                "dt": 1727775600,
                "dt_txt": "2026-10-01 15:00:00",
                "main": {"temp": 27.5, "feels_like": 29.8, "humidity": 80},
                "weather": [{"main": "Rain", "description": "light rain"}],
                "wind": {"speed": 5.0},
                "pop": 0.75,
                "rain": {"3h": 2.4},
            },
        ]
    }

    with patch.object(WeatherService, "_make_api_request", return_value=mock_raw_forecast):
        forecast = WeatherService.get_forecast(15.4989, 73.8278, location_name="Goa")

        assert len(forecast) == 2
        assert forecast[0]["date"] == "2026-10-01"
        assert forecast[0]["time"] == "12:00"
        assert forecast[0]["temperature"] == 29.0
        assert forecast[0]["rain_probability"] == 0.15

        assert forecast[1]["temperature"] == 27.5
        assert forecast[1]["rain_probability"] == 0.75
        assert forecast[1]["precipitation"] == 2.4
        assert forecast[1]["weather_condition"] == "Rain"


def test_4_valid_coordinates_validation():
    """Verify valid lat/lon pairs convert properly."""
    lat, lon = WeatherService.validate_coordinates("15.4989", "73.8278")
    assert lat == 15.4989
    assert lon == 73.8278


def test_5_invalid_coordinates_validation():
    """Verify out-of-bounds or malformed coordinates raise ValueError."""
    with pytest.raises(ValueError):
        WeatherService.validate_coordinates(95.0, 73.0)  # Lat > 90

    with pytest.raises(ValueError):
        WeatherService.validate_coordinates(15.0, 200.0)  # Lon > 180

    with pytest.raises(ValueError):
        WeatherService.validate_coordinates("invalid", "73.0")

    with pytest.raises(ValueError):
        WeatherService.validate_coordinates(None, 73.0)


def test_6_missing_api_key_handling():
    """Verify WeatherServiceError is raised when API key is empty."""
    with patch.object(WeatherService, "get_api_key", return_value=""):
        with pytest.raises(WeatherServiceError, match="OPENWEATHER_API_KEY is not configured"):
            WeatherService._make_api_request("https://api.openweathermap.org/data/2.5/weather")


def test_7_weather_api_timeout_handling():
    """Verify timeout is caught and raises descriptive WeatherServiceError."""
    with patch.object(WeatherService, "get_api_key", return_value="test-key"):
        with patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
            with pytest.raises(WeatherServiceError, match="timed out|Unexpected"):
                WeatherService.get_current_weather(15.0, 73.0)


def test_8_weather_api_http_errors():
    """Verify HTTP status codes raise user-friendly WeatherServiceError."""
    mock_http_err_401 = urllib.error.HTTPError(
        url="http://test",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=MagicMock(read=lambda: b'{"message": "Invalid API key"}'),
    )

    with patch.object(WeatherService, "get_api_key", return_value="bad-key"):
        with patch("urllib.request.urlopen", side_effect=mock_http_err_401):
            with pytest.raises(WeatherServiceError, match="Invalid OpenWeatherMap API key"):
                WeatherService.get_current_weather(15.0, 73.0)


def test_9_malformed_api_response_handling():
    """Verify non-JSON response raises clean WeatherServiceError."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = b"<html>Server Error Bad Gateway</html>"

    with patch.object(WeatherService, "get_api_key", return_value="test-key"):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(WeatherServiceError, match="Malformed JSON response"):
                WeatherService.get_current_weather(15.0, 73.0)


# ==============================================================================
# 2. UNIT TESTS: WeatherAgent
# ==============================================================================


def test_10_weather_agent_initialization():
    """Verify WeatherAgent exports expected static methods."""
    assert hasattr(WeatherAgent, "analyze_weather")
    assert hasattr(WeatherAgent, "resolve_destination_coordinates")
    assert hasattr(WeatherAgent, "generate_weather_insights")
    assert hasattr(WeatherAgent, "fetch_places_weather")


def test_11_weather_insight_generation():
    """Verify deterministic insights logic triggers on rain, heat, wind, and pleasant conditions."""
    # Scenario A: Rainy & windy
    rainy_weather = {
        "temperature": 26.0,
        "feels_like": 28.0,
        "weather_condition": "Rain",
        "rain_probability": 0.8,
        "wind_speed": 7.5,
        "humidity": 90,
        "visibility": 4000,
    }
    insights_a = WeatherAgent.generate_weather_insights(rainy_weather, [], "Goa")
    types_a = [i["type"] for i in insights_a]
    assert "rain_alert" in types_a
    assert "wind_warning" in types_a
    assert "visibility_warning" in types_a

    # Scenario B: High heat
    hot_weather = {
        "temperature": 35.0,
        "feels_like": 39.0,
        "weather_condition": "Clear",
        "rain_probability": 0.0,
        "wind_speed": 2.0,
        "humidity": 65,
        "visibility": 10000,
    }
    insights_b = WeatherAgent.generate_weather_insights(hot_weather, [], "Jaipur")
    types_b = [i["type"] for i in insights_b]
    assert "temperature_comfort" in types_b
    assert any("High Heat" in i["title"] for i in insights_b)


def test_12_top_places_weather_fetching():
    """Verify WeatherAgent queries weather for top recommended places with coordinates."""
    mock_recs = [
        {"name": "Aguada Fort", "category": "famous_place", "latitude": 15.492, "longitude": 73.773},
        {"name": "Divar Island", "category": "hidden_gem", "latitude": 15.518, "longitude": 73.896},
        {"name": "No Coords Spot", "category": "food_dining"},  # Should be skipped
    ]

    mock_weather = {
        "latitude": 15.492,
        "longitude": 73.773,
        "temperature": 29.0,
        "weather_condition": "Clear",
        "weather_description": "Clear Sky",
        "rain_probability": 0.0,
    }

    with patch.object(WeatherService, "get_current_weather", return_value=mock_weather):
        place_weathers = WeatherAgent.fetch_places_weather(mock_recs, limit=2)
        assert len(place_weathers) == 2
        assert place_weathers[0]["place_name"] == "Aguada Fort"
        assert place_weathers[1]["place_name"] == "Divar Island"


# ==============================================================================
# 3. INTEGRATION TESTS: LangGraph Weather Pipeline
# ==============================================================================


@pytest.mark.anyio
async def test_13_weather_graph_execution():
    """Verify the 6-node weather LangGraph workflow executes end-to-end and updates TravelState."""
    initial_state = create_initial_travel_state(
        trip_id="trip-weather-graph",
        user_id="user-weather-1",
        trip_data={
            "destination": "Goa",
            "destination_latitude": 15.4989,
            "destination_longitude": 73.8278,
            "duration_days": 3,
        },
    )

    mock_current = {
        "location_name": "Goa",
        "latitude": 15.4989,
        "longitude": 73.8278,
        "temperature": 28.0,
        "feels_like": 30.0,
        "humidity": 70,
        "wind_speed": 3.0,
        "precipitation": 0.0,
        "rain_probability": 0.1,
        "weather_condition": "Clear",
        "weather_description": "Clear Sky",
        "visibility": 10000,
        "observed_at": "2026-10-01T12:00:00Z",
        "source": "OpenWeatherMap",
    }

    with patch.object(WeatherService, "get_current_weather", return_value=mock_current):
        with patch.object(WeatherService, "get_forecast", return_value=[]):
            final_state = await run_weather_graph(initial_state)

            assert final_state["weather_status"] == "ready"
            assert final_state["weather_current"] is not None
            assert final_state["weather_current"]["temperature"] == 28.0
            assert final_state["agent_status"] == "weather_analysis_ready"


# ==============================================================================
# 4. END-TO-END API TESTS: POST /api/agent/weather/start
# ==============================================================================


def test_14_api_authentication_enforcement():
    """Verify POST /api/agent/weather/start rejects unauthenticated requests with 401."""
    res = client.post("/api/agent/weather/start", json={"trip_id": str(uuid.uuid4())})
    assert res.status_code == 401


def test_15_api_trip_ownership_enforcement():
    """Verify User B cannot access weather analysis for User A's trip (403 Forbidden)."""
    user_a_token = generate_mock_jwt("user-a-owner", "owner@example.com")
    user_b_token = generate_mock_jwt("user-b-intruder", "intruder@example.com")

    # Create trip for User A
    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "title": "Private Vacation",
            "starting_location": "Mumbai",
            "destination": "Goa",
            "budget": 20000,
            "duration_days": 3,
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    # User B attempts to access weather agent
    unauth_res = client.post(
        "/api/agent/weather/start",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={"trip_id": trip_id},
    )
    assert unauth_res.status_code == 403


def test_16_api_invalid_trip_id_not_found():
    """Verify POST /api/agent/weather/start returns 404 for nonexistent trip ID."""
    token = generate_mock_jwt("user-valid", "valid@example.com")
    fake_id = str(uuid.uuid4())
    res = client.post(
        "/api/agent/weather/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"trip_id": fake_id},
    )
    assert res.status_code == 404


def test_17_api_realistic_weather_scenario():
    """Verify complete API flow: create trip -> run weather agent -> receive structured weather data."""
    token = generate_mock_jwt("user-traveler", "traveler@example.com")

    # 1. Create trip
    create_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Goa Sunshine Retreat",
            "starting_location": "Bangalore",
            "destination": "Goa",
            "duration_days": 4,
            "budget": 30000.0,
            "transport_mode": "flight",
        },
    )
    assert create_res.status_code == 201
    trip_id = create_res.json()["id"]

    mock_current = {
        "location_name": "Goa",
        "latitude": 15.4989,
        "longitude": 73.8278,
        "temperature": 29.5,
        "feels_like": 33.0,
        "humidity": 72,
        "wind_speed": 4.0,
        "precipitation": 0.0,
        "rain_probability": 0.1,
        "weather_condition": "Clear",
        "weather_description": "Clear Sky",
        "visibility": 10000,
        "observed_at": "2026-10-01T12:00:00Z",
        "source": "OpenWeatherMap",
    }

    mock_forecast = [
        {
            "date": "2026-10-01",
            "time": "15:00",
            "temperature": 30.0,
            "feels_like": 34.0,
            "humidity": 70,
            "precipitation": 0.0,
            "rain_probability": 0.1,
            "wind_speed": 4.2,
            "weather_condition": "Clear",
            "weather_description": "Clear Sky",
        }
    ]

    with patch.object(WeatherService, "geocode_location", return_value=(15.4989, 73.8278)):
        with patch.object(WeatherService, "get_current_weather", return_value=mock_current):
            with patch.object(WeatherService, "get_forecast", return_value=mock_forecast):
                weather_res = client.post(
                    "/api/agent/weather/start",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"trip_id": trip_id},
                )
                assert weather_res.status_code == 200
                body = weather_res.json()

                assert body["success"] is True
                data = body["data"]
                assert data["trip_id"] == trip_id
                assert data["destination"] == "Goa"
                assert data["weather_status"] == "ready"
                assert data["current_weather"]["temperature"] == 29.5
                assert len(data["forecast"]) == 1
                assert len(data["insights"]) > 0


def test_18_openapi_schema_contains_weather_endpoint():
    """Verify OpenAPI documentation registers POST /api/agent/weather/start."""
    openapi_res = client.get("/api/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()

    paths = schema.get("paths", {})
    assert "/api/agent/weather/start" in paths
    assert "post" in paths["/api/agent/weather/start"]


def test_19_no_fake_weather_on_api_failure():
    """Verify that when weather API fails, no fake temperatures or forecasts are generated."""
    token = generate_mock_jwt("user-test-fail", "fail@example.com")

    trip_res = client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Failing Weather Trip",
            "starting_location": "Base City",
            "destination": "Unknown Remote Peak",
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    with patch.object(WeatherService, "geocode_location", return_value=None):
        weather_res = client.post(
            "/api/agent/weather/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"trip_id": trip_id},
        )
        assert weather_res.status_code == 200
        data = weather_res.json()["data"]
        assert data["weather_status"] == "unavailable"
        assert data["current_weather"] is None
        assert data["forecast"] == []
        assert len(data["weather_errors"]) > 0
