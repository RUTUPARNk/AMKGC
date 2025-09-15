import React, { useState } from 'react';
import { ConflictDiffViewer } from './ConflictDiffViewer';

interface ConflictData {
  id: string;
  parentId: string;
  parentSnapshot: {
    id: string;
    content: string;
    commitId: string;
  };
  children: Array<{
    id: string;
    nodeId: string;
    nodeLabel: string;
    content: string;
    commitId: string;
    semanticSummary: string;
  }>;
}

interface ConflictResolutionModalProps {
  conflict: ConflictData;
  isOpen: boolean;
  onClose: () => void;
  onResolve: (conflictId: string, choice: 'accept_first' | 'accept_second' | 'sequential' | 'spawn_node') => void;
}

export const ConflictResolutionModal: React.FC<ConflictResolutionModalProps> = ({ 
  conflict, 
  isOpen, 
  onClose,
  onResolve
}) => {
  const [selectedTab, setSelectedTab] = useState<'diff' | 'semantic'>('diff');
  
  if (!isOpen) return null;
  
  const handleResolve = (choice: 'accept_first' | 'accept_second' | 'sequential' | 'spawn_node') => {
    onResolve(conflict.id, choice);
    onClose();
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Merge Conflict: {conflict.parentId.substring(0, 8)}...</h2>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="mt-2 text-sm text-gray-500">
            Parent Snapshot: {conflict.parentSnapshot.commitId.substring(0, 7)}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto">
          {/* Tabs */}
          <div className="border-b">
            <nav className="flex">
              <button
                className={`px-4 py-2 text-sm font-medium ${selectedTab === 'diff' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                onClick={() => setSelectedTab('diff')}
              >
                Textual Diff
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium ${selectedTab === 'semantic' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                onClick={() => setSelectedTab('semantic')}
              >
                Semantic Summary
              </button>
            </nav>
          </div>
          
          {/* Diff Viewer */}
          <div className="p-4">
            {selectedTab === 'diff' ? (
              <ConflictDiffViewer 
                children={conflict.children}
                viewType="diff"
              />
            ) : (
              <ConflictDiffViewer 
                children={conflict.children}
                viewType="semantic"
              />
            )}
          </div>
        </div>
        
        {/* Footer with actions */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => handleResolve('accept_first')}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Accept Child 1
            </button>
            
            {conflict.children.length > 2 ? (
              <button
                onClick={() => handleResolve('sequential')}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Sequential Merge
              </button>
            ) : (
              <button
                onClick={() => handleResolve('accept_second')}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Accept Child 2
              </button>
            )}
            
            <button
              onClick={() => handleResolve('spawn_node')}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
            >
              Create Conflict Node
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
