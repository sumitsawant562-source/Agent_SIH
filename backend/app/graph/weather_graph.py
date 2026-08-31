"""
LangGraph workflow for Weather Intelligence Agent (Stage 6).

Executes a 6-node state graph:
validate_weather_requirements -> resolve_weather_coordinates -> fetch_current_weather
-> fetch_weather_forecast -> analyze_weather -> store_weather_results
"""

import logging
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from app.agents.weather_agent import WeatherAgent
from app.graph.state import TravelState
from app.services.weather import WeatherService, WeatherServiceError

logger = logging.getLogger(__name__)


async def validate_weather_requirements(state: TravelState) -> Dict[str, Any]:
    """Node 1: Checks if destination information exists in state."""
    dest = state.get("destination")
    if not dest or not dest.strip():
        return {
            "weather_status": "unavailable",
            "weather_errors": ["No destination specified in travel state."],
            "agent_status": "weather_validation_failed",
        }
    return {
        "weather_errors": [],
        "agent_status": "weather_requirements_validated",
    }


async def resolve_weather_coordinates(state: TravelState) -> Dict[str, Any]:
    """Node 2: Resolves coordinates for destination."""
    if state.get("weather_status") == "unavailable":
        return {}

    lat, lon = WeatherAgent.resolve_destination_coordinates(state)
    if lat is None or lon is None:
        dest = state.get("destination", "")
        return {
            "weather_status": "unavailable",
            "weather_errors": [f"Could not resolve geographical coordinates for destination '{dest}'."],
            "agent_status": "weather_coordinates_failed",
        }

    return {
        "destination_latitude": lat,
        "destination_longitude": lon,
        "agent_status": "weather_coordinates_resolved",
    }


async def fetch_current_weather(state: TravelState) -> Dict[str, Any]:
    """Node 3: Fetches live current weather from WeatherService."""
    if state.get("weather_status") == "unavailable":
        return {}

    lat = state.get("destination_latitude")
    lon = state.get("destination_longitude")
    dest = state.get("destination") or "Unknown"

    try:
        current = WeatherService.get_current_weather(lat, lon, location_name=dest)
        return {
            "weather_current": current,
            "agent_status": "current_weather_fetched",
        }
    except WeatherServiceError as wse:
        return {
            "weather_status": "unavailable",
            "weather_errors": [str(wse)],
            "agent_status": "weather_fetch_failed",
        }
    except Exception as e:
        return {
            "weather_status": "unavailable",
            "weather_errors": [f"Failed to fetch current weather: {str(e)}"],
            "agent_status": "weather_fetch_failed",
        }


async def fetch_weather_forecast(state: TravelState) -> Dict[str, Any]:
    """Node 4: Fetches forecast from WeatherService."""
    if state.get("weather_status") == "unavailable":
        return {}

    lat = state.get("destination_latitude")
    lon = state.get("destination_longitude")
    dest = state.get("destination") or "Unknown"

    try:
        forecast = WeatherService.get_forecast(lat, lon, location_name=dest)
        return {
            "weather_forecast": forecast,
            "agent_status": "weather_forecast_fetched",
        }
    except WeatherServiceError as wse:
        logger.warning(f"Forecast fetch failed: {wse}")
        return {
            "weather_forecast": [],
            "agent_status": "forecast_partial_failure",
        }
    except Exception as e:
        logger.warning(f"Forecast fetch unexpected error: {e}")
        return {
            "weather_forecast": [],
            "agent_status": "forecast_partial_failure",
        }


async def analyze_weather(state: TravelState) -> Dict[str, Any]:
    """Node 5: Generates deterministic travel insights based on weather data."""
    if state.get("weather_status") == "unavailable":
        return {}

    current = state.get("weather_current")
    forecast = state.get("weather_forecast") or []
    dest = state.get("destination") or "Unknown"

    insights = WeatherAgent.generate_weather_insights(current, forecast, dest)
    recs = state.get("destination_recommendations") or []
    place_weathers = WeatherAgent.fetch_places_weather(recs, limit=3)

    return {
        "weather_insights": insights,
        "place_weathers": place_weathers,
        "agent_status": "weather_analyzed",
    }


async def store_weather_results(state: TravelState) -> Dict[str, Any]:
    """Node 6: Finalizes weather fields in TravelState."""
    status = "ready" if state.get("weather_current") else state.get("weather_status", "unavailable")
    return {
        "weather_status": status,
        "agent_status": "weather_analysis_ready",
    }


def build_weather_graph():
    """Builds and compiles the 6-node LangGraph for Weather Intelligence."""
    workflow = StateGraph(TravelState)

    workflow.add_node("validate_weather_requirements", validate_weather_requirements)
    workflow.add_node("resolve_weather_coordinates", resolve_weather_coordinates)
    workflow.add_node("fetch_current_weather", fetch_current_weather)
    workflow.add_node("fetch_weather_forecast", fetch_weather_forecast)
    workflow.add_node("analyze_weather", analyze_weather)
    workflow.add_node("store_weather_results", store_weather_results)

    workflow.add_edge(START, "validate_weather_requirements")
    workflow.add_edge("validate_weather_requirements", "resolve_weather_coordinates")
    workflow.add_edge("resolve_weather_coordinates", "fetch_current_weather")
    workflow.add_edge("fetch_current_weather", "fetch_weather_forecast")
    workflow.add_edge("fetch_weather_forecast", "analyze_weather")
    workflow.add_edge("analyze_weather", "store_weather_results")
    workflow.add_edge("store_weather_results", END)

    return workflow.compile()


weather_graph = build_weather_graph()


async def run_weather_graph(initial_state: TravelState) -> TravelState:
    """Executes compiled weather graph pipeline on input TravelState."""
    final_output = await weather_graph.ainvoke(initial_state)
    return final_output
