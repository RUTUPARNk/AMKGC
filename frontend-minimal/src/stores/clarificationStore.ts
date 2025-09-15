import { create } from 'zustand';
import api from '../services/api';

interface HallucinationIssue {
  type: 'MissingFact' | 'WrongAssumption' | 'Speculation';
  snippet: string;
  confidence: number;
  explanation: string | null;
}

interface HallucinationRecord {
  id: string;
  node_id: string;
  type: 'MissingFact' | 'WrongAssumption' | 'Speculation';
  snippet: string;
  created_at: string;
  resolved: boolean;
  resolution_notes: string | null;
}

interface ClarificationState {
  hallucinations: Record<string, HallucinationRecord[]>;
  loading: boolean;
  error: string | null;
  analyzeResponse: (nodeId: string, responseText: string) => Promise<HallucinationIssue[]>;
  getHallucinations: (nodeId: string, unresolvedOnly?: boolean) => Promise<void>;
  createClarificationNode: (parentNodeId: string, snippet: string) => Promise<{ child_id: string }>;
  resolveHallucination: (hallucinationId: string, resolutionNotes?: string) => Promise<boolean>;
  clearError: () => void;
}

export const useClarificationStore = create<ClarificationState>((set, get) => ({
  hallucinations: {},
  loading: false,
  error: null,
  
  analyzeResponse: async (nodeId: string, responseText: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.post<{ issues: HallucinationIssue[] }>(
        '/clarification/analyze',
        {
          node_id: nodeId,
          response_text: responseText
        }
      );
      
      set({ loading: false });
      return response.data.issues;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to analyze response';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  getHallucinations: async (nodeId: string, unresolvedOnly: boolean = true) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.get<{ hallucinations: HallucinationRecord[] }>(
        `/clarification/node/${nodeId}?unresolved_only=${unresolvedOnly}`
      );
      
      const records = response.data.hallucinations;
      
      set(state => ({
        hallucinations: {
          ...state.hallucinations,
          [nodeId]: records
        },
        loading: false
      }));
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to get hallucinations';
      set({ loading: false, error: errorMessage });
    }
  },
  
  createClarificationNode: async (parentNodeId: string, snippet: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.post<{ child_id: string }>(
        `/clarification/node/${parentNodeId}/child`,
        {
          parent_node_id: parentNodeId,
          snippet
        }
      );
      
      set({ loading: false });
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create clarification node';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  resolveHallucination: async (hallucinationId: string, resolutionNotes?: string) => {
    set({ loading: true, error: null });
    
    try {
      const response = await api.post<{ success: boolean }>(
        `/clarification/hallucination/${hallucinationId}/resolve`,
        {
          resolution_notes: resolutionNotes
        }
      );
      
      set({ loading: false });
      return response.data.success;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to resolve hallucination';
      set({ loading: false, error: errorMessage });
      throw error;
    }
  },
  
  clearError: () => set({ error: null })
}));
