"""Pydantic models for request/response validation and database schemas."""

from app.models.user import (
    Token,
    TokenData,
    UserCreate,
    UserInDB,
    UserResponse,
)
from app.models.emission import (
    EmissionCalculationRequest,
    EmissionComparisonResult,
    EmissionFactorInfo,
    EmissionFactors,
    EmissionResult,
    TransportMode,
)
from app.models.route import (
    Coordinates,
    ModeComparison,
    MultiModalRoute,
    RouteInfo,
    RouteRequest,
    RouteResponse,
    RouteSegment,
    Waypoint,
)
from app.models.search import (
    PaginationMeta,
    SearchCreate,
    SearchFilters,
    SearchListResponse,
    SearchResponse,
)

__all__ = [
    # User models
    "Token",
    "TokenData",
    "UserCreate",
    "UserInDB",
    "UserResponse",
    # Emission models
    "EmissionCalculationRequest",
    "EmissionComparisonResult",
    "EmissionFactorInfo",
    "EmissionFactors",
    "EmissionResult",
    "TransportMode",
    # Route models
    "Coordinates",
    "ModeComparison",
    "MultiModalRoute",
    "RouteInfo",
    "RouteRequest",
    "RouteResponse",
    "RouteSegment",
    "Waypoint",
    # Search models
    "PaginationMeta",
    "SearchCreate",
    "SearchFilters",
    "SearchListResponse",
    "SearchResponse",
]
