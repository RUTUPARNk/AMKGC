import React from 'react';
import { useDashboardStore } from '../../stores/dashboardStore';
import { NodeReliabilityCard } from '.';

interface HallucinationHeatmapProps {
  onNodeClick?: (nodeId: string) => void;
}

export const HallucinationHeatmap: React.FC<HallucinationHeatmapProps> = ({ onNodeClick }) => {
  const { globalStats, filters } = useDashboardStore();
  
  // Filter stats based on current filters
  const filteredStats = React.useMemo(() => {
    return globalStats.filter(stat => {
      // Filter by unresolved only if enabled
      if (filters.unresolvedOnly && stat.unresolved === 0) {
        return false;
      }
      
      // Filter by critical only if enabled (>= 3 hallucinations)
      if (filters.criticalOnly && stat.hallucinations < 3) {
        return false;
      }
      
      return true;
    });
  }, [globalStats, filters]);
  
  return (
    <div className="hallucination-heatmap">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStats.map((stat) => (
          <NodeReliabilityCard 
            key={stat.node_id}
            nodeId={stat.node_id}
            hallucinations={stat.hallucinations}
            unresolved={stat.unresolved}
            lastUpdated={stat.last_updated}
            onClick={() => onNodeClick?.(stat.node_id)}
          />
        ))}
      </div>
      
      {filteredStats.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No nodes match the current filters
        </div>
      )}
    </div>
  );
};
