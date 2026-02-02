import { create } from 'zustand';
import type {
  Coordinates,
  RouteResponse,
  LocationSuggestion,
} from '../types';
import { searchApi } from '../lib/api';

interface CalculatorState {
  // Form inputs
  originName: string;
  originCoordinates: Coordinates | null;
  destinationName: string;
  destinationCoordinates: Coordinates | null;
  weightKg: string;

  // Location suggestions
  originSuggestions: LocationSuggestion[];
  destinationSuggestions: LocationSuggestion[];
  showOriginSuggestions: boolean;
  showDestinationSuggestions: boolean;

  // Results
  routeResult: RouteResponse | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setOrigin: (name: string, coordinates?: Coordinates) => void;
  setDestination: (name: string, coordinates?: Coordinates) => void;
  setWeightKg: (weight: string) => void;
  setOriginSuggestions: (suggestions: LocationSuggestion[]) => void;
  setDestinationSuggestions: (suggestions: LocationSuggestion[]) => void;
  setShowOriginSuggestions: (show: boolean) => void;
  setShowDestinationSuggestions: (show: boolean) => void;
  calculateRoutes: () => Promise<void>;
  clearResults: () => void;
  reset: () => void;
}

const initialState = {
  originName: '',
  originCoordinates: null,
  destinationName: '',
  destinationCoordinates: null,
  weightKg: '',
  originSuggestions: [],
  destinationSuggestions: [],
  showOriginSuggestions: false,
  showDestinationSuggestions: false,
  routeResult: null,
  isLoading: false,
  error: null,
};

export const useCalculatorStore = create<CalculatorState>((set, get) => ({
  ...initialState,

  setOrigin: (name: string, coordinates?: Coordinates) => {
    set({
      originName: name,
      originCoordinates: coordinates || null,
      showOriginSuggestions: false,
    });
  },

  setDestination: (name: string, coordinates?: Coordinates) => {
    set({
      destinationName: name,
      destinationCoordinates: coordinates || null,
      showDestinationSuggestions: false,
    });
  },

  setWeightKg: (weight: string) => set({ weightKg: weight }),

  setOriginSuggestions: (suggestions: LocationSuggestion[]) =>
    set({ originSuggestions: suggestions }),

  setDestinationSuggestions: (suggestions: LocationSuggestion[]) =>
    set({ destinationSuggestions: suggestions }),

  setShowOriginSuggestions: (show: boolean) =>
    set({ showOriginSuggestions: show }),

  setShowDestinationSuggestions: (show: boolean) =>
    set({ showDestinationSuggestions: show }),

  calculateRoutes: async () => {
    const state = get();

    // Validate inputs
    if (!state.originCoordinates) {
      set({ error: 'Please select an origin location' });
      return;
    }
    if (!state.destinationCoordinates) {
      set({ error: 'Please select a destination location' });
      return;
    }
    if (!state.weightKg || parseFloat(state.weightKg) <= 0) {
      set({ error: 'Please enter a valid cargo weight' });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const result = await searchApi.create({
        origin_name: state.originName,
        origin_coordinates: state.originCoordinates,
        destination_name: state.destinationName,
        destination_coordinates: state.destinationCoordinates,
        weight_kg: parseFloat(state.weightKg),
      });

      set({ routeResult: result, isLoading: false });
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : 'Failed to calculate routes';
      set({ error: message, isLoading: false });
    }
  },

  clearResults: () => set({ routeResult: null, error: null }),

  reset: () => set(initialState),
}));
