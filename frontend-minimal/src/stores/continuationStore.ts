import { create } from 'zustand';
import api from '../services/api';

interface ContinuationNode {
  id: string;
  name: string;
  node_type: string;
  status: string;
  created_at: string;
  continuation_of: string | null;
}

interface NodeChain {
  root_node_id: string;
  nodes: ContinuationNode[];
}

interface ContinuationState {
  chains: Record<string, NodeChain>;
  loading: boolean;
  error: string | null;
  loadContinuationChain: (nodeId: string) => Promise<NodeChain>;
  getActiveNode: (nodeId: string) => Promise<ContinuationNode>;
  clearError: () => void;
}

export const useContinuationStore = create<ContinuationState>((set, get) => ({
  chains: {},
  loading: false,
  error: null,
  
  loadContinuationChain: async (nodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.get<NodeChain>(`/continuation/chain/${nodeId}`);
      const chain = response.data;
      
      set(state => ({
        chains: {
          ...state.chains,
          [nodeId]: chain
        },
        loading: false
      }));
      
      return chain;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load continuation chain';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  getActiveNode: async (nodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.get<{ node: ContinuationNode }>(`/continuation/active/${nodeId}`);
      set({ loading: false });
      return response.data.node;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to get active node';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  clearError: () => set({ error: null })
}));
