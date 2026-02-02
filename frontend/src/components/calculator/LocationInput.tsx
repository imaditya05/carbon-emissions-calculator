import { useState, useEffect, useRef } from 'react';
import { MapPin } from 'lucide-react';
import { Input } from '../ui/Input';
import { searchPlaces } from '../../lib/mapbox';
import type { Coordinates, LocationSuggestion } from '../../types';

interface LocationInputProps {
  id?: string;
  value: string;
  placeholder: string;
  iconColor?: string;
  onChange: (name: string, coordinates?: Coordinates) => void;
}

export function LocationInput({
  id,
  value,
  placeholder,
  onChange,
}: LocationInputProps) {
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout>();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    onChange(query);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.length >= 2) {
      setIsSearching(true);
      debounceRef.current = setTimeout(async () => {
        const results = await searchPlaces(query);
        setSuggestions(results);
        setShowSuggestions(true);
        setIsSearching(false);
      }, 300);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSelect = (suggestion: LocationSuggestion) => {
    onChange(suggestion.place_name, suggestion.coordinates);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Input
          id={id}
          value={value}
          onChange={handleInputChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder={placeholder}
          autoComplete="off"
          className="bg-card border-border/50 focus:border-primary"
        />
        {isSearching && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-md shadow-lg overflow-hidden">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              type="button"
              onClick={() => handleSelect(suggestion)}
              className="w-full px-3 py-2.5 text-left text-sm hover:bg-accent transition-colors flex items-start gap-2"
            >
              <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-foreground">{suggestion.place_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
