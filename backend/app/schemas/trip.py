from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


TransportMode = Literal["car", "bike", "bus", "train", "flight", "any"]
FoodPreference = Literal["vegetarian", "non-vegetarian", "vegan", "no preference", "any"]
StayPreference = Literal["hotel", "homestay", "hostel", "resort", "any"]
TravelStyle = Literal["relaxed", "balanced", "adventure", "budget", "luxury", "family"]
TripStatus = Literal["draft", "planning", "generating", "completed", "cancelled"]


class TripBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the trip")
    
    # Location fields (support start_location as canonical, starting_location as alias)
    start_location: Optional[str] = Field(None, max_length=150, description="Starting location/origin")
    starting_location: Optional[str] = Field(None, max_length=150, description="Alias for start_location")
    start_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Origin latitude coordinate")
    start_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Origin longitude coordinate")
    
    destination: str = Field(..., min_length=1, max_length=150, description="Travel destination")
    destination_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Destination latitude coordinate")
    destination_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Destination longitude coordinate")
    
    # Date & Duration fields
    start_date: Optional[date] = Field(None, description="Start date of travel")
    end_date: Optional[date] = Field(None, description="End date of travel")
    travel_date: Optional[date] = Field(None, description="Alias for start_date")
    duration_days: Optional[int] = Field(None, gt=0, le=365, description="Number of travel days (must be >= 1)")
    
    # Travelers
    travelers: Optional[int] = Field(1, ge=1, le=100, description="Total travelers count")
    adults: Optional[int] = Field(1, ge=1, le=100, description="Number of adults (must be >= 1)")
    children: Optional[int] = Field(0, ge=0, le=100, description="Number of children (must be >= 0)")
    
    # Budget & Currency
    budget: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2, description="Estimated total budget (must be >= 0)")
    currency: Optional[str] = Field("INR", max_length=10, description="Currency code (e.g. INR, USD)")
    
    # Preferences
    transport_mode: Optional[str] = Field("flight", description="Preferred mode of transportation")
    food_preference: Optional[str] = Field("no preference", description="Food preference")
    stay_preference: Optional[str] = Field("hotel", description="Accommodation/stay preference")
    accommodation_preference: Optional[str] = Field(None, description="Alias for stay_preference")
    travel_style: Optional[str] = Field("balanced", description="Overall travel pace and style")
    interests: Optional[Union[List[str], Any]] = Field(default_factory=list, description="Travel interests (list or JSONB structure)")
    special_requirements: Optional[str] = Field(None, description="Special physical or accessibility requirements")
    status: Optional[str] = Field("draft", description="Trip planning status")

    @model_validator(mode="before")
    @classmethod
    def reconcile_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Reconcile start_location <-> starting_location
            if not data.get("start_location") and data.get("starting_location"):
                data["start_location"] = data["starting_location"]
            elif not data.get("starting_location") and data.get("start_location"):
                data["starting_location"] = data["start_location"]
            
            # Ensure at least one start location is set and non-empty
            loc = (data.get("start_location") or data.get("starting_location") or "").strip()
            if not loc:
                raise ValueError("start_location cannot be empty")
            data["start_location"] = loc
            data["starting_location"] = loc

            # Reconcile start_date <-> travel_date
            if not data.get("start_date") and data.get("travel_date"):
                data["start_date"] = data["travel_date"]
            elif not data.get("travel_date") and data.get("start_date"):
                data["travel_date"] = data["start_date"]

            # Reconcile stay_preference <-> accommodation_preference
            if not data.get("stay_preference") and data.get("accommodation_preference"):
                data["stay_preference"] = data["accommodation_preference"]
            elif not data.get("accommodation_preference") and data.get("stay_preference"):
                data["accommodation_preference"] = data["stay_preference"]

            # Reconcile travelers count
            adults_cnt = int(data.get("adults") or 1)
            kids_cnt = int(data.get("children") or 0)
            if not data.get("travelers"):
                data["travelers"] = max(1, adults_cnt + kids_cnt)

            # Ensure duration_days fallback if not provided
            if not data.get("duration_days"):
                data["duration_days"] = 1
        return data

    @field_validator("title", "destination", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return v_stripped
        return v


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    start_location: Optional[str] = Field(None, min_length=1, max_length=150)
    starting_location: Optional[str] = Field(None, min_length=1, max_length=150)
    start_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    start_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    destination: Optional[str] = Field(None, min_length=1, max_length=150)
    destination_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    destination_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    travel_date: Optional[date] = None
    duration_days: Optional[int] = Field(None, gt=0, le=365)
    travelers: Optional[int] = Field(None, ge=1, le=100)
    adults: Optional[int] = Field(None, ge=1, le=100)
    children: Optional[int] = Field(None, ge=0, le=100)
    budget: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    currency: Optional[str] = None
    transport_mode: Optional[str] = None
    food_preference: Optional[str] = None
    stay_preference: Optional[str] = None
    accommodation_preference: Optional[str] = None
    travel_style: Optional[str] = None
    interests: Optional[Union[List[str], Any]] = None
    special_requirements: Optional[str] = None
    status: Optional[str] = None

    @field_validator("title", "start_location", "starting_location", "destination", mode="before")
    @classmethod
    def validate_optional_non_empty_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return v_stripped
        return v


class TripResponse(TripBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TripListResponse(BaseModel):
    total: int
    trips: List[TripResponse]
