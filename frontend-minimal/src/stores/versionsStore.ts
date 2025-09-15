import { create } from 'zustand';
import api from '../services/api';

interface Version {
  commit_id: string;
  author: string;
  reason: string;
  created_at: string;
  diff_summary: string | null;
}

interface DiffResult {
  commit_a: string;
  commit_b: string;
  diff_summary: string;
  diff_patch: any[];
  changes: any;
}

interface VersionsState {
  versions: Record<string, Version[]>;
  diffs: Record<string, DiffResult>;
  loading: boolean;
  error: string | null;
  loadVersions: (nodeId: string) => Promise<void>;
  loadDiff: (commitA: string, commitB: string) => Promise<DiffResult>;
  rollbackVersion: (nodeId: string, commitId: string) => Promise<boolean>;
  clearError: () => void;
}

export const useVersionsStore = create<VersionsState>((set, get) => ({
  versions: {},
  diffs: {},
  loading: false,
  error: null,
  
  loadVersions: async (nodeId: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.get<{ versions: Version[] }>(`/versions/nodes/${nodeId}/history`);
      const versions = response.data.versions;
      
      set(state => ({
        versions: {
          ...state.versions,
          [nodeId]: versions
        },
        loading: false
      }));
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load versions';
      set({ loading: false, error: errorMessage });
    }
  },
  
  loadDiff: async (commitA: string, commitB: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.post<DiffResult>('/versions/diff', {
        commit_a: commitA,
        commit_b: commitB
      });
      const diff = response.data;
      
      const diffKey = `${commitA}-${commitB}`;
      set(state => ({
        diffs: {
          ...state.diffs,
          [diffKey]: diff
        },
        loading: false
      }));
      
      return diff;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load diff';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  rollbackVersion: async (nodeId: string, commitId: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.post<{ success: boolean }>('/versions/rollback', {
        node_id: nodeId,
        commit_id: commitId
      });
      
      set({ loading: false });
      return response.data.success;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to rollback version';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  clearError: () => set({ error: null })
}));
