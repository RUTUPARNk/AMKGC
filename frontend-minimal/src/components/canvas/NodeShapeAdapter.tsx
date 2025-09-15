import { useEffect } from 'react';
import { useEditor, TLGeoShape, toRichText } from 'tldraw';
import { useGraphStore } from '../../store/graph';
import { GNode } from '../../store/graph';

interface NodeShapeAdapterProps {
  sessionId: string;
}

export function NodeShapeAdapter({ sessionId }: NodeShapeAdapterProps) {
  const editor = useEditor();
  const nodes = useGraphStore(state => state.nodes);
  // In a real implementation, we would use useContinuationStore to check for continuations
  // For now, we'll just check the node type
  
  function getNodeLabelText(node: GNode): string {
    let labelText = node.label || '';
    
    // Add continuation indicator if this is a continuation node
    if (node.type === 'continuation') {
      labelText = `⤵️ ${labelText}`;
    }
    
    return labelText;
  }
  
  // Sync nodes from Zustand store to tldraw shapes
  useEffect(() => {
    const sessionNodes = Object.values(nodes).filter(node => node.sessionId === sessionId);
    
    // Get existing shapes from tldraw
    const existingShapes = editor.getCurrentPageShapes();
    const existingNodeShapes = existingShapes.filter(shape => 
      shape.type === 'geo' && (shape as TLGeoShape).meta?.nodeId
    ) as TLGeoShape[];
    
    // Create a map of existing node shapes by nodeId
    const existingNodeShapeMap = new Map<string, TLGeoShape>();
    existingNodeShapes.forEach(shape => {
      existingNodeShapeMap.set((shape.meta as any).nodeId, shape);
    });
    
    // Create/update shapes for each node
    sessionNodes.forEach(node => {
      const existingShape = existingNodeShapeMap.get(node.id);
      
      if (existingShape) {
        // Update existing shape
        const labelText = getNodeLabelText(node);
        editor.updateShape({
          id: existingShape.id,
          type: 'geo',
          props: {
            ...existingShape.props,
            text: labelText,
            fill: getNodeStatusColor(node.status)
          },
          meta: {
            ...existingShape.meta,
            nodeId: node.id
          }
        });
      } else {
        // Create new shape with all required properties
        const labelText = getNodeLabelText(node);
        editor.createShape({
          type: 'geo',
          x: Math.random() * 400, // Random position for now
          y: Math.random() * 400,
          props: {
            w: 200,
            h: 100,
            geo: 'rectangle',
            dash: 'draw',
            growY: 0,
            url: '',
            scale: 1,
            color: 'black',
            labelColor: 'black',
            fill: getNodeStatusColor(node.status),
            size: 'm',
            font: 'draw',
            align: 'middle',
            verticalAlign: 'middle',
            richText: toRichText(labelText),
            text: labelText
          },
          meta: {
            nodeId: node.id
          }
        });
      }
    });
    
    // Remove shapes that no longer correspond to nodes
    const nodeIds = new Set(sessionNodes.map(node => node.id));
    existingNodeShapes.forEach(shape => {
      if (!nodeIds.has((shape.meta as any).nodeId)) {
        editor.deleteShape(shape.id);
      }
    });
  }, [nodes, sessionId, editor]);
  
  return null;
}

function getNodeStatusColor(status: GNode['status']): string {
  switch (status) {
    case 'active': return 'light-green';
    case 'stale': return 'grey';
    case 'merge_pending': return 'yellow';
    case 'completed': return 'light-blue';
    case 'failed': return 'red';
    default: return 'white';
  }
}
