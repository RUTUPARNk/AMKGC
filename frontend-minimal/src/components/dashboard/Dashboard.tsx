import React, { useEffect } from 'react';
import { useDashboardStore } from '../../stores/dashboardStore';
import { HallucinationHeatmap } from './HallucinationHeatmap';
import { GapSidebar } from './GapSidebar';
import { TrendChart } from './TrendChart';

export const Dashboard: React.FC = () => {
  const { fetchGlobalSummary, fetchTrends, loading, error } = useDashboardStore();
  
  useEffect(() => {
    // Fetch initial data when component mounts
    fetchGlobalSummary();
    fetchTrends();
  }, [fetchGlobalSummary, fetchTrends]);
  
  const handleNodeClick = (nodeId: string) => {
    // In a real implementation, this would open the node's chat/history
    console.log(`Clicked on node: ${nodeId}`);
    // Example: navigate to node chat or open a modal
  };
  
  return (
    <div className="dashboard flex flex-col h-full">
      <div className="p-4 border-b bg-white">
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Gap Dashboard</h1>
        <p className="text-gray-600 mt-1">Monitor hallucinations and knowledge gaps across your graph</p>
      </div>
      
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 m-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <>
              <HallucinationHeatmap onNodeClick={handleNodeClick} />
              <TrendChart />
            </>
          )}
        </div>
        
        <GapSidebar />
      </div>
    </div>
  );
};
