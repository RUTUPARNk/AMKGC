import React, { useState } from 'react';
import { useContinuationStore } from '../../stores/continuationStore';

interface ContinuationLoaderProps {
  nodeId: string;
  onMessagesLoaded?: (messages: any[]) => void;
}

const ContinuationLoader: React.FC<ContinuationLoaderProps> = ({ 
  nodeId, 
  onMessagesLoaded 
}) => {
  const { loadContinuationChain, loading, error } = useContinuationStore();
  const [expanded, setExpanded] = useState(false);
  
  const handleLoadChain = async () => {
    try {
      const chain = await loadContinuationChain(nodeId);
      setExpanded(!expanded);
      
      // Extract messages from all nodes in the chain
      const allMessages: any[] = [];
      chain.nodes.forEach(node => {
        // Assuming node has a messages array or similar
        if (node.messages) {
          allMessages.push(...node.messages);
        }
      });
      
      if (onMessagesLoaded) {
        onMessagesLoaded(allMessages);
      }
    } catch (err) {
      console.error('Failed to load continuation chain:', err);
    }
  };
  
  return (
    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-yellow-600 mr-2">⚠️</span>
          <span className="text-sm text-yellow-700">Node exceeded token budget.</span>
        </div>
        <button
          onClick={handleLoadChain}
          disabled={loading}
          className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 disabled:opacity-50"
        >
          <span>⤵️ Click to load continuation chain</span>
          <span className="ml-1">{expanded ? '▲' : '▼'}</span>
        </button>
      </div>
      
      {loading && (
        <div className="mt-2 text-sm text-gray-500">Loading continuation chain...</div>
      )}
      
      {error && (
        <div className="mt-2 text-sm text-red-600">Error: {error}</div>
      )}
      
      {expanded && (
        <div className="mt-3 text-sm text-gray-600">
          Loaded {0} additional messages from continuation chain
        </div>
      )}
    </div>
  );
};

export default ContinuationLoader;
