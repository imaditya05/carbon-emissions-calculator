"""Search history Pydantic models."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.emission import TransportMode
from app.models.route import Coordinates, RouteInfo, ModeComparison


class SearchBase(BaseModel):
    """Base search model with common fields."""

    origin_name: str
    origin_coordinates: Coordinates
    destination_name: str
    destination_coordinates: Coordinates
    weight_kg: Annotated[float, Field(gt=0)]


class SearchCreate(SearchBase):
    """Model for creating a new search record."""

    shortest_route: RouteInfo
    efficient_route: RouteInfo
    mode_comparison: list[ModeComparison] = Field(default_factory=list)


class SearchInDB(SearchBase):
    """Model representing a search in the database."""

    id: str = Field(alias="_id")
    user_id: str
    shortest_route: RouteInfo
    efficient_route: RouteInfo
    mode_comparison: list[ModeComparison] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "origin_name": "New York, NY",
                "origin_coordinates": {"latitude": 40.7128, "longitude": -74.006},
                "destination_name": "Los Angeles, CA",
                "destination_coordinates": {"latitude": 34.0522, "longitude": -118.2437},
                "weight_kg": 5000.0,
                "shortest_route": {
                    "distance_km": 3936.5,
                    "duration_hours": 39.4,
                    "geometry": [],
                    "emission_kg_co2": 1220.33,
                    "route_type": "shortest",
                    "transport_mode": "land",
                },
                "efficient_route": {
                    "distance_km": 9500.0,
                    "duration_hours": 316.7,
                    "geometry": [],
                    "emission_kg_co2": 475.0,
                    "route_type": "efficient",
                    "transport_mode": "sea",
                },
                "mode_comparison": [],
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class SearchResponse(SearchBase):
    """Response model for a single search."""

    id: str
    shortest_route: RouteInfo
    efficient_route: RouteInfo
    mode_comparison: list[ModeComparison] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "origin_name": "New York, NY",
                "origin_coordinates": {"latitude": 40.7128, "longitude": -74.006},
                "destination_name": "Los Angeles, CA",
                "destination_coordinates": {"latitude": 34.0522, "longitude": -118.2437},
                "weight_kg": 5000.0,
                "shortest_route": {
                    "distance_km": 3936.5,
                    "duration_hours": 39.4,
                    "geometry": [],
                    "emission_kg_co2": 1220.33,
                    "route_type": "shortest",
                    "transport_mode": "land",
                },
                "efficient_route": {
                    "distance_km": 9500.0,
                    "duration_hours": 316.7,
                    "geometry": [],
                    "emission_kg_co2": 475.0,
                    "route_type": "efficient",
                    "transport_mode": "sea",
                },
                "mode_comparison": [],
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class SearchListResponse(BaseModel):
    """Paginated response for search history."""

    items: list[SearchResponse]
    pagination: PaginationMeta

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "origin_name": "New York, NY",
                        "origin_coordinates": {"latitude": 40.7128, "longitude": -74.006},
                        "destination_name": "Los Angeles, CA",
                        "destination_coordinates": {"latitude": 34.0522, "longitude": -118.2437},
                        "weight_kg": 5000.0,
                        "shortest_route": {
                            "distance_km": 3936.5,
                            "duration_hours": 39.4,
                            "geometry": [],
                            "emission_kg_co2": 1220.33,
                            "route_type": "shortest",
                            "transport_mode": "land",
                        },
                        "efficient_route": {
                            "distance_km": 9500.0,
                            "duration_hours": 316.7,
                            "geometry": [],
                            "emission_kg_co2": 475.0,
                            "route_type": "efficient",
                            "transport_mode": "sea",
                        },
                        "mode_comparison": [],
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                ],
                "pagination": {
                    "total": 25,
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 3,
                    "has_next": True,
                    "has_prev": False,
                },
            }
        },
    )


class SearchFilters(BaseModel):
    """Query parameters for filtering searches."""

    shortest_mode: TransportMode | None = Field(
        default=None, description="Filter by shortest route transport mode"
    )
    efficient_mode: TransportMode | None = Field(
        default=None, description="Filter by efficient route transport mode"
    )
    origin_name: str | None = Field(
        default=None, description="Filter by origin name (partial match)"
    )
    destination_name: str | None = Field(
        default=None, description="Filter by destination name (partial match)"
    )
    date_from: datetime | None = Field(
        default=None, description="Filter searches from this date"
    )
    date_to: datetime | None = Field(
        default=None, description="Filter searches until this date"
    )
