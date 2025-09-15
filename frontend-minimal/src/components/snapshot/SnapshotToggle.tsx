import React from 'react';
import { useSnapshotStore } from '../../stores/snapshotStore';

export const SnapshotToggle: React.FC<{ nodeId: string }> = ({ nodeId }) => {
  const { mode, setMode, fetchCommitMap } = useSnapshotStore();
  
  const handleModeChange = (newMode: 'live' | 'snapshot') => {
    setMode(newMode);
    if (newMode === 'snapshot') {
      fetchCommitMap(nodeId);
    }
  };
  
  return (
    <div className="p-4 border border-gray-200 rounded-md mb-4">
      <h3 className="text-sm font-medium text-gray-900 mb-3">Snapshot Mode</h3>
      
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input
            type="radio"
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={mode === 'live'}
            onChange={() => handleModeChange('live')}
          />
          <span className="ml-2 text-sm text-gray-700">Live</span>
        </label>
        
        <label className="inline-flex items-center">
          <input
            type="radio"
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={mode === 'snapshot'}
            onChange={() => handleModeChange('snapshot')}
          />
          <span className="ml-2 text-sm text-gray-700">Snapshot</span>
        </label>
      </div>
      
      <p className="mt-2 text-xs text-gray-500">
        {mode === 'live' 
          ? 'Showing latest live versions of all nodes' 
          : 'Showing fixed snapshot commits for reproducibility'}
      </p>
    </div>
  );
};
