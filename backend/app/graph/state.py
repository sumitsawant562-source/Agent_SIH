"""
LangGraph TravelState definition.

Structured, typed state passed between nodes in the agent graph.
"""

from typing import Any, Dict, List, Optional, TypedDict


class TravelState(TypedDict, total=False):
    # Core identifiers
    trip_id: str
    user_id: str
    title: Optional[str]

    # Geographical locations & coordinates
    start_location: Optional[str]
    destination: Optional[str]
    start_latitude: Optional[float]
    start_longitude: Optional[float]
    destination_latitude: Optional[float]
    destination_longitude: Optional[float]

    # Dates & Duration
    start_date: Optional[str]
    end_date: Optional[str]
    duration_days: Optional[int]

    # Travelers composition
    travelers: Optional[int]
    adults: Optional[int]
    children: Optional[int]

    # Budget & Currency
    budget: Optional[float]
    currency: Optional[str]

    # Preferences
    transport_mode: Optional[str]
    food_preference: Optional[str]
    stay_preference: Optional[str]
    interests: Optional[List[str]]
    special_requirements: Optional[str]

    # Agent requirement tracking & conversation
    missing_information: List[str]
    questions: List[str]
    user_answers: Optional[str]
    requirements_complete: bool
    conversation_history: List[Dict[str, Any]]
    errors: List[str]
    agent_status: str

    # Destination recommendations (Stage 5)
    destination_recommendations: Optional[List[Dict[str, Any]]]

    # Weather intelligence (Stage 6)
    weather_current: Optional[Dict[str, Any]]
    weather_forecast: Optional[List[Dict[str, Any]]]
    weather_insights: Optional[List[str]]
    weather_status: Optional[str]
    weather_errors: Optional[List[str]]

    # Itinerary planning (Stage 7)
    itinerary: Optional[Dict[str, Any]]
    itinerary_status: Optional[str]
    itinerary_errors: Optional[List[str]]


def create_initial_travel_state(
    trip_id: str,
    user_id: str,
    trip_data: Optional[Dict[str, Any]] = None,
    user_answers: Optional[str] = None,
) -> TravelState:
    """
    Initializes a structured TravelState from trip record data and optional user input.
    """
    data = trip_data or {}
    
    # Handle possible string / float / int conversions cleanly
    budget_val = data.get("budget")
    if budget_val is not None:
        try:
            budget_val = float(budget_val)
        except (ValueError, TypeError):
            budget_val = None

    travelers_val = data.get("travelers")
    if travelers_val is not None:
        try:
            travelers_val = int(travelers_val)
        except (ValueError, TypeError):
            travelers_val = None

    adults_val = data.get("adults")
    if adults_val is not None:
        try:
            adults_val = int(adults_val)
        except (ValueError, TypeError):
            adults_val = None

    children_val = data.get("children")
    if children_val is not None:
        try:
            children_val = int(children_val)
        except (ValueError, TypeError):
            children_val = 0

    duration_val = data.get("duration_days")
    if duration_val is not None:
        try:
            duration_val = int(duration_val)
        except (ValueError, TypeError):
            duration_val = None

    interests_val = data.get("interests")
    if interests_val is not None:
        if isinstance(interests_val, str):
            interests_val = [i.strip() for i in interests_val.split(",") if i.strip()]
        elif not isinstance(interests_val, list):
            interests_val = list(interests_val)
    else:
        interests_val = []

    start_date_val = str(data.get("start_date") or data.get("travel_date") or "")
    if not start_date_val or start_date_val == "None":
        start_date_val = None

    end_date_val = str(data.get("end_date") or "")
    if not end_date_val or end_date_val == "None":
        end_date_val = None

    start_loc = data.get("start_location") or data.get("starting_location") or None
    if start_loc and isinstance(start_loc, str):
        start_loc = start_loc.strip() or None

    dest = data.get("destination") or None
    if dest and isinstance(dest, str):
        dest = dest.strip() or None

    return TravelState(
        trip_id=trip_id,
        user_id=user_id,
        title=data.get("title") or (f"Trip to {dest}" if dest else "Untitled Trip"),
        start_location=start_loc,
        destination=dest,
        start_latitude=data.get("start_latitude"),
        start_longitude=data.get("start_longitude"),
        destination_latitude=data.get("destination_latitude"),
        destination_longitude=data.get("destination_longitude"),
        start_date=start_date_val,
        end_date=end_date_val,
        duration_days=duration_val,
        travelers=travelers_val,
        adults=adults_val,
        children=children_val,
        budget=budget_val,
        currency=data.get("currency") or "INR",
        transport_mode=data.get("transport_mode") or "flight",
        food_preference=data.get("food_preference") or "no preference",
        stay_preference=data.get("stay_preference") or data.get("accommodation_preference") or "hotel",
        interests=interests_val,
        special_requirements=data.get("special_requirements"),
        missing_information=[],
        questions=[],
        user_answers=user_answers,
        requirements_complete=False,
        conversation_history=data.get("conversation_history") or [],
        errors=[],
        agent_status="idle",
        destination_recommendations=data.get("destination_recommendations") or [],
        weather_current=data.get("weather_current"),
        weather_forecast=data.get("weather_forecast") or [],
        weather_insights=data.get("weather_insights") or [],
        weather_status=data.get("weather_status") or "pending",
        weather_errors=data.get("weather_errors") or [],
        itinerary=data.get("itinerary"),
        itinerary_status=data.get("itinerary_status") or "pending",
        itinerary_errors=data.get("itinerary_errors") or [],
    )


