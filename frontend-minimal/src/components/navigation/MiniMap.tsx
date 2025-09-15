import React, { useMemo } from 'react';
import { useGraphStore } from '../../store/graph';

interface MiniMapProps {
  sessionId: string;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export const MiniMap: React.FC<MiniMapProps> = ({ 
  sessionId, 
  onNodeClick,
  className = 'absolute bottom-4 right-4'
}) => {
  const { nodes } = useGraphStore();
  
  // Filter nodes by session
  const sessionNodes = useMemo(() => 
    Object.values(nodes).filter(node => node.sessionId === sessionId),
    [nodes, sessionId]
  );
  
  // Calculate bounds for positioning
  const bounds = useMemo(() => {
    if (sessionNodes.length === 0) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
    
    // In a real implementation, we would use actual node positions
    // For now, we'll simulate with random positions
    return {
      minX: 0,
      minY: 0,
      maxX: 300,
      maxY: 200
    };
  }, [sessionNodes]);
  
  // Convert nodes to minimap coordinates
  const minimapNodes = useMemo(() => {
    return sessionNodes.map(node => {
      // Simulate positioning within bounds
      const x = 20 + (Math.random() * 260);
      const y = 20 + (Math.random() * 160);
      
      return {
        ...node,
        x,
        y
      };
    });
  }, [sessionNodes]);
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'stale': return 'bg-gray-500';
      case 'merge_pending': return 'bg-yellow-500';
      case 'completed': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-300';
    }
  };
  
  return (
    <div className={`${className} bg-white rounded-lg shadow-lg border p-2 w-48 h-32`}>
      <div className="text-xs font-medium text-gray-700 mb-1">Mini Map</div>
      <div className="relative w-full h-full bg-gray-50 rounded border">
        {minimapNodes.map(node => (
          <div
            key={node.id}
            className={`absolute w-2 h-2 rounded-full cursor-pointer ${getStatusColor(node.status)} ${onNodeClick ? 'hover:ring-2 hover:ring-indigo-500' : ''}`}
            style={{
              left: `${node.x / bounds.maxX * 100}%`,
              top: `${node.y / bounds.maxY * 100}%`,
              transform: 'translate(-50%, -50%)'
            }}
            onClick={() => onNodeClick?.(node.id)}
            title={`${node.label} (${node.status})`}
          />
        ))}
        
        {sessionNodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">
            No nodes
          </div>
        )}
      </div>
    </div>
  );
};
