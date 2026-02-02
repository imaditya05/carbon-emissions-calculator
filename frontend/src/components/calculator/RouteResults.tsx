import { Route, Leaf, Gauge, ArrowRight, Truck, Ship, Plane, Check, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { RouteResponse, TransportMode, MultiModalRoute } from '../../types';

interface RouteResultsProps {
  result: RouteResponse;
}

const getModeIcon = (mode: TransportMode) => {
  switch (mode) {
    case 'land': return <Truck className="h-4 w-4" />;
    case 'sea': return <Ship className="h-4 w-4" />;
    case 'air': return <Plane className="h-4 w-4" />;
  }
};

const getModeLabel = (mode: TransportMode) => {
  switch (mode) {
    case 'land': return 'Land (Truck)';
    case 'sea': return 'Sea (Ship)';
    case 'air': return 'Air (Cargo)';
  }
};

const getModeColor = (mode: TransportMode) => {
  switch (mode) {
    case 'land': return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'sea': return 'text-cyan-600 bg-cyan-50 border-cyan-200';
    case 'air': return 'text-purple-600 bg-purple-50 border-purple-200';
  }
};

const formatDuration = (hours: number | null) => {
  if (!hours) return 'N/A';
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 24) return `${hours.toFixed(1)} hrs`;
  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);
  return `${days}d ${remainingHours}h`;
};

const formatNumber = (num: number) => num.toLocaleString(undefined, { maximumFractionDigits: 0 });

