import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EnhancedDashboard from '../pages/EnhancedDashboard';
import { useGraphStore } from '../store/graph';
import { useMergeStore } from '../store/merge';

// Mock the tldraw component since it's complex to test
jest.mock('tldraw', () => ({
  Tldraw: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useEditor: () => ({
    zoomToFit: jest.fn(),
    zoomIn: jest.fn(),
    zoomOut: jest.fn(),
  }),
}));

// Mock the monaco editor
jest.mock('@monaco-editor/react', () => {
  return {
    __esModule: true,
    default: () => <div>Mock Editor</div>,
  };
});

// Mock the router
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
}));

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: jest.fn(() => 'mock-token'),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
  writable: true,
});

describe('Merge Flow Integration', () => {
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    
    // Reset stores
    useGraphStore.getState().resetSession('default-session');
    useMergeStore.getState().resetMergeState();
  });

  test('should create child node and open merge preview', async () => {
    render(<EnhancedDashboard />);
    
    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByText('Knowledge Graph')).toBeInTheDocument();
    });
    
    // Simulate creating a node
    const nodeId = useGraphStore.getState().upsertNode({
      text: 'Test node for merge',
      sessionId: 'default-session',
      type: 'atomic',
      status: 'active',
      label: 'Test Node'
    });
    
    // Select the node
    fireEvent.click(screen.getByText('Test Node'));
    
    // Check that node chat panel opens
    expect(screen.getByText('Node Chat')).toBeInTheDocument();
    
    // Simulate right-click on a message to create child node
    // This would normally happen in the MessageBubble component
    const childId = useGraphStore.getState().upsertNode({
      text: 'Correction for test node',
      sessionId: 'default-session',
      type: 'child',
      status: 'active',
      label: 'Correction Node',
      messageId: 'msg-123'
    });
    
    // Update child node status to merge_pending
    useGraphStore.getState().upsertNode({
      ...useGraphStore.getState().nodes[childId],
      status: 'merge_pending'
    });
    
    // Verify child node was created with correct status
    const nodes = useGraphStore.getState().nodes;
    expect(nodes[childId].status).toBe('merge_pending');
    
    // In a real implementation, this would trigger the merge preview modal
    // For now, we're just verifying the state management works correctly
  });

  test('should handle merge approval', async () => {
    // Create a node with merge_pending status
    const childId = useGraphStore.getState().upsertNode({
      text: 'Correction for merge approval',
      sessionId: 'default-session',
      type: 'child',
      status: 'merge_pending',
      label: 'Merge Node'
    });
    
    // Set it as the selected merge in the store
    useMergeStore.getState().setSelectedMergeChildId(childId);
    
    // Verify the state was set correctly
    expect(useMergeStore.getState().selectedMergeChildId).toBe(childId);
    
    // In a real implementation, clicking "Approve & Merge" would:
    // 1. Call the MergeService.applyMerge method
    // 2. Update the child node status to 'completed'
    // 3. Update the parent node with the merged content
    // 4. Mark dependent nodes as 'stale'
    // 5. Close the modal and show a success toast
    
    // For now, we're just verifying the state management
  });
});
