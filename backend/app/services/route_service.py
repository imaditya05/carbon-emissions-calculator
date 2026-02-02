"""Route computation service using Mapbox Directions API.

This service computes routes between locations using:
1. Mapbox Directions API for land routes (if access token configured)
2. Great-circle distance calculation as fallback for all modes

References:
- Mapbox Directions API: https://docs.mapbox.com/api/navigation/directions/
- Haversine formula for great-circle distance
"""

import math
from typing import Any

import httpx

from app.core.config import settings
from app.models.emission import TransportMode
from app.models.route import Coordinates, RouteInfo
from app.services.emission_service import EmissionService


class RouteServiceError(Exception):
    """Base exception for route service errors."""

    pass


class RouteAPIError(RouteServiceError):
    """Raised when the routing API returns an error."""

    pass


class RouteNotFoundError(RouteServiceError):
    """Raised when no route can be found between points."""

    pass


class RouteService:
    """Service for computing routes between locations.

    Uses Mapbox Directions API for land routes when access token is configured.
    Falls back to great-circle distance calculation for all modes.
    """

    # Mapbox API endpoint
    MAPBOX_DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox"

    # Average speeds for duration estimation (km/h)
    AVERAGE_SPEEDS: dict[TransportMode, float] = {
        TransportMode.LAND: 60.0,   # Heavy truck average
        TransportMode.SEA: 30.0,    # Container ship average
        TransportMode.AIR: 800.0,   # Cargo aircraft average
    }

    def __init__(self, emission_service: EmissionService | None = None) -> None:
        """Initialize the route service.

        Args:
            emission_service: Optional emission service for CO2 calculations.
        """
        self.emission_service = emission_service or EmissionService()

    @staticmethod
    def haversine_distance(origin: Coordinates, destination: Coordinates) -> float:
        """Calculate great-circle distance using Haversine formula.

        Args:
            origin: Starting coordinates.
            destination: Ending coordinates.

        Returns:
            Distance in kilometers.
        """
        R = 6371.0  # Earth's radius in kilometers

        lat1 = math.radians(origin.latitude)
        lat2 = math.radians(destination.latitude)
        dlat = math.radians(destination.latitude - origin.latitude)
        dlon = math.radians(destination.longitude - origin.longitude)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _interpolate_great_circle(
        self,
        origin: Coordinates,
        destination: Coordinates,
        num_points: int = 20,
    ) -> list[list[float]]:
        """Generate intermediate points along a great-circle path.

        Args:
            origin: Starting coordinates.
            destination: Ending coordinates.
            num_points: Number of points to generate.

        Returns:
            List of [longitude, latitude] coordinate pairs (GeoJSON format).
        """
        points: list[list[float]] = []

        lat1 = math.radians(origin.latitude)
        lon1 = math.radians(origin.longitude)
        lat2 = math.radians(destination.latitude)
        lon2 = math.radians(destination.longitude)

        # Angular distance
        d = 2 * math.asin(
            math.sqrt(
                math.sin((lat2 - lat1) / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
            )
        )

        for i in range(num_points + 1):
            f = i / num_points

            if d == 0:
                lat = lat1
                lon = lon1
            else:
                A = math.sin((1 - f) * d) / math.sin(d)
                B = math.sin(f * d) / math.sin(d)

                x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
                y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
                z = A * math.sin(lat1) + B * math.sin(lat2)

                lat = math.atan2(z, math.sqrt(x**2 + y**2))
                lon = math.atan2(y, x)

            # GeoJSON format: [longitude, latitude]
            points.append([math.degrees(lon), math.degrees(lat)])

        return points

    async def _get_mapbox_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        alternatives: bool = False,
    ) -> list[dict[str, Any]]:
        """Get route(s) from Mapbox Directions API.

        Args:
            origin: Starting coordinates.
            destination: Ending coordinates.
            alternatives: Whether to request alternative routes.

        Returns:
            List of route data with distance, duration, and geometry.

        Raises:
            RouteAPIError: If API request fails.
            RouteNotFoundError: If no route found.
        """
        if not settings.mapbox_access_token:
            raise RouteAPIError("Mapbox access token not configured")

        # Use driving profile (suitable for cargo vehicles)
        profile = "driving"
        coords = f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        url = f"{self.MAPBOX_DIRECTIONS_URL}/{profile}/{coords}"

        params = {
            "access_token": settings.mapbox_access_token,
            "geometries": "geojson",
            "overview": "full",
            "alternatives": "true" if alternatives else "false",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)

                if response.status_code == 401:
                    raise RouteAPIError("Invalid Mapbox access token")

                if response.status_code == 422:
                    raise RouteNotFoundError(
                        "No route found between the specified points"
                    )

                response.raise_for_status()
                data = response.json()

            except httpx.HTTPStatusError as e:
                raise RouteAPIError(f"Mapbox API error: {e.response.text}")
            except httpx.RequestError as e:
                raise RouteAPIError(f"Mapbox API request failed: {str(e)}")

        if data.get("code") != "Ok" or not data.get("routes"):
            raise RouteNotFoundError("No route found between the specified points")

        routes = []
        for route in data["routes"]:
            geometry = route.get("geometry", {}).get("coordinates", [])
            routes.append({
                "distance_km": route.get("distance", 0) / 1000,  # Convert meters to km
                "duration_hours": route.get("duration", 0) / 3600,  # Convert seconds to hours
                "geometry": geometry,
            })

        return routes

    async def compute_routes(
        self,
        origin: Coordinates,
        destination: Coordinates,
        weight_kg: float,
        transport_mode: TransportMode,
    ) -> tuple[RouteInfo, RouteInfo]:
        """Compute both shortest and most efficient routes.

        Args:
            origin: Starting coordinates.
            destination: Ending coordinates.
            weight_kg: Cargo weight in kilograms.
            transport_mode: Mode of transport.

        Returns:
            Tuple of (shortest_route, efficient_route).
        """
        # For land transport, try to use Mapbox API
        if transport_mode == TransportMode.LAND and settings.mapbox_access_token:
            try:
                return await self._compute_mapbox_routes(
                    origin, destination, weight_kg, transport_mode
                )
            except RouteServiceError:
                # Fall back to direct calculation
                pass

        # Use great-circle distance for sea, air, or when API unavailable
        return await self._compute_direct_routes(
            origin, destination, weight_kg, transport_mode
        )

    async def _compute_mapbox_routes(
        self,
        origin: Coordinates,
        destination: Coordinates,
        weight_kg: float,
        transport_mode: TransportMode,
    ) -> tuple[RouteInfo, RouteInfo]:
        """Compute routes using Mapbox Directions API.

        Args:
            origin: Starting coordinates.
            destination: Ending coordinates.
            weight_kg: Cargo weight in kilograms.
            transport_mode: Transport mode.

        Returns:
            Tuple of (shortest_route, efficient_route).
        """
        # Request routes with alternatives
        routes = await self._get_mapbox_route(origin, destination, alternatives=True)

        if not routes:
            raise RouteNotFoundError("No routes returned from Mapbox")

        # First route is typically the fastest/shortest
        shortest_data = routes[0]
        shortest_emission = self.emission_service.calculate_emission(
            shortest_data["distance_km"], weight_kg, transport_mode
        )

        shortest_route = RouteInfo(
            distance_km=round(shortest_data["distance_km"], 2),
            duration_hours=round(shortest_data["duration_hours"], 2),
            geometry=shortest_data["geometry"],
            emission_kg_co2=shortest_emission.emission_kg_co2,
            route_type="shortest",
        )

        # Use alternative route if available, otherwise simulate efficient route
        if len(routes) > 1:
            # Find the route with lowest emissions
            best_efficient = None
            best_emission = float("inf")

            for route_data in routes[1:]:
                emission = self.emission_service.calculate_emission(
                    route_data["distance_km"], weight_kg, transport_mode
                )
                if emission.emission_kg_co2 < best_emission:
                    best_emission = emission.emission_kg_co2
                    best_efficient = route_data

            if best_efficient and best_emission < shortest_emission.emission_kg_co2:
                efficient_route = RouteInfo(
                    distance_km=round(best_efficient["distance_km"], 2),
                    duration_hours=round(best_efficient["duration_hours"], 2),
                    geometry=best_efficient["geometry"],
                    emission_kg_co2=round(best_emission, 4),
                    route_type="efficient",
                )
            else:
                # No better alternative, use simulated efficient route
                efficient_route = self._create_simulated_efficient_route(
                    shortest_data, shortest_emission.emission_kg_co2, transport_mode
                )
        else:
            # No alternatives, simulate efficient route
            efficient_route = self._create_simulated_efficient_route(
                shortest_data, shortest_emission.emission_kg_co2, transport_mode
            )

        return shortest_route, efficient_route

    def _create_simulated_efficient_route(
        self,
        base_route: dict[str, Any],
        base_emission: float,
        transport_mode: TransportMode,
    ) -> RouteInfo:
        """Create a simulated efficient route when no alternative available.

        Args:
            base_route: The base route data.
            base_emission: Base emission in kg CO2.
            transport_mode: Transport mode.

        Returns:
            Simulated efficient route.
        """
        # Simulate a route that trades slightly more distance for lower emissions
        # (e.g., avoiding hills, using more efficient roads)
        efficiency_factor = 0.95  # 5% emission reduction

        return RouteInfo(
            distance_km=round(base_route["distance_km"] * 1.02, 2),  # 2% longer
            duration_hours=round(base_route["duration_hours"] * 1.05, 2),  # 5% slower
            geometry=base_route["geometry"],
            emission_kg_co2=round(base_emission * efficiency_factor, 4),
            route_type="efficient",
        )

    async def _compute_direct_routes(
        self,
        origin: Coordinates,
        destination: Coordinates,
        weight_kg: float,
        transport_mode: TransportMode,
    ) -> tuple[RouteInfo, RouteInfo]:
        """Compute routes using great-circle distance.

        For sea and air transport, the shortest path is the great-circle route.
        The "efficient" route simulates minor optimizations.

        Args:
            origin: Starting coordinates.
            destination: Ending coordinates.
            weight_kg: Cargo weight in kilograms.
            transport_mode: Transport mode.

        Returns:
            Tuple of (shortest_route, efficient_route).
        """
        # Calculate great-circle distance
        distance_km = self.haversine_distance(origin, destination)

        # For land without API, add ~30% for road distance approximation
        if transport_mode == TransportMode.LAND:
            distance_km *= 1.3

        # Calculate duration based on average speed
        duration_hours = distance_km / self.AVERAGE_SPEEDS[transport_mode]

        # Generate geometry points
        num_points = max(10, int(distance_km / 200))
        geometry = self._interpolate_great_circle(origin, destination, num_points)

        # Calculate emission for shortest route
        shortest_emission = self.emission_service.calculate_emission(
            distance_km, weight_kg, transport_mode
        )

        shortest_route = RouteInfo(
            distance_km=round(distance_km, 2),
            duration_hours=round(duration_hours, 2),
            geometry=geometry,
            emission_kg_co2=shortest_emission.emission_kg_co2,
            route_type="shortest",
        )

        # Simulate efficient route (slightly longer but lower emissions)
        efficient_factor = {
            TransportMode.LAND: 0.95,  # 5% emission reduction
            TransportMode.SEA: 0.97,   # 3% emission reduction (slower speeds)
            TransportMode.AIR: 0.99,   # 1% emission reduction (optimal altitude)
        }

        efficient_distance = distance_km * 1.02  # Slightly longer route
        efficient_emission = self.emission_service.calculate_emission(
            efficient_distance, weight_kg, transport_mode
        )

        # Apply efficiency factor to emissions
        efficient_emission_value = (
            efficient_emission.emission_kg_co2 * efficient_factor[transport_mode]
        )

        efficient_route = RouteInfo(
            distance_km=round(efficient_distance, 2),
            duration_hours=round(efficient_distance / self.AVERAGE_SPEEDS[transport_mode], 2),
            geometry=geometry,
            emission_kg_co2=round(efficient_emission_value, 4),
            route_type="efficient",
        )

        return shortest_route, efficient_route
