import { create } from 'zustand';
import { MergePreview } from '../services/mergeService';

export type MergeStatus = 'idle' | 'loading' | 'success' | 'error';

interface MergeState {
  // Merge preview state
  mergePreview: MergePreview | null;
  mergeStatus: MergeStatus;
  mergeError: string | null;
  
  // Currently selected merge
  selectedMergeChildId: string | null;
  
  // Actions
  setMergePreview: (preview: MergePreview | null) => void;
  setMergeStatus: (status: MergeStatus) => void;
  setMergeError: (error: string | null) => void;
  setSelectedMergeChildId: (childId: string | null) => void;
  
  // Reset state
  resetMergeState: () => void;
}

export const useMergeStore = create<MergeState>((set) => ({
  // Merge preview state
  mergePreview: null,
  mergeStatus: 'idle',
  mergeError: null,
  
  // Currently selected merge
  selectedMergeChildId: null,
  
  // Actions
  setMergePreview: (preview) => set({ mergePreview: preview }),
  setMergeStatus: (status) => set({ mergeStatus: status }),
  setMergeError: (error) => set({ mergeError: error }),
  setSelectedMergeChildId: (childId) => set({ selectedMergeChildId: childId }),
  
  // Reset state
  resetMergeState: () => set({
    mergePreview: null,
    mergeStatus: 'idle',
    mergeError: null,
    selectedMergeChildId: null,
  }),
}));
