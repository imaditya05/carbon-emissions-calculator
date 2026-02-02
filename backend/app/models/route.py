"""Route-related Pydantic models for multi-modal route computation."""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.emission import TransportMode


class Coordinates(BaseModel):
    """Geographic coordinates (latitude/longitude)."""

    latitude: Annotated[float, Field(ge=-90, le=90, description="Latitude in degrees")]
    longitude: Annotated[float, Field(ge=-180, le=180, description="Longitude in degrees")]

    model_config = ConfigDict(
        json_schema_extra={"example": {"latitude": 40.7128, "longitude": -74.0060}}
    )


class RouteRequest(BaseModel):
    """Request body for route computation."""

    origin_name: Annotated[str, Field(min_length=1, max_length=200)]
    origin_coordinates: Coordinates
    destination_name: Annotated[str, Field(min_length=1, max_length=200)]
    destination_coordinates: Coordinates
    weight_kg: Annotated[float, Field(gt=0, le=1_000_000, description="Cargo weight in kg")]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_name": "Bengaluru, India",
                "origin_coordinates": {"latitude": 12.9716, "longitude": 77.5946},
                "destination_name": "New Delhi, India",
                "destination_coordinates": {"latitude": 28.6139, "longitude": 77.2090},
                "weight_kg": 1000,
            }
        }
    )


class RouteSegment(BaseModel):
    """A single segment of a multi-modal route."""

    mode: TransportMode = Field(description="Transport mode for this segment")
    from_name: str = Field(description="Starting point name")
    from_coordinates: Coordinates
    to_name: str = Field(description="Ending point name")
    to_coordinates: Coordinates
    distance_km: float = Field(description="Distance in kilometers")
    duration_hours: float = Field(description="Duration in hours")
    emission_kg_co2: float = Field(description="CO2 emission for this segment")
    geometry: list[list[float]] = Field(description="Route geometry coordinates")


class Waypoint(BaseModel):
    """A waypoint (airport/port) in a multi-modal route."""

    name: str
    type: str  # "airport" or "port"
    coordinates: Coordinates


class MultiModalRoute(BaseModel):
    """A complete multi-modal route with segments and waypoints."""

    segments: list[RouteSegment] = Field(description="Route segments")
    total_distance_km: float
    total_duration_hours: float
    total_emission_kg_co2: float
    transport_mode: TransportMode = Field(description="Primary transport mode")
    is_viable: bool = Field(default=True)
    waypoints: list[dict[str, Any]] = Field(default_factory=list)
    not_viable_reason: str | None = Field(default=None)


class RouteInfo(BaseModel):
    """Summary information about a computed route."""

    distance_km: float = Field(description="Total distance in kilometers")
    duration_hours: float | None = Field(default=None, description="Estimated duration in hours")
    geometry: list[list[float]] = Field(description="Combined route geometry")
    emission_kg_co2: float = Field(description="Total carbon emission in kg CO2")
    route_type: str = Field(description="Type: 'shortest' or 'efficient'")
    transport_mode: TransportMode = Field(
        default=TransportMode.LAND, description="Primary transport mode"
    )


class ModeComparison(BaseModel):
    """Comparison data for a single transport mode."""

    transport_mode: TransportMode
    distance_km: float
    duration_hours: float
    emission_kg_co2: float
    is_shortest: bool = False
    is_most_efficient: bool = False
    is_viable: bool = True
    not_viable_reason: str | None = None


class RouteResponse(BaseModel):
    """Response containing route analysis results."""

    origin_name: str
    origin_coordinates: Coordinates
    destination_name: str
    destination_coordinates: Coordinates
    weight_kg: float
    shortest_route: RouteInfo
    efficient_route: RouteInfo
    mode_comparison: list[ModeComparison]
    detailed_routes: list[MultiModalRoute] = Field(
        default_factory=list,
        description="Detailed multi-modal routes with segments"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_name": "Bengaluru, India",
                "origin_coordinates": {"latitude": 12.9716, "longitude": 77.5946},
                "destination_name": "New Delhi, India",
                "destination_coordinates": {"latitude": 28.6139, "longitude": 77.2090},
                "weight_kg": 1000,
                "shortest_route": {
                    "distance_km": 1800,
                    "duration_hours": 3.5,
                    "geometry": [],
                    "emission_kg_co2": 250,
                    "route_type": "shortest",
                    "transport_mode": "air",
                },
                "efficient_route": {
                    "distance_km": 2200,
                    "duration_hours": 36,
                    "geometry": [],
                    "emission_kg_co2": 68,
                    "route_type": "efficient",
                    "transport_mode": "land",
                },
                "mode_comparison": [],
                "detailed_routes": [],
            }
        }
    )
