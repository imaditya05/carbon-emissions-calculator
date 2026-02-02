"""Emission calculation related Pydantic models."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TransportMode(str, Enum):
    """Supported transport modes for cargo movement."""

    LAND = "land"
    SEA = "sea"
    AIR = "air"


class EmissionFactors(BaseModel):
    """Carbon emission factors for different transport modes.

    Emission factors are expressed in kg CO2 per tonne-kilometer (kg CO2/t-km).

    Sources and references:
    - European Environment Agency (EEA) - EMEP/EEA air pollutant emission inventory
    - International Maritime Organization (IMO) - Fourth GHG Study 2020
    - International Civil Aviation Organization (ICAO) - Carbon Emissions Calculator
    - IPCC Guidelines for National Greenhouse Gas Inventories

    Transport mode emission factors:
    - Land (truck): ~0.062 kg CO2/t-km (heavy-duty truck average)
    - Sea (container ship): ~0.016 kg CO2/t-km (large container vessel)
    - Air (cargo plane): ~0.602 kg CO2/t-km (freight aircraft average)
    """

    land: float = Field(
        default=0.062,
        description="kg CO2 per tonne-km for road transport (heavy-duty truck)",
    )
    sea: float = Field(
        default=0.016,
        description="kg CO2 per tonne-km for sea transport (container ship)",
    )
    air: float = Field(
        default=0.602,
        description="kg CO2 per tonne-km for air transport (cargo aircraft)",
    )

    def get_factor(self, mode: TransportMode) -> float:
        """Get the emission factor for a specific transport mode."""
        factors = {
            TransportMode.LAND: self.land,
            TransportMode.SEA: self.sea,
            TransportMode.AIR: self.air,
        }
        return factors[mode]


class EmissionCalculationRequest(BaseModel):
    """Request body for emission calculation."""

    distance_km: Annotated[float, Field(gt=0, description="Distance in kilometers")]
    weight_kg: Annotated[float, Field(gt=0, description="Cargo weight in kilograms")]
    transport_mode: TransportMode = Field(description="Mode of transport")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "distance_km": 1000.0,
                "weight_kg": 5000.0,
                "transport_mode": "land",
            }
        }
    )


class EmissionResult(BaseModel):
    """Result of carbon emission calculation."""

    transport_mode: TransportMode
    distance_km: float = Field(description="Distance in kilometers")
    weight_kg: float = Field(description="Cargo weight in kilograms")
    emission_kg_co2: float = Field(description="Total CO2 emission in kilograms")
    emission_factor_used: float = Field(
        description="Emission factor used (kg CO2/t-km)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transport_mode": "land",
                "distance_km": 1000.0,
                "weight_kg": 5000.0,
                "emission_kg_co2": 310.0,
                "emission_factor_used": 0.062,
            }
        }
    )


class EmissionFactorInfo(BaseModel):
    """Detailed information about an emission factor."""

    mode: TransportMode
    factor: float = Field(description="Emission factor in kg CO2/t-km")
    unit: str = "kg CO2/t-km"
    vehicle_type: str
    source: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mode": "land",
                "factor": 0.062,
                "unit": "kg CO2/t-km",
                "vehicle_type": "Heavy-duty truck (average)",
                "source": "EEA/IPCC transport emission factors",
            }
        }
    )


class EmissionComparisonResult(BaseModel):
    """Comparison of emissions across all transport modes."""

    land: EmissionResult
    sea: EmissionResult
    air: EmissionResult
    most_efficient: TransportMode
    least_efficient: TransportMode
