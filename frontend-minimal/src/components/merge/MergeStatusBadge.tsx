import React from 'react';

interface MergeStatusBadgeProps {
  status: 'fresh' | 'stale' | 'merge_pending' | 'merge_conflict';
  className?: string;
}

export const MergeStatusBadge: React.FC<MergeStatusBadgeProps> = ({ 
  status, 
  className = '' 
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'fresh':
        return {
          text: 'Fresh',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          icon: (
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
              <circle cx="4" cy="4" r="3" />
            </svg>
          )
        };
      case 'stale':
        return {
          text: 'Stale',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          icon: (
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
              <circle cx="4" cy="4" r="3" />
            </svg>
          )
        };
      case 'merge_pending':
        return {
          text: 'Merge Pending',
          bgColor: 'bg-yellow-100',
          textColor: 'text-yellow-800',
          icon: (
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
              <circle cx="4" cy="4" r="3" />
            </svg>
          )
        };
      case 'merge_conflict':
        return {
          text: 'Merge Conflict',
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          icon: (
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
              <circle cx="4" cy="4" r="3" />
            </svg>
          )
        };
      default:
        return {
          text: status,
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          icon: null
        };
    }
  };
  
  const config = getStatusConfig();
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} ${className}`}>
      {config.icon && <span className="mr-1.5">{config.icon}</span>}
      {config.text}
    </span>
  );
};
