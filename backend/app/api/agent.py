"""
AI Agent API Router.

Exposes endpoints for the Requirement Agent workflow.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import AuthenticatedUser, get_current_user
from app.graph.destination_graph import run_destination_graph
from app.graph.requirement_graph import run_requirement_graph
from app.graph.state import create_initial_travel_state
from app.schemas.agent import (
    DestinationRecommendationItem,
    DestinationResponse,
    DestinationResponseData,
    DestinationStartRequest,
    RequirementData,
    RequirementRespondRequest,
    RequirementResponse,
    RequirementStartRequest,
)
from app.schemas.trip import TripUpdate
from app.services.trip_service import TripService

router = APIRouter(prefix="/agent", tags=["AI Agents"])


@router.post(
    "/requirements/start",
    response_model=RequirementResponse,
    summary="Start Requirement Evaluation",
    description="Initializes the TravelState for a trip and evaluates requirement completeness.",
)
async def start_requirements(
    req: RequirementStartRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Authenticates the user.
    2. Loads trip & verifies ownership.
    3. Initializes TravelState.
    4. Runs Requirement Graph.
    5. Returns requirement status and clarification questions.
    """
    # 1 & 2: Load trip and enforce ownership (raises 404/403 automatically)
    trip = await TripService.get_trip_by_id(current_user.id, req.trip_id)

    # 3: Initialize TravelState
    initial_state = create_initial_travel_state(
        trip_id=req.trip_id,
        user_id=current_user.id,
        trip_data=trip,
    )

    # 4: Run requirement graph
    try:
        final_state = await run_requirement_graph(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate travel requirements.",
        )

    # 5: Return structured response
    return RequirementResponse(
        success=True,
        data=RequirementData(
            trip_id=req.trip_id,
            requirements_complete=final_state.get("requirements_complete", False),
            missing_information=final_state.get("missing_information", []),
            questions=final_state.get("questions", []),
            start_location=final_state.get("start_location"),
            destination=final_state.get("destination"),
            start_date=final_state.get("start_date"),
            end_date=final_state.get("end_date"),
            duration_days=final_state.get("duration_days"),
            travelers=final_state.get("travelers"),
            adults=final_state.get("adults"),
            children=final_state.get("children"),
            budget=final_state.get("budget"),
            currency=final_state.get("currency"),
            transport_mode=final_state.get("transport_mode"),
            food_preference=final_state.get("food_preference"),
            stay_preference=final_state.get("stay_preference"),
            interests=final_state.get("interests"),
            special_requirements=final_state.get("special_requirements"),
        ),
    )


@router.post(
    "/requirements/respond",
    response_model=RequirementResponse,
    summary="Process User Answers to Requirements",
    description="Processes user's natural language answers, extracts parameters, and re-evaluates requirements.",
)
async def respond_requirements(
    req: RequirementRespondRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Authenticates user & verifies trip ownership.
    2. Loads current state from trip record.
    3. Runs Requirement Graph with user's answers.
    4. Syncs updated fields back to trip database.
    5. Returns updated requirement status.
    """
    # 1: Load trip and enforce ownership
    trip = await TripService.get_trip_by_id(current_user.id, req.trip_id)

    # 2: Create state with user answers
    state_with_answers = create_initial_travel_state(
        trip_id=req.trip_id,
        user_id=current_user.id,
        trip_data=trip,
        user_answers=req.answers,
    )

    # 3: Run requirement graph
    try:
        final_state = await run_requirement_graph(state_with_answers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process travel requirement response.",
        )

    # 4: Sync extracted parameters back to the trip record
    update_fields: dict = {}
    if final_state.get("start_date"):
        update_fields["start_date"] = final_state["start_date"]
    if final_state.get("end_date"):
        update_fields["end_date"] = final_state["end_date"]
    if final_state.get("duration_days"):
        update_fields["duration_days"] = final_state["duration_days"]
    if final_state.get("travelers"):
        update_fields["travelers"] = final_state["travelers"]
    if final_state.get("adults"):
        update_fields["adults"] = final_state["adults"]
    if final_state.get("children") is not None:
        update_fields["children"] = final_state["children"]
    if final_state.get("budget"):
        update_fields["budget"] = Decimal(str(final_state["budget"]))
    if final_state.get("food_preference"):
        update_fields["food_preference"] = final_state["food_preference"]
    if final_state.get("stay_preference"):
        update_fields["stay_preference"] = final_state["stay_preference"]
    if final_state.get("transport_mode"):
        update_fields["transport_mode"] = final_state["transport_mode"]
    if final_state.get("interests"):
        update_fields["interests"] = final_state["interests"]
    if final_state.get("special_requirements"):
        update_fields["special_requirements"] = final_state["special_requirements"]

    if update_fields:
        try:
            trip_update = TripUpdate(**update_fields)
            await TripService.update_trip(current_user.id, req.trip_id, trip_update)
        except Exception as e:
            print(f"[Agent API Warning] Failed to sync trip update: {e}")

    # 5: Return updated status
    return RequirementResponse(
        success=True,
        data=RequirementData(
            trip_id=req.trip_id,
            requirements_complete=final_state.get("requirements_complete", False),
            missing_information=final_state.get("missing_information", []),
            questions=final_state.get("questions", []),
            start_location=final_state.get("start_location"),
            destination=final_state.get("destination"),
            start_date=final_state.get("start_date"),
            end_date=final_state.get("end_date"),
            duration_days=final_state.get("duration_days"),
            travelers=final_state.get("travelers"),
            adults=final_state.get("adults"),
            children=final_state.get("children"),
            budget=final_state.get("budget"),
            currency=final_state.get("currency"),
            transport_mode=final_state.get("transport_mode"),
            food_preference=final_state.get("food_preference"),
            stay_preference=final_state.get("stay_preference"),
            interests=final_state.get("interests"),
            special_requirements=final_state.get("special_requirements"),
        ),
    )


@router.post(
    "/destinations/start",
    response_model=DestinationResponse,
    summary="Start Destination Intelligence Evaluation",
    description="Analyzes completed TravelState and generates categorized, personalized destination recommendations using Gemini AI.",
)
async def start_destinations(
    req: DestinationStartRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Authenticates user & verifies trip ownership.
    2. Loads trip data & initializes TravelState.
    3. Runs Destination Graph pipeline.
    4. Computes category summaries & returns structured recommendations.
    """
    # 1: Load trip and enforce ownership (raises 404/403 automatically)
    trip = await TripService.get_trip_by_id(current_user.id, req.trip_id)

    # 2: Initialize TravelState
    initial_state = create_initial_travel_state(
        trip_id=req.trip_id,
        user_id=current_user.id,
        trip_data=trip,
    )

    # 3: Run destination graph
    try:
        final_state = await run_destination_graph(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate destination recommendations.",
        )

    recommendations_raw = final_state.get("destination_recommendations") or []
    
    # Cast to DestinationRecommendationItem models
    items: list[DestinationRecommendationItem] = []
    category_counts: dict[str, int] = {}

    for r in recommendations_raw:
        item = DestinationRecommendationItem(**r)
        items.append(item)
        category_counts[item.category] = category_counts.get(item.category, 0) + 1

    destination_name = final_state.get("destination") or trip.get("destination") or "Unknown"

    return DestinationResponse(
        success=True,
        data=DestinationResponseData(
            trip_id=req.trip_id,
            destination=destination_name,
            recommendations=items,
            categories_summary=category_counts,
            total_recommendations=len(items),
        ),
    )

