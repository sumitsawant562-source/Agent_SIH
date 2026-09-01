"""
LangGraph workflow for Live Route & GPS Agent (Stage 8).

Executes a 5-node state graph:
validate_route_request -> validate_coordinates -> calculate_route -> validate_route_response -> store_route
"""

import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from app.agents.route_agent import RouteAgent
from app.graph.state import TravelState
from app.services.routing import RoutingService

logger = logging.getLogger(__name__)


async def validate_route_request(state: TravelState) -> Dict[str, Any]:
    """Node 1: Validates presence of origin and destination in TravelState."""
    origin = state.get("route_origin")
    destination = state.get("route_destination")

    if not origin or not destination:
        return {
            "route_status": "unavailable",
            "route_error": "Both origin and destination coordinates are required.",
            "agent_status": "route_validation_failed",
        }

    return {
        "route_error": None,
        "agent_status": "route_request_validated",
    }


async def validate_coordinates(state: TravelState) -> Dict[str, Any]:
    """Node 2: Validates latitude and longitude ranges."""
    if state.get("route_status") == "unavailable":
        return {}

    origin = state.get("route_origin") or {}
    dest = state.get("route_destination") or {}

    try:
        RoutingService.validate_coordinates(origin.get("latitude"), origin.get("longitude"))
        RoutingService.validate_coordinates(dest.get("latitude"), dest.get("longitude"))
        return {
            "agent_status": "route_coordinates_validated",
        }
    except Exception as e:
        return {
            "route_status": "unavailable",
            "route_error": str(e),
            "agent_status": "route_coordinates_invalid",
        }


async def calculate_route(state: TravelState) -> Dict[str, Any]:
    """Node 3: Invokes RoutingService to compute real distance, duration, and geometry."""
    if state.get("route_status") == "unavailable":
        return {}

    res = RouteAgent.calculate_route(state)
    return res


async def validate_route_response(state: TravelState) -> Dict[str, Any]:
    """Node 4: Assesses the resulting route metrics."""
    if state.get("route_status") == "unavailable":
        return {}

    dist = state.get("route_distance_km") or 0.0
    geom = state.get("route_geometry")

    if dist < 0 or geom is None:
        return {
            "route_status": "unavailable",
            "route_error": "Invalid route geometry or distance received from routing engine.",
            "agent_status": "route_response_invalid",
        }

    return {
        "agent_status": "route_response_validated",
    }


async def store_route(state: TravelState) -> Dict[str, Any]:
    """Node 5: Finalizes route results in TravelState."""
    status = "ready" if state.get("route_status") != "unavailable" else "unavailable"
    return {
        "route_status": status,
        "agent_status": "route_ready",
    }


def build_route_graph():
    """Builds and compiles the 5-node LangGraph for Live Routing."""
    workflow = StateGraph(TravelState)

    workflow.add_node("validate_route_request", validate_route_request)
    workflow.add_node("validate_coordinates", validate_coordinates)
    workflow.add_node("calculate_route", calculate_route)
    workflow.add_node("validate_route_response", validate_route_response)
    workflow.add_node("store_route", store_route)

    workflow.add_edge(START, "validate_route_request")
    workflow.add_edge("validate_route_request", "validate_coordinates")
    workflow.add_edge("validate_coordinates", "calculate_route")
    workflow.add_edge("calculate_route", "validate_route_response")
    workflow.add_edge("validate_route_response", "store_route")
    workflow.add_edge("store_route", END)

    return workflow.compile()


route_graph = build_route_graph()


async def run_route_graph(initial_state: TravelState) -> TravelState:
    """Executes compiled route graph pipeline on input TravelState."""
    final_output = await route_graph.ainvoke(initial_state)
    return final_output
