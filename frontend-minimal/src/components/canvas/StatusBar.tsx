import { useMemo } from 'react';
import { useGraphStore } from '../../store/graph';

interface StatusBarProps {
  nodeCount: number;
  sessionId: string;
}

export function StatusBar({ nodeCount, sessionId }: StatusBarProps) {
  const { nodes } = useGraphStore();
  
  // Calculate counts for each status
  const statusCounts = useMemo(() => {
    const counts = {
      active: 0,
      stale: 0,
      merge_pending: 0,
      completed: 0,
      failed: 0
    };
    
    Object.values(nodes).forEach(node => {
      if (node.sessionId === sessionId) {
        counts[node.status] = (counts[node.status] || 0) + 1;
      }
    });
    
    return counts;
  }, [nodes, sessionId]);
  
  return (
    <div className="absolute bottom-0 left-0 right-0 bg-gray-800 text-white px-4 py-2 flex items-center justify-between text-sm">
      <div className="flex items-center space-x-4">
        <div className="flex items-center bg-gray-700 px-2 py-1 rounded">
          <span className="mr-2">Total:</span>
          <span className="font-semibold">{nodeCount}</span>
        </div>
        <div className="flex items-center bg-green-700 px-2 py-1 rounded">
          <span className="mr-2">Active:</span>
          <span className="font-semibold">{statusCounts.active}</span>
        </div>
        <div className="flex items-center bg-yellow-700 px-2 py-1 rounded">
          <span className="mr-2">Stale:</span>
          <span className="font-semibold">{statusCounts.stale}</span>
        </div>
        <div className="flex items-center bg-blue-700 px-2 py-1 rounded">
          <span className="mr-2">Merge:</span>
          <span className="font-semibold">{statusCounts.merge_pending}</span>
        </div>
      </div>
      <div className="text-gray-400">
        Ready
      </div>
    </div>
  );
}
