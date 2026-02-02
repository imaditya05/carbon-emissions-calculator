"""Multi-modal route computation service using Mapbox APIs.

This service computes realistic multi-hop routes:
1. Land: Direct road transport
2. Air: Road to nearest airport → Flight → Road from destination airport
3. Sea: Road to nearest port → Shipping → Road from destination port

Uses Mapbox Geocoding to find airports/ports and Directions for road routes.
"""

import math
import re
import urllib.parse
from typing import Any

import httpx

from app.core.config import settings
from app.models.emission import TransportMode
from app.models.route import Coordinates, RouteInfo, ModeComparison, RouteSegment, MultiModalRoute
from app.services.emission_service import EmissionService


class RouteServiceError(Exception):
    """Base exception for route service errors."""
    pass


class RouteService:
    """Service for computing realistic multi-modal routes with waypoints."""

    MAPBOX_GEOCODING_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    MAPBOX_DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox"

    AVERAGE_SPEEDS = {
        TransportMode.LAND: 60.0,
        TransportMode.SEA: 30.0,
        TransportMode.AIR: 800.0,
    }

    MAX_AIRPORT_DISTANCE = 200.0
    MAX_PORT_DISTANCE_NEARBY = 200.0  # For cities near coast
    MAX_PORT_DISTANCE_INLAND = 1500.0  # For landlocked cities (e.g., Delhi → Mumbai port)
    MIN_FLIGHT_DISTANCE = 200.0

    # Known major airports database (coordinates: lat, lon)
    KNOWN_AIRPORTS: dict[tuple[float, float], dict[str, str]] = {
        # India
        (28.5562, 77.1000): {"name": "Indira Gandhi International Airport", "city": "New Delhi"},
        (19.0896, 72.8656): {"name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai"},
        (12.9941, 77.7064): {"name": "Kempegowda International Airport", "city": "Bengaluru"},
        (13.0827, 80.2707): {"name": "Chennai International Airport", "city": "Chennai"},
        (22.6520, 88.4463): {"name": "Netaji Subhas Chandra Bose International Airport", "city": "Kolkata"},
        (17.2403, 78.4294): {"name": "Rajiv Gandhi International Airport", "city": "Hyderabad"},
        (26.8242, 75.8122): {"name": "Jaipur International Airport", "city": "Jaipur"},
        (23.0728, 72.6347): {"name": "Sardar Vallabhbhai Patel International Airport", "city": "Ahmedabad"},
        (15.3808, 73.8314): {"name": "Goa International Airport", "city": "Goa"},
        # UAE
        (25.2528, 55.3644): {"name": "Dubai International Airport", "city": "Dubai"},
        (24.4539, 54.6511): {"name": "Abu Dhabi International Airport", "city": "Abu Dhabi"},
        (25.3287, 55.5172): {"name": "Sharjah International Airport", "city": "Sharjah"},
        # UK
        (51.4700, -0.4543): {"name": "Heathrow Airport", "city": "London"},
        (51.1537, -0.1821): {"name": "Gatwick Airport", "city": "London"},
        (51.8747, -0.3683): {"name": "Luton Airport", "city": "London"},
        (51.5048, 0.0495): {"name": "London City Airport", "city": "London"},
        (53.3537, -2.2750): {"name": "Manchester Airport", "city": "Manchester"},
        (55.9500, -3.3725): {"name": "Edinburgh Airport", "city": "Edinburgh"},
        # USA
        (40.6413, -73.7781): {"name": "JFK International Airport", "city": "New York"},
        (40.7769, -73.8740): {"name": "LaGuardia Airport", "city": "New York"},
        (33.9425, -118.4081): {"name": "Los Angeles International Airport", "city": "Los Angeles"},
        (41.9742, -87.9073): {"name": "O'Hare International Airport", "city": "Chicago"},
        (37.6213, -122.3790): {"name": "San Francisco International Airport", "city": "San Francisco"},
        # Europe
        (48.1103, 16.5697): {"name": "Vienna International Airport", "city": "Vienna"},
        (52.5597, 13.2877): {"name": "Berlin Brandenburg Airport", "city": "Berlin"},
        (50.0379, 8.5622): {"name": "Frankfurt Airport", "city": "Frankfurt"},
        (48.3538, 11.7861): {"name": "Munich Airport", "city": "Munich"},
        (49.0097, 2.5479): {"name": "Charles de Gaulle Airport", "city": "Paris"},
        (52.3105, 4.7683): {"name": "Amsterdam Schiphol Airport", "city": "Amsterdam"},
        (41.2971, 2.0785): {"name": "Barcelona–El Prat Airport", "city": "Barcelona"},
        (40.4983, -3.5676): {"name": "Madrid–Barajas Airport", "city": "Madrid"},
        (41.8003, 12.2389): {"name": "Rome Fiumicino Airport", "city": "Rome"},
        # Asia
        (35.5494, 139.7798): {"name": "Tokyo Haneda Airport", "city": "Tokyo"},
        (35.7720, 140.3929): {"name": "Narita International Airport", "city": "Tokyo"},
        (22.3080, 113.9185): {"name": "Hong Kong International Airport", "city": "Hong Kong"},
        (1.3644, 103.9915): {"name": "Singapore Changi Airport", "city": "Singapore"},
        (13.6900, 100.7501): {"name": "Suvarnabhumi Airport", "city": "Bangkok"},
        (37.4602, 126.4407): {"name": "Incheon International Airport", "city": "Seoul"},
        (31.1443, 121.8083): {"name": "Shanghai Pudong International Airport", "city": "Shanghai"},
        (40.0799, 116.6031): {"name": "Beijing Capital International Airport", "city": "Beijing"},
        # Australia
        (-33.9399, 151.1753): {"name": "Sydney Kingsford Smith Airport", "city": "Sydney"},
        (-37.6733, 144.8433): {"name": "Melbourne Airport", "city": "Melbourne"},
        # Middle East
        (29.0344, 40.0994): {"name": "King Fahd International Airport", "city": "Dammam"},
        (24.9578, 46.6989): {"name": "King Khalid International Airport", "city": "Riyadh"},
        (21.6805, 39.1566): {"name": "King Abdulaziz International Airport", "city": "Jeddah"},
        (25.2731, 51.6081): {"name": "Hamad International Airport", "city": "Doha"},
    }

    # Known major ports database
    KNOWN_PORTS: dict[tuple[float, float], dict[str, str]] = {
        # India
        (18.9542, 72.8479): {"name": "Jawaharlal Nehru Port", "city": "Mumbai"},
        (13.0878, 80.2915): {"name": "Chennai Port", "city": "Chennai"},
        (22.2350, 68.9671): {"name": "Kandla Port", "city": "Kandla"},
        (15.4208, 73.8000): {"name": "Mormugao Port", "city": "Goa"},
        (8.4855, 76.9492): {"name": "Thiruvananthapuram Port", "city": "Thiruvananthapuram"},
        # UAE
        (25.0657, 55.1306): {"name": "Jebel Ali Port", "city": "Dubai"},
        (25.2697, 55.2963): {"name": "Port Rashid", "city": "Dubai"},
        (24.5198, 54.4050): {"name": "Khalifa Port", "city": "Abu Dhabi"},
        # Europe
        (51.9500, 4.1500): {"name": "Port of Rotterdam", "city": "Rotterdam"},
        (53.5503, 9.9936): {"name": "Port of Hamburg", "city": "Hamburg"},
        (51.2277, 4.4003): {"name": "Port of Antwerp", "city": "Antwerp"},
        (43.1000, 5.9333): {"name": "Port of Marseille", "city": "Marseille"},
        (41.3500, 2.1833): {"name": "Port of Barcelona", "city": "Barcelona"},
        (51.5074, 0.1278): {"name": "Port of London", "city": "London"},
        # Asia
        (22.2783, 114.1747): {"name": "Hong Kong Port", "city": "Hong Kong"},
        (1.2655, 103.8200): {"name": "Port of Singapore", "city": "Singapore"},
        (31.2304, 121.4737): {"name": "Port of Shanghai", "city": "Shanghai"},
        (35.4437, 139.6380): {"name": "Port of Yokohama", "city": "Yokohama"},
        (37.4563, 126.7052): {"name": "Incheon Port", "city": "Seoul"},
        # USA
        (33.7490, -118.2689): {"name": "Port of Los Angeles", "city": "Los Angeles"},
        (32.7157, -117.1611): {"name": "Port of San Diego", "city": "San Diego"},
        (40.6892, -74.0445): {"name": "Port of New York", "city": "New York"},
        (25.7617, -80.1918): {"name": "Port of Miami", "city": "Miami"},
        (29.7604, -95.3698): {"name": "Port of Houston", "city": "Houston"},
    }

    # Country code mapping for Mapbox API
    COUNTRY_CODES: dict[str, str] = {
        "india": "in", "united arab emirates": "ae", "uae": "ae",
        "united kingdom": "gb", "uk": "gb", "united states": "us",
        "usa": "us", "germany": "de", "france": "fr", "spain": "es",
        "italy": "it", "netherlands": "nl", "belgium": "be",
        "japan": "jp", "china": "cn", "singapore": "sg",
        "australia": "au", "saudi arabia": "sa", "qatar": "qa",
        "hong kong": "hk", "thailand": "th", "south korea": "kr",
    }

    def __init__(self, emission_service: EmissionService | None = None) -> None:
        self.emission_service = emission_service or EmissionService()

    @staticmethod
    def haversine_distance(origin: Coordinates, destination: Coordinates) -> float:
        """Calculate great-circle distance using Haversine formula."""
        R = 6371.0
        lat1 = math.radians(origin.latitude)
        lat2 = math.radians(destination.latitude)
        dlat = math.radians(destination.latitude - origin.latitude)
        dlon = math.radians(destination.longitude - origin.longitude)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _interpolate_great_circle(
        self, origin: Coordinates, destination: Coordinates, num_points: int = 20
    ) -> list[list[float]]:
        """Generate points along great-circle path."""
        points: list[list[float]] = []
        lat1 = math.radians(origin.latitude)
        lon1 = math.radians(origin.longitude)
        lat2 = math.radians(destination.latitude)
        lon2 = math.radians(destination.longitude)

        d = 2 * math.asin(
            math.sqrt(
                math.sin((lat2 - lat1) / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
            )
        )

        for i in range(num_points + 1):
            f = i / num_points
            if d == 0:
                lat, lon = lat1, lon1
            else:
                A = math.sin((1 - f) * d) / math.sin(d)
                B = math.sin(f * d) / math.sin(d)
                x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
                y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
                z = A * math.sin(lat1) + B * math.sin(lat2)
                lat = math.atan2(z, math.sqrt(x**2 + y**2))
                lon = math.atan2(y, x)
            points.append([math.degrees(lon), math.degrees(lat)])
        return points

    async def _geocode_search(
        self, search_term: str, proximity: Coordinates | None = None
    ) -> list[dict[str, Any]]:
        """Search Mapbox Geocoding API and return results."""
        return await self._geocode_search_with_country(search_term, proximity, None)

    async def _geocode_search_with_country(
        self, search_term: str, proximity: Coordinates | None = None,
        country_code: str | None = None
    ) -> list[dict[str, Any]]:
        """Search Mapbox Geocoding API with optional country filter."""
        if not settings.mapbox_access_token:
            return []

        encoded_term = urllib.parse.quote(search_term)
        url = f"{self.MAPBOX_GEOCODING_URL}/{encoded_term}.json"
        params: dict[str, Any] = {
            "access_token": settings.mapbox_access_token,
            "limit": 5,
        }
        
        if proximity:
            params["proximity"] = f"{proximity.longitude},{proximity.latitude}"
        
        if country_code:
            params["country"] = country_code

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return []
                data = response.json()
            except (httpx.HTTPStatusError, httpx.RequestError):
                return []

        results = []
        for feature in data.get("features", []):
            coords = feature.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                results.append({
                    "name": feature.get("text", "Unknown"),
                    "full_name": feature.get("place_name", ""),
                    "coordinates": Coordinates(latitude=coords[1], longitude=coords[0]),
                    "place_type": feature.get("place_type", []),
                })
        
        return results

    def _is_actual_airport(self, name: str, full_name: str) -> bool:
        """Check if the result is an actual airport, not a road near an airport."""
        name_lower = name.lower()
        full_lower = full_name.lower()
        combined = name_lower + " " + full_lower
        
        # Exclusion patterns - roads, roundabouts, etc.
        exclude_patterns = [
            r"airport\s+road", r"airport\s+rd", r"airport\s+roundabout",
            r"airport\s+street", r"airport\s+st", r"airport\s+drive",
            r"airport\s+avenue", r"airport\s+ave", r"airport\s+lane",
            r"airport\s+boulevard", r"airport\s+blvd", r"airport\s+highway",
            r"airport\s+way", r"airport\s+area",
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, combined):
                return False
        
        # Must match airport patterns
        airport_patterns = [
            r"\bairport\b$",  # Ends with 'airport'
            r"\bairport\s+arrivals?\b",
            r"\bairport\s+departures?\b", 
            r"\bairport\s+terminal\b",
            r"\binternational\s+airport\b",
            r"\bdomestic\s+airport\b",
            r"\baerodrome\b",
            r"\bairfield\b",
        ]
        
        for pattern in airport_patterns:
            if re.search(pattern, name_lower) or re.search(pattern, full_lower):
                return True
        
        return False

    def _find_nearest_known_airport(
        self, location: Coordinates
    ) -> dict[str, Any] | None:
        """Find nearest airport from the known airports database."""
        best_result = None
        best_distance = float('inf')
        
        for (apt_lat, apt_lon), info in self.KNOWN_AIRPORTS.items():
            apt_coords = Coordinates(latitude=apt_lat, longitude=apt_lon)
            distance = self.haversine_distance(location, apt_coords)
            
            if distance <= self.MAX_AIRPORT_DISTANCE and distance < best_distance:
                best_result = {
                    "name": info["name"],
                    "full_name": f"{info['name']}, {info['city']}",
                    "coordinates": apt_coords,
                    "distance_km": distance,
                }
                best_distance = distance
        
        return best_result

    async def _find_nearest_airport(
        self, location: Coordinates, location_name: str
    ) -> dict[str, Any] | None:
        """Find nearest airport using database + Mapbox fallback."""
        
        # First try the known airports database (most reliable)
        known_airport = self._find_nearest_known_airport(location)
        if known_airport and known_airport["distance_km"] < 100:
            return known_airport
        
        # Try Mapbox Geocoding with country filter
        parts = [p.strip() for p in location_name.split(",")]
        city_name = parts[0] if parts else "Unknown"
        country_name = parts[-1].lower() if len(parts) > 1 else ""
        country_code = self.COUNTRY_CODES.get(country_name)
        
        search_queries = [
            f"{city_name} International Airport",
            f"{city_name} Airport",
            "International Airport",
        ]
        
        best_mapbox_result = None
        best_distance = float('inf')
        
        for query in search_queries:
            results = await self._geocode_search_with_country(query, location, country_code)
            
            for result in results:
                if not self._is_actual_airport(result["name"], result["full_name"]):
                    continue
                
                distance = self.haversine_distance(location, result["coordinates"])
                
                if distance <= self.MAX_AIRPORT_DISTANCE and distance < best_distance:
                    best_mapbox_result = result
                    best_distance = distance
                    result["distance_km"] = distance
                    
                    if distance < 50:
                        return best_mapbox_result
        
        # Return the best result (prefer closer one)
        if known_airport and best_mapbox_result:
            if known_airport["distance_km"] <= best_mapbox_result["distance_km"]:
                return known_airport
            return best_mapbox_result
        
        return known_airport or best_mapbox_result

    def _is_actual_port(self, name: str, full_name: str) -> bool:
        """Check if the result is an actual port, not a street near a port."""
        name_lower = name.lower()
        full_lower = full_name.lower()
        combined = name_lower + " " + full_lower
        
        exclude_patterns = [
            r"port\s+road", r"port\s+street", r"port\s+avenue",
            r"port\s+drive", r"port\s+lane", r"port\s+way",
            r"port\s+view", r"port\s+side",
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, combined):
                return False
        
        port_patterns = [
            r"\bport\b$", r"\bport\s+of\b", r"\bseaport\b",
            r"\bharbou?r\b$", r"\bharbou?r\s+terminal\b",
            r"\bcontainer\s+terminal\b", r"\bmaritime\s+terminal\b",
            r"\bwharf\b", r"\bdock\b", r"\bpier\b",
            r"\bjebel\s+ali\b",
        ]
        
        for pattern in port_patterns:
            if re.search(pattern, name_lower) or re.search(pattern, full_lower):
                return True
        
        return False

    def _find_nearest_known_port(
        self, location: Coordinates, max_distance: float
    ) -> dict[str, Any] | None:
        """Find nearest port from the known ports database within max_distance."""
        best_result = None
        best_distance = float('inf')
        
        for (port_lat, port_lon), info in self.KNOWN_PORTS.items():
            port_coords = Coordinates(latitude=port_lat, longitude=port_lon)
            distance = self.haversine_distance(location, port_coords)
            
            if distance <= max_distance and distance < best_distance:
                best_result = {
                    "name": info["name"],
                    "full_name": f"{info['name']}, {info['city']}",
                    "coordinates": port_coords,
                    "distance_km": distance,
                }
                best_distance = distance
        
        return best_result

    async def _find_nearest_port(
        self, location: Coordinates, location_name: str
    ) -> dict[str, Any] | None:
        """Find nearest port using database + Mapbox fallback.
        
        For coastal cities: looks within 200km
        For inland/landlocked cities: looks within 1500km to find nearest major port
        """
        
        # First, try to find a nearby port (coastal city)
        nearby_port = self._find_nearest_known_port(location, self.MAX_PORT_DISTANCE_NEARBY)
        if nearby_port:
            return nearby_port
        
        # Try Mapbox for nearby ports
        parts = [p.strip() for p in location_name.split(",")]
        city_name = parts[0] if parts else "Unknown"
        country_name = parts[-1].lower() if len(parts) > 1 else ""
        country_code = self.COUNTRY_CODES.get(country_name)
        
        search_queries = [
            f"{city_name} Port",
            f"Port of {city_name}",
            f"{city_name} Seaport",
        ]
        
        best_mapbox_result = None
        best_distance = float('inf')
        
        for query in search_queries:
            results = await self._geocode_search_with_country(query, location, country_code)
            
            for result in results:
                if not self._is_actual_port(result["name"], result["full_name"]):
                    continue
                
                distance = self.haversine_distance(location, result["coordinates"])
                
                if distance <= self.MAX_PORT_DISTANCE_NEARBY and distance < best_distance:
                    best_mapbox_result = result
                    best_distance = distance
                    result["distance_km"] = distance
        
        if best_mapbox_result:
            return best_mapbox_result
        
        # No nearby port found - this might be a landlocked city
        # Search for the nearest major port even if it's far (for sea route viability)
        inland_port = self._find_nearest_known_port(location, self.MAX_PORT_DISTANCE_INLAND)
        if inland_port:
            return inland_port
        
        return None

    async def _get_road_route(
        self, origin: Coordinates, destination: Coordinates
    ) -> dict[str, Any] | None:
        """Get road route from Mapbox Directions API."""
        if not settings.mapbox_access_token:
            return None

        coords = f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        url = f"{self.MAPBOX_DIRECTIONS_URL}/driving/{coords}"
        params = {
            "access_token": settings.mapbox_access_token,
            "geometries": "geojson",
            "overview": "full",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return None
                data = response.json()
            except (httpx.HTTPStatusError, httpx.RequestError):
                return None

        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        route = data["routes"][0]
        return {
            "distance_km": route.get("distance", 0) / 1000,
            "duration_hours": route.get("duration", 0) / 3600,
            "geometry": route.get("geometry", {}).get("coordinates", []),
        }

    async def _compute_land_route(
        self, origin: Coordinates, destination: Coordinates, weight_kg: float
    ) -> MultiModalRoute:
        """Compute direct land (road) route."""
        road_route = await self._get_road_route(origin, destination)

        if road_route:
            distance_km = road_route["distance_km"]
            duration_hours = road_route["duration_hours"]
            geometry = road_route["geometry"]
        else:
            direct_distance = self.haversine_distance(origin, destination)
            distance_km = direct_distance * 1.3
            duration_hours = distance_km / self.AVERAGE_SPEEDS[TransportMode.LAND]
            geometry = self._interpolate_great_circle(origin, destination, 20)

        emission = self.emission_service.calculate_emission(
            distance_km, weight_kg, TransportMode.LAND
        )

        segment = RouteSegment(
            mode=TransportMode.LAND,
            from_name="Origin",
            from_coordinates=origin,
            to_name="Destination",
            to_coordinates=destination,
            distance_km=round(distance_km, 2),
            duration_hours=round(duration_hours, 2),
            emission_kg_co2=emission.emission_kg_co2,
            geometry=geometry,
        )

        return MultiModalRoute(
            segments=[segment],
            total_distance_km=round(distance_km, 2),
            total_duration_hours=round(duration_hours, 2),
            total_emission_kg_co2=emission.emission_kg_co2,
            transport_mode=TransportMode.LAND,
            is_viable=True,
            waypoints=[],
        )

    async def _compute_air_route(
        self, origin: Coordinates, destination: Coordinates, weight_kg: float,
        origin_name: str, destination_name: str
    ) -> MultiModalRoute:
        """Compute air route: road → airport → flight → airport → road."""
        
        origin_airport = await self._find_nearest_airport(origin, origin_name)
        dest_airport = await self._find_nearest_airport(destination, destination_name)

        origin_city = origin_name.split(",")[0]
        dest_city = destination_name.split(",")[0]

        if not origin_airport:
            return MultiModalRoute(
                segments=[],
                total_distance_km=0,
                total_duration_hours=0,
                total_emission_kg_co2=0,
                transport_mode=TransportMode.AIR,
                is_viable=False,
                waypoints=[],
                not_viable_reason=f"No airport found near {origin_city}",
            )

        if not dest_airport:
            return MultiModalRoute(
                segments=[],
                total_distance_km=0,
                total_duration_hours=0,
                total_emission_kg_co2=0,
                transport_mode=TransportMode.AIR,
                is_viable=False,
                waypoints=[],
                not_viable_reason=f"No airport found near {dest_city}",
            )

        flight_distance = self.haversine_distance(
            origin_airport["coordinates"], dest_airport["coordinates"]
        )

        if flight_distance < self.MIN_FLIGHT_DISTANCE:
            return MultiModalRoute(
                segments=[],
                total_distance_km=0,
                total_duration_hours=0,
                total_emission_kg_co2=0,
                transport_mode=TransportMode.AIR,
                is_viable=False,
                waypoints=[],
                not_viable_reason=f"Flight distance ({flight_distance:.0f}km) too short",
            )

        segments = []
        waypoints = []
        total_distance = 0
        total_duration = 0
        total_emission = 0

        # Segment 1: Road to origin airport
        road1 = await self._get_road_route(origin, origin_airport["coordinates"])
        if road1:
            road1_distance = road1["distance_km"]
            road1_duration = road1["duration_hours"]
            road1_geometry = road1["geometry"]
        else:
            road1_distance = origin_airport["distance_km"] * 1.3
            road1_duration = road1_distance / self.AVERAGE_SPEEDS[TransportMode.LAND]
            road1_geometry = self._interpolate_great_circle(
                origin, origin_airport["coordinates"], 10
            )

        road1_emission = self.emission_service.calculate_emission(
            road1_distance, weight_kg, TransportMode.LAND
        )

        segments.append(RouteSegment(
            mode=TransportMode.LAND,
            from_name=origin_city,
            from_coordinates=origin,
            to_name=origin_airport["name"],
            to_coordinates=origin_airport["coordinates"],
            distance_km=round(road1_distance, 2),
            duration_hours=round(road1_duration, 2),
            emission_kg_co2=road1_emission.emission_kg_co2,
            geometry=road1_geometry,
        ))
        
        waypoints.append({
            "name": origin_airport["name"],
            "type": "airport",
            "coordinates": origin_airport["coordinates"],
        })

        total_distance += road1_distance
        total_duration += road1_duration
        total_emission += road1_emission.emission_kg_co2

        # Segment 2: Flight
        flight_duration = flight_distance / self.AVERAGE_SPEEDS[TransportMode.AIR]
        flight_duration += 1.5

        flight_emission = self.emission_service.calculate_emission(
            flight_distance, weight_kg, TransportMode.AIR
        )

        flight_geometry = self._interpolate_great_circle(
            origin_airport["coordinates"], dest_airport["coordinates"], 30
        )

        segments.append(RouteSegment(
            mode=TransportMode.AIR,
            from_name=origin_airport["name"],
            from_coordinates=origin_airport["coordinates"],
            to_name=dest_airport["name"],
            to_coordinates=dest_airport["coordinates"],
            distance_km=round(flight_distance, 2),
            duration_hours=round(flight_duration, 2),
            emission_kg_co2=flight_emission.emission_kg_co2,
            geometry=flight_geometry,
        ))

        waypoints.append({
            "name": dest_airport["name"],
            "type": "airport",
            "coordinates": dest_airport["coordinates"],
        })

        total_distance += flight_distance
        total_duration += flight_duration
        total_emission += flight_emission.emission_kg_co2

        # Segment 3: Road from destination airport
        road2 = await self._get_road_route(dest_airport["coordinates"], destination)
        if road2:
            road2_distance = road2["distance_km"]
            road2_duration = road2["duration_hours"]
            road2_geometry = road2["geometry"]
        else:
            road2_distance = dest_airport["distance_km"] * 1.3
            road2_duration = road2_distance / self.AVERAGE_SPEEDS[TransportMode.LAND]
            road2_geometry = self._interpolate_great_circle(
                dest_airport["coordinates"], destination, 10
            )

        road2_emission = self.emission_service.calculate_emission(
            road2_distance, weight_kg, TransportMode.LAND
        )

        segments.append(RouteSegment(
            mode=TransportMode.LAND,
            from_name=dest_airport["name"],
            from_coordinates=dest_airport["coordinates"],
            to_name=dest_city,
            to_coordinates=destination,
            distance_km=round(road2_distance, 2),
            duration_hours=round(road2_duration, 2),
            emission_kg_co2=road2_emission.emission_kg_co2,
            geometry=road2_geometry,
        ))

        total_distance += road2_distance
        total_duration += road2_duration
        total_emission += road2_emission.emission_kg_co2

        return MultiModalRoute(
            segments=segments,
            total_distance_km=round(total_distance, 2),
            total_duration_hours=round(total_duration, 2),
            total_emission_kg_co2=round(total_emission, 4),
            transport_mode=TransportMode.AIR,
            is_viable=True,
            waypoints=waypoints,
        )

    async def _compute_sea_route(
        self, origin: Coordinates, destination: Coordinates, weight_kg: float,
        origin_name: str, destination_name: str
    ) -> MultiModalRoute:
        """Compute sea route: road → port → shipping → port → road."""
        
        origin_port = await self._find_nearest_port(origin, origin_name)
        dest_port = await self._find_nearest_port(destination, destination_name)

        origin_city = origin_name.split(",")[0]
        dest_city = destination_name.split(",")[0]

        if not origin_port:
            return MultiModalRoute(
                segments=[],
                total_distance_km=0,
                total_duration_hours=0,
                total_emission_kg_co2=0,
                transport_mode=TransportMode.SEA,
                is_viable=False,
                waypoints=[],
                not_viable_reason=f"No port found near {origin_city}",
            )

        if not dest_port:
            return MultiModalRoute(
                segments=[],
                total_distance_km=0,
                total_duration_hours=0,
                total_emission_kg_co2=0,
                transport_mode=TransportMode.SEA,
                is_viable=False,
                waypoints=[],
                not_viable_reason=f"No port found near {dest_city}",
            )

        shipping_distance = self.haversine_distance(
            origin_port["coordinates"], dest_port["coordinates"]
        ) * 1.3

        segments = []
        waypoints = []
        total_distance = 0
        total_duration = 0
        total_emission = 0

        # Segment 1: Road to origin port
        road1 = await self._get_road_route(origin, origin_port["coordinates"])
        if road1:
            road1_distance = road1["distance_km"]
            road1_duration = road1["duration_hours"]
            road1_geometry = road1["geometry"]
        else:
            road1_distance = origin_port["distance_km"] * 1.3
            road1_duration = road1_distance / self.AVERAGE_SPEEDS[TransportMode.LAND]
            road1_geometry = self._interpolate_great_circle(
                origin, origin_port["coordinates"], 10
            )

        road1_emission = self.emission_service.calculate_emission(
            road1_distance, weight_kg, TransportMode.LAND
        )

        segments.append(RouteSegment(
            mode=TransportMode.LAND,
            from_name=origin_city,
            from_coordinates=origin,
            to_name=origin_port["name"],
            to_coordinates=origin_port["coordinates"],
            distance_km=round(road1_distance, 2),
            duration_hours=round(road1_duration, 2),
            emission_kg_co2=road1_emission.emission_kg_co2,
            geometry=road1_geometry,
        ))

        waypoints.append({
            "name": origin_port["name"],
            "type": "port",
            "coordinates": origin_port["coordinates"],
        })

        total_distance += road1_distance
        total_duration += road1_duration
        total_emission += road1_emission.emission_kg_co2

        # Segment 2: Shipping
        shipping_duration = shipping_distance / self.AVERAGE_SPEEDS[TransportMode.SEA]
        shipping_duration += 24

        shipping_emission = self.emission_service.calculate_emission(
            shipping_distance, weight_kg, TransportMode.SEA
        )

        shipping_geometry = self._interpolate_great_circle(
            origin_port["coordinates"], dest_port["coordinates"], 40
        )

        segments.append(RouteSegment(
            mode=TransportMode.SEA,
            from_name=origin_port["name"],
            from_coordinates=origin_port["coordinates"],
            to_name=dest_port["name"],
            to_coordinates=dest_port["coordinates"],
            distance_km=round(shipping_distance, 2),
            duration_hours=round(shipping_duration, 2),
            emission_kg_co2=shipping_emission.emission_kg_co2,
            geometry=shipping_geometry,
        ))

        waypoints.append({
            "name": dest_port["name"],
            "type": "port",
            "coordinates": dest_port["coordinates"],
        })

        total_distance += shipping_distance
        total_duration += shipping_duration
        total_emission += shipping_emission.emission_kg_co2

        # Segment 3: Road from destination port
        road2 = await self._get_road_route(dest_port["coordinates"], destination)
        if road2:
            road2_distance = road2["distance_km"]
            road2_duration = road2["duration_hours"]
            road2_geometry = road2["geometry"]
        else:
            road2_distance = dest_port["distance_km"] * 1.3
            road2_duration = road2_distance / self.AVERAGE_SPEEDS[TransportMode.LAND]
            road2_geometry = self._interpolate_great_circle(
                dest_port["coordinates"], destination, 10
            )

        road2_emission = self.emission_service.calculate_emission(
            road2_distance, weight_kg, TransportMode.LAND
        )

        segments.append(RouteSegment(
            mode=TransportMode.LAND,
            from_name=dest_port["name"],
            from_coordinates=dest_port["coordinates"],
            to_name=dest_city,
            to_coordinates=destination,
            distance_km=round(road2_distance, 2),
            duration_hours=round(road2_duration, 2),
            emission_kg_co2=road2_emission.emission_kg_co2,
            geometry=road2_geometry,
        ))

        total_distance += road2_distance
        total_duration += road2_duration
        total_emission += road2_emission.emission_kg_co2

        return MultiModalRoute(
            segments=segments,
            total_distance_km=round(total_distance, 2),
            total_duration_hours=round(total_duration, 2),
            total_emission_kg_co2=round(total_emission, 4),
            transport_mode=TransportMode.SEA,
            is_viable=True,
            waypoints=waypoints,
        )

    async def compute_all_routes(
        self, origin: Coordinates, destination: Coordinates, weight_kg: float,
        origin_name: str = "Origin", destination_name: str = "Destination"
    ) -> tuple[RouteInfo, RouteInfo, list[ModeComparison], list[MultiModalRoute]]:
        """Compute all viable multi-modal routes and return best options."""

        land_route = await self._compute_land_route(origin, destination, weight_kg)
        air_route = await self._compute_air_route(
            origin, destination, weight_kg, origin_name, destination_name
        )
        sea_route = await self._compute_sea_route(
            origin, destination, weight_kg, origin_name, destination_name
        )

        all_routes = [land_route, air_route, sea_route]
        viable_routes = [r for r in all_routes if r.is_viable]

        if not viable_routes:
            viable_routes = [land_route]

        shortest = min(viable_routes, key=lambda r: r.total_distance_km)
        efficient = min(viable_routes, key=lambda r: r.total_emission_kg_co2)

        def combine_geometries(route: MultiModalRoute) -> list[list[float]]:
            all_coords = []
            for segment in route.segments:
                all_coords.extend(segment.geometry)
            return all_coords

        shortest_route = RouteInfo(
            distance_km=shortest.total_distance_km,
            duration_hours=shortest.total_duration_hours,
            geometry=combine_geometries(shortest),
            emission_kg_co2=shortest.total_emission_kg_co2,
            route_type="shortest",
            transport_mode=shortest.transport_mode,
        )

        efficient_route = RouteInfo(
            distance_km=efficient.total_distance_km,
            duration_hours=efficient.total_duration_hours,
            geometry=combine_geometries(efficient),
            emission_kg_co2=efficient.total_emission_kg_co2,
            route_type="efficient",
            transport_mode=efficient.transport_mode,
        )

        mode_comparison = []
        for route in all_routes:
            comparison = ModeComparison(
                transport_mode=route.transport_mode,
                distance_km=route.total_distance_km,
                duration_hours=route.total_duration_hours,
                emission_kg_co2=route.total_emission_kg_co2,
                is_shortest=route.transport_mode == shortest.transport_mode,
                is_most_efficient=route.transport_mode == efficient.transport_mode,
                is_viable=route.is_viable,
                not_viable_reason=route.not_viable_reason,
            )
            mode_comparison.append(comparison)

        return shortest_route, efficient_route, mode_comparison, all_routes
