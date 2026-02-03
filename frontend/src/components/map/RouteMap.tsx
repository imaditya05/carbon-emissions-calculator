import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Map, Plane, Ship, Truck } from 'lucide-react';
import { getMapboxToken, getBounds } from '../../lib/mapbox';
import type { RouteResponse, TransportMode } from '../../types';

interface RouteMapProps {
  routeResult: RouteResponse | null;
}

// Colors for different modes
const MODE_COLORS: Record<TransportMode, string> = {
  land: '#f97316', // Orange for road
  air: '#8b5cf6',  // Purple for air
  sea: '#0ea5e9',  // Cyan for sea
};

export function RouteMap({ routeResult }: RouteMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [activeRoute, setActiveRoute] = useState<'efficient' | 'shortest'>('efficient');

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const token = getMapboxToken();
    if (!token) {
      console.error('Mapbox token not found');
      return;
    }

    mapboxgl.accessToken = token;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [0, 20],
      zoom: 1.5,
      projection: 'mercator',
    });

    map.current.addControl(
      new mapboxgl.NavigationControl({ showCompass: false }),
      'top-right'
    );

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Remove existing layers and sources
    const existingLayers = map.current.getStyle()?.layers || [];
    existingLayers.forEach((layer) => {
      if (layer.id.startsWith('route-segment-') || layer.id.startsWith('route-glow-')) {
        map.current?.removeLayer(layer.id);
      }
    });

    const existingSources = Object.keys(map.current.getStyle()?.sources || {});
    existingSources.forEach((source) => {
      if (source.startsWith('route-segment-')) {
        map.current?.removeSource(source);
      }
    });

    if (!routeResult) {
      map.current.flyTo({ center: [0, 20], zoom: 1.5, duration: 1000 });
      return;
    }

    const { origin_coordinates, destination_coordinates, detailed_routes } = routeResult;

    // Find the active detailed route
    const activeDetailedRoute = detailed_routes.find(
      (r) => r.transport_mode === (activeRoute === 'efficient' 
        ? routeResult.efficient_route.transport_mode 
        : routeResult.shortest_route.transport_mode)
    );

    if (activeDetailedRoute && activeDetailedRoute.segments.length > 0) {
      // Draw each segment with different styles
      activeDetailedRoute.segments.forEach((segment, index) => {
        const sourceId = `route-segment-${index}`;
        const layerId = `route-segment-${index}`;
        const glowLayerId = `route-glow-${index}`;

        map.current!.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates: segment.geometry,
            },
          },
        });

        // Glow effect
        map.current!.addLayer({
          id: glowLayerId,
          type: 'line',
          source: sourceId,
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': MODE_COLORS[segment.mode],
            'line-width': 10,
            'line-opacity': 0.2,
            'line-blur': 4,
          },
        });

        // Main line - dashed for air/sea, solid for land
        const isDashed = segment.mode === 'air' || segment.mode === 'sea';
        map.current!.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': MODE_COLORS[segment.mode],
            'line-width': segment.mode === 'land' ? 4 : 3,
            'line-opacity': 0.9,
            ...(isDashed ? { 'line-dasharray': [2, 1] } : {}),
          },
        });
      });

      // Add waypoint markers (airports/ports)
      activeDetailedRoute.waypoints.forEach((waypoint) => {
        const el = document.createElement('div');
        el.className = 'waypoint-marker';
        
        const isAirport = waypoint.type === 'airport';
        const bgColor = isAirport ? '#8b5cf6' : '#0ea5e9';
        
        el.innerHTML = `
          <div style="
            width: 32px;
            height: 32px;
            background: ${bgColor};
            border: 3px solid white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
              ${isAirport 
                ? '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>'
                : '<path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76"/><path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"/><path d="M12 10v4"/><path d="M12 2v3"/>'
              }
            </svg>
          </div>
        `;

        const marker = new mapboxgl.Marker({ element: el })
          .setLngLat([waypoint.coordinates.longitude, waypoint.coordinates.latitude])
          .setPopup(
            new mapboxgl.Popup({ offset: 25, closeButton: false }).setHTML(
              `<div style="font-weight: 600; color: ${bgColor};">${isAirport ? '✈️ Airport' : '⚓ Port'}</div>
               <div style="font-size: 13px; color: #666;">${waypoint.name}</div>`
            )
          )
          .addTo(map.current!);
        markersRef.current.push(marker);
      });
    }

    // Origin marker (green)
    const originEl = document.createElement('div');
    originEl.innerHTML = `
      <div style="
        width: 28px;
        height: 28px;
        background: #22c55e;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      "></div>
    `;
    const originMarker = new mapboxgl.Marker({ element: originEl })
      .setLngLat([origin_coordinates.longitude, origin_coordinates.latitude])
      .setPopup(
        new mapboxgl.Popup({ offset: 25, closeButton: false }).setHTML(
          `<div style="font-weight: 600; color: #22c55e;">📍 Origin</div>
           <div style="font-size: 13px; color: #666;">${routeResult.origin_name}</div>`
        )
      )
      .addTo(map.current);
    markersRef.current.push(originMarker);

    // Destination marker (red)
    const destEl = document.createElement('div');
    destEl.innerHTML = `
      <div style="
        width: 28px;
        height: 28px;
        background: #ef4444;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      "></div>
    `;
    const destMarker = new mapboxgl.Marker({ element: destEl })
      .setLngLat([destination_coordinates.longitude, destination_coordinates.latitude])
      .setPopup(
        new mapboxgl.Popup({ offset: 25, closeButton: false }).setHTML(
          `<div style="font-weight: 600; color: #ef4444;">📍 Destination</div>
           <div style="font-size: 13px; color: #666;">${routeResult.destination_name}</div>`
        )
      )
      .addTo(map.current);
    markersRef.current.push(destMarker);

    // Fit bounds
    const bounds = getBounds([origin_coordinates, destination_coordinates]);
    map.current.fitBounds(bounds, {
      padding: { top: 100, bottom: 100, left: 100, right: 100 },
      duration: 1000,
    });
  }, [routeResult, mapLoaded, activeRoute]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Placeholder when no route */}
      {!routeResult && (
        <div className="absolute inset-0 bg-gradient-to-br from-[#1a4d2e] via-[#2d5a3d] to-[#1e5245] flex flex-col items-center justify-center pointer-events-none">
          <div
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage: `
                linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px',
            }}
          />
          <div className="text-center z-10">
            <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Map className="w-8 h-8 text-white/60" strokeWidth={1.5} />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Route Visualization</h3>
            <p className="text-white/50 text-sm max-w-xs">
              Enter origin and destination to see multi-modal routes
            </p>
          </div>
        </div>
      )}

      {/* Route toggle */}
      {routeResult && routeResult.shortest_route.transport_mode !== routeResult.efficient_route.transport_mode && (
        <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200 p-2">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveRoute('efficient')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1.5 ${
                activeRoute === 'efficient'
                  ? 'bg-green-500 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              🌱 Eco-Efficient
            </button>
            <button
              onClick={() => setActiveRoute('shortest')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1.5 ${
                activeRoute === 'shortest'
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              ⚡ Shortest
            </button>
          </div>
        </div>
      )}

      {/* Legend */}
      {routeResult && (
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200 p-3">
          <div className="text-xs font-medium text-gray-500 mb-2">ROUTE LEGEND</div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2.5">
              <div className="w-5 h-1 rounded-full" style={{ backgroundColor: '#f97316' }} />
              <Truck className="w-3.5 h-3.5" style={{ color: '#f97316' }} />
              <span className="text-gray-700">Road</span>
            </div>
            <div className="flex items-center gap-2.5">
              <svg width="20" height="4" className="flex-shrink-0">
                <line x1="0" y1="2" x2="20" y2="2" stroke="#8b5cf6" strokeWidth="2" strokeDasharray="4 2" />
              </svg>
              <Plane className="w-3.5 h-3.5" style={{ color: '#8b5cf6' }} />
              <span className="text-gray-700">Air</span>
            </div>
            <div className="flex items-center gap-2.5">
              <svg width="20" height="4" className="flex-shrink-0">
                <line x1="0" y1="2" x2="20" y2="2" stroke="#0ea5e9" strokeWidth="2" strokeDasharray="4 2" />
              </svg>
              <Ship className="w-3.5 h-3.5" style={{ color: '#0ea5e9' }} />
              <span className="text-gray-700">Sea</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
