import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Truck,
  Ship,
  Plane,
  MapPin,
  ArrowRight,
  Leaf,
  Search,
  Gauge,
  Filter,
  X,
} from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { searchApi } from '../lib/api';
import type { SearchItem, SearchListResponse, TransportMode } from '../types';

const getModeIcon = (mode: TransportMode) => {
  switch (mode) {
    case 'land': return Truck;
    case 'sea': return Ship;
    case 'air': return Plane;
  }
};

export function HistoryPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<SearchListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  
  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [modeFilter, setModeFilter] = useState<TransportMode | ''>('');

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const result = await searchApi.getAll({
        page,
        page_size: 10,
        origin_name: searchQuery || undefined,
        shortest_mode: modeFilter || undefined,
      });
      setData(result);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, modeFilter]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1); // Reset to first page when searching
      fetchHistory();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this search?')) return;

    try {
      await searchApi.delete(id);
      fetchHistory();
    } catch (error) {
      console.error('Failed to delete search:', error);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to delete all search history?')) return;

    try {
      await searchApi.deleteAll();
      fetchHistory();
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setModeFilter('');
    setPage(1);
  };

  const hasActiveFilters = searchQuery || modeFilter;

  const formatDate = (dateString: string) => {
    const utcDateString = dateString.endsWith('Z') || dateString.includes('+') 
      ? dateString 
      : dateString + 'Z';
    
    const date = new Date(utcDateString);
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatNumber = (num: number) => num.toLocaleString(undefined, { maximumFractionDigits: 0 });

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <History className="h-6 w-6 text-primary" />
              Search History
            </h1>
            <p className="text-muted-foreground mt-1">
              {data?.pagination.total || 0} searches saved
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button 
              variant={showFilters ? "default" : "outline"} 
              size="sm" 
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4" />
              Filters
              {hasActiveFilters && (
                <span className="ml-1 w-2 h-2 bg-primary rounded-full" />
              )}
            </Button>
            {data && data.items.length > 0 && (
              <Button variant="outline" size="sm" onClick={handleClearAll}>
                <Trash2 className="h-4 w-4" />
                Clear All
              </Button>
            )}
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <Card className="mb-6">
            <CardContent className="pt-4">
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Search Input */}
                <div className="flex-1">
                  <label className="text-sm font-medium text-muted-foreground mb-1.5 block">
                    Search by location
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search origin or destination..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 text-sm border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                  </div>
                </div>

                {/* Mode Filter */}
                <div className="sm:w-48">
                  <label className="text-sm font-medium text-muted-foreground mb-1.5 block">
                    Transport mode
                  </label>
                  <select
                    value={modeFilter}
                    onChange={(e) => {
                      setModeFilter(e.target.value as TransportMode | '');
                      setPage(1);
                    }}
                    className="w-full px-3 py-2 text-sm border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  >
                    <option value="">All modes</option>
                    <option value="land">🚛 Land</option>
                    <option value="air">✈️ Air</option>
                    <option value="sea">🚢 Sea</option>
                  </select>
                </div>

                {/* Clear Filters */}
                {hasActiveFilters && (
                  <div className="flex items-end">
                    <Button variant="ghost" size="sm" onClick={clearFilters}>
                      <X className="h-4 w-4 mr-1" />
                      Clear
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Active Filters Display */}
        {hasActiveFilters && !showFilters && (
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <span className="text-sm text-muted-foreground">Active filters:</span>
            {searchQuery && (
              <Badge variant="secondary" className="flex items-center gap-1">
                Search: {searchQuery}
                <button onClick={() => setSearchQuery('')} className="ml-1 hover:text-destructive">
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
            {modeFilter && (
              <Badge variant="secondary" className="flex items-center gap-1 capitalize">
                Mode: {modeFilter}
                <button onClick={() => setModeFilter('')} className="ml-1 hover:text-destructive">
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
          </div>
        )}

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <div className="space-y-4">
              {data.items.map((item: SearchItem) => {
                const ShortestIcon = getModeIcon(item.shortest_route.transport_mode);
                const EfficientIcon = getModeIcon(item.efficient_route.transport_mode);

                return (
                  <Card key={item.id} className="group">
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-base flex items-center gap-2 flex-wrap">
                            <MapPin className="h-3 w-3 text-primary shrink-0" />
                            <span className="truncate max-w-[200px]">{item.origin_name}</span>
                            <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                            <MapPin className="h-3 w-3 text-destructive shrink-0" />
                            <span className="truncate max-w-[200px]">{item.destination_name}</span>
                          </CardTitle>
                          <CardDescription className="mt-1">
                            {formatDate(item.created_at)} · {formatNumber(item.weight_kg)} kg cargo
                          </CardDescription>
                        </div>

                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(item.id)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>

                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        {/* Shortest Route */}
                        <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
                          <div className="flex items-center gap-2 text-sm font-medium text-blue-700 mb-2">
                            <Gauge className="h-4 w-4" />
                            <span>Shortest</span>
                            <Badge className="ml-auto bg-blue-100 text-blue-700 border-blue-200 text-xs flex items-center gap-1">
                              <ShortestIcon className="h-3 w-3" />
                              <span className="capitalize">{item.shortest_route.transport_mode}</span>
                            </Badge>
                          </div>
                          <div className="text-xs text-blue-600 space-y-1">
                            <p>{formatNumber(item.shortest_route.distance_km)} km</p>
                            <p>{formatNumber(item.shortest_route.emission_kg_co2)} kg CO₂</p>
                          </div>
                        </div>

                        {/* Efficient Route */}
                        <div className="p-3 rounded-lg bg-green-50 border border-green-100">
                          <div className="flex items-center gap-2 text-sm font-medium text-green-700 mb-2">
                            <Leaf className="h-4 w-4" />
                            <span>Eco-Efficient</span>
                            <Badge className="ml-auto bg-green-100 text-green-700 border-green-200 text-xs flex items-center gap-1">
                              <EfficientIcon className="h-3 w-3" />
                              <span className="capitalize">{item.efficient_route.transport_mode}</span>
                            </Badge>
                          </div>
                          <div className="text-xs text-green-600 space-y-1">
                            <p>{formatNumber(item.efficient_route.distance_km)} km</p>
                            <p>{formatNumber(item.efficient_route.emission_kg_co2)} kg CO₂</p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Pagination */}
            {data.pagination.total_pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!data.pagination.has_prev}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>

                <span className="px-4 py-2 text-sm text-muted-foreground">
                  Page {data.pagination.page} of {data.pagination.total_pages}
                </span>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.pagination.has_next}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        ) : (
          <Card className="text-center py-16">
            <CardContent>
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {hasActiveFilters ? 'No matches found' : 'No searches yet'}
              </h3>
              <p className="text-muted-foreground mb-6">
                {hasActiveFilters 
                  ? 'Try adjusting your filters to find what you\'re looking for'
                  : 'Start calculating carbon emissions to build your history'
                }
              </p>
              {hasActiveFilters ? (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              ) : (
                <Button onClick={() => navigate('/calculator')}>
                  Go to Calculator
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
