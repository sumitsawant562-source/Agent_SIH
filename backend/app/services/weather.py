"""
Weather Service for fetching live meteorological data and forecasts.

Integrates with OpenWeatherMap API with robust error handling, timeouts,
coordinate validation, and structured data normalization.
"""

import json
import logging
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherServiceError(Exception):
    """Custom exception raised for weather service failures."""
    pass


class WeatherService:
    """Service to interact with OpenWeatherMap API."""

    @staticmethod
    def get_api_key() -> str:
        """Returns the configured OpenWeatherMap API key."""
        return settings.OPENWEATHER_API_KEY.strip()

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if OpenWeatherMap API key is provided."""
        return bool(cls.get_api_key())

    @classmethod
    def validate_coordinates(cls, lat: Any, lon: Any) -> Tuple[float, float]:
        """
        Validates and converts latitude and longitude into valid float coordinates.
        Raises ValueError if invalid or out of geographic bounds.
        """
        if lat is None or lon is None:
            raise ValueError("Latitude and longitude must not be None")
        
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid coordinate format: {e}")

        if not (-90.0 <= lat_f <= 90.0):
            raise ValueError(f"Latitude out of bounds [-90, 90]: {lat_f}")
        if not (-180.0 <= lon_f <= 180.0):
            raise ValueError(f"Longitude out of bounds [-180, 180]: {lon_f}")

        return lat_f, lon_f

    @classmethod
    def _make_api_request(cls, url: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Executes an HTTP GET request to OpenWeatherMap API.
        Handles status codes, network timeouts, and JSON decoding safely.
        """
        api_key = cls.get_api_key()
        if not api_key:
            raise WeatherServiceError("OPENWEATHER_API_KEY is not configured on the server")

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "TravelIntelligencePlatform/1.0",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8")
                try:
                    data = json.loads(raw_body)
                except Exception as json_err:
                    raise WeatherServiceError(f"Malformed JSON response from weather API: {json_err}")
                return data
        except urllib.error.HTTPError as http_err:
            status = http_err.code
            err_body = http_err.read().decode("utf-8", errors="replace")
            try:
                parsed_err = json.loads(err_body)
                err_msg = parsed_err.get("message") or err_body
            except Exception:
                err_msg = err_body

            if status == 401:
                raise WeatherServiceError("Invalid OpenWeatherMap API key or unauthorized")
            elif status == 404:
                raise WeatherServiceError(f"Weather location not found: {err_msg}")
            elif status == 429:
                raise WeatherServiceError("OpenWeatherMap API rate limit exceeded")
            elif 500 <= status <= 599:
                raise WeatherServiceError(f"OpenWeatherMap server error ({status}): {err_msg}")
            else:
                raise WeatherServiceError(f"Weather API error ({status}): {err_msg}")
        except urllib.error.URLError as url_err:
            if "timed out" in str(url_err).lower():
                raise WeatherServiceError("Weather API request timed out")
            raise WeatherServiceError(f"Failed to connect to weather API: {url_err.reason}")
        except Exception as e:
            if isinstance(e, WeatherServiceError):
                raise
            raise WeatherServiceError(f"Unexpected error calling weather API: {str(e)}")

    @classmethod
    def geocode_location(cls, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Resolves a location or city name to (latitude, longitude) coordinates.
        Returns None if resolution fails or location is empty.
        """
        if not location_name or not location_name.strip():
            return None

        clean_name = location_name.strip()
        encoded_query = urllib.parse.quote(clean_name)
        api_key = cls.get_api_key()
        if not api_key:
            logger.warning("OPENWEATHER_API_KEY not configured, cannot geocode location")
            return None

        url = f"{settings.OPENWEATHER_GEO_URL}/direct?q={encoded_query}&limit=1&appid={api_key}"
        try:
            results = cls._make_api_request(url)
            if isinstance(results, list) and len(results) > 0:
                item = results[0]
                lat = item.get("lat")
                lon = item.get("lon")
                if lat is not None and lon is not None:
                    return cls.validate_coordinates(lat, lon)
        except Exception as e:
            logger.warning(f"Geocoding failed for '{location_name}': {e}")
            return None
        return None

    @classmethod
    def get_current_weather(
        cls,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetches current weather for given coordinates.
        Returns normalized dictionary adhering to CurrentWeather schema.
        """
        valid_lat, valid_lon = cls.validate_coordinates(lat, lon)
        api_key = cls.get_api_key()
        url = (
            f"{settings.OPENWEATHER_BASE_URL}/weather"
            f"?lat={valid_lat}&lon={valid_lon}&appid={api_key}&units=metric"
        )

        data = cls._make_api_request(url)
        
        main = data.get("main") or {}
        weather_list = data.get("weather") or [{}]
        primary_weather = weather_list[0] if len(weather_list) > 0 else {}
        wind = data.get("wind") or {}
        sys_data = data.get("sys") or {}
        rain = data.get("rain") or {}

        # Precipitation in last 1 hour or 3 hours (mm)
        precip = 0.0
        if isinstance(rain, dict):
            precip = float(rain.get("1h") or rain.get("3h") or 0.0)

        # Calculate rough rain probability from weather ID if not explicit
        # Weather ID 2xx = Thunderstorm, 3xx = Drizzle, 5xx = Rain
        w_id = primary_weather.get("id") or 800
        rain_prob = 0.0
        if 200 <= w_id < 300:
            rain_prob = 0.85
        elif 300 <= w_id < 400:
            rain_prob = 0.60
        elif 500 <= w_id < 600:
            rain_prob = 0.90
        elif w_id == 804:  # Overcast clouds
            rain_prob = 0.30

        # Formulate timestamp
        dt_val = data.get("dt")
        if dt_val:
            observed_at = datetime.fromtimestamp(dt_val, tz=timezone.utc).isoformat()
        else:
            observed_at = datetime.now(timezone.utc).isoformat()

        sunrise_iso = None
        if sys_data.get("sunrise"):
            sunrise_iso = datetime.fromtimestamp(sys_data["sunrise"], tz=timezone.utc).strftime("%H:%M UTC")

        sunset_iso = None
        if sys_data.get("sunset"):
            sunset_iso = datetime.fromtimestamp(sys_data["sunset"], tz=timezone.utc).strftime("%H:%M UTC")

        return {
            "location_name": location_name or data.get("name") or "Unknown Location",
            "latitude": round(valid_lat, 4),
            "longitude": round(valid_lon, 4),
            "temperature": round(float(main.get("temp", 0.0)), 1),
            "feels_like": round(float(main.get("feels_like", main.get("temp", 0.0))), 1),
            "temperature_min": round(float(main.get("temp_min", main.get("temp", 0.0))), 1) if main.get("temp_min") is not None else None,
            "temperature_max": round(float(main.get("temp_max", main.get("temp", 0.0))), 1) if main.get("temp_max") is not None else None,
            "humidity": int(main.get("humidity", 0)),
            "pressure": int(main.get("pressure", 1013)) if main.get("pressure") else None,
            "wind_speed": round(float(wind.get("speed", 0.0)), 1),
            "wind_direction": int(wind.get("deg")) if wind.get("deg") is not None else None,
            "precipitation": round(precip, 2),
            "rain_probability": round(rain_prob, 2),
            "weather_condition": primary_weather.get("main") or "Clear",
            "weather_description": (primary_weather.get("description") or "clear sky").title(),
            "visibility": int(data.get("visibility", 10000)) if data.get("visibility") is not None else 10000,
            "sunrise": sunrise_iso,
            "sunset": sunset_iso,
            "observed_at": observed_at,
            "source": "OpenWeatherMap",
        }

    @classmethod
    def get_forecast(
        cls,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
        limit: int = 16,
    ) -> List[Dict[str, Any]]:
        """
        Fetches 5-day / 3-hour forecast for given coordinates.
        Returns normalized list of ForecastItem dictionaries.
        """
        valid_lat, valid_lon = cls.validate_coordinates(lat, lon)
        api_key = cls.get_api_key()
        url = (
            f"{settings.OPENWEATHER_BASE_URL}/forecast"
            f"?lat={valid_lat}&lon={valid_lon}&appid={api_key}&units=metric"
        )

        data = cls._make_api_request(url)
        raw_list = data.get("list") or []

        forecast_items: List[Dict[str, Any]] = []

        for item in raw_list[:limit]:
            dt_txt = item.get("dt_txt")  # Format: "2026-09-01 12:00:00"
            date_str = ""
            time_str = ""
            if dt_txt:
                parts = dt_txt.split(" ")
                date_str = parts[0] if len(parts) > 0 else ""
                time_str = parts[1][:5] if len(parts) > 1 else ""  # "12:00"
            else:
                dt_val = item.get("dt")
                if dt_val:
                    dt_obj = datetime.fromtimestamp(dt_val, tz=timezone.utc)
                    date_str = dt_obj.strftime("%Y-%m-%d")
                    time_str = dt_obj.strftime("%H:%M")

            main = item.get("main") or {}
            weather_list = item.get("weather") or [{}]
            w_item = weather_list[0] if len(weather_list) > 0 else {}
            wind = item.get("wind") or {}
            rain = item.get("rain") or {}

            pop = float(item.get("pop", 0.0))  # Probability of precipitation (0.0 to 1.0)
            precip = 0.0
            if isinstance(rain, dict):
                precip = float(rain.get("3h") or 0.0)

            forecast_items.append({
                "date": date_str,
                "time": time_str,
                "temperature": round(float(main.get("temp", 0.0)), 1),
                "feels_like": round(float(main.get("feels_like", main.get("temp", 0.0))), 1),
                "humidity": int(main.get("humidity", 0)),
                "precipitation": round(precip, 2),
                "rain_probability": round(pop, 2),
                "wind_speed": round(float(wind.get("speed", 0.0)), 1),
                "weather_condition": w_item.get("main") or "Clear",
                "weather_description": (w_item.get("description") or "clear sky").title(),
            })

        return forecast_items
