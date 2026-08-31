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


# ==============================================================================
# Stage 5: Destination Intelligence Schemas
# ==============================================================================


class DestinationRecommendationItem(BaseModel):
    name: str = Field(..., description="Name of the place, area, or activity")
    category: str = Field(
        ...,
        description="Category: famous_place, hidden_gem, nearby_place, food_dining, stay_area, nature_adventure, cultural_historical, family_friendly",
    )
    description: str = Field(..., description="Rich summary of the recommendation")
    why_recommended: str = Field(..., description="Reasoning personalized to user interests/preferences")
    estimated_visit_duration: Optional[str] = Field(None, description="e.g. '2-3 hours', 'Half day'")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in local currency")
    currency: str = Field("INR", description="Currency code (e.g. INR, USD)")
    latitude: Optional[float] = Field(None, description="Latitude coordinate if available")
    longitude: Optional[float] = Field(None, description="Longitude coordinate if available")
    best_time_to_visit: Optional[str] = Field(None, description="e.g. 'Morning', 'Sunset', 'October to March'")
    distance_from_destination: Optional[str] = Field(None, description="e.g. 'Central', '15 km north'")
    distance_from_previous_location: Optional[str] = Field(None, description="Distance from origin or transit hub")
    tags: List[str] = Field(default_factory=list, description="Keywords / theme tags")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Recommendation confidence score between 0.0 and 1.0")


class DestinationStartRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")


class DestinationResponseData(BaseModel):
    trip_id: str
    destination: str
    recommendations: List[DestinationRecommendationItem]
    categories_summary: Optional[Dict[str, int]] = None
    total_recommendations: int


class DestinationResponse(BaseModel):
    success: bool
    data: DestinationResponseData


# ==============================================================================
# Stage 6: Weather Intelligence Schemas
# ==============================================================================


class CurrentWeather(BaseModel):
    location_name: str = Field(..., description="Name of the weather observation location")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    temperature: float = Field(..., description="Current temperature in Celsius")
    feels_like: float = Field(..., description="Perceived temperature in Celsius")
    temperature_min: Optional[float] = Field(None, description="Minimum temperature in Celsius")
    temperature_max: Optional[float] = Field(None, description="Maximum temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: Optional[int] = Field(None, description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., ge=0.0, description="Wind speed in meters/second")
    wind_direction: Optional[int] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    precipitation: float = Field(0.0, ge=0.0, description="Recent precipitation volume in mm")
    rain_probability: float = Field(0.0, ge=0.0, le=1.0, description="Estimated rain probability between 0.0 and 1.0")
    weather_condition: str = Field(..., description="Main weather condition (e.g. Clear, Clouds, Rain)")
    weather_description: str = Field(..., description="Detailed condition (e.g. Scattered Clouds, Light Rain)")
    visibility: int = Field(10000, description="Visibility in meters (max 10000)")
    sunrise: Optional[str] = Field(None, description="Sunrise time string")
    sunset: Optional[str] = Field(None, description="Sunset time string")
    observed_at: str = Field(..., description="ISO 8601 timestamp of observation")
    source: str = Field("OpenWeatherMap", description="Data provider attribution")


class ForecastItem(BaseModel):
    date: str = Field(..., description="Forecast date (YYYY-MM-DD)")
    time: str = Field(..., description="Forecast time (HH:MM)")
    temperature: float = Field(..., description="Forecasted temperature in Celsius")
    feels_like: float = Field(..., description="Forecasted perceived temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Forecasted humidity percentage")
    precipitation: float = Field(0.0, description="Precipitation in mm")
    rain_probability: float = Field(0.0, ge=0.0, le=1.0, description="Rain probability (0.0 to 1.0)")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    weather_condition: str = Field(..., description="Weather category")
    weather_description: str = Field(..., description="Detailed description")


class WeatherInsight(BaseModel):
    type: str = Field(..., description="Insight type: rain_alert, temperature_comfort, wind_warning, visibility_warning, optimal_period, precaution")
    title: str = Field(..., description="Short headline for the insight")
    message: str = Field(..., description="Actionable recommendation for traveler itinerary planning")
    severity: str = Field("info", description="Severity level: info, moderate, alert")


class PlaceWeatherItem(BaseModel):
    place_name: str
    category: str
    latitude: float
    longitude: float
    temperature: float
    weather_condition: str
    weather_description: str
    rain_probability: float


class WeatherStartRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")


class WeatherResponseData(BaseModel):
    trip_id: str
    destination: str
    current_weather: Optional[CurrentWeather] = None
    forecast: List[ForecastItem] = Field(default_factory=list)
    insights: List[WeatherInsight] = Field(default_factory=list)
    place_weathers: List[PlaceWeatherItem] = Field(default_factory=list)
    weather_status: str = Field(..., description="'ready', 'unavailable', or 'pending'")
    weather_errors: List[str] = Field(default_factory=list)


class WeatherResponse(BaseModel):
    success: bool
    data: WeatherResponseData


