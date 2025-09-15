import React, { useEffect, useState } from 'react';
import { useVersionsStore } from '../../stores/versionsStore';
import CommitItem from './CommitItem';

interface NodeHistoryTabProps {
  nodeId: string;
}

interface Version {
  commit_id: string;
  author: string;
  reason: string;
  created_at: string;
  diff_summary: string | null;
}

const NodeHistoryTab: React.FC<NodeHistoryTabProps> = ({ nodeId }) => {
  const { versions, loading, error, loadVersions, clearError } = useVersionsStore();
  const [localVersions, setLocalVersions] = useState<Version[]>([]);
  
  useEffect(() => {
    if (nodeId) {
      loadVersions(nodeId);
    }
  }, [nodeId, loadVersions]);
  
  useEffect(() => {
    if (versions[nodeId]) {
      setLocalVersions(versions[nodeId]);
    }
  }, [versions, nodeId]);
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <div className="flex justify-between items-center">
          <span>Error: {error}</span>
          <button 
            onClick={clearError}
            className="text-sm text-red-500 hover:text-red-700"
          >
            Clear
          </button>
        </div>
      </div>
    );
  }
  
  if (localVersions.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No version history found for this node.
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-medium text-gray-900">Commit History</h3>
      <div className="space-y-3">
        {localVersions.map((version) => (
          <CommitItem 
            key={version.commit_id} 
            version={version} 
            nodeId={nodeId}
          />
        ))}
      </div>
    </div>
  );
};

export default NodeHistoryTab;
