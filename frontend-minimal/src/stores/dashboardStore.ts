import { create } from 'zustand';
import axios from 'axios';

export interface NodeHallucinationStat {
  node_id: string;
  hallucinations: number;
  unresolved: number;
  last_updated: string;
}

export interface HallucinationTrendPoint {
  date: string;
  node_id: string;
  hallucination_count: number;
}

interface DashboardState {
  globalStats: NodeHallucinationStat[];
  trends: HallucinationTrendPoint[];
  filters: {
    unresolvedOnly: boolean;
    criticalOnly: boolean;
    timeRange: '7d' | '30d' | '90d' | 'all';
  };
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchGlobalSummary: () => Promise<void>;
  fetchTrends: () => Promise<void>;
  setFilters: (filters: Partial<DashboardState['filters']>) => void;
  clearError: () => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  globalStats: [],
  trends: [],
  filters: {
    unresolvedOnly: false,
    criticalOnly: false,
    timeRange: '7d',
  },
  loading: false,
  error: null,
  
  fetchGlobalSummary: async () => {
    set({ loading: true, error: null });
    
    try {
      const response = await axios.get<NodeHallucinationStat[]>('/api/v1/clarification/summary/global');
      set({ globalStats: response.data, loading: false });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch global summary';
      set({ loading: false, error: errorMessage });
    }
  },
  
  fetchTrends: async () => {
    set({ loading: true, error: null });
    
    try {
      const response = await axios.get<HallucinationTrendPoint[]>('/api/v1/clarification/trends');
      set({ trends: response.data, loading: false });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch trends';
      set({ loading: false, error: errorMessage });
    }
  },
  
  setFilters: (newFilters) => {
    set(state => ({
      filters: {
        ...state.filters,
        ...newFilters
      }
    }));
  },
  
  clearError: () => set({ error: null })
}));
