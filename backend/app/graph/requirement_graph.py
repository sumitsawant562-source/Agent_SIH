"""
LangGraph Requirement Graph Workflow.

Defines the state graph for evaluating requirements and parsing user responses.
"""

from typing import Any, Dict
from langgraph.graph import StateGraph, START, END

from app.agents.requirement_agent import RequirementAgent
from app.graph.state import TravelState


def process_user_answers_node(state: TravelState) -> Dict[str, Any]:
    """
    LangGraph node: Parses natural-language user responses and updates state fields.
    """
    user_answers = state.get("user_answers")
    if not user_answers or not str(user_answers).strip():
        return {}

    updates = RequirementAgent.extract_from_user_text(user_answers, current_state=state)
    
    # Track in conversation history
    history = list(state.get("conversation_history") or [])
    history.append({
        "role": "user",
        "content": user_answers,
    })

    updates["conversation_history"] = history
    return updates


def evaluate_requirements_node(state: TravelState) -> Dict[str, Any]:
    """
    LangGraph node: Evaluates completeness of requirements, generating questions if needed.
    """
    eval_result = RequirementAgent.evaluate_state(state)
    
    # If questions were generated, append agent message to history
    questions = eval_result.get("questions") or []
    history = list(state.get("conversation_history") or [])
    if questions:
        history.append({
            "role": "assistant",
            "content": " ".join(questions),
            "missing_fields": eval_result.get("missing_information", [])
        })

    eval_result["conversation_history"] = history
    return eval_result


def build_requirement_graph():
    """
    Constructs and compiles the Requirement Agent LangGraph workflow.
    """
    workflow = StateGraph(TravelState)

    # Add nodes
    workflow.add_node("process_user_answers", process_user_answers_node)
    workflow.add_node("evaluate_requirements", evaluate_requirements_node)

    # Set flow: START -> process_user_answers -> evaluate_requirements -> END
    workflow.add_edge(START, "process_user_answers")
    workflow.add_edge("process_user_answers", "evaluate_requirements")
    workflow.add_edge("evaluate_requirements", END)

    return workflow.compile()


# Singleton compiled graph instance
requirement_graph = build_requirement_graph()


async def run_requirement_graph(initial_state: TravelState) -> TravelState:
    """
    Executes the requirement graph asynchronously with the given initial TravelState.
    """
    result = await requirement_graph.ainvoke(initial_state)
    return result
