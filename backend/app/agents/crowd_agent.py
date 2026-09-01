"""
Crowd Monitoring & Overcrowding Agent (Stage 9).

Responsible for:
1. Validating crowd inputs (people count, venue capacity, GPS coordinates, destination name).
2. Calculating deterministic crowd metrics (LOW, MODERATE, HIGH, VERY_HIGH, OVER_CROWDED).
3. Evaluating overcrowding safety thresholds.
4. Intelligent alternative destination discovery and ranking from Destination Agent recommendations.
5. Considering weather conditions for alternative recommendations.
6. Generating personalized Gemini AI explanations with robust deterministic fallbacks.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.destination_agent import DestinationAgent
from app.core.config import settings
from app.graph.state import TravelState
from app.services.crowd import CrowdDetectionResult, CrowdService, CrowdServiceError
from app.services.gemini import get_gemini_client

logger = logging.getLogger(__name__)


class CrowdAgent:
    """Agent responsible for crowd intelligence, overcrowding prevention, and alternative routing recommendations."""

    @classmethod
    def validate_inputs(
        cls,
        destination_name: Optional[str],
        people_count: Any,
        capacity: Optional[Any] = None,
        latitude: Optional[Any] = None,
        longitude: Optional[Any] = None,
        confidence: Optional[Any] = 0.95,
    ) -> Dict[str, Any]:
        """
        Validates all crowd monitoring inputs.
        Raises CrowdServiceError on invalid inputs.
        """
        dest = (destination_name or "").strip()
        if not dest:
            raise CrowdServiceError("Destination or place name is required for crowd monitoring.")

        valid_count = CrowdService.validate_people_count(people_count)
        valid_capacity = CrowdService.validate_capacity(capacity)

        valid_lat, valid_lon = None, None
        if latitude is not None and longitude is not None:
            valid_lat, valid_lon = CrowdService.validate_coordinates(latitude, longitude)

        try:
            valid_conf = float(confidence) if confidence is not None else 0.95
            valid_conf = max(0.0, min(1.0, valid_conf))
        except (ValueError, TypeError):
            valid_conf = 0.95

        return {
            "destination": dest,
            "people_count": valid_count,
            "capacity": valid_capacity,
            "latitude": valid_lat,
            "longitude": valid_lon,
            "confidence": valid_conf,
        }

    @classmethod
    def calculate_crowd(cls, state: TravelState) -> Dict[str, Any]:
        """
        Calculates deterministic crowd metrics from TravelState.
        """
        count = state.get("crowd_count", 0)
        capacity = state.get("crowd_capacity", CrowdService.DEFAULT_CAPACITY)

        metrics = CrowdService.calculate_crowd_metrics(count, capacity)
        return metrics

    @classmethod
    def find_alternative_places(cls, state: TravelState) -> List[Dict[str, Any]]:
        """
        Discovers and ranks alternative destinations from Destination Agent recommendations.
        Filters out the current place, integrates distances and weather conditions.
        """
        current_place = (state.get("crowd_location") or state.get("destination") or "").strip().lower()
        recs = state.get("destination_recommendations") or []

        # If recommendations are not populated in state, generate from DestinationAgent
        if not recs and state.get("destination"):
            try:
                recs = DestinationAgent.generate_recommendations(state)
            except Exception as e:
                logger.warning(f"Failed to generate destination recommendations: {e}")
                recs = []

        ref_lat = state.get("current_latitude") or state.get("crowd_latitude") or state.get("destination_latitude")
        ref_lon = state.get("current_longitude") or state.get("crowd_longitude") or state.get("destination_longitude")

        weather_current = state.get("weather_current") or {}
        weather_condition = weather_current.get("weather_condition", "Clear")
        rain_prob = weather_current.get("rain_probability", 0.0)

        alternatives: List[Dict[str, Any]] = []
        seen_names = set()

        # Categories that make good lower-crowd alternatives
        category_weights = {
            "hidden_gem": 10,
            "nature_adventure": 8,
            "nearby_place": 7,
            "cultural_historical": 6,
            "family_friendly": 5,
            "famous_place": 3,
            "stay_area": 2,
            "food_dining": 2,
        }

        for item in recs:
            name = (item.get("name") or "").strip()
            if not name:
                continue

            name_lower = name.lower()
            # Do not recommend the same place
            if name_lower == current_place or current_place in name_lower or name_lower in current_place:
                continue

            if name_lower in seen_names:
                continue
            seen_names.add(name_lower)

            category = item.get("category", "nearby_place")
            p_lat = item.get("latitude")
            p_lon = item.get("longitude")

            dist_km: Optional[float] = None
            if ref_lat is not None and ref_lon is not None and p_lat is not None and p_lon is not None:
                try:
                    dist_km = CrowdService.haversine_distance_km(
                        float(ref_lat), float(ref_lon), float(p_lat), float(p_lon)
                    )
                except Exception:
                    dist_km = None

            # Assess weather suitability for this alternative
            weather_suitability = "Suitable"
            if rain_prob > 0.6 and category in ["nature_adventure", "famous_place"]:
                weather_suitability = f"Caution: High rain probability ({int(rain_prob * 100)}%)"
            elif weather_condition in ["Rain", "Thunderstorm", "Snow"]:
                weather_suitability = f"Indoor or covered areas recommended ({weather_condition})"

            # Calculate a ranking score (higher is better)
            base_weight = category_weights.get(category, 4)
            distance_penalty = (dist_km * 0.2) if dist_km is not None else 2.0
            rank_score = base_weight * 10.0 - distance_penalty

            alternatives.append({
                "name": name,
                "category": category,
                "description": item.get("description", ""),
                "why_recommended": item.get("why_recommended") or f"Great alternative with lower crowd density.",
                "estimated_visit_duration": item.get("estimated_visit_duration") or "1-2 hours",
                "estimated_cost": item.get("estimated_cost", 0.0),
                "currency": item.get("currency", "INR"),
                "latitude": p_lat,
                "longitude": p_lon,
                "distance_km": dist_km,
                "weather_suitability": weather_suitability,
                "confidence": item.get("confidence", 0.9),
                "_rank_score": rank_score,
            })

        # Sort by rank score descending (best alternatives first)
        alternatives.sort(key=lambda x: x["_rank_score"], reverse=True)

        # Remove internal score field before returning
        for alt in alternatives:
            alt.pop("_rank_score", None)

        # Return top 4 suitable alternatives
        return alternatives[:4]

    @classmethod
    def generate_ai_explanation(
        cls,
        state: TravelState,
        metrics: Dict[str, Any],
        alternatives: List[Dict[str, Any]],
    ) -> str:
        """
        Uses Gemini AI to generate a natural, context-aware explanation and recommendation.
        Guaranteed to fall back gracefully to a structured deterministic explanation.
        """
        place = state.get("crowd_location") or state.get("destination") or "Destination"
        level = metrics.get("crowd_level", "MODERATE")
        percentage = metrics.get("crowd_percentage", 50.0)
        is_overcrowded = metrics.get("is_overcrowded", False)
        base_rec = metrics.get("base_recommendation", "Visit")

        # Deterministic fallback text
        alt_names = [a["name"] for a in alternatives[:2]]
        alt_text = f" Recommended alternatives include {', '.join(alt_names)}." if alt_names and is_overcrowded else ""
        deterministic_explanation = (
            f"{place} is currently at {percentage}% capacity ({level.replace('_', ' ')} crowd level). "
            f"{base_rec}.{alt_text}"
        )

        client = get_gemini_client()
        if not client:
            return deterministic_explanation

        try:
            interests_str = ", ".join(state.get("interests") or ["sightseeing"])
            prompt = (
                f"You are the Crowd Monitoring & Travel Intelligence AI. "
                f"The user is visiting '{place}'.\n"
                f"Current crowd metrics:\n"
                f"- People Count: {metrics.get('people_count')}\n"
                f"- Capacity: {metrics.get('capacity')}\n"
                f"- Capacity Percentage: {percentage}%\n"
                f"- Crowd Level: {level}\n"
                f"- Status: {'OVERCROWDED' if is_overcrowded else 'NORMAL'}\n"
                f"- Base Safety Recommendation: {base_rec}\n"
                f"- User Travel Interests: {interests_str}\n"
                f"- Suggested Alternatives: {[a['name'] for a in alternatives[:3]]}\n\n"
                f"Write a concise, professional 2-3 sentence travel recommendation. "
                f"Clearly explain why the recommendation is made based on the crowd data. "
                f"Do NOT change the numerical percentages or crowd levels."
            )

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            text = (getattr(response, "text", "") or "").strip()
            if text and len(text) > 15:
                return text
            return deterministic_explanation
        except Exception as e:
            logger.warning(f"Gemini crowd explanation generation failed: {e}. Using deterministic fallback.")
            return deterministic_explanation
