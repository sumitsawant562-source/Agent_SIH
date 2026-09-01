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


# ==============================================================================
# Stage 7: Itinerary Planning Schemas
# ==============================================================================


class ItineraryActivityItem(BaseModel):
    time_slot: str = Field(..., description="Slot: 'morning', 'afternoon', 'evening', or 'night'")
    start_time: str = Field(..., description="Estimated start time in HH:MM format (e.g. '09:00')")
    end_time: str = Field(..., description="Estimated end time in HH:MM format (e.g. '11:30')")
    place_name: str = Field(..., description="Name of the visited place, attraction, or area")
    category: str = Field("famous_place", description="Category tag")
    description: str = Field(..., description="Details and context for the activity")
    what_to_do: Optional[str] = Field(None, description="Actionable highlights and specific things to do at this location")
    why_recommended: Optional[str] = Field(None, description="Personalized reasoning for why this place is recommended")
    estimated_cost: float = Field(0.0, ge=0.0, description="Estimated activity or entry cost")
    currency: str = Field("INR", description="Currency code (e.g. INR, USD)")
    visit_duration_minutes: int = Field(120, ge=15, description="Estimated duration in minutes")
    visit_duration: Optional[str] = Field(None, description="Human readable duration (e.g. '2.5 hours')")
    travel_time_from_previous: Optional[str] = Field(None, description="Estimated transit duration from prior location (e.g. '15 mins via taxi')")
    transport_mode: Optional[str] = Field(None, description="Recommended mode of transit (e.g. 'taxi', 'walking', 'metro', 'auto')")
    practical_tips: Optional[str] = Field(None, description="Practical travel advice, what to carry, booking notes, or best photo spots")
    is_indoor: Optional[bool] = Field(None, description="Whether activity is primarily indoor (True) or outdoor (False)")
    weather_suitability: Optional[str] = Field(None, description="Weather compatibility note (e.g. 'Optimal for clear morning')")
    notes: Optional[str] = Field(None, description="Helpful tips, weather precautions, or travel suggestions")


class ItineraryFoodRecommendation(BaseModel):
    name: str = Field(..., description="Name of recommended restaurant, cafe, or dining area")
    meal: str = Field(..., description="Meal type: 'breakfast', 'lunch', 'dinner', or 'snack'")
    restaurant_type: Optional[str] = Field(None, description="Restaurant style (e.g. 'Heritage Cafe', 'Fine Dining', 'Street Food')")
    cuisine_type: Optional[str] = Field(None, description="Cuisine description (e.g. 'Goan Vegetarian', 'Seafood Cafe')")
    estimated_cost: float = Field(0.0, ge=0.0, description="Estimated cost per person or meal")
    currency: str = Field("INR", description="Currency code")
    suggested_time: Optional[str] = Field(None, description="Suggested dining time window (e.g. '13:00 - 14:15')")
    local_specialty: Optional[str] = Field(None, description="Local specialty or signature dish recommendation")
    dietary_fit: Optional[str] = Field(None, description="Dietary fit (e.g. 'Pure Vegetarian', 'Vegan options')")


class ItineraryDay(BaseModel):
    day_number: int = Field(..., ge=1, description="Sequential day number (1, 2, ...)")
    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    theme: str = Field(..., description="Thematic headline for the day (e.g. 'Heritage Walk & Sunset Beach')")
    summary: Optional[str] = Field(None, description="Narrative summary of the day's highlights and flow")
    weather_summary: Optional[str] = Field(None, description="Weather forecast summary for this day")
    weather_note: Optional[str] = Field(None, description="Specific weather caution or optimal window note")
    morning: Optional[Dict[str, Any]] = Field(None, description="Morning plan container with activities")
    afternoon: Optional[Dict[str, Any]] = Field(None, description="Afternoon plan container with activities")
    evening: Optional[Dict[str, Any]] = Field(None, description="Evening plan container with activities")
    night: Optional[Dict[str, Any]] = Field(None, description="Night plan container with activities")
    meals: Optional[Dict[str, Any]] = Field(None, description="Structured meals dictionary (breakfast, lunch, snack, dinner)")
    activities: List[ItineraryActivityItem] = Field(default_factory=list, description="All scheduled activities for the day")
    food_recommendations: List[ItineraryFoodRecommendation] = Field(default_factory=list, description="Recommended dining list")
    daily_budget: Optional[Dict[str, float]] = Field(None, description="Daily budget breakdown (food, transport, activities, miscellaneous, total)")
    travel_tips: List[str] = Field(default_factory=list, description="Day-specific practical logistics & transit tips")
    estimated_day_cost: float = Field(0.0, ge=0.0, description="Sum of estimated activity and food costs for the day")
    notes: Optional[str] = Field(None, description="Day-level transit, packing, or pacing advice")


