import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MergePreviewModal } from '../components/diff/MergePreviewModal';
import { MergeService } from '../services/mergeService';

// Mock the monaco editor
jest.mock('@monaco-editor/react', () => {
  return {
    __esModule: true,
    default: () => <div>Mock Editor</div>,
  };
});

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

describe('Error Handling', () => {
  const mockProps = {
    isOpen: true,
    onClose: jest.fn(),
    childNodeId: 'child-123',
    parentNodeId: 'parent-456',
    onApprove: jest.fn(),
    onReject: jest.fn(),
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('should display loading state', () => {
    render(<MergePreviewModal {...mockProps} />);
    
    // Initially should show loading state
    expect(screen.getByText('Loading merge preview...')).toBeInTheDocument();
  });
  
  test('should handle merge service errors', async () => {
    // Mock the merge service to throw an error
    const mockGetMergePreview = jest.spyOn(MergeService.prototype, 'getMergePreview')
      .mockRejectedValue(new Error('Network error'));
    
    render(<MergePreviewModal {...mockProps} />);
    
    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText('Error Loading Merge Preview')).toBeInTheDocument();
    });
    
    // Should show the error message
    expect(screen.getByText('Network error')).toBeInTheDocument();
    
    // Clean up mock
    mockGetMergePreview.mockRestore();
  });
  
  test('should handle empty merge preview', async () => {
    // Mock the merge service to return empty data
    const mockGetMergePreview = jest.spyOn(MergeService.prototype, 'getMergePreview')
      .mockResolvedValue({
        merge_id: 'merge-123',
        text_diff: '',
        json_patch: [],
        diff_summary: '',
        impact: {
          added_lines: 0,
          removed_lines: 0,
          total_changes: 0
        },
        conflict: false,
        conflict_node_id: null
      });
    
    render(<MergePreviewModal {...mockProps} />);
    
    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText('Merge Preview')).toBeInTheDocument();
    });
    
    // Should show appropriate messages for empty content
    expect(screen.getByText('No semantic summary available.')).toBeInTheDocument();
    
    // Clean up mock
    mockGetMergePreview.mockRestore();
  });
  
  test('should handle merge conflicts', async () => {
    // Mock the merge service to return conflict data
    const mockGetMergePreview = jest.spyOn(MergeService.prototype, 'getMergePreview')
      .mockResolvedValue({
        merge_id: 'merge-123',
        text_diff: '@@ -1,1 +1,1 @@\n-Old content\n+New content',
        json_patch: [],
        diff_summary: 'Conflicting changes detected',
        impact: {
          added_lines: 1,
          removed_lines: 1,
          total_changes: 2
        },
        conflict: true,
        conflict_node_id: 'conflict-789',
        error: 'Merge conflict detected'
      });
    
    render(<MergePreviewModal {...mockProps} />);
    
    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText('Merge Preview')).toBeInTheDocument();
    });
    
    // Should show conflict information
    expect(screen.getByText('Conflicting changes detected')).toBeInTheDocument();
    
    // Clean up mock
    mockGetMergePreview.mockRestore();
  });
});
