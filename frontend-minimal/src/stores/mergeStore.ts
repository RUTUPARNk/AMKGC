import { create } from 'zustand';
import axios from 'axios';

interface Conflict {
  id: string;
  parentId: string;
  parentSnapshot: {
    id: string;
    content: string;
    commitId: string;
  };
  children: Array<{
    id: string;
    nodeId: string;
    nodeLabel: string;
    content: string;
    commitId: string;
    semanticSummary: string;
  }>;
  createdAt: string;
  resolved: boolean;
}

interface MergeState {
  conflicts: Record<string, Conflict[]>; // nodeId -> conflicts
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchConflicts: (nodeId: string) => Promise<void>;
  resolveConflict: (conflictId: string, choice: 'accept_first' | 'accept_second' | 'sequential' | 'spawn_node') => Promise<boolean>;
  spawnConflictNode: (conflictId: string) => Promise<string | null>; // returns new node id
  clearError: () => void;
}

export const useMergeStore = create<MergeState>((set, get) => ({
  conflicts: {},
  loading: false,
  error: null,
  
  fetchConflicts: async (nodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      // In a real implementation, this would call:
      // GET /api/v1/merge/conflicts/{node_id}
      const response = await axios.get(`/api/v1/merge/conflicts/${nodeId}`);
      
      set(state => ({
        conflicts: {
          ...state.conflicts,
          [nodeId]: response.data.conflicts
        },
        loading: false
      }));
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch conflicts';
      set({ loading: false, error: errorMessage });
    }
  },
  
  resolveConflict: async (conflictId: string, choice: 'accept_first' | 'accept_second' | 'sequential' | 'spawn_node') => {
    set({ loading: true, error: null });
    
    try {
      // In a real implementation, this would call:
      // POST /api/v1/merge/conflict/{conflict_id}/resolve
      const response = await axios.post(`/api/v1/merge/conflict/${conflictId}/resolve`, {
        choice
      });
      
      // Update local state to mark conflict as resolved
      set(state => {
        const updatedConflicts = { ...state.conflicts };
        Object.keys(updatedConflicts).forEach(nodeId => {
          updatedConflicts[nodeId] = updatedConflicts[nodeId].map(conflict => 
            conflict.id === conflictId ? { ...conflict, resolved: true } : conflict
          );
        });
        
        return {
          conflicts: updatedConflicts,
          loading: false
        };
      });
      
      return response.data.success;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to resolve conflict';
      set({ loading: false, error: errorMessage });
      return false;
    }
  },
  
  spawnConflictNode: async (conflictId: string) => {
    set({ loading: true, error: null });
    
    try {
      // In a real implementation, this would call:
      // POST /api/v1/merge/conflict/{conflict_id}/spawn
      const response = await axios.post(`/api/v1/merge/conflict/${conflictId}/spawn`);
      
      set({ loading: false });
      return response.data.node_id;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to spawn conflict node';
      set({ loading: false, error: errorMessage });
      return null;
    }
  },
  
  clearError: () => set({ error: null })
}));
