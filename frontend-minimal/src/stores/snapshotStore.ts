import { create } from 'zustand';
import axios from 'axios';

interface CommitMapEntry {
  nodeId: string;
  nodeLabel: string;
  commitId: string;
  commitMessage: string;
}

interface SnapshotState {
  mode: 'live' | 'snapshot';
  commitMap: Record<string, CommitMapEntry>; // nodeId -> commit info
  loading: boolean;
  error: string | null;
  
  // Actions
  setMode: (mode: 'live' | 'snapshot') => void;
  fetchCommitMap: (mainNodeId: string) => Promise<void>;
  updateSnapshot: (mainNodeId: string) => Promise<boolean>;
  exportSnapshot: (mainNodeId: string) => Promise<string | null>; // returns export URL
  clearError: () => void;
}

export const useSnapshotStore = create<SnapshotState>((set, get) => ({
  mode: 'live',
  commitMap: {},
  loading: false,
  error: null,
  
  setMode: (mode) => set({ mode }),
  
  fetchCommitMap: async (mainNodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      // In a real implementation, this would call:
      // GET /api/v1/snapshot/commit_map/{main_node}
      const response = await axios.get(`/api/v1/snapshot/commit_map/${mainNodeId}`);
      
      set({ 
        commitMap: response.data.commit_map || {}, 
        loading: false 
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch commit map';
      set({ loading: false, error: errorMessage });
    }
  },
  
  updateSnapshot: async (mainNodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      // In a real implementation, this would call:
      // POST /api/v1/snapshot/update/{main_node}
      const response = await axios.post(`/api/v1/snapshot/update/${mainNodeId}`);
      
      set({ loading: false });
      return response.data.success;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update snapshot';
      set({ loading: false, error: errorMessage });
      return false;
    }
  },
  
  exportSnapshot: async (mainNodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      // In a real implementation, this would call:
      // POST /api/v1/snapshot/export/{main_node}
      const response = await axios.post(`/api/v1/snapshot/export/${mainNodeId}`);
      
      set({ loading: false });
      return response.data.export_url;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to export snapshot';
      set({ loading: false, error: errorMessage });
      return null;
    }
  },
  
  clearError: () => set({ error: null })
}));
