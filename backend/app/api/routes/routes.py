"""Route computation endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser
from app.models.route import RouteRequest, RouteResponse
from app.services.route_service import RouteService, RouteServiceError

router = APIRouter(prefix="/routes", tags=["Routes"])

route_service = RouteService()


@router.post(
    "/compute",
    response_model=RouteResponse,
    summary="Compute multi-modal routes between two locations",
    description="""
    Compute realistic multi-modal routes between origin and destination.

    The system finds actual airports and ports near both locations and calculates:
    - **Land**: Direct road route
    - **Air**: Road to airport → Flight → Road from airport
    - **Sea**: Road to port → Shipping → Road from port

    Returns:
    - **Shortest route**: Minimum total distance
    - **Efficient route**: Lowest CO2 emissions
    - **Mode comparison**: All modes with viability status
    - **Detailed routes**: Segment-by-segment breakdown with waypoints
    """,
)
async def compute_routes(
    request: RouteRequest,
    current_user: CurrentUser,
) -> RouteResponse:
    """Compute multi-modal routes with actual airport/port waypoints."""
    try:
        shortest_route, efficient_route, mode_comparison, detailed_routes = (
            await route_service.compute_all_routes(
                origin=request.origin_coordinates,
                destination=request.destination_coordinates,
                weight_kg=request.weight_kg,
                origin_name=request.origin_name,
                destination_name=request.destination_name,
            )
        )

        return RouteResponse(
            origin_name=request.origin_name,
            origin_coordinates=request.origin_coordinates,
            destination_name=request.destination_name,
            destination_coordinates=request.destination_coordinates,
            weight_kg=request.weight_kg,
            shortest_route=shortest_route,
            efficient_route=efficient_route,
            mode_comparison=mode_comparison,
            detailed_routes=detailed_routes,
        )

    except RouteServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Route computation failed: {str(e)}",
        )
