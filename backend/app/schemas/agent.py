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
