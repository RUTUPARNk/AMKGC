import { useGraphStore } from '../../store/graph';

interface NodeContextMenuProps {
  x: number;
  y: number;
  nodeId?: string;
  onClose: () => void;
  onNodeSelect: (nodeId: string) => void;
  sessionId: string;
}

export function NodeContextMenu({ x, y, nodeId, onClose, onNodeSelect, sessionId }: NodeContextMenuProps) {
  const upsertNode = useGraphStore(s => s.upsertNode);
  
  const handleCreateNode = () => {
    // In a real implementation, we would show a modal to get node details
    // For now, we'll create a simple node
    const newNodeId = upsertNode({
      text: 'New node',
      sessionId: sessionId,
      type: 'atomic',
      status: 'active',
      label: 'New Node'
    });
    
    onNodeSelect(newNodeId);
    onClose();
  };
  
  const handleAddDependency = () => {
    // Implementation for adding dependency
    console.log('Add dependency');
    onClose();
  };
  
  const handleAskQuestion = () => {
    // Implementation for asking question
    console.log('Ask question');
    onClose();
  };
  
  return (
    <div 
      className="absolute bg-white shadow-lg rounded-md py-2 z-50 min-w-[200px]"
      style={{ left: x, top: y }}
      onClick={(e) => e.stopPropagation()}
    >
      {nodeId ? (
        // Context menu for existing node
        <>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
            onClick={() => onNodeSelect(nodeId)}
          >
            Open Node
          </button>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
            onClick={handleAddDependency}
          >
            Add Dependency
          </button>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
            onClick={handleAskQuestion}
          >
            Ask Question
          </button>
          <div className="border-t my-1"></div>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-red-600"
            onClick={onClose}
          >
            Delete Node
          </button>
        </>
      ) : (
        // Context menu for canvas
        <>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
            onClick={handleCreateNode}
          >
            Create Node
          </button>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
            onClick={onClose}
          >
            Add Dependency
          </button>
          <button 
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
            onClick={onClose}
          >
            Ask Question
          </button>
        </>
      )}
    </div>
  );
}
