import { create } from 'zustand';
import axios from 'axios';

interface SearchCommit {
  commitId: string;
  message: string;
  timestamp: string;
  score?: number; // For semantic search results
}

interface SearchResult {
  nodeId: string;
  nodeLabel: string;
  nodeStatus: 'fresh' | 'stale' | 'merge_pending' | 'merge_conflict';
  commits: SearchCommit[];
  score?: number; // Overall similarity score for the node
}

interface SearchState {
  query: string;
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  provider: 'ollama' | 'openai' | 'local' | null;
  
  // Actions
  searchNodes: (query: string) => Promise<void>;
  searchSemantic: (query: string) => Promise<void>;
  setProvider: (provider: 'ollama' | 'openai' | 'local' | null) => void;
  clearResults: () => void;
  clearError: () => void;
}

export const useSearchStore = create<SearchState>((set, get) => ({
  query: '',
  results: [],
  loading: false,
  error: null,
  provider: null,
  
  searchNodes: async (query: string) => {
    if (!query.trim()) {
      set({ results: [], query: '', loading: false });
      return;
    }
    
    set({ loading: true, error: null, query });
    
    try {
      // In a real implementation, this would call:
      // GET /api/v1/search/nodes?q={query}
      const response = await axios.get(`/api/v1/search/nodes`, {
        params: { q: query }
      });
      
      set({ 
        results: response.data.results || [], 
        loading: false 
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to search nodes';
      set({ loading: false, error: errorMessage });
    }
  },
  
  searchSemantic: async (query: string) => {
    if (!query.trim()) {
      set({ results: [], query: '', loading: false });
      return;
    }
    
    set({ loading: true, error: null, query });
    
    try {
      // Call the new semantic search endpoint
      const response = await axios.post(`/api/v1/vector/search/semantic`, {
        query: query,
        top_k: 20, // Get more results for semantic search
        provider: get().provider // Pass the selected provider
      });
      
      // Transform the semantic search results into the format expected by the UI
      // Group fragments by node
      const nodeMap: Record<string, SearchResult> = {};
      
      response.data.fragments.forEach((fragment: any) => {
        if (!nodeMap[fragment.node_id]) {
          nodeMap[fragment.node_id] = {
            nodeId: fragment.node_id,
            nodeLabel: `Node ${fragment.node_id.substring(0, 8)}`, // Placeholder until we get the actual label
            nodeStatus: 'fresh', // Placeholder until we get the actual status
            commits: [],
            score: fragment.score // Overall similarity score for the node
          };
        }
        
        // Add the fragment as a commit with score
        nodeMap[fragment.node_id].commits.push({
          commitId: fragment.commit_id || 'latest',
          message: fragment.text,
          timestamp: fragment.created_at,
          score: fragment.score
        });
      });
      
      // Convert to array and sort by score
      const results = Object.values(nodeMap)
        .sort((a, b) => (b.score || 0) - (a.score || 0));
      
      set({ 
        results,
        loading: false 
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to perform semantic search';
      set({ loading: false, error: errorMessage });
    }
  },
  
  setProvider: (provider) => set({ provider }),
  
  clearResults: () => set({ results: [], query: '' }),
  
  clearError: () => set({ error: null })
}));
