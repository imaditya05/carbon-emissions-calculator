// Coordinates type
export interface Coordinates {
  latitude: number;
  longitude: number;
}

// Transport modes
export type TransportMode = 'land' | 'sea' | 'air';

// A single segment of a multi-modal route
export interface RouteSegment {
  mode: TransportMode;
  from_name: string;
  from_coordinates: Coordinates;
  to_name: string;
  to_coordinates: Coordinates;
  distance_km: number;
  duration_hours: number;
  emission_kg_co2: number;
  geometry: [number, number][]; // [longitude, latitude][]
}

// Waypoint in a multi-modal route
export interface Waypoint {
  name: string;
  type: 'airport' | 'port';
  coordinates: Coordinates;
}

// Complete multi-modal route with segments
export interface MultiModalRoute {
  segments: RouteSegment[];
  total_distance_km: number;
  total_duration_hours: number;
  total_emission_kg_co2: number;
  transport_mode: TransportMode;
  is_viable: boolean;
  waypoints: Waypoint[];
  not_viable_reason?: string;
}

// Route summary information
export interface RouteInfo {
  distance_km: number;
  duration_hours: number | null;
  geometry: [number, number][]; // [longitude, latitude][]
  emission_kg_co2: number;
  route_type: 'shortest' | 'efficient';
  transport_mode: TransportMode;
}

// Mode comparison data
export interface ModeComparison {
  transport_mode: TransportMode;
  distance_km: number;
  duration_hours: number;
  emission_kg_co2: number;
  is_shortest: boolean;
  is_most_efficient: boolean;
  is_viable: boolean;
  not_viable_reason?: string;
}

// Route request
export interface RouteRequest {
  origin_name: string;
  origin_coordinates: Coordinates;
  destination_name: string;
  destination_coordinates: Coordinates;
  weight_kg: number;
}

// Route response
export interface RouteResponse {
  origin_name: string;
  origin_coordinates: Coordinates;
  destination_name: string;
  destination_coordinates: Coordinates;
  weight_kg: number;
  shortest_route: RouteInfo;
  efficient_route: RouteInfo;
  mode_comparison: ModeComparison[];
  detailed_routes: MultiModalRoute[];
}

// Search history item
export interface SearchItem {
  id: string;
  origin_name: string;
  origin_coordinates: Coordinates;
  destination_name: string;
  destination_coordinates: Coordinates;
  weight_kg: number;
  shortest_route: RouteInfo;
  efficient_route: RouteInfo;
  mode_comparison: ModeComparison[];
  created_at: string;
}

// Pagination metadata
export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Paginated search response
export interface SearchListResponse {
  items: SearchItem[];
  pagination: PaginationMeta;
}

// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// API Error
export interface ApiError {
  detail: string;
}

// Location suggestion from Mapbox Geocoding
export interface LocationSuggestion {
  id: string;
  place_name: string;
  coordinates: Coordinates;
}
