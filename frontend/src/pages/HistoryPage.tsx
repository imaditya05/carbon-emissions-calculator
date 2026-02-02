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

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const result = await searchApi.getAll({
        page,
        page_size: 10,
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
  }, [page]);

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

  const formatDate = (dateString: string) => {
    // Ensure the date is treated as UTC if no timezone info
    // Backend stores in UTC, append 'Z' if not present
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <History className="h-6 w-6 text-primary" />
              Search History
            </h1>
            <p className="text-muted-foreground mt-1">
              {data?.pagination.total || 0} searches saved
            </p>
          </div>

          <div className="flex items-center gap-3">
            {data && data.items.length > 0 && (
              <Button variant="outline" size="sm" onClick={handleClearAll}>
                <Trash2 className="h-4 w-4" />
                Clear All
              </Button>
            )}
          </div>
        </div>

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
                          <CardTitle className="text-base flex items-center gap-2">
                            <MapPin className="h-3 w-3 text-primary" />
                            {item.origin_name}
                            <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            <MapPin className="h-3 w-3 text-destructive" />
                            {item.destination_name}
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
              <h3 className="text-lg font-semibold text-foreground mb-2">No searches yet</h3>
              <p className="text-muted-foreground mb-6">
                Start calculating carbon emissions to build your history
              </p>
              <Button onClick={() => navigate('/calculator')}>
                Go to Calculator
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
