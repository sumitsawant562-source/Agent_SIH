from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional, Union


@dataclass
class Trip:
    id: str
    user_id: str
    title: str
    start_location: str
    destination: str
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    destination_latitude: Optional[float] = None
    destination_longitude: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    travel_date: Optional[date] = None
    duration_days: int = 1
    travelers: int = 1
    adults: int = 1
    children: int = 0
    budget: Optional[Decimal] = None
    currency: str = "INR"
    transport_mode: str = "flight"
    food_preference: str = "no preference"
    stay_preference: str = "hotel"
    accommodation_preference: Optional[str] = None
    travel_style: str = "balanced"
    interests: Any = field(default_factory=list)
    special_requirements: Optional[str] = None
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
