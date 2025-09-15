import React, { useState } from 'react';

interface SearchResult {
  nodeId: string;
  nodeLabel: string;
  nodeStatus: 'fresh' | 'stale' | 'merge_pending' | 'merge_conflict';
  commits: Array<{
    commitId: string;
    message: string;
    timestamp: string;
    score?: number;
  }>;
  score?: number;
}

interface ResultItemProps {
  result: SearchResult;
}

export const ResultItem: React.FC<ResultItemProps> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'fresh': return 'bg-green-100 text-green-800';
      case 'stale': return 'bg-gray-100 text-gray-800';
      case 'merge_pending': return 'bg-yellow-100 text-yellow-800';
      case 'merge_conflict': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const handleNodeClick = () => {
    // In a real implementation, this would navigate to the node
    console.log('Navigate to node:', result.nodeId);
  };
  
  return (
    <div className="border border-gray-200 rounded-md overflow-hidden">
      <div 
        className="p-3 bg-white hover:bg-gray-50 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex justify-between items-start">
          <div>
            <div className="font-medium text-gray-900">{result.nodeLabel}</div>
            <div className="text-sm text-gray-500">Node: {result.nodeId.substring(0, 8)}...</div>
            {result.score !== undefined && (
              <div className="text-xs text-blue-600 font-medium">Score: {(result.score * 100).toFixed(1)}%</div>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(result.nodeStatus)}`}>
              {result.nodeStatus.replace('_', ' ')}
            </span>
            <svg 
              className={`h-5 w-5 text-gray-400 transform ${expanded ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>
      
      {expanded && (
        <div className="bg-gray-50 border-t border-gray-200 p-3">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Commits:</h4>
          <ul className="space-y-2">
            {result.commits.map((commit) => (
              <li key={commit.commitId} className="text-sm">
                <div className="flex justify-between">
                  <div className="font-mono text-gray-700">{commit.commitId.substring(0, 7)}</div>
                  {commit.score !== undefined && (
                    <div className="text-xs text-blue-600 font-medium">{(commit.score * 100).toFixed(1)}%</div>
                  )}
                </div>
                <div className="text-gray-600">{commit.message}</div>
                <div className="text-xs text-gray-500">
                  {new Date(commit.timestamp).toLocaleString()}
                </div>
              </li>
            ))}
          </ul>
          <button
            onClick={handleNodeClick}
            className="mt-3 inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Go to Node
          </button>
        </div>
      )}
    </div>
  );
};