function RouteSegments({ route }: { route: MultiModalRoute }) {
  const [expanded, setExpanded] = useState(false);

  if (!route.segments || route.segments.length === 0) return null;

  return (
    <div className="mt-3 border-t border-border/50 pt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full"
      >
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        <span>Route Details ({route.segments.length} segments)</span>
      </button>
      
      {expanded && (
        <div className="mt-3 space-y-2">
          {route.segments.map((segment, index) => (
            <div
              key={index}
              className={`p-2.5 rounded-md border ${getModeColor(segment.mode)}`}
            >
              <div className="flex items-center gap-2 mb-1">
                {getModeIcon(segment.mode)}
                <span className="font-medium text-sm capitalize">{segment.mode}</span>
                <span className="text-xs opacity-70">
                  {formatNumber(segment.distance_km)} km · {formatDuration(segment.duration_hours)}
                </span>
              </div>
              <div className="text-xs flex items-center gap-1">
                <span className="truncate max-w-[120px]">{segment.from_name}</span>
                <ArrowRight className="h-3 w-3 flex-shrink-0" />
                <span className="truncate max-w-[120px]">{segment.to_name}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function RouteResults({ result }: RouteResultsProps) {
  const { shortest_route, efficient_route, mode_comparison, detailed_routes } = result;

  const emissionsSaved = shortest_route.emission_kg_co2 - efficient_route.emission_kg_co2;
  const percentSaved = emissionsSaved > 0 
    ? ((emissionsSaved / shortest_route.emission_kg_co2) * 100).toFixed(1) 
    : '0';

  // Find detailed routes for display
  const efficientDetailed = detailed_routes.find(
    r => r.transport_mode === efficient_route.transport_mode && r.is_viable
  );
  const shortestDetailed = detailed_routes.find(
    r => r.transport_mode === shortest_route.transport_mode && r.is_viable
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Route className="h-5 w-5 text-primary" />
          Route Comparison
        </CardTitle>
        <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
          <span className="font-medium text-foreground">{result.origin_name}</span>
          <ArrowRight className="h-3 w-3" />
          <span className="font-medium text-foreground">{result.destination_name}</span>
          <span className="mx-1">|</span>
          <span>{formatNumber(result.weight_kg)} kg</span>
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Shortest Route */}
        <div className="p-4 rounded-lg bg-blue-50 border border-blue-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-700 flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Shortest Route
            </span>
            <Badge className="bg-blue-100 text-blue-700 border-blue-200 flex items-center gap-1">
              {getModeIcon(shortest_route.transport_mode)}
              {getModeLabel(shortest_route.transport_mode)}
            </Badge>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <p className="text-xs text-blue-600">Distance</p>
              <p className="text-lg font-semibold text-blue-900">
                {formatNumber(shortest_route.distance_km)} km
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-600">Duration</p>
              <p className="text-lg font-semibold text-blue-900">
                {formatDuration(shortest_route.duration_hours)}
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-600">CO₂ Emissions</p>
              <p className="text-lg font-semibold text-blue-900">
                {formatNumber(shortest_route.emission_kg_co2)} kg
              </p>
            </div>
          </div>
          {shortestDetailed && <RouteSegments route={shortestDetailed} />}
        </div>

        {/* Efficient Route */}
        <div className="p-4 rounded-lg bg-green-50 border border-green-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-green-700 flex items-center gap-2">
              <Leaf className="h-4 w-4" />
              Eco-Efficient Route
            </span>
            <Badge className="bg-green-100 text-green-700 border-green-200 flex items-center gap-1">
              {getModeIcon(efficient_route.transport_mode)}
              {getModeLabel(efficient_route.transport_mode)}
            </Badge>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <p className="text-xs text-green-600">Distance</p>
              <p className="text-lg font-semibold text-green-900">
                {formatNumber(efficient_route.distance_km)} km
              </p>
            </div>
            <div>
              <p className="text-xs text-green-600">Duration</p>
              <p className="text-lg font-semibold text-green-900">
                {formatDuration(efficient_route.duration_hours)}
              </p>
            </div>
            <div>
              <p className="text-xs text-green-600">CO₂ Emissions</p>
              <p className="text-lg font-semibold text-green-900">
                {formatNumber(efficient_route.emission_kg_co2)} kg
              </p>
            </div>
          </div>
          {efficientDetailed && <RouteSegments route={efficientDetailed} />}
        </div>

        {/* CO2 Savings */}
        {emissionsSaved > 0 && (
          <div className="p-3 rounded-lg bg-primary/5 border border-primary/10 text-center">
            <p className="text-sm text-muted-foreground">
              By choosing the eco-efficient route, you save
            </p>
            <p className="text-xl font-bold text-primary">
              {formatNumber(emissionsSaved)} kg CO₂ ({percentSaved}%)
            </p>
          </div>
        )}

        {/* Mode Comparison Table */}
        {mode_comparison && mode_comparison.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium text-foreground mb-3">Transport Mode Analysis</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-2 font-medium text-muted-foreground">Mode</th>
                    <th className="text-right py-2 px-2 font-medium text-muted-foreground">Distance</th>
                    <th className="text-right py-2 px-2 font-medium text-muted-foreground">Duration</th>
                    <th className="text-right py-2 px-2 font-medium text-muted-foreground">CO₂</th>
                    <th className="text-center py-2 px-2 font-medium text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {mode_comparison.map((mode) => (
                    <tr 
                      key={mode.transport_mode} 
                      className={`border-b border-border/50 ${
                        !mode.is_viable 
                          ? 'opacity-50' 
                          : mode.is_shortest || mode.is_most_efficient 
                            ? 'bg-muted/30' 
                            : ''
                      }`}
                    >
                      <td className="py-2.5 px-2">
                        <span className="flex items-center gap-2">
                          {getModeIcon(mode.transport_mode)}
                          <span className="capitalize">{mode.transport_mode}</span>
                        </span>
                      </td>
                      <td className="text-right py-2.5 px-2">
                        {mode.is_viable ? `${formatNumber(mode.distance_km)} km` : '-'}
                      </td>
                      <td className="text-right py-2.5 px-2">
                        {mode.is_viable ? formatDuration(mode.duration_hours) : '-'}
                      </td>
                      <td className="text-right py-2.5 px-2">
                        {mode.is_viable ? `${formatNumber(mode.emission_kg_co2)} kg` : '-'}
                      </td>
                      <td className="text-center py-2.5 px-2">
                        <div className="flex items-center justify-center gap-1 flex-wrap">
                          {!mode.is_viable ? (
                            <span className="inline-flex items-center gap-0.5 text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded" title={mode.not_viable_reason || ''}>
                              <AlertCircle className="h-3 w-3" />
                              N/A
                            </span>
                          ) : (
                            <>
                              {mode.is_shortest && (
                                <span className="inline-flex items-center gap-0.5 text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                                  <Check className="h-3 w-3" />
                                  Shortest
                                </span>
                              )}
                              {mode.is_most_efficient && (
                                <span className="inline-flex items-center gap-0.5 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                                  <Leaf className="h-3 w-3" />
                                  Eco
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Show reasons for non-viable modes */}
            {mode_comparison.some(m => !m.is_viable && m.not_viable_reason) && (
              <div className="mt-3 space-y-1">
                {mode_comparison
                  .filter(m => !m.is_viable && m.not_viable_reason)
                  .map(m => (
                    <p key={m.transport_mode} className="text-xs text-muted-foreground italic flex items-start gap-1">
                      <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                      <span>
                        <strong className="capitalize">{m.transport_mode}</strong>: {m.not_viable_reason}
                      </span>
                    </p>
                  ))
                }
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
