import React, { useState } from 'react';
import { useGraphStore } from '../../store/graph';
import { useClarificationStore } from '../../stores/clarificationStore';

interface NodeFilterBarProps {
  sessionId: string;
  onFilterChange?: (filters: NodeFilters) => void;
  className?: string;
}

interface NodeFilters {
  status: 'all' | 'active' | 'stale' | 'merge_pending' | 'completed' | 'failed';
  hasHallucinations: boolean;
}

export const NodeFilterBar: React.FC<NodeFilterBarProps> = ({ 
  sessionId, 
  onFilterChange,
  className = 'p-4 border-b'
}) => {
  const { nodes } = useGraphStore();
  const { hallucinations } = useClarificationStore();
  
  const [statusFilter, setStatusFilter] = useState<NodeFilters['status']>('all');
  const [hasHallucinationsFilter, setHasHallucinationsFilter] = useState(false);
  
  // Get nodes with hallucinations for the current session
  const nodesWithHallucinations = Object.values(hallucinations)
    .flatMap(records => records.map(record => record.node_id));
  
  const handleStatusFilterChange = (filter: NodeFilters['status']) => {
    setStatusFilter(filter);
    onFilterChange?.({ status: filter, hasHallucinations: hasHallucinationsFilter });
  };
  
  const handleHallucinationFilterChange = (checked: boolean) => {
    setHasHallucinationsFilter(checked);
    onFilterChange?.({ status: statusFilter, hasHallucinations: checked });
  };
  
  // Count nodes by status
  const nodeCounts = Object.values(nodes)
    .filter(node => node.sessionId === sessionId)
    .reduce((counts, node) => {
      counts[node.status] = (counts[node.status] || 0) + 1;
      return counts;
    }, {} as Record<string, number>);
  
  // Count nodes with hallucinations
  const hallucinationCount = nodesWithHallucinations.length;
  
  return (
    <div className={`${className} flex flex-wrap items-center gap-4`}>
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">Status:</span>
        <div className="flex space-x-1">
          <button
            className={`px-3 py-1 text-xs rounded-md ${statusFilter === 'all' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            onClick={() => handleStatusFilterChange('all')}
          >
            All ({Object.values(nodeCounts).reduce((a, b) => a + b, 0)})
          </button>
          <button
            className={`px-3 py-1 text-xs rounded-md flex items-center ${statusFilter === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            onClick={() => handleStatusFilterChange('active')}
          >
            <span className="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
            Active ({nodeCounts.active || 0})
          </button>
          <button
            className={`px-3 py-1 text-xs rounded-md flex items-center ${statusFilter === 'merge_pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            onClick={() => handleStatusFilterChange('merge_pending')}
          >
            <span className="w-2 h-2 rounded-full bg-yellow-500 mr-1"></span>
            Merge ({nodeCounts.merge_pending || 0})
          </button>
          <button
            className={`px-3 py-1 text-xs rounded-md flex items-center ${statusFilter === 'stale' ? 'bg-gray-100 text-gray-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            onClick={() => handleStatusFilterChange('stale')}
          >
            <span className="w-2 h-2 rounded-full bg-gray-500 mr-1"></span>
            Stale ({nodeCounts.stale || 0})
          </button>
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">Filters:</span>
        <label className="flex items-center text-sm">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            checked={hasHallucinationsFilter}
            onChange={(e) => handleHallucinationFilterChange(e.target.checked)}
          />
          <span className="ml-2 text-gray-700">
            Has Hallucinations ({hallucinationCount})
          </span>
        </label>
      </div>
    </div>
  );
};
