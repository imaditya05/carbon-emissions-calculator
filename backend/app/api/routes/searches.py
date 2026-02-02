"""Search history API endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUser
from app.models.emission import TransportMode
from app.models.route import RouteRequest, RouteResponse
from app.models.search import SearchCreate, SearchListResponse, SearchResponse
from app.services.route_service import RouteService, RouteServiceError
from app.services.search_service import SearchNotFoundError, SearchService
from app.models.search import SearchFilters

router = APIRouter(prefix="/searches", tags=["Search History"])

# Service instances
search_service = SearchService()
route_service = RouteService()


@router.post(
    "/",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compute routes and save to search history",
    description="""
    Computes routes between origin and destination, calculates emissions,
    and saves the search to the user's history.

    This is the main endpoint for the calculator - it combines route computation
    with search history storage in a single operation.
    """,
)
async def create_search(
    request: RouteRequest,
    current_user: CurrentUser,
) -> RouteResponse:
    """Create a new search with route computation."""
    try:
        # Compute routes
        shortest_route, efficient_route = await route_service.compute_routes(
            origin=request.origin_coordinates,
            destination=request.destination_coordinates,
            weight_kg=request.weight_kg,
            transport_mode=request.transport_mode,
        )

        # Save to search history
        search_data = SearchCreate(
            origin_name=request.origin_name,
            origin_coordinates=request.origin_coordinates,
            destination_name=request.destination_name,
            destination_coordinates=request.destination_coordinates,
            weight_kg=request.weight_kg,
            transport_mode=request.transport_mode,
            shortest_route=shortest_route,
            efficient_route=efficient_route,
        )

        await search_service.create_search(search_data, current_user.id)

        # Return route response
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


@router.get(
    "/",
    response_model=SearchListResponse,
    summary="Get search history",
    description="""
    Retrieve the authenticated user's search history with optional filters
    and pagination.

    **Filters:**
    - `transport_mode`: Filter by land, sea, or air
    - `origin_name`: Partial match on origin name
    - `destination_name`: Partial match on destination name
    - `date_from`: Searches after this date
    - `date_to`: Searches before this date

    **Pagination:**
    - Default page size is 10
    - Results are sorted by date (most recent first)
    """,
)
async def get_searches(
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Items per page")
    ] = 10,
    transport_mode: Annotated[
        TransportMode | None, Query(description="Filter by transport mode")
    ] = None,
    origin_name: Annotated[
        str | None, Query(description="Filter by origin name (partial match)")
    ] = None,
    destination_name: Annotated[
        str | None, Query(description="Filter by destination name (partial match)")
    ] = None,
    date_from: Annotated[
        datetime | None, Query(description="Filter searches from this date")
    ] = None,
    date_to: Annotated[
        datetime | None, Query(description="Filter searches until this date")
    ] = None,
) -> SearchListResponse:
    """Get paginated search history with filters."""
    filters = SearchFilters(
        transport_mode=transport_mode,
        origin_name=origin_name,
        destination_name=destination_name,
        date_from=date_from,
        date_to=date_to,
    )

    return await search_service.get_user_searches(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        filters=filters,
    )


@router.get(
    "/{search_id}",
    response_model=SearchResponse,
    summary="Get a specific search",
    description="Retrieve details of a specific search by ID.",
)
async def get_search(
    search_id: str,
    current_user: CurrentUser,
) -> SearchResponse:
    """Get a specific search by ID."""
    try:
        return await search_service.get_search_by_id(search_id, current_user.id)
    except SearchNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a search",
    description="Delete a specific search from history.",
)
async def delete_search(
    search_id: str,
    current_user: CurrentUser,
) -> None:
    """Delete a specific search."""
    try:
        await search_service.delete_search(search_id, current_user.id)
    except SearchNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Delete all search history",
    description="Delete all searches from the user's history.",
)
async def delete_all_searches(
    current_user: CurrentUser,
) -> dict[str, int]:
    """Delete all user searches."""
    count = await search_service.delete_all_user_searches(current_user.id)
    return {"deleted_count": count}
