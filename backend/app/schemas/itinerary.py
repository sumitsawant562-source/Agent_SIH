"""
Itinerary Pydantic schemas for request validation and response serialization.

Itineraries store AI-generated travel plans linked to trips.
Supports versioning for re-generation and adaptation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


ItineraryStatus = Literal["draft", "generating", "completed", "failed"]


class ItineraryCreate(BaseModel):
    """Schema for creating a new itinerary linked to a trip."""
    trip_id: str = Field(..., description="UUID of the parent trip")
    version: int = Field(1, ge=1, description="Itinerary version number")
    itinerary_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="JSONB itinerary content (day-by-day plan, activities, etc.)"
    )
    estimated_cost: Optional[Decimal] = Field(
        None, ge=0, max_digits=12, decimal_places=2,
        description="Estimated total cost of the itinerary"
    )
    currency: str = Field("INR", max_length=10, description="Currency code (e.g., INR, USD)")
    status: ItineraryStatus = Field("draft", description="Itinerary generation status")


class ItineraryUpdate(BaseModel):
    """Schema for updating an existing itinerary."""
    version: Optional[int] = Field(None, ge=1)
    itinerary_data: Optional[Dict[str, Any]] = None
    estimated_cost: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=10)
    status: Optional[ItineraryStatus] = None


class ItineraryResponse(BaseModel):
    """Schema for itinerary API responses."""
    id: str
    trip_id: str
    version: int
    itinerary_data: Optional[Dict[str, Any]] = None
    estimated_cost: Optional[float] = None
    currency: str = "INR"
    status: str = "draft"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItineraryListResponse(BaseModel):
    """Schema for listing multiple itineraries."""
    total: int
    itineraries: List[ItineraryResponse]