class ItineraryData(BaseModel):
    trip_id: str
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: int = Field(..., ge=1)
    total_estimated_cost: float = Field(0.0, ge=0.0)
    cost_per_traveler: Optional[float] = Field(None, ge=0.0, description="Estimated cost per traveler")
    budget: Optional[float] = None
    currency: str = "INR"
    budget_status: str = Field("within_budget", description="'within_budget', 'near_budget', 'exceeds_budget', or 'unspecified'")
    budget_warning: Optional[str] = None
    weather_advisory: Optional[str] = None
    trip_summary: Optional[Dict[str, Any]] = Field(None, description="Executive trip summary")
    overall_tips: List[str] = Field(default_factory=list, description="Holistic travel & safety advice")
    packing_suggestions: List[str] = Field(default_factory=list, description="Tailored packing suggestions")
    days: List[ItineraryDay] = Field(default_factory=list)


class ItineraryStartRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")


class ItineraryResponseData(BaseModel):
    trip_id: str
    destination: str
    itinerary: Optional[ItineraryData] = None
    itinerary_status: str = Field("ready", description="'ready', 'unavailable', or 'pending'")
    itinerary_errors: List[str] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    success: bool
    data: ItineraryResponseData


# ==============================================================================
# Stage 8: Live Route & GPS Schemas
# ==============================================================================


class CoordinatePoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class RouteCalculateRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")
    origin: CoordinatePoint = Field(..., description="Starting location coordinate (e.g. current GPS position)")
    destination: CoordinatePoint = Field(..., description="Target destination coordinate")
    transport_mode: str = Field("driving", description="Transport mode: 'driving', 'walking', or 'cycling'")


class RouteData(BaseModel):
    trip_id: str
    origin: CoordinatePoint
    destination: CoordinatePoint
    distance_km: float = Field(0.0, ge=0.0, description="Calculated route distance in kilometers")
    duration_minutes: float = Field(0.0, ge=0.0, description="Estimated transit duration in minutes")
    transport_mode: str = Field("driving", description="'driving', 'walking', or 'cycling'")
    geometry: Optional[Any] = Field(None, description="Polyline coordinates [[lat, lon], ...] for map rendering")
    source: Optional[str] = Field("osrm", description="Routing data provider source")
    route_status: str = Field("ready", description="'ready', 'unavailable', or 'error'")
    route_error: Optional[str] = Field(None, description="Error or failure message if routing failed")


class RouteResponse(BaseModel):
    success: bool
    data: RouteData


# ==============================================================================
# Stage 9: Crowd Monitoring & Overcrowding Schemas
# ==============================================================================


class AlternativePlaceItem(BaseModel):
    name: str = Field(..., description="Alternative place or venue name")
    category: str = Field("nearby_place", description="Category of alternative place")
    description: Optional[str] = Field(None, description="Place description")
    why_recommended: str = Field(..., description="Reason for alternative recommendation")
    estimated_visit_duration: Optional[str] = Field("1-2 hours", description="Estimated visit duration")
    estimated_cost: Optional[float] = Field(0.0, description="Estimated entry or visit cost")
    currency: str = Field("INR", description="Currency code")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    distance_km: Optional[float] = Field(None, description="Distance from reference location in kilometers")
    weather_suitability: Optional[str] = Field("Suitable", description="Weather compatibility note")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Confidence score")


class CrowdStartRequest(BaseModel):
    trip_id: str = Field(..., description="Unique UUID of the trip")
    destination: Optional[str] = Field(None, description="Name of the place or attraction being monitored")
    people_count: int = Field(..., ge=0, description="Observed/detected number of people at the location")
    capacity: Optional[int] = Field(100, gt=0, description="Venue or area safe capacity limit")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Destination latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Destination longitude coordinate")
    confidence: Optional[float] = Field(0.95, ge=0.0, le=1.0, description="Detection confidence score")
    source: Optional[str] = Field("simulated_detector", description="Detection source (e.g. simulated, camera, cv_model)")


class CrowdData(BaseModel):
    trip_id: str
    destination: str
    people_count: int = Field(..., ge=0, description="People detected")
    capacity: int = Field(100, gt=0, description="Total capacity")
    crowd_percentage: float = Field(..., ge=0.0, description="Percentage of capacity occupied")
    crowd_level: str = Field(..., description="'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH', or 'OVER_CROWDED'")
    crowd_score: float = Field(..., ge=0.0, description="Normalized crowd metric score")
    crowd_status: str = Field("Normal", description="'Normal', 'Busy', or 'Overcrowded'")
    is_overcrowded: bool = Field(False, description="True if crowd level warrants alternatives")
    crowd_confidence: float = Field(0.95, ge=0.0, le=1.0, description="Confidence in crowd estimation")
    recommendation: str = Field(..., description="Deterministic action recommendation")
    ai_explanation: Optional[str] = Field(None, description="Personalized AI explanation of crowd status")
    alternative_places: List[AlternativePlaceItem] = Field(default_factory=list, description="Recommended alternative destinations")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = "simulated_detector"
    timestamp: Optional[str] = None


class CrowdResponse(BaseModel):
    success: bool
    data: CrowdData





