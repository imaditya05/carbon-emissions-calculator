"""Route computation endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser
from app.models.route import RouteRequest, RouteResponse
from app.services.route_service import RouteService, RouteServiceError

router = APIRouter(prefix="/routes", tags=["Routes"])

# Create service instance
route_service = RouteService()


@router.post(
    "/compute",
    response_model=RouteResponse,
    summary="Compute routes between two locations",
    description="""
    Compute both shortest and most efficient routes between origin and destination.

    **For land transport:**
    - Uses OpenRouteService API when API key is configured
    - Falls back to great-circle distance with road factor (~1.3x) otherwise

    **For sea and air transport:**
    - Uses great-circle (geodesic) distance
    - Generates interpolated waypoints for map visualization

    **Returns:**
    - Shortest route: Minimizes distance
    - Efficient route: Optimizes for lower CO2 emissions
    """,
)
async def compute_routes(
    request: RouteRequest,
    current_user: CurrentUser,
) -> RouteResponse:
    """Compute shortest and most efficient routes."""
    try:
        shortest_route, efficient_route = await route_service.compute_routes(
            origin=request.origin_coordinates,
            destination=request.destination_coordinates,
            weight_kg=request.weight_kg,
            transport_mode=request.transport_mode,
        )

        return RouteResponse(
            origin_name=request.origin_name,
            origin_coordinates=request.origin_coordinates,
            destination_name=request.destination_name,
            destination_coordinates=request.destination_coordinates,
            weight_kg=request.weight_kg,
            transport_mode=request.transport_mode,
            shortest_route=shortest_route,
            efficient_route=efficient_route,
        )

    except RouteServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Route computation failed: {str(e)}",
        )
