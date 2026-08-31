"""
LangGraph Destination Graph Workflow.

Defines the state graph for evaluating destination requirements, generating
intelligent personalized recommendations, validating data quality, and storing results.
"""

from typing import Any, Dict, List
from langgraph.graph import StateGraph, START, END

from app.agents.destination_agent import DestinationAgent
from app.graph.state import TravelState


def validate_destination_requirements_node(state: TravelState) -> Dict[str, Any]:
    """
    LangGraph Node 1: Verifies that the mandatory destination field is present in TravelState.
    """
    destination = state.get("destination")
    errors = list(state.get("errors") or [])

    if not destination or not str(destination).strip():
        errors.append("Destination is required to generate destination recommendations.")
        return {
            "errors": errors,
            "agent_status": "error_missing_destination",
        }

    return {
        "agent_status": "destination_validated",
    }


def generate_destination_recommendations_node(state: TravelState) -> Dict[str, Any]:
    """
    LangGraph Node 2: Calls DestinationAgent to generate recommendations using Gemini or Fallback.
    """
    if "error_missing_destination" in state.get("agent_status", ""):
        return {"destination_recommendations": []}

    recommendations = DestinationAgent.generate_recommendations(state)
    return {
        "destination_recommendations": recommendations,
        "agent_status": "recommendations_generated",
    }


def validate_and_deduplicate_recommendations_node(state: TravelState) -> Dict[str, Any]:
    """
    LangGraph Node 3: Ensures recommendation quality, schema conformance, and deduplication.
    """
    raw_items = state.get("destination_recommendations") or []
    cleaned_items = DestinationAgent.validate_and_deduplicate(raw_items, state)

    return {
        "destination_recommendations": cleaned_items,
        "agent_status": "recommendations_validated",
    }


def store_destination_results_node(state: TravelState) -> Dict[str, Any]:
    """
    LangGraph Node 4: Finalizes state with summary metrics and sets completed agent status.
    """
    items = state.get("destination_recommendations") or []
    status_str = "destination_recommendations_ready" if len(items) > 0 else "no_recommendations_found"

    return {
        "destination_recommendations": items,
        "agent_status": status_str,
    }


def build_destination_graph():
    """
    Constructs and compiles the Destination Intelligence LangGraph workflow.
    """
    workflow = StateGraph(TravelState)

    # 1. Add nodes
    workflow.add_node("validate_destination_requirements", validate_destination_requirements_node)
    workflow.add_node("generate_destination_recommendations", generate_destination_recommendations_node)
    workflow.add_node("validate_and_deduplicate_recommendations", validate_and_deduplicate_recommendations_node)
    workflow.add_node("store_destination_results", store_destination_results_node)

    # 2. Add edges: sequential pipeline
    workflow.add_edge(START, "validate_destination_requirements")
    workflow.add_edge("validate_destination_requirements", "generate_destination_recommendations")
    workflow.add_edge("generate_destination_recommendations", "validate_and_deduplicate_recommendations")
    workflow.add_edge("validate_and_deduplicate_recommendations", "store_destination_results")
    workflow.add_edge("store_destination_results", END)

    return workflow.compile()


# Singleton compiled graph instance
destination_graph = build_destination_graph()


async def run_destination_graph(initial_state: TravelState) -> TravelState:
    """
    Executes the destination graph asynchronously with the given initial TravelState.
    """
    result = await destination_graph.ainvoke(initial_state)
    return result
