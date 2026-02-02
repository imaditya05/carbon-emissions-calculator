"""Carbon emission calculation service.

This service calculates carbon emissions for cargo transport based on
industry-standard emission factors from authoritative sources.
"""

from app.models.emission import (
    EmissionComparisonResult,
    EmissionFactorInfo,
    EmissionFactors,
    EmissionResult,
    TransportMode,
)


class EmissionService:
    """Service for calculating carbon emissions from cargo transport.

    Emission factors are based on industry standards from:
    - European Environment Agency (EEA) - EMEP/EEA emission inventory guidebook
    - International Maritime Organization (IMO) - Fourth GHG Study 2020
    - International Civil Aviation Organization (ICAO) - Carbon Emissions Calculator
    - IPCC Guidelines for National Greenhouse Gas Inventories
    - Global Logistics Emissions Council (GLEC) Framework

    The emission factor unit is kg CO2 per tonne-kilometer (kg CO2/t-km).
    """

    # Emission factor metadata for documentation
    EMISSION_FACTOR_INFO: dict[TransportMode, dict[str, str]] = {
        TransportMode.LAND: {
            "vehicle_type": "Heavy-duty truck (average)",
            "source": "EEA/IPCC transport emission factors",
        },
        TransportMode.SEA: {
            "vehicle_type": "Large container vessel (8000+ TEU)",
            "source": "IMO Fourth GHG Study 2020",
        },
        TransportMode.AIR: {
            "vehicle_type": "Cargo aircraft (freighter average)",
            "source": "ICAO Carbon Emissions Calculator",
        },
    }

    def __init__(self, emission_factors: EmissionFactors | None = None) -> None:
        """Initialize the emission service.

        Args:
            emission_factors: Optional custom emission factors.
                            Defaults to standard factors.
        """
        self.factors = emission_factors or EmissionFactors()

    def calculate_emission(
        self,
        distance_km: float,
        weight_kg: float,
        transport_mode: TransportMode,
    ) -> EmissionResult:
        """Calculate carbon emissions for cargo transport.

        The formula used is:
            CO2 (kg) = distance (km) × weight (tonnes) × emission_factor (kg CO2/t-km)

        Where:
            - distance is in kilometers
            - weight is converted from kg to tonnes (÷ 1000)
            - emission_factor varies by transport mode

        Args:
            distance_km: Distance to travel in kilometers.
            weight_kg: Cargo weight in kilograms.
            transport_mode: Mode of transport (land, sea, air).

        Returns:
            EmissionResult containing the calculated emission.

        Raises:
            ValueError: If distance or weight is negative.
        """
        if distance_km < 0:
            raise ValueError("Distance cannot be negative")
        if weight_kg < 0:
            raise ValueError("Weight cannot be negative")

        # Get emission factor for the transport mode
        factor = self.factors.get_factor(transport_mode)

        # Convert weight from kg to tonnes
        weight_tonnes = weight_kg / 1000.0

        # Calculate emission: distance × weight (in tonnes) × factor
        emission_kg_co2 = distance_km * weight_tonnes * factor

        return EmissionResult(
            transport_mode=transport_mode,
            distance_km=round(distance_km, 2),
            weight_kg=round(weight_kg, 2),
            emission_kg_co2=round(emission_kg_co2, 4),
            emission_factor_used=factor,
        )

    def compare_transport_modes(
        self,
        distance_km: float,
        weight_kg: float,
    ) -> EmissionComparisonResult:
        """Compare emissions across all transport modes.

        Args:
            distance_km: Distance in kilometers.
            weight_kg: Cargo weight in kilograms.

        Returns:
            EmissionComparisonResult with emissions for each mode.
        """
        results: dict[TransportMode, EmissionResult] = {}

        for mode in TransportMode:
            results[mode] = self.calculate_emission(distance_km, weight_kg, mode)

        # Find most and least efficient
        sorted_by_emission = sorted(
            results.items(),
            key=lambda x: x[1].emission_kg_co2,
        )
        most_efficient = sorted_by_emission[0][0]
        least_efficient = sorted_by_emission[-1][0]

        return EmissionComparisonResult(
            land=results[TransportMode.LAND],
            sea=results[TransportMode.SEA],
            air=results[TransportMode.AIR],
            most_efficient=most_efficient,
            least_efficient=least_efficient,
        )

    def get_emission_factors_info(self) -> list[EmissionFactorInfo]:
        """Get detailed information about all emission factors.

        Returns:
            List of EmissionFactorInfo for each transport mode.
        """
        info_list: list[EmissionFactorInfo] = []

        for mode in TransportMode:
            factor = self.factors.get_factor(mode)
            metadata = self.EMISSION_FACTOR_INFO[mode]

            info_list.append(
                EmissionFactorInfo(
                    mode=mode,
                    factor=factor,
                    unit="kg CO2/t-km",
                    vehicle_type=metadata["vehicle_type"],
                    source=metadata["source"],
                )
            )

        return info_list
