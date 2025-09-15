import React, { useMemo } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  ReactFlowProvider, 
  Node, 
  Edge,
  NodeProps
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useGraphStore, GNode } from '../../store/graph';

interface GraphViewProps {
  sessionId: string;
  onNodeSelect?: (nodeId: string) => void;
}

// Custom node component with styling based on node status
const CustomNode: React.FC<NodeProps> = ({ data, selected }) => {
  const statusColors: Record<string, string> = {
    active: 'bg-green-100 border-green-500',
    stale: 'bg-gray-100 border-gray-500',
    merge_pending: 'bg-yellow-100 border-yellow-500',
    completed: 'bg-blue-100 border-blue-500',
    failed: 'bg-red-100 border-red-500',
  };
  
  const colorClass = statusColors[data.status] || 'bg-white border-gray-300';
  
  return (
    <div 
      className={`px-4 py-2 shadow-md rounded-md border-2 ${colorClass} ${selected ? 'ring-2 ring-indigo-500' : ''}`}
    >
      <div className="font-bold text-sm">{data.label}</div>
      <div className="text-xs text-gray-500 mt-1">{data.type}</div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export const GraphView: React.FC<GraphViewProps> = ({ sessionId, onNodeSelect }) => {
  const { nodes, edges } = useGraphStore();
  
  // Filter nodes and edges by session
  const sessionNodes = useMemo(() => 
    Object.values(nodes).filter(node => node.sessionId === sessionId),
    [nodes, sessionId]
  );
  
  const sessionEdges = useMemo(() => 
    Object.values(edges).filter(edge => {
      const sourceNode = nodes[edge.source];
      const targetNode = nodes[edge.target];
      return sourceNode?.sessionId === sessionId && targetNode?.sessionId === sessionId;
    }),
    [edges, nodes, sessionId]
  );
  
  // Convert nodes to React Flow format
  const flowNodes: Node[] = useMemo(() => 
    sessionNodes.map((node: GNode) => ({
      id: node.id,
      type: 'custom',
      position: { x: Math.random() * 500, y: Math.random() * 500 }, // In a real implementation, we would use actual positions
      data: { 
        label: node.label,
        type: node.type,
        status: node.status,
        text: node.text
      },
    })),
    [sessionNodes]
  );
  
  // Convert edges to React Flow format
  const flowEdges: Edge[] = useMemo(() => 
    sessionEdges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      animated: edge.label === 'sequence',
      style: { stroke: '#94a3b8' },
      labelStyle: { fill: '#64748b', fontWeight: 400 },
    })),
    [sessionEdges]
  );
  
  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    if (onNodeSelect) {
      onNodeSelect(node.id);
    }
  };
  
  if (sessionNodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 mb-2">No nodes to display</div>
          <div className="text-sm text-gray-400">Create nodes in Canvas View to see them here</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full w-full">
      <ReactFlowProvider>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={true}
        >
          <Controls />
          <Background gap={12} size={1} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
};
