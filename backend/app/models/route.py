"""Route-related Pydantic models for route computation."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.emission import TransportMode


class Coordinates(BaseModel):
    """Geographic coordinates (latitude/longitude)."""

    latitude: Annotated[float, Field(ge=-90, le=90, description="Latitude in degrees")]
    longitude: Annotated[float, Field(ge=-180, le=180, description="Longitude in degrees")]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"latitude": 40.7128, "longitude": -74.0060}
        }
    )


class RouteRequest(BaseModel):
    """Request body for route computation."""

    origin_name: Annotated[str, Field(min_length=1, max_length=200)]
    origin_coordinates: Coordinates
    destination_name: Annotated[str, Field(min_length=1, max_length=200)]
    destination_coordinates: Coordinates
    weight_kg: Annotated[float, Field(gt=0, le=1_000_000, description="Cargo weight in kg")]
    transport_mode: TransportMode

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_name": "New York, NY",
                "origin_coordinates": {"latitude": 40.7128, "longitude": -74.0060},
                "destination_name": "Los Angeles, CA",
                "destination_coordinates": {"latitude": 34.0522, "longitude": -118.2437},
                "weight_kg": 5000,
                "transport_mode": "land",
            }
        }
    )


class RouteInfo(BaseModel):
    """Information about a computed route."""

    distance_km: float = Field(description="Total distance in kilometers")
    duration_hours: float | None = Field(
        default=None, description="Estimated duration in hours"
    )
    geometry: list[list[float]] = Field(
        description="Route geometry as [longitude, latitude] coordinate pairs"
    )
    emission_kg_co2: float = Field(description="Carbon emission in kg CO2")
    route_type: str = Field(description="Type of route: 'shortest' or 'efficient'")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "distance_km": 3936.5,
                "duration_hours": 39.4,
                "geometry": [[-74.006, 40.7128], [-118.2437, 34.0522]],
                "emission_kg_co2": 1220.33,
                "route_type": "shortest",
            }
        }
    )


class RouteResponse(BaseModel):
    """Response containing both shortest and most efficient routes."""

    origin_name: str
    origin_coordinates: Coordinates
    destination_name: str
    destination_coordinates: Coordinates
    weight_kg: float
    transport_mode: TransportMode
    shortest_route: RouteInfo
    efficient_route: RouteInfo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_name": "New York, NY",
                "origin_coordinates": {"latitude": 40.7128, "longitude": -74.0060},
                "destination_name": "Los Angeles, CA",
                "destination_coordinates": {"latitude": 34.0522, "longitude": -118.2437},
                "weight_kg": 5000,
                "transport_mode": "land",
                "shortest_route": {
                    "distance_km": 3936.5,
                    "duration_hours": 39.4,
                    "geometry": [[-74.006, 40.7128], [-118.2437, 34.0522]],
                    "emission_kg_co2": 1220.33,
                    "route_type": "shortest",
                },
                "efficient_route": {
                    "distance_km": 4100.0,
                    "duration_hours": 41.0,
                    "geometry": [[-74.006, 40.7128], [-118.2437, 34.0522]],
                    "emission_kg_co2": 1195.0,
                    "route_type": "efficient",
                },
            }
        }
    )
