import React from 'react';

interface FragmentData {
  id: string;
  nodeId: string;
  nodeLabel: string;
  commitId: string;
  score: number;
  text: string;
  used: boolean;
  metadata?: Record<string, any>;
}

interface FragmentPreviewProps {
  fragment: FragmentData;
  className?: string;
  onClick?: () => void;
}

export const FragmentPreview: React.FC<FragmentPreviewProps> = ({ 
  fragment, 
  className = '',
  onClick
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    if (score >= 0.4) return 'text-orange-600';
    return 'text-red-600';
  };
  
  const getStatusIcon = (used: boolean) => {
    if (used) {
      return (
        <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      );
    }
    return (
      <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    );
  };
  
  return (
    <div 
      className={`p-3 bg-gray-50 rounded-md text-sm ${className} ${onClick ? 'cursor-pointer hover:bg-gray-100' : ''}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div className="font-medium text-gray-900 truncate">{fragment.nodeLabel}</div>
        <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
          {getStatusIcon(fragment.used)}
          <span className={`font-mono text-xs ${getScoreColor(fragment.score)}`}>
            {Math.round(fragment.score * 100)}%
          </span>
        </div>
      </div>
      
      <div className="mt-1 text-gray-600 truncate">
        {fragment.text.substring(0, 100)}
        {fragment.text.length > 100 ? '...' : ''}
      </div>
      
      <div className="mt-2 flex justify-between text-xs text-gray-500">
        <span className="font-mono bg-gray-200 px-1.5 py-0.5 rounded">
          {fragment.commitId.substring(0, 7)}
        </span>
        <span>Node: {fragment.nodeId.substring(0, 8)}...</span>
      </div>
      
      {fragment.metadata && (
        <div className="mt-2 text-xs text-gray-500 flex flex-wrap gap-1">
          {Object.entries(fragment.metadata).map(([key, value]) => (
            <span key={key} className="bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
              {key}: {String(value)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
