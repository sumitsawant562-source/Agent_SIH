"""
Crowd Monitoring & Overcrowding Service (Stage 9).

Provides deterministic crowd classification, capacity calculations, coordinate validation,
and a clean abstraction for computer vision (YOLO/OpenCV/video/simulated) detection inputs.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class CrowdServiceError(Exception):
    """Raised when crowd evaluation or validation encounters an error."""
    pass


@dataclass
class CrowdDetectionResult:
    """
    Clean abstraction for computer vision detection results.
    Allows future YOLO, OpenCV, or video stream detection backends to plug in seamlessly.
    """
    people_count: int
    confidence: float = 0.95
    source: str = "simulated_detector"
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class CrowdService:
    """
    Deterministic crowd intelligence and capacity evaluation service.
    """

    # Deterministic crowd thresholds based on venue capacity percentage
    # 0 - 30%   : LOW
    # 31 - 60%  : MODERATE
    # 61 - 80%  : HIGH
    # 81 - 100% : VERY_HIGH
    # > 100%    : OVER_CROWDED
    CROWD_LEVEL_THRESHOLDS = [
        (30.0, "LOW", "Visit"),
        (60.0, "MODERATE", "Visit with caution"),
        (80.0, "HIGH", "Consider visiting during a less busy time"),
        (100.0, "VERY_HIGH", "Consider an alternative"),
    ]

    DEFAULT_CAPACITY = 100

    @classmethod
    def validate_coordinates(cls, lat: Any, lon: Any) -> Tuple[float, float]:
        """
        Validates latitude (-90 to 90) and longitude (-180 to 180).
        Raises CrowdServiceError on invalid coordinates.
        """
        try:
            latitude = float(lat)
            longitude = float(lon)
        except (ValueError, TypeError):
            raise CrowdServiceError(f"Invalid coordinate format: lat={lat}, lon={lon}")

        if not (-90.0 <= latitude <= 90.0):
            raise CrowdServiceError(f"Latitude {latitude} is outside valid range [-90.0, 90.0]")
        if not (-180.0 <= longitude <= 180.0):
            raise CrowdServiceError(f"Longitude {longitude} is outside valid range [-180.0, 180.0]")

        return round(latitude, 6), round(longitude, 6)

    @classmethod
    def validate_people_count(cls, count: Any) -> int:
        """
        Validates non-negative integer person count.
        """
        try:
            val = int(count)
        except (ValueError, TypeError):
            raise CrowdServiceError(f"Invalid people_count '{count}': must be a non-negative integer.")

        if val < 0:
            raise CrowdServiceError(f"people_count cannot be negative: {val}")

        return val

    @classmethod
    def validate_capacity(cls, capacity: Any) -> int:
        """
        Validates positive venue capacity.
        """
        if capacity is None:
            return cls.DEFAULT_CAPACITY

        try:
            val = int(capacity)
        except (ValueError, TypeError):
            raise CrowdServiceError(f"Invalid capacity '{capacity}': must be a positive integer.")

        if val <= 0:
            raise CrowdServiceError(f"capacity must be greater than 0: {val}")

        return val

    @classmethod
    def calculate_crowd_metrics(
        cls,
        people_count: int,
        capacity: int = DEFAULT_CAPACITY,
    ) -> Dict[str, Any]:
        """
        Deterministically computes crowd percentage, level classification,
        overcrowding boolean, and base recommendation.
        """
        valid_count = cls.validate_people_count(people_count)
        valid_capacity = cls.validate_capacity(capacity)

        percentage = round((valid_count / valid_capacity) * 100.0, 1)

        if percentage <= 30.0:
            level = "LOW"
            rec = "Visit"
            status = "Normal"
            is_overcrowded = False
        elif percentage <= 60.0:
            level = "MODERATE"
            rec = "Visit with caution"
            status = "Normal"
            is_overcrowded = False
        elif percentage <= 80.0:
            level = "HIGH"
            rec = "Consider visiting during a less busy time"
            status = "Busy"
            is_overcrowded = False
        elif percentage <= 100.0:
            level = "VERY_HIGH"
            rec = "Consider an alternative"
            status = "Busy"
            is_overcrowded = True
        else:
            level = "OVER_CROWDED"
            rec = "Switch to an alternative destination"
            status = "Overcrowded"
            is_overcrowded = True

        score = min(round(percentage / 100.0, 2), 2.0)

        return {
            "people_count": valid_count,
            "capacity": valid_capacity,
            "crowd_percentage": percentage,
            "crowd_level": level,
            "crowd_score": score,
            "crowd_status": status,
            "is_overcrowded": is_overcrowded,
            "base_recommendation": rec,
        }

    @classmethod
    def haversine_distance_km(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Computes great-circle distance between two points in kilometers.
        """
        r = 6371.0  # Earth radius in kilometers
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)
