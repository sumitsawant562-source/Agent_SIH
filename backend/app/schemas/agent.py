"""
Pydantic schemas for AI Agent endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementStartRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")


class RequirementRespondRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")
    answers: str = Field(..., min_length=1, max_length=2000, description="User's natural language response")


class RequirementData(BaseModel):
    trip_id: str
    requirements_complete: bool
    missing_information: List[str]
    questions: List[str]
    start_location: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None
    travelers: Optional[int] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    transport_mode: Optional[str] = None
    food_preference: Optional[str] = None
    stay_preference: Optional[str] = None
    interests: Optional[List[str]] = None
    special_requirements: Optional[str] = None


class RequirementResponse(BaseModel):
    success: bool
    data: RequirementData


# ==============================================================================
# Stage 5: Destination Intelligence Schemas
# ==============================================================================


class DestinationRecommendationItem(BaseModel):
    name: str = Field(..., description="Name of the place, area, or activity")
    category: str = Field(
        ...,
        description="Category: famous_place, hidden_gem, nearby_place, food_dining, stay_area, nature_adventure, cultural_historical, family_friendly",
    )
    description: str = Field(..., description="Rich summary of the recommendation")
    why_recommended: str = Field(..., description="Reasoning personalized to user interests/preferences")
    estimated_visit_duration: Optional[str] = Field(None, description="e.g. '2-3 hours', 'Half day'")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in local currency")
    currency: str = Field("INR", description="Currency code (e.g. INR, USD)")
    latitude: Optional[float] = Field(None, description="Latitude coordinate if available")
    longitude: Optional[float] = Field(None, description="Longitude coordinate if available")
    best_time_to_visit: Optional[str] = Field(None, description="e.g. 'Morning', 'Sunset', 'October to March'")
    distance_from_destination: Optional[str] = Field(None, description="e.g. 'Central', '15 km north'")
    distance_from_previous_location: Optional[str] = Field(None, description="Distance from origin or transit hub")
    tags: List[str] = Field(default_factory=list, description="Keywords / theme tags")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Recommendation confidence score between 0.0 and 1.0")


class DestinationStartRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")


class DestinationResponseData(BaseModel):
    trip_id: str
    destination: str
    recommendations: List[DestinationRecommendationItem]
    categories_summary: Optional[Dict[str, int]] = None
    total_recommendations: int


class DestinationResponse(BaseModel):
    success: bool
    data: DestinationResponseData

