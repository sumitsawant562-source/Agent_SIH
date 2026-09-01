"""
LangGraph workflow for Crowd Monitoring & Overcrowding Agent (Stage 9).

Executes a 7-node state graph:
validate_crowd_input -> calculate_crowd_level -> evaluate_overcrowding ->
find_alternative_places -> consider_weather -> generate_ai_explanation -> store_crowd_result
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from app.agents.crowd_agent import CrowdAgent
from app.graph.state import TravelState
from app.services.crowd import CrowdService, CrowdServiceError

logger = logging.getLogger(__name__)


async def validate_crowd_input(state: TravelState) -> Dict[str, Any]:
    """Node 1: Validates presence and format of crowd inputs in TravelState."""
    dest = state.get("crowd_location") or state.get("destination")
    people_count = state.get("crowd_count")
    capacity = state.get("crowd_capacity") or CrowdService.DEFAULT_CAPACITY
    lat = state.get("crowd_latitude") or state.get("current_latitude")
    lon = state.get("crowd_longitude") or state.get("current_longitude")
    conf = state.get("crowd_confidence", 0.95)

    try:
        validated = CrowdAgent.validate_inputs(
            destination_name=dest,
            people_count=people_count if people_count is not None else 0,
            capacity=capacity,
            latitude=lat,
            longitude=lon,
            confidence=conf,
        )
        return {
            "crowd_location": validated["destination"],
            "crowd_count": validated["people_count"],
            "crowd_capacity": validated["capacity"],
            "crowd_latitude": validated["latitude"],
            "crowd_longitude": validated["longitude"],
            "crowd_confidence": validated["confidence"],
            "crowd_status": "input_validated",
            "agent_status": "crowd_input_validated",
        }
    except CrowdServiceError as cse:
        logger.warning(f"Crowd input validation error: {cse}")
        return {
            "crowd_status": "error",
            "crowd_recommendation": str(cse),
            "errors": (state.get("errors") or []) + [str(cse)],
            "agent_status": "crowd_validation_failed",
        }


async def calculate_crowd_level(state: TravelState) -> Dict[str, Any]:
    """Node 2: Deterministically calculates crowd percentage, score, and level classification."""
    if state.get("crowd_status") == "error":
        return {}

    count = state.get("crowd_count", 0)
    capacity = state.get("crowd_capacity", CrowdService.DEFAULT_CAPACITY)

    metrics = CrowdService.calculate_crowd_metrics(count, capacity)
    return {
        "crowd_percentage": metrics["crowd_percentage"],
        "crowd_level": metrics["crowd_level"],
        "crowd_score": metrics["crowd_score"],
        "is_overcrowded": metrics["is_overcrowded"],
        "crowd_recommendation": metrics["base_recommendation"],
        "crowd_status": metrics["crowd_status"],
        "agent_status": "crowd_calculated",
    }


async def evaluate_overcrowding(state: TravelState) -> Dict[str, Any]:
    """Node 3: Evaluates safety thresholds and prepares recommendation strategy."""
    if state.get("crowd_status") == "error":
        return {}

    is_overcrowded = state.get("is_overcrowded", False)
    level = state.get("crowd_level", "LOW")

    # Safety status categorization
    if is_overcrowded:
        status_text = "Overcrowded"
    elif level in ["HIGH", "VERY_HIGH"]:
        status_text = "Busy"
    else:
        status_text = "Normal"

    return {
        "crowd_status": status_text,
        "agent_status": "overcrowding_evaluated",
    }


async def find_alternative_places(state: TravelState) -> Dict[str, Any]:
    """Node 4: Identifies nearby or hidden alternative spots if crowded or on request."""
    if state.get("crowd_status") == "error":
        return {}

    alternatives = CrowdAgent.find_alternative_places(state)
    return {
        "alternative_places": alternatives,
        "agent_status": "alternatives_identified",
    }


async def consider_weather(state: TravelState) -> Dict[str, Any]:
    """Node 5: Contextualizes alternatives and current venue against current weather."""
    if state.get("crowd_status") == "error":
        return {}

    weather = state.get("weather_current") or {}
    condition = weather.get("weather_condition", "Clear")

    # Weather annotation is already attached to alternatives in CrowdAgent
    return {
        "agent_status": "weather_considered",
    }


async def generate_ai_explanation(state: TravelState) -> Dict[str, Any]:
    """Node 6: Generates personalized Gemini AI summary explanation with fallback."""
    if state.get("crowd_status") == "error":
        return {}

    metrics = {
        "people_count": state.get("crowd_count", 0),
        "capacity": state.get("crowd_capacity", CrowdService.DEFAULT_CAPACITY),
        "crowd_percentage": state.get("crowd_percentage", 0.0),
        "crowd_level": state.get("crowd_level", "LOW"),
        "is_overcrowded": state.get("is_overcrowded", False),
        "base_recommendation": state.get("crowd_recommendation", "Visit"),
    }
    alternatives = state.get("alternative_places") or []

    explanation = CrowdAgent.generate_ai_explanation(state, metrics, alternatives)
    return {
        "crowd_ai_explanation": explanation,
        "agent_status": "explanation_generated",
    }


async def store_crowd_result(state: TravelState) -> Dict[str, Any]:
    """Node 7: Finalizes timestamp, metadata, and status in TravelState."""
    now_iso = datetime.now(timezone.utc).isoformat()
    final_status = "ready" if state.get("crowd_status") != "error" else "error"

    return {
        "crowd_timestamp": now_iso,
        "agent_status": f"crowd_{final_status}",
    }


def build_crowd_graph():
    """Builds and compiles the 7-node LangGraph for Crowd Monitoring."""
    workflow = StateGraph(TravelState)

    workflow.add_node("validate_crowd_input", validate_crowd_input)
    workflow.add_node("calculate_crowd_level", calculate_crowd_level)
    workflow.add_node("evaluate_overcrowding", evaluate_overcrowding)
    workflow.add_node("find_alternative_places", find_alternative_places)
    workflow.add_node("consider_weather", consider_weather)
    workflow.add_node("generate_ai_explanation", generate_ai_explanation)
    workflow.add_node("store_crowd_result", store_crowd_result)

    workflow.add_edge(START, "validate_crowd_input")
    workflow.add_edge("validate_crowd_input", "calculate_crowd_level")
    workflow.add_edge("calculate_crowd_level", "evaluate_overcrowding")
    workflow.add_edge("evaluate_overcrowding", "find_alternative_places")
    workflow.add_edge("find_alternative_places", "consider_weather")
    workflow.add_edge("consider_weather", "generate_ai_explanation")
    workflow.add_edge("generate_ai_explanation", "store_crowd_result")
    workflow.add_edge("store_crowd_result", END)

    return workflow.compile()


crowd_graph = build_crowd_graph()


async def run_crowd_graph(initial_state: TravelState) -> TravelState:
    """Executes compiled crowd graph pipeline on input TravelState."""
    final_output = await crowd_graph.ainvoke(initial_state)
    return final_output
