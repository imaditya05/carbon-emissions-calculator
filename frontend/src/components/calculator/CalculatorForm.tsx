import { MapPin, Loader2, Calculator } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { LocationInput } from './LocationInput';
import { useCalculatorStore } from '../../stores/calculatorStore';

export function CalculatorForm() {
  const {
    originName,
    destinationName,
    weightKg,
    isLoading,
    error,
    setOrigin,
    setDestination,
    setWeightKg,
    calculateRoutes,
  } = useCalculatorStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    calculateRoutes();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="origin">
          <MapPin className="h-4 w-4 text-primary" />
          Origin City
        </Label>
        <LocationInput
          id="origin"
          value={originName}
          placeholder="e.g., New York"
          iconColor="text-primary"
          onChange={setOrigin}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="destination">
          <MapPin className="h-4 w-4 text-destructive" />
          Destination City
        </Label>
        <LocationInput
          id="destination"
          value={destinationName}
          placeholder="e.g., London"
          iconColor="text-destructive"
          onChange={setDestination}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="weight">Cargo Weight (kg)</Label>
        <Input
          id="weight"
          type="number"
          value={weightKg}
          onChange={(e) => setWeightKg(e.target.value)}
          placeholder="e.g., 1000"
          min="1"
          required
        />
      </div>

      <div className="pt-2">
        <p className="text-xs text-muted-foreground mb-4">
          The system will automatically calculate routes for all transport modes 
          (Land, Sea, Air) and determine the shortest and most CO₂-efficient options.
        </p>
        <Button type="submit" className="w-full h-12 text-base" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Calculating Routes...
            </>
          ) : (
            <>
              <Calculator className="h-4 w-4" />
              Calculate Routes
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
