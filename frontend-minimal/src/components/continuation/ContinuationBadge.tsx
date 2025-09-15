import React from 'react';

interface ContinuationBadgeProps {
  count?: number;
  onClick?: () => void;
}

const ContinuationBadge: React.FC<ContinuationBadgeProps> = ({ 
  count = 0, 
  onClick 
}) => {
  if (count === 0) return null;
  
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
      aria-label={`Node has ${count} continuation${count > 1 ? 's' : ''}`}
    >
      <span className="mr-1">⤵️</span>
      {count > 1 && (
        <span className="font-bold">{count}</span>
      )}
    </button>
  );
};

export default ContinuationBadge;
