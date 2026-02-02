"""Emission calculation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser
from app.models.emission import (
    EmissionCalculationRequest,
    EmissionComparisonResult,
    EmissionFactorInfo,
    EmissionResult,
)
from app.services.emission_service import EmissionService

router = APIRouter(prefix="/emissions", tags=["Emissions"])

# Create a single instance of the service
emission_service = EmissionService()


@router.post(
    "/calculate",
    response_model=EmissionResult,
    summary="Calculate carbon emissions",
    description="""
    Calculate CO2 emissions for cargo transport based on distance, weight, and mode.

    **Formula:** `CO2 (kg) = distance (km) × weight (tonnes) × emission_factor`

    **Emission Factors (kg CO2/t-km):**
    - Land (truck): 0.062
    - Sea (ship): 0.016
    - Air (plane): 0.602
    """,
)
async def calculate_emissions(
    request: EmissionCalculationRequest,
    current_user: CurrentUser,
) -> EmissionResult:
    """Calculate carbon emissions for a cargo shipment."""
    return emission_service.calculate_emission(
        distance_km=request.distance_km,
        weight_kg=request.weight_kg,
        transport_mode=request.transport_mode,
    )


@router.get(
    "/factors",
    response_model=list[EmissionFactorInfo],
    summary="Get emission factors",
    description="Get detailed information about the emission factors used for calculations, including sources.",
)
async def get_emission_factors(
    current_user: CurrentUser,
) -> list[EmissionFactorInfo]:
    """Get emission factors and their sources."""
    return emission_service.get_emission_factors_info()


@router.get(
    "/compare",
    response_model=EmissionComparisonResult,
    summary="Compare emissions between transport modes",
    description="Compare CO2 emissions for the same cargo across all transport modes (land, sea, air).",
)
async def compare_transport_modes(
    current_user: CurrentUser,
    distance_km: Annotated[float, Query(gt=0, description="Distance in kilometers")],
    weight_kg: Annotated[float, Query(gt=0, description="Cargo weight in kilograms")],
) -> EmissionComparisonResult:
    """Compare emissions across all transport modes."""
    return emission_service.compare_transport_modes(
        distance_km=distance_km,
        weight_kg=weight_kg,
    )
