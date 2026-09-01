"""
Routing Service (Stage 8).

Integrates with OpenRouteService and open-source OpenStreetMap OSRM routing engines
to calculate real distances, durations, and polyline geometries for travel navigation.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_TRANSPORT_MODES = {
    "driving": {
        "ors_profile": "driving-car",
        "osrm_profile": "driving",
    },
    "walking": {
        "ors_profile": "foot-walking",
        "osrm_profile": "walking",
    },
    "cycling": {
        "ors_profile": "cycling-regular",
        "osrm_profile": "cycling",
    },
}


class RoutingServiceError(Exception):
    """Custom exception raised for routing failures or invalid queries."""
    pass


class RoutingService:
    """Core routing service with OpenRouteService and OSRM integration."""

    @classmethod
    def validate_coordinates(cls, latitude: Any, longitude: Any) -> Tuple[float, float]:
        """
        Validates latitude and longitude values.
        Latitude must be in [-90.0, 90.0] and Longitude in [-180.0, 180.0].
        """
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError):
            raise RoutingServiceError(f"Invalid coordinate format: lat={latitude}, lon={longitude}")

        if not (-90.0 <= lat <= 90.0):
            raise RoutingServiceError(f"Latitude out of bounds [-90, 90]: {lat}")
        if not (-180.0 <= lon <= 180.0):
            raise RoutingServiceError(f"Longitude out of bounds [-180, 180]: {lon}")

        return lat, lon

    @classmethod
    def validate_transport_mode(cls, mode: Optional[str]) -> str:
        """
        Normalizes and validates travel mode.
        Supported modes: 'driving', 'walking', 'cycling'.
        """
        clean_mode = (mode or "driving").strip().lower()
        if clean_mode not in SUPPORTED_TRANSPORT_MODES:
            raise RoutingServiceError(
                f"Unsupported transport mode '{mode}'. Supported modes are: {list(SUPPORTED_TRANSPORT_MODES.keys())}"
            )
        return clean_mode

    @classmethod
    def calculate_route_ors(
        cls,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        transport_mode: str,
        timeout: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Queries OpenRouteService API if API key is configured.
        """
        api_key = settings.OPENROUTESERVICE_API_KEY
        if not api_key:
            return None

        profile = SUPPORTED_TRANSPORT_MODES[transport_mode]["ors_profile"]
        url = f"{settings.OPENROUTESERVICE_BASE_URL.rstrip('/')}/directions/{profile}/geojson"

        payload = {
            "coordinates": [
                [origin_lon, origin_lat],
                [dest_lon, dest_lat],
            ]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.getcode() == 200:
                    body = json.loads(response.read().decode("utf-8"))
                    features = body.get("features", [])
                    if features:
                        feat = features[0]
                        props = feat.get("properties", {}).get("summary", {})
                        dist_meters = float(props.get("distance", 0.0))
                        dur_seconds = float(props.get("duration", 0.0))
                        coords = feat.get("geometry", {}).get("coordinates", [])

                        # Convert coordinates from [lon, lat] to [lat, lon] for Leaflet
                        lat_lon_geometry = [[c[1], c[0]] for c in coords if len(c) >= 2]

                        return {
                            "distance_km": round(dist_meters / 1000.0, 2),
                            "duration_minutes": round(dur_seconds / 60.0, 1),
                            "geometry": lat_lon_geometry,
                            "transport_mode": transport_mode,
                            "source": "openrouteservice",
                        }
        except Exception as e:
            logger.warning(f"OpenRouteService query failed: {e}; attempting OSRM fallback.")

        return None

    @classmethod
    def calculate_route_osrm(
        cls,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        transport_mode: str,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """
        Queries OSRM routing engine (OpenStreetMap).
        """
        profile = SUPPORTED_TRANSPORT_MODES[transport_mode]["osrm_profile"]
        base = settings.OSRM_BASE_URL.rstrip("/")
        # OSRM expects coordinates formatted as {lon},{lat};{lon},{lat}
        coords_str = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        url = f"{base}/route/v1/{profile}/{coords_str}?overview=full&geometries=geojson"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TravelIntelligencePlatform/1.0"},
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                if status_code == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    routes = data.get("routes", [])
                    if routes:
                        r = routes[0]
                        dist_meters = float(r.get("distance", 0.0))
                        dur_seconds = float(r.get("duration", 0.0))
                        coords = r.get("geometry", {}).get("coordinates", [])

                        # Convert from [lon, lat] to [lat, lon]
                        lat_lon_geometry = [[c[1], c[0]] for c in coords if len(c) >= 2]

                        return {
                            "distance_km": round(dist_meters / 1000.0, 2),
                            "duration_minutes": round(dur_seconds / 60.0, 1),
                            "geometry": lat_lon_geometry,
                            "transport_mode": transport_mode,
                            "source": "osrm",
                        }
                    else:
                        raise RoutingServiceError("No route found between the specified coordinates.")
                else:
                    raise RoutingServiceError(f"OSRM returned status {status_code}")
        except urllib.error.HTTPError as e:
            raise RoutingServiceError(f"Routing HTTP error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise RoutingServiceError(f"Routing connection error: {e.reason}")
        except Exception as e:
            if isinstance(e, RoutingServiceError):
                raise
            raise RoutingServiceError(f"Failed to calculate route: {str(e)}")

    @classmethod
    def calculate_route(
        cls,
        origin_lat: Any,
        origin_lon: Any,
        dest_lat: Any,
        dest_lon: Any,
        transport_mode: Optional[str] = "driving",
    ) -> Dict[str, Any]:
        """
        Validates inputs and calculates real route via OpenRouteService or OSRM.
        """
        o_lat, o_lon = cls.validate_coordinates(origin_lat, origin_lon)
        d_lat, d_lon = cls.validate_coordinates(dest_lat, dest_lon)
        mode = cls.validate_transport_mode(transport_mode)

        # 1. Try OpenRouteService if configured
        ors_res = cls.calculate_route_ors(o_lat, o_lon, d_lat, d_lon, mode)
        if ors_res:
            return ors_res

        # 2. Fall back to standard OSRM engine
        return cls.calculate_route_osrm(o_lat, o_lon, d_lat, d_lon, mode)
