"""
Route & GPS Agent (Stage 8).

Responsible for coordinate validation, transport mode checking, and executing
real routing queries via RoutingService for live navigation.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from app.graph.state import TravelState
from app.services.routing import RoutingService, RoutingServiceError

logger = logging.getLogger(__name__)


class RouteAgent:
    """Agent responsible for validating and orchestrating live route calculations."""

    @classmethod
    def validate_inputs(
        cls,
        origin: Optional[Dict[str, Any]],
        destination: Optional[Dict[str, Any]],
        transport_mode: Optional[str],
    ) -> Tuple[float, float, float, float, str]:
        """
        Validates origin, destination, and transport mode.
        Raises RoutingServiceError on validation failures.
        """
        if not origin or not isinstance(origin, dict):
            raise RoutingServiceError("Missing or invalid origin coordinates.")
        if not destination or not isinstance(destination, dict):
            raise RoutingServiceError("Missing or invalid destination coordinates.")

        o_lat = origin.get("latitude")
        o_lon = origin.get("longitude")
        d_lat = destination.get("latitude")
        d_lon = destination.get("longitude")

        if o_lat is None or o_lon is None:
            raise RoutingServiceError("Origin latitude and longitude are required.")
        if d_lat is None or d_lon is None:
            raise RoutingServiceError("Destination latitude and longitude are required.")

        valid_o_lat, valid_o_lon = RoutingService.validate_coordinates(o_lat, o_lon)
        valid_d_lat, valid_d_lon = RoutingService.validate_coordinates(d_lat, d_lon)
        mode = RoutingService.validate_transport_mode(transport_mode)

        return valid_o_lat, valid_o_lon, valid_d_lat, valid_d_lon, mode

    @classmethod
    def calculate_route(cls, state: TravelState) -> Dict[str, Any]:
        """
        Executes routing calculation using state parameters and updates route state.
        """
        origin = state.get("route_origin")
        destination = state.get("route_destination")
        transport_mode = state.get("route_transport_mode") or "driving"

        try:
            o_lat, o_lon, d_lat, d_lon, mode = cls.validate_inputs(origin, destination, transport_mode)
            res = RoutingService.calculate_route(o_lat, o_lon, d_lat, d_lon, mode)

            return {
                "route_distance_km": res.get("distance_km", 0.0),
                "route_duration_minutes": res.get("duration_minutes", 0.0),
                "route_geometry": res.get("geometry", []),
                "route_transport_mode": mode,
                "route_status": "ready",
                "route_error": None,
                "agent_status": "route_calculated",
            }
        except RoutingServiceError as rse:
            logger.warning(f"Route calculation rejected: {rse}")
            return {
                "route_distance_km": 0.0,
                "route_duration_minutes": 0.0,
                "route_geometry": None,
                "route_status": "unavailable",
                "route_error": str(rse),
                "agent_status": "route_calculation_failed",
            }
        except Exception as e:
            logger.error(f"Unexpected routing error: {e}")
            return {
                "route_distance_km": 0.0,
                "route_duration_minutes": 0.0,
                "route_geometry": None,
                "route_status": "unavailable",
                "route_error": f"Failed to compute route: {str(e)}",
                "agent_status": "route_calculation_failed",
            }
