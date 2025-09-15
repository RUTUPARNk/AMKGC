import React from 'react';

interface ChildData {
  id: string;
  nodeId: string;
  nodeLabel: string;
  content: string;
  commitId: string;
  semanticSummary: string;
}

interface ConflictDiffViewerProps {
  children: ChildData[];
  viewType: 'diff' | 'semantic';
}

export const ConflictDiffViewer: React.FC<ConflictDiffViewerProps> = ({ 
  children, 
  viewType 
}) => {
  // In a real implementation, this would use Monaco Editor for diff viewing
  
  const renderDiffView = () => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {children.map((child, index) => (
          <div key={child.id} className="border rounded-lg overflow-hidden">
            <div className="bg-gray-100 px-4 py-2 border-b">
              <div className="font-medium text-gray-900">{child.nodeLabel}</div>
              <div className="text-sm text-gray-500">Node: {child.nodeId.substring(0, 8)}... | Commit: {child.commitId.substring(0, 7)}</div>
            </div>
            <div className="p-4 bg-gray-50 font-mono text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
              {child.content}
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  const renderSemanticView = () => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {children.map((child, index) => (
          <div key={child.id} className="border rounded-lg overflow-hidden">
            <div className="bg-gray-100 px-4 py-2 border-b">
              <div className="font-medium text-gray-900">Semantic Summary: {child.nodeLabel}</div>
              <div className="text-sm text-gray-500">Node: {child.nodeId.substring(0, 8)}... | Commit: {child.commitId.substring(0, 7)}</div>
            </div>
            <div className="p-4 bg-gray-50 whitespace-pre-wrap max-h-60 overflow-y-auto">
              {child.semanticSummary}
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div className="min-h-[300px]">
      {viewType === 'diff' ? renderDiffView() : renderSemanticView()}
      
      {children.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No conflicting changes to display
        </div>
      )}
    </div>
  );
};
