"""
Destination Intelligence Agent for Travel Intelligence Platform.

Responsible for:
1. Receiving a completed TravelState.
2. Generating intelligent, personalized destination recommendations using Gemini AI.
3. Classifying places into structured categories (famous places, hidden gems, nearby places, food/dining, stay areas, nature, culture, family).
4. Sanitizing, validating coordinates/costs, deduplicating places, and computing confidence scores.
5. Providing deterministic fallback recommendations if Gemini is unavailable or errors out.
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.graph.state import TravelState
from app.services.gemini import get_gemini_client

# Standard recognized destination categories
VALID_CATEGORIES = {
    "famous_place",
    "hidden_gem",
    "nearby_place",
    "food_dining",
    "stay_area",
    "nature_adventure",
    "cultural_historical",
    "family_friendly",
}

# Category normalization alias mapping
CATEGORY_ALIASES = {
    "famous_places": "famous_place",
    "famous": "famous_place",
    "attraction": "famous_place",
    "tourist_spot": "famous_place",
    "hidden_gems": "hidden_gem",
    "hidden": "hidden_gem",
    "offbeat": "hidden_gem",
    "secret_spot": "hidden_gem",
    "nearby_places": "nearby_place",
    "nearby": "nearby_place",
    "day_trip": "nearby_place",
    "excursion": "nearby_place",
    "food": "food_dining",
    "dining": "food_dining",
    "restaurant": "food_dining",
    "food_restaurant": "food_dining",
    "food_area": "food_dining",
    "stay": "stay_area",
    "hotel": "stay_area",
    "accommodation": "stay_area",
    "stay_areas": "stay_area",
    "nature": "nature_adventure",
    "adventure": "nature_adventure",
    "outdoor": "nature_adventure",
    "culture": "cultural_historical",
    "heritage": "cultural_historical",
    "history": "cultural_historical",
    "historical": "cultural_historical",
    "family": "family_friendly",
    "kids": "family_friendly",
}


class DestinationAgent:
    """
    Destination Intelligence Agent generates contextual and personalized place recommendations.
    """

    @classmethod
    def generate_recommendations(cls, state: TravelState) -> List[Dict[str, Any]]:
        """
        Main entrypoint: generates structured recommendations for the destination in state.
        Uses Gemini when available, falling back to a deterministic generator if needed.
        """
        destination = state.get("destination")
        if not destination or not str(destination).strip():
            return []

        raw_items: List[Dict[str, Any]] = []
        gemini_success = False

        client = get_gemini_client()
        if client:
            try:
                prompt = cls._build_destination_prompt(state)
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                response_text = getattr(response, "text", "") or ""
                raw_items = cls._parse_gemini_json_response(response_text)
                if raw_items and isinstance(raw_items, list) and len(raw_items) > 0:
                    gemini_success = True
            except Exception as e:
                print(f"[DestinationAgent Warning] Gemini generation encountered an error: {e}")

        # Fallback if Gemini failed or returned empty results
        if not gemini_success or not raw_items:
            raw_items = cls._generate_fallback_recommendations(state)

        # Sanitize, validate and deduplicate
        validated_items = cls.validate_and_deduplicate(raw_items, state)
        return validated_items

    @classmethod
    def _build_destination_prompt(cls, state: TravelState) -> str:
        """
        Builds a comprehensive, personalized prompt for Gemini recommendation generation.
        """
        destination = state.get("destination", "Unknown")
        start_location = state.get("start_location") or "Not specified"
        duration_days = state.get("duration_days") or 3
        adults = state.get("adults") or state.get("travelers") or 1
        children = state.get("children") or 0
        budget = state.get("budget")
        currency = state.get("currency") or "INR"
        transport_mode = state.get("transport_mode") or "standard transport"
        food_pref = state.get("food_preference") or "no preference"
        stay_pref = state.get("stay_preference") or "hotel"
        interests = state.get("interests") or []
        special_req = state.get("special_requirements") or "None"

        interests_str = ", ".join(interests) if interests else "General sightseeing, culture, relaxation"

        return f"""You are the Destination Intelligence Agent for an advanced travel planning platform.
Generate personalized, high-quality, diverse destination recommendations for the following travel profile:

Travel Details:
- Destination: {destination}
- Origin: {start_location}
- Duration: {duration_days} days
- Group: {adults} adults, {children} children
- Total Budget: {budget} {currency}
- Transport Mode: {transport_mode}
- Dietary / Food Preference: {food_pref}
- Accommodation Preference: {stay_pref}
- User Interests: {interests_str}
- Special Requirements: {special_req}

