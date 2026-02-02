"""Search history API endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUser
from app.models.emission import TransportMode
from app.models.route import RouteRequest, RouteResponse
from app.models.search import SearchCreate, SearchFilters, SearchListResponse, SearchResponse
from app.services.route_service import RouteService, RouteServiceError
from app.services.search_service import SearchNotFoundError, SearchService

router = APIRouter(prefix="/searches", tags=["Search History"])

search_service = SearchService()
route_service = RouteService()


@router.post(
    "/",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compute routes and save to search history",
    description="""
    Computes multi-modal routes between origin and destination,
    calculates emissions, and saves the search to history.
    """,
)
async def create_search(
    request: RouteRequest,
    current_user: CurrentUser,
) -> RouteResponse:
    """Create a new search with multi-modal route computation."""
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

        # Save to search history (without detailed_routes to keep storage minimal)
        search_data = SearchCreate(
            origin_name=request.origin_name,
            origin_coordinates=request.origin_coordinates,
            destination_name=request.destination_name,
            destination_coordinates=request.destination_coordinates,
            weight_kg=request.weight_kg,
            shortest_route=shortest_route,
            efficient_route=efficient_route,
            mode_comparison=mode_comparison,
        )

        await search_service.create_search(search_data, current_user.id)

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


@router.get(
    "/",
    response_model=SearchListResponse,
    summary="Get search history",
)
async def get_searches(
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    shortest_mode: Annotated[TransportMode | None, Query()] = None,
    efficient_mode: Annotated[TransportMode | None, Query()] = None,
    origin_name: Annotated[str | None, Query()] = None,
    destination_name: Annotated[str | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> SearchListResponse:
    """Get paginated search history with filters."""
    filters = SearchFilters(
        shortest_mode=shortest_mode,
        efficient_mode=efficient_mode,
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


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search(search_id: str, current_user: CurrentUser) -> SearchResponse:
    """Get a specific search by ID."""
    try:
        return await search_service.get_search_by_id(search_id, current_user.id)
    except SearchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search(search_id: str, current_user: CurrentUser) -> None:
    """Delete a specific search."""
    try:
        await search_service.delete_search(search_id, current_user.id)
    except SearchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_all_searches(current_user: CurrentUser) -> dict[str, int]:
    """Delete all user searches."""
    count = await search_service.delete_all_user_searches(current_user.id)
    return {"deleted_count": count}
