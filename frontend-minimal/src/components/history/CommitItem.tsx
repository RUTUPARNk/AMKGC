import React, { useState } from 'react';
import { useVersionsStore } from '../../stores/versionsStore';

interface Version {
  commit_id: string;
  author: string;
  reason: string;
  created_at: string;
  diff_summary: string | null;
}

interface CommitItemProps {
  version: Version;
  nodeId: string;
}

const CommitItem: React.FC<CommitItemProps> = ({ version, nodeId }) => {
  const { loadDiff, rollbackVersion, loading } = useVersionsStore();
  const [showDiff, setShowDiff] = useState(false);
  
  // Format the date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else {
      return `${diffDays} days ago`;
    }
  };
  
  const handlePreview = async () => {
    try {
      // This would open a diff preview modal
      console.log(`Previewing diff for commit ${version.commit_id}`);
    } catch (error) {
      console.error('Failed to preview diff:', error);
    }
  };
  
  const handleDiff = async () => {
    try {
      // Compare with previous version or current version
      console.log(`Showing diff for commit ${version.commit_id}`);
      setShowDiff(!showDiff);
    } catch (error) {
      console.error('Failed to show diff:', error);
    }
  };
  
  const handleRollback = async () => {
    if (!window.confirm('Are you sure you want to rollback to this version?')) {
      return;
    }
    
    try {
      await rollbackVersion(nodeId, version.commit_id);
      alert('Successfully rolled back to this version');
    } catch (error) {
      console.error('Failed to rollback:', error);
      alert('Failed to rollback to this version');
    }
  };
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-800 mr-2">
              ✔
            </span>
            <span className="font-mono text-sm text-gray-500 mr-2">
              {version.commit_id.substring(0, 8)}
            </span>
            <span className="text-sm text-gray-500">-</span>
            <span className="ml-2 text-sm font-medium text-gray-900">
              {version.reason || 'Unnamed commit'}
            </span>
          </div>
          <div className="mt-1 ml-8 text-sm text-gray-500">
            {version.author} • {formatDate(version.created_at)}
          </div>
          {version.diff_summary && (
            <div className="mt-2 ml-8 text-sm text-gray-600">
              {version.diff_summary}
            </div>
          )}
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={handlePreview}
            className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Preview
          </button>
          <button
            onClick={handleDiff}
            className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Diff
          </button>
          <button
            onClick={handleRollback}
            disabled={loading}
            className="px-3 py-1 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
          >
            Rollback
          </button>
        </div>
      </div>
      
      {showDiff && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-600">Diff content would be displayed here...</p>
        </div>
      )}
    </div>
  );
};

export default CommitItem;
