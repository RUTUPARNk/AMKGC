import React from 'react';

interface NodeReliabilityCardProps {
  nodeId: string;
  hallucinations: number;
  unresolved: number;
  lastUpdated: string;
  onClick?: () => void;
}

export const NodeReliabilityCard: React.FC<NodeReliabilityCardProps> = ({
  nodeId,
  hallucinations,
  unresolved,
  lastUpdated,
  onClick
}) => {
  // Determine status based on hallucination count
  const getStatus = () => {
    if (hallucinations === 0) return 'Safe';
    if (hallucinations < 3) return 'At Risk';
    return 'Critical';
  };
  
  const getStatusColor = () => {
    if (hallucinations === 0) return 'bg-green-100 text-green-800';
    if (hallucinations < 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };
  
  const getBarColor = () => {
    if (hallucinations === 0) return 'bg-green-500';
    if (hallucinations < 3) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  // Calculate bar width based on hallucination count (max 10 for visualization)
  const barWidth = Math.min(100, (hallucinations / 10) * 100);
  
  return (
    <div 
      className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-white"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-medium text-gray-900 truncate">{nodeId}</h3>
        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor()}`}>
          {getStatus()}
        </span>
      </div>
      
      <div className="mb-3">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Hallucinations: {hallucinations}</span>
          <span>Unresolved: {unresolved}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${getBarColor()}`}
            style={{ width: `${barWidth}%` }}
          ></div>
        </div>
      </div>
      
      <div className="text-xs text-gray-500">
        Last updated: {new Date(lastUpdated).toLocaleDateString()}
      </div>
    </div>
  );
};
