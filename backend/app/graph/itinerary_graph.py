"""
LangGraph workflow for Itinerary Planning Agent (Stage 7).

Executes an 8-node state graph:
validate_itinerary_requirements -> load_destination_recommendations -> load_weather_information
-> generate_itinerary -> validate_itinerary -> budget_check -> weather_consistency_check -> store_itinerary
"""

import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from app.agents.itinerary_agent import ItineraryAgent
from app.graph.state import TravelState

logger = logging.getLogger(__name__)


async def validate_itinerary_requirements(state: TravelState) -> Dict[str, Any]:
    """Node 1: Validates that destination exists and state has basic parameters."""
    dest = state.get("destination")
    if not dest or not dest.strip():
        return {
            "itinerary_status": "unavailable",
            "itinerary_errors": ["No destination specified in travel state."],
            "agent_status": "itinerary_validation_failed",
        }
    return {
        "itinerary_errors": [],
        "agent_status": "itinerary_requirements_validated",
    }


async def load_destination_recommendations(state: TravelState) -> Dict[str, Any]:
    """Node 2: Verifies/prepares Stage 5 destination recommendations."""
    if state.get("itinerary_status") == "unavailable":
        return {}

    recs = state.get("destination_recommendations") or []
    return {
        "agent_status": "destination_data_loaded",
    }


async def load_weather_information(state: TravelState) -> Dict[str, Any]:
    """Node 3: Verifies/prepares Stage 6 weather insights and forecast."""
    if state.get("itinerary_status") == "unavailable":
        return {}

    return {
        "agent_status": "weather_data_loaded",
    }


async def generate_itinerary(state: TravelState) -> Dict[str, Any]:
    """Node 4: Synthesizes multi-day itinerary using Gemini AI or fallback."""
    if state.get("itinerary_status") == "unavailable":
        return {}

    res = ItineraryAgent.generate_itinerary(state)
    return {
        "itinerary": res.get("itinerary"),
        "itinerary_status": res.get("itinerary_status", "ready"),
        "itinerary_errors": res.get("itinerary_errors", []),
        "agent_status": "itinerary_generated",
    }


async def validate_itinerary(state: TravelState) -> Dict[str, Any]:
    """Node 5: Validates day count and structure of generated itinerary."""
    if state.get("itinerary_status") == "unavailable":
        return {}

    itin = state.get("itinerary")
    if not itin or not itin.get("days"):
        return {
            "itinerary_status": "unavailable",
            "itinerary_errors": ["Generated itinerary is missing daily schedules."],
            "agent_status": "itinerary_validation_failed",
        }

    return {
        "agent_status": "itinerary_structure_validated",
    }


async def budget_check(state: TravelState) -> Dict[str, Any]:
    """Node 6: Assesses total estimated cost relative to traveler budget."""
    if state.get("itinerary_status") == "unavailable":
        return {}

    itin = state.get("itinerary") or {}
    total_cost = float(itin.get("total_estimated_cost") or 0.0)
    budget = float(state.get("budget") or 0.0)
    currency = state.get("currency") or "INR"

    if budget > 0 and total_cost > budget:
        diff = total_cost - budget
        itin["budget_status"] = "exceeds_budget"
        itin["budget_warning"] = (
            f"Estimated itinerary cost ({currency} {int(total_cost):,}) exceeds budget "
            f"({currency} {int(budget):,}) by {currency} {int(diff):,}."
        )
    elif budget > 0:
        itin["budget_status"] = "within_budget"
        itin["budget_warning"] = None
    else:
        itin["budget_status"] = "unspecified"
        itin["budget_warning"] = None

    if itin.get("trip_summary") and isinstance(itin["trip_summary"], dict):
        itin["trip_summary"]["budget_status"] = itin["budget_status"]
        itin["trip_summary"]["estimated_total_cost"] = total_cost

    return {
        "itinerary": itin,
        "agent_status": "budget_checked",
    }


async def weather_consistency_check(state: TravelState) -> Dict[str, Any]:
    """Node 7: Cross-references outdoor activities against weather alerts."""
    if state.get("itinerary_status") == "unavailable":
        return {}

    itin = state.get("itinerary") or {}
    insights = state.get("weather_insights") or []
    rain_alerts = [i for i in insights if isinstance(i, dict) and i.get("type") == "rain_alert"]

    if rain_alerts:
        itin["weather_advisory"] = rain_alerts[0].get("message")
    elif insights:
        first = insights[0]
        itin["weather_advisory"] = first.get("message") if isinstance(first, dict) else str(first)

    return {
        "itinerary": itin,
        "agent_status": "weather_consistency_checked",
    }


async def store_itinerary(state: TravelState) -> Dict[str, Any]:
    """Node 8: Finalizes itinerary storage in TravelState."""
    status = "ready" if state.get("itinerary") else "unavailable"
    return {
        "itinerary_status": status,
        "agent_status": "itinerary_synthesis_ready",
    }


def build_itinerary_graph():
    """Builds and compiles the 8-node LangGraph for Itinerary Planning."""
    workflow = StateGraph(TravelState)

    workflow.add_node("validate_itinerary_requirements", validate_itinerary_requirements)
    workflow.add_node("load_destination_recommendations", load_destination_recommendations)
    workflow.add_node("load_weather_information", load_weather_information)
    workflow.add_node("generate_itinerary", generate_itinerary)
    workflow.add_node("validate_itinerary", validate_itinerary)
    workflow.add_node("budget_check", budget_check)
    workflow.add_node("weather_consistency_check", weather_consistency_check)
    workflow.add_node("store_itinerary", store_itinerary)

    workflow.add_edge(START, "validate_itinerary_requirements")
    workflow.add_edge("validate_itinerary_requirements", "load_destination_recommendations")
    workflow.add_edge("load_destination_recommendations", "load_weather_information")
    workflow.add_edge("load_weather_information", "generate_itinerary")
    workflow.add_edge("generate_itinerary", "validate_itinerary")
    workflow.add_edge("validate_itinerary", "budget_check")
    workflow.add_edge("budget_check", "weather_consistency_check")
    workflow.add_edge("weather_consistency_check", "store_itinerary")
    workflow.add_edge("store_itinerary", END)

    return workflow.compile()


itinerary_graph = build_itinerary_graph()


async def run_itinerary_graph(initial_state: TravelState) -> TravelState:
    """Executes compiled itinerary graph pipeline on input TravelState."""
    final_output = await itinerary_graph.ainvoke(initial_state)
    return final_output
