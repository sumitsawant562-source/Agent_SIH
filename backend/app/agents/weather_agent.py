"""
Weather Intelligence Agent (Stage 6).

Fetches live meteorological data and forecasts from OpenWeatherMap,
analyzes atmospheric parameters, generates deterministic itinerary recommendations,
and updates TravelState without inventing artificial weather metrics.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.graph.state import TravelState
from app.services.gemini import get_gemini_client
from app.services.weather import WeatherService, WeatherServiceError

logger = logging.getLogger(__name__)


KNOWN_DESTINATION_COORDINATES: Dict[str, Tuple[float, float]] = {
    "goa": (15.4989, 73.8278),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "jaipur": (26.9124, 75.7873),
    "kerala": (9.9312, 76.2673),
    "kochi": (9.9312, 76.2673),
    "manali": (32.2432, 77.1892),
    "shimla": (31.1048, 77.1734),
    "ooty": (11.4102, 76.6950),
    "agra": (27.1767, 78.0081),
    "varanasi": (25.3176, 82.9739),
    "paris": (48.8566, 2.3522),
    "london": (51.5074, -0.1278),
    "tokyo": (35.6762, 139.6503),
    "new york": (40.7128, -74.0060),
    "dubai": (25.2048, 55.2708),
    "singapore": (1.3521, 103.8198),
    "bali": (-8.4095, 115.1889),
}


class WeatherAgent:
    """Agent responsible for meteorological analysis and itinerary insight generation."""

    @classmethod
    def resolve_destination_coordinates(cls, state: TravelState) -> Tuple[Optional[float], Optional[float]]:
        """
        Determines latitude and longitude for the trip destination.
        Priority:
        1. Explicit state coordinates (destination_latitude, destination_longitude)
        2. Geocoding resolution for destination name
        3. Known destination coordinate database
        4. Coordinates from top destination recommendations if present
        """
        lat = state.get("destination_latitude")
        lon = state.get("destination_longitude")

        if lat is not None and lon is not None:
            try:
                return WeatherService.validate_coordinates(lat, lon)
            except ValueError:
                pass

        destination_name = state.get("destination")
        if destination_name:
            clean_name = destination_name.strip().lower()
            coords = WeatherService.geocode_location(destination_name)
            if coords:
                return coords

            # Check known coordinate catalog
            for city_key, city_coords in KNOWN_DESTINATION_COORDINATES.items():
                if city_key in clean_name or clean_name in city_key:
                    return city_coords

        # Check recommendations for coordinates
        recs = state.get("destination_recommendations") or []
        for r in recs:
            r_lat = r.get("latitude")
            r_lon = r.get("longitude")
            if r_lat is not None and r_lon is not None:
                try:
                    return WeatherService.validate_coordinates(r_lat, r_lon)
                except ValueError:
                    continue

        return None, None

    @classmethod
    def generate_weather_insights(
        cls,
        current_weather: Optional[Dict[str, Any]],
        forecast: List[Dict[str, Any]],
        destination: str,
    ) -> List[Dict[str, Any]]:
        """
        Computes deterministic, actionable travel insights derived strictly
        from real weather metrics.
        """
        insights: List[Dict[str, Any]] = []

        if not current_weather:
            return insights

        temp = current_weather.get("temperature", 25.0)
        feels_like = current_weather.get("feels_like", temp)
        condition = (current_weather.get("weather_condition") or "").lower()
        rain_prob = current_weather.get("rain_probability", 0.0)
        wind_speed = current_weather.get("wind_speed", 0.0)
        visibility = current_weather.get("visibility", 10000)
        humidity = current_weather.get("humidity", 50)

        # 1. Rain & Precipitation Assessment
        forecast_rain_times = [
            f"{f.get('date')} {f.get('time')}"
            for f in forecast
            if (f.get("rain_probability", 0.0) >= 0.5 or "rain" in (f.get("weather_condition") or "").lower())
        ]

        if rain_prob >= 0.5 or "rain" in condition or "thunderstorm" in condition or "drizzle" in condition:
            insights.append({
                "type": "rain_alert",
                "title": "Precipitation Warning",
                "message": (
                    f"Rain or wet conditions currently observed in {destination}. "
                    "Prioritize indoor cultural sites, museums, and covered dining, and carry waterproof gear."
                ),
                "severity": "alert",
            })
        elif forecast_rain_times:
            sample_time = forecast_rain_times[0]
            insights.append({
                "type": "rain_alert",
                "title": "Upcoming Rain in Forecast",
                "message": (
                    f"Rain is forecasted around {sample_time}. "
                    "Consider scheduling open-air activities in clear intervals and keeping flexible backup plans."
                ),
                "severity": "moderate",
            })
        else:
            insights.append({
                "type": "optimal_period",
                "title": "Dry & Clear Outlook",
                "message": (
                    f"Low chance of precipitation in {destination}. "
                    "Excellent conditions for beach walks, nature excursions, and open-air sightseeing."
                ),
                "severity": "info",
            })

        # 2. Temperature & Comfort Evaluation
        if temp >= 33.0 or feels_like >= 36.0:
            insights.append({
                "type": "temperature_comfort",
                "title": "High Heat Alert",
                "message": (
                    f"High temperature ({temp}°C, feels like {feels_like}°C) with {humidity}% humidity. "
                    "Schedule intensive outdoor exploration during early mornings or evenings. Stay well-hydrated."
                ),
                "severity": "moderate",
            })
        elif temp <= 14.0:
            insights.append({
                "type": "temperature_comfort",
                "title": "Cool Climate Precaution",
                "message": (
                    f"Cool weather ({temp}°C). Pack warm layered clothing, especially for evening outings."
                ),
                "severity": "info",
            })
        else:
            insights.append({
                "type": "temperature_comfort",
                "title": "Pleasant Exploration Climate",
                "message": (
                    f"Pleasant ambient temperature ({temp}°C). "
                    "Comfortable for full-day walking tours and outdoor transit."
                ),
                "severity": "info",
            })

        # 3. Wind & Marine / Elevated Caution
        if wind_speed >= 6.5:
            insights.append({
                "type": "wind_warning",
                "title": "Breezy / Wind Advisory",
                "message": (
                    f"Moderate to high wind speeds ({wind_speed} m/s). "
                    "Exercise caution for open-water boat transfers, ferry routes, and exposed viewpoints."
                ),
                "severity": "moderate",
            })

        # 4. Visibility & Transit
        if visibility < 5000:
            insights.append({
                "type": "visibility_warning",
                "title": "Low Visibility Advisory",
                "message": (
                    f"Reduced visibility ({visibility}m). "
                    "Allow extra travel buffer time when driving or booking early transit connections."
                ),
                "severity": "moderate",
            })

        return insights

    @classmethod
    def fetch_places_weather(
        cls,
        recommendations: List[Dict[str, Any]],
        limit: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Fetches current weather for top recommendations that have valid coordinates.
        Restricts API requests to prevent excessive overhead.
        """
        results: List[Dict[str, Any]] = []
        valid_items = [r for r in recommendations if r.get("latitude") and r.get("longitude")]

        for rec in valid_items[:limit]:
            lat = rec.get("latitude")
            lon = rec.get("longitude")
            name = rec.get("name", "Recommended Spot")
            category = rec.get("category", "place")
            try:
                w = WeatherService.get_current_weather(lat, lon, location_name=name)
                results.append({
                    "place_name": name,
                    "category": category,
                    "latitude": w["latitude"],
                    "longitude": w["longitude"],
                    "temperature": w["temperature"],
                    "weather_condition": w["weather_condition"],
                    "weather_description": w["weather_description"],
                    "rain_probability": w["rain_probability"],
                })
            except Exception as e:
                logger.warning(f"Could not fetch weather for place '{name}': {e}")
                continue

        return results

    @classmethod
    def analyze_weather(cls, state: TravelState) -> Dict[str, Any]:
        """
        Main execution step for WeatherAgent.
        Fetches live weather, forecasts, place weathers, and builds insights.
        """
        destination = state.get("destination")
        if not destination or not destination.strip():
            return {
                "weather_current": None,
                "weather_forecast": [],
                "weather_insights": [],
                "weather_status": "unavailable",
                "weather_errors": ["No destination specified in travel state."],
            }

        lat, lon = cls.resolve_destination_coordinates(state)
        if lat is None or lon is None:
            return {
                "weather_current": None,
                "weather_forecast": [],
                "weather_insights": [],
                "weather_status": "unavailable",
                "weather_errors": [f"Could not resolve geographical coordinates for destination '{destination}'."],
            }

        try:
            current = WeatherService.get_current_weather(lat, lon, location_name=destination)
            forecast = WeatherService.get_forecast(lat, lon, location_name=destination)
            insights = cls.generate_weather_insights(current, forecast, destination)

            # Optional: fetch weather for top places
            recs = state.get("destination_recommendations") or []
            place_weathers = cls.fetch_places_weather(recs, limit=3)

            return {
                "weather_current": current,
                "weather_forecast": forecast,
                "weather_insights": insights,
                "place_weathers": place_weathers,
                "weather_status": "ready",
                "weather_errors": [],
            }
        except WeatherServiceError as wse:
            logger.error(f"WeatherService error for '{destination}': {wse}")
            return {
                "weather_current": None,
                "weather_forecast": [],
                "weather_insights": [],
                "weather_status": "unavailable",
                "weather_errors": [str(wse)],
            }
        except Exception as e:
            logger.exception(f"Unexpected failure in WeatherAgent for '{destination}': {e}")
            return {
                "weather_current": None,
                "weather_forecast": [],
                "weather_insights": [],
                "weather_status": "unavailable",
                "weather_errors": [f"Weather analysis failed: {str(e)}"],
            }
