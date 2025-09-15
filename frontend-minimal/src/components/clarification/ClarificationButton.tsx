import React from 'react';
import { useClarificationStore } from '../../stores/clarificationStore';

interface ClarificationButtonProps {
  parentNodeId: string;
  snippet: string;
  onCreated?: (childNodeId: string) => void;
}

const ClarificationButton: React.FC<ClarificationButtonProps> = ({ 
  parentNodeId, 
  snippet,
  onCreated
}) => {
  const { createClarificationNode, loading, error } = useClarificationStore();
  
  const handleCreateClarification = async () => {
    try {
      const result = await createClarificationNode(parentNodeId, snippet);
      if (onCreated) {
        onCreated(result.child_id);
      }
    } catch (err) {
      console.error('Failed to create clarification node:', err);
    }
  };
  
  return (
    <div className="inline-flex items-center ml-2">
      <button
        onClick={handleCreateClarification}
        disabled={loading}
        className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
      >
        <span className="mr-1">📝</span>
        Create Clarification Node
      </button>
      
      {loading && (
        <span className="ml-2 text-xs text-gray-500">Creating...</span>
      )}
      
      {error && (
        <span className="ml-2 text-xs text-red-600">Error: {error}</span>
      )}
    </div>
  );
};

export default ClarificationButton;