Instructions:
1. Provide between 8 to 14 high-value recommendations across these categories:
   - "famous_place" (must-visit iconic landmarks)
   - "hidden_gem" (offbeat / lesser-known scenic or cultural spots)
   - "nearby_place" (day-trip spots or scenic getaways nearby)
   - "food_dining" (popular food streets, local cuisine hubs aligned with {food_pref})
   - "stay_area" (recommended neighborhoods/areas matching {stay_pref} and budget)
   - "nature_adventure" (outdoor / nature / adventure spots aligned with user interests)
   - "cultural_historical" (heritage, museums, ancient temples/forts)
   - "family_friendly" (safe and engaging spots especially if children are travelling)
2. Every item must clearly explain 'why_recommended' tailored directly to the user's budget ({budget} {currency}), interests ({interests_str}), and food/stay preferences.
3. Ensure approximate realistic latitude and longitude coordinates for {destination}.
4. Provide estimated visit duration and realistic estimated cost in {currency}.

Return ONLY a valid JSON array of objects with this exact structure (no markdown, no preamble, no backticks outside JSON):
[
  {{
    "name": "Name of Place or Area",
    "category": "famous_place",
    "description": "Engaging 2-3 sentence overview of this place.",
    "why_recommended": "Specific reason why this fits the user's budget, interests, and group profile.",
    "estimated_visit_duration": "2-3 hours",
    "estimated_cost": 500.0,
    "currency": "{currency}",
    "latitude": 15.4989,
    "longitude": 73.8278,
    "best_time_to_visit": "Early morning or sunset",
    "distance_from_destination": "Central / 5 km from main hub",
    "distance_from_previous_location": null,
    "tags": ["beach", "scenic", "heritage"],
    "confidence": 0.95
  }}
]
"""

    @classmethod
    def _parse_gemini_json_response(cls, response_text: str) -> List[Dict[str, Any]]:
        """
        Parses raw text from Gemini into a list of dictionaries, handling code fences.
        """
        if not response_text or not response_text.strip():
            return []

        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "recommendations" in parsed and isinstance(parsed["recommendations"], list):
                return parsed["recommendations"]
        except Exception:
            # Fallback regex search for JSON array [...]
            match = re.search(r"\[.*\]", clean_text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass

        return []

    @classmethod
    def validate_and_deduplicate(
        cls, items: List[Dict[str, Any]], state: Optional[TravelState] = None
    ) -> List[Dict[str, Any]]:
        """
        Validates item schema, normalizes categories, sanitizes numbers/strings,
        and deduplicates by normalized name.
        """
        if not items:
            return []

        currency = (state.get("currency") if state else None) or "INR"
        seen_names = set()
        validated: List[Dict[str, Any]] = []

        for raw in items:
            if not isinstance(raw, dict):
                continue

            name = str(raw.get("name") or "").strip()
            if not name or len(name) < 2:
                continue

            # Deduplication by lowercase alphanumeric key
            norm_key = re.sub(r"[^a-z0-9]", "", name.lower())
            if not norm_key or norm_key in seen_names:
                continue
            seen_names.add(norm_key)

            # Category normalization
            raw_cat = str(raw.get("category") or "famous_place").strip().lower()
            category = CATEGORY_ALIASES.get(raw_cat, raw_cat)
            if category not in VALID_CATEGORIES:
                category = "famous_place"

            # Description & Reasoning
            description = str(raw.get("description") or f"Popular destination in {name}.").strip()
            why_recommended = str(raw.get("why_recommended") or "Matches your travel interests and preferences.").strip()

            # Duration
            duration = str(raw.get("estimated_visit_duration") or "1-2 hours").strip()

            # Cost validation
            cost: Optional[float] = None
            raw_cost = raw.get("estimated_cost")
            if raw_cost is not None:
                try:
                    cost_val = float(str(raw_cost).replace(",", "").strip())
                    if cost_val >= 0:
                        cost = cost_val
                except (ValueError, TypeError):
                    cost = None

            # Latitude & Longitude validation
            lat: Optional[float] = None
            lng: Optional[float] = None
            raw_lat = raw.get("latitude")
            raw_lng = raw.get("longitude")
            if raw_lat is not None:
                try:
                    lat_val = float(raw_lat)
                    if -90.0 <= lat_val <= 90.0:
                        lat = lat_val
                except (ValueError, TypeError):
                    lat = None
            if raw_lng is not None:
                try:
                    lng_val = float(raw_lng)
                    if -180.0 <= lng_val <= 180.0:
                        lng = lng_val
                except (ValueError, TypeError):
                    lng = None

            # Best time to visit & Distance
            best_time = raw.get("best_time_to_visit")
            best_time_str = str(best_time).strip() if best_time else "Morning or Late Afternoon"

            distance_dest = raw.get("distance_from_destination")
            distance_dest_str = str(distance_dest).strip() if distance_dest else "Central"

            distance_prev = raw.get("distance_from_previous_location")
            distance_prev_str = str(distance_prev).strip() if distance_prev else None

            # Tags
            raw_tags = raw.get("tags") or []
            tags: List[str] = []
            if isinstance(raw_tags, list):
                tags = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
            elif isinstance(raw_tags, str):
                tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]

            # Confidence score [0.0, 1.0]
            confidence = 0.90
            raw_conf = raw.get("confidence")
            if raw_conf is not None:
                try:
                    c_val = float(raw_conf)
                    confidence = max(0.0, min(1.0, c_val))
                except (ValueError, TypeError):
                    confidence = 0.90

            validated.append({
                "name": name,
                "category": category,
                "description": description,
                "why_recommended": why_recommended,
                "estimated_visit_duration": duration,
                "estimated_cost": cost,
                "currency": str(raw.get("currency") or currency),
                "latitude": lat,
                "longitude": lng,
                "best_time_to_visit": best_time_str,
                "distance_from_destination": distance_dest_str,
                "distance_from_previous_location": distance_prev_str,
                "tags": tags,
                "confidence": round(confidence, 2),
            })

        return validated

    @classmethod
    def _generate_fallback_recommendations(cls, state: TravelState) -> List[Dict[str, Any]]:
        """
        Deterministic, rich fallback generator for common travel destinations and generic hubs.
        Ensures uninterrupted platform functionality when external AI is offline.
        """
        dest = (state.get("destination") or "Destination").strip()
        currency = state.get("currency") or "INR"
        interests = [i.lower() for i in (state.get("interests") or [])]
        dest_lower = dest.lower()

        # Destination-specific curated seed sets
        if "goa" in dest_lower:
            return [
                {
                    "name": "Fort Aguada & Lighthouse",
                    "category": "famous_place",
                    "description": "A well-preserved seventeenth-century Portuguese fort standing on Sinquerim Beach overlooking the Arabian Sea.",
                    "why_recommended": "Iconic historic vantage point offering panoramic coastal views and rich colonial heritage.",
                    "estimated_visit_duration": "2 hours",
                    "estimated_cost": 100.0,
                    "currency": currency,
                    "latitude": 15.4926,
                    "longitude": 73.7736,
                    "best_time_to_visit": "Late afternoon for sunset",
                    "distance_from_destination": "15 km from Panaji",
                    "tags": ["heritage", "coastal", "photography", "views"],
                    "confidence": 0.96,
                },
                {
                    "name": "Palolem Beach & Butterfly Beach",
                    "category": "nature_adventure",
                    "description": "Scenic semi-circular white sand beach in South Goa famous for calm waters, kayaking, and dolphin boat rides.",
                    "why_recommended": "Perfect for relaxed relaxation, coastal nature, and swimming away from high-density commercial crowds.",
                    "estimated_visit_duration": "3-4 hours",
                    "estimated_cost": 300.0,
                    "currency": currency,
                    "latitude": 15.0100,
                    "longitude": 74.0232,
                    "best_time_to_visit": "Early morning or evening",
                    "distance_from_destination": "South Goa (35 km from Margao)",
                    "tags": ["beach", "nature", "swimming", "kayaking"],
                    "confidence": 0.94,
                },
                {
                    "name": "Fontainhas Latin Quarter",
                    "category": "cultural_historical",
                    "description": "Historic neighborhood in Panaji maintaining authentic Portuguese-style heritage homes, vibrant painted alleys, and quaint bakeries.",
                    "why_recommended": "Rich architectural walking trail ideal for photography, cultural immersion, and historic exploration.",
                    "estimated_visit_duration": "2 hours",
                    "estimated_cost": 0.0,
                    "currency": currency,
                    "latitude": 15.4989,
                    "longitude": 73.8322,
                    "best_time_to_visit": "Morning walking hours",
                    "distance_from_destination": "Central Panaji",
                    "tags": ["culture", "heritage", "architecture", "photography"],
                    "confidence": 0.92,
                },
                {
                    "name": "Divar Island",
                    "category": "hidden_gem",
                    "description": "Tranquil, scenic island on the Mandovi River accessible by ferry, featuring serene village roads, old churches, and lush paddy fields.",
                    "why_recommended": "An offbeat tranquil escape showcasing rural Goan countryside charm away from commercial beach traffic.",
                    "estimated_visit_duration": "Half day",
                    "estimated_cost": 150.0,
                    "currency": currency,
                    "latitude": 15.5186,
                    "longitude": 73.9103,
                    "best_time_to_visit": "Early morning",
                    "distance_from_destination": "10 km northeast of Panaji",
                    "tags": ["hidden gem", "nature", "cycling", "peaceful"],
                    "confidence": 0.88,
                },
                {
                    "name": "Dudhsagar Waterfalls Trek",
                    "category": "nearby_place",
                    "description": "Four-tiered majestic waterfall located on the Mandovi River inside Bhagwan Mahaveer Sanctuary near the Goa-Karnataka border.",
                    "why_recommended": "Exciting scenic day trip offering jeep safari rides through lush Western Ghats forests.",
                    "estimated_visit_duration": "Full day",
                    "estimated_cost": 1200.0,
                    "currency": currency,
                    "latitude": 15.3144,
                    "longitude": 74.3143,
                    "best_time_to_visit": "Morning departure",
                    "distance_from_destination": "60 km east of Panaji",
                    "tags": ["adventure", "waterfalls", "nature", "safari"],
                    "confidence": 0.91,
                },
                {
                    "name": "Anjuna & Vagator Cliffside Dining Hub",
                    "category": "food_dining",
                    "description": "Vibrant seaside culinary stretch featuring organic cafes, fresh coastal seafood, vegetarian bistro spots, and sunset views.",
                    "why_recommended": "Exceptional dining ambiance offering varied vegetarian and local culinary experiences with cliffside ocean sunsets.",
                    "estimated_visit_duration": "2 hours",
                    "estimated_cost": 800.0,
                    "currency": currency,
                    "latitude": 15.5843,
                    "longitude": 73.7438,
                    "best_time_to_visit": "Sunset & Dinner",
                    "distance_from_destination": "18 km from Panaji",
                    "tags": ["food", "dining", "sunset", "seaside"],
                    "confidence": 0.93,
                },
                {
                    "name": "Candolim & Calangute Coastal Belt",
                    "category": "stay_area",
                    "description": "Well-connected beachfront neighborhood with accessible resorts, boutique hotels, reliable transport, and family-friendly amenities.",
                    "why_recommended": "Strategic central hub for comfortable stay options with immediate access to beach activities and local transit.",
                    "estimated_visit_duration": "Overnight Stay",
                    "estimated_cost": 2500.0,
                    "currency": currency,
                    "latitude": 15.5170,
                    "longitude": 73.7667,
                    "best_time_to_visit": "All day / Base stay",
                    "distance_from_destination": "North Goa coastline",
                    "tags": ["stay", "hospitality", "hotels", "convenient"],
                    "confidence": 0.90,
                },
                {
                    "name": "Salim Ali Bird Sanctuary (Chorão Island)",
                    "category": "family_friendly",
                    "description": "Estuarine mangrove habitat along the Mandovi River with wooden canopy boardwalks and boat rides for birdwatching.",
                    "why_recommended": "Safe, educational, and serene nature experience ideal for families and nature enthusiasts.",
                    "estimated_visit_duration": "2-3 hours",
                    "estimated_cost": 200.0,
                    "currency": currency,
                    "latitude": 15.5080,
                    "longitude": 73.8680,
                    "best_time_to_visit": "Early morning (7:00 AM - 10:00 AM)",
                    "distance_from_destination": "5 km from Panaji",
                    "tags": ["family", "birds", "nature", "educational"],
                    "confidence": 0.89,
                },
            ]

        # Generic destination dynamic generator tailored to user parameters
        return [
            {
                "name": f"{dest} City Center & Historic Landmarks",
                "category": "famous_place",
                "description": f"The primary cultural and commercial core of {dest}, featuring prominent heritage architecture, pedestrian avenues, and local monuments.",
                "why_recommended": f"Essential first-stop landmark to understand the history and vibrant urban pulse of {dest}.",
                "estimated_visit_duration": "2-3 hours",
                "estimated_cost": 200.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Morning or Late Afternoon",
                "distance_from_destination": "Central",
                "tags": ["landmark", "culture", "city center"],
                "confidence": 0.92,
            },
            {
                "name": f"{dest} Old Town Artisan Quarter",
                "category": "hidden_gem",
                "description": f"A charming heritage neighborhood tucked away from busy highways with traditional craft workshops, local tea houses, and vintage architecture.",
                "why_recommended": "Offers an authentic, unhurried cultural immersion into local community crafts and daily life.",
                "estimated_visit_duration": "2 hours",
                "estimated_cost": 100.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Morning walking hours",
                "distance_from_destination": "3 km from city center",
                "tags": ["hidden gem", "artisan", "heritage", "walk"],
                "confidence": 0.88,
            },
            {
                "name": f"{dest} Panoramic Valley & Nature Lookout",
                "category": "nature_adventure",
                "description": f"Elevated scenic viewpoint providing sweeping vistas of the surrounding landscapes, hills, and waterways around {dest}.",
                "why_recommended": "Inspiring natural setting for walking trails, photography, and refreshing open-air scenery.",
                "estimated_visit_duration": "2 hours",
                "estimated_cost": 50.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Sunrise or Sunset",
                "distance_from_destination": "8 km from center",
                "tags": ["nature", "scenic", "viewpoint", "outdoors"],
                "confidence": 0.90,
            },
            {
                "name": f"{dest} Heritage Museum & Cultural Pavilion",
                "category": "cultural_historical",
                "description": f"Comprehensive cultural center displaying artifacts, historical narratives, and regional folklore unique to {dest}.",
                "why_recommended": "Deepens appreciation of local art and historical evolution in a comfortable, curated setting.",
                "estimated_visit_duration": "2-3 hours",
                "estimated_cost": 150.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Mid-day / Afternoon",
                "distance_from_destination": "Central cultural district",
                "tags": ["culture", "museum", "history", "learning"],
                "confidence": 0.89,
            },
            {
                "name": f"{dest} Culinary Street & Local Food Bazaar",
                "category": "food_dining",
                "description": f"Renowned culinary hub offering authentic regional delicacies, vegetarian options, and traditional specialty dishes.",
                "why_recommended": "Directly satisfies your dietary preferences with authentic, fresh local culinary specialties.",
                "estimated_visit_duration": "1.5 hours",
                "estimated_cost": 400.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Evening / Dinner time",
                "distance_from_destination": "City center marketplace",
                "tags": ["food", "dining", "local cuisine", "street food"],
                "confidence": 0.94,
            },
            {
                "name": f"{dest} Scenic Countryside Day-Trip",
                "category": "nearby_place",
                "description": f"Picturesque rural retreat located just outside {dest} featuring organic orchards, serene lakes, and countryside tranquility.",
                "why_recommended": "A refreshing excursion allowing you to experience the natural beauty surrounding the destination.",
                "estimated_visit_duration": "Half day to Full day",
                "estimated_cost": 600.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Morning departure",
                "distance_from_destination": "20-30 km outskirts",
                "tags": ["nearby", "day trip", "countryside", "nature"],
                "confidence": 0.87,
            },
            {
                "name": f"{dest} Central Hospitality District",
                "category": "stay_area",
                "description": f"Strategic neighborhood offering well-reviewed accommodation options, secure surroundings, and convenient transit links.",
                "why_recommended": f"Optimal base location aligning with your stay preferences and transit routes across {dest}.",
                "estimated_visit_duration": "Base Stay",
                "estimated_cost": 2000.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "All day / Base camp",
                "distance_from_destination": "Central",
                "tags": ["stay", "hotels", "neighborhood", "convenient"],
                "confidence": 0.91,
            },
            {
                "name": f"{dest} Botanical Gardens & Promenade",
                "category": "family_friendly",
                "description": f"Manicured green expanse with shaded walking paths, flowering gardens, and recreational areas.",
                "why_recommended": "Safe, serene, and relaxing space suitable for leisure walks and family gatherings.",
                "estimated_visit_duration": "1.5 - 2 hours",
                "estimated_cost": 50.0,
                "currency": currency,
                "latitude": None,
                "longitude": None,
                "best_time_to_visit": "Morning or Late Afternoon",
                "distance_from_destination": "4 km from center",
                "tags": ["family", "gardens", "park", "peaceful"],
                "confidence": 0.90,
            },
        ]
