from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class Itinerary:
    id: str
    trip_id: str
    version: int = 1
    itinerary_data: Dict[str, Any] = field(default_factory=dict)
    estimated_cost: Optional[Decimal] = None
    currency: str = "INR"
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
