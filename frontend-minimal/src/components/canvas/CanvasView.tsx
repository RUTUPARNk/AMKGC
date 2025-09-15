import React, { useCallback, useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useGraphStore } from '../../store/graph';
import { Tldraw, useEditor } from 'tldraw';
import { NodeContextMenu } from './NodeContextMenu';
import { StatusBar } from './StatusBar';
import { CustomToolbar } from './CustomToolbar';
import { NodeShapeAdapter } from './NodeShapeAdapter';
import { MiniMap } from '../navigation/MiniMap';
import 'tldraw/tldraw.css';

interface CanvasViewProps {
  sessionId: string;
  onNodeSelect: (nodeId: string) => void;
}

// Create a component that can access the editor context
const CanvasWithToolbar: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const editor = useEditor();
  
  return (
    <>
      <CustomToolbar editor={editor} />
      <NodeShapeAdapter sessionId={sessionId} />
    </>
  );
};

export const CanvasView: React.FC<CanvasViewProps> = ({ sessionId, onNodeSelect }) => {
  const { nodes } = useGraphStore();
  const [isNewNodeAnimation, setIsNewNodeAnimation] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId?: string } | null>(null);
  
  // Filter nodes by session
  const sessionNodes = useMemo(() => 
    Object.values(nodes).filter(node => node.sessionId === sessionId),
    [nodes, sessionId]
  );
  
  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY });
  }, []);
  
  // Handle canvas click (close context menu)
  const handleCanvasClick = useCallback(() => {
    setContextMenu(null);
  }, []);
  
  // Handle node selection
  const handleNodeSelect = useCallback((nodeId: string) => {
    onNodeSelect(nodeId);
    setContextMenu(null);
  }, [onNodeSelect]);
  
  // Trigger animation when a new node is added
  useEffect(() => {
    if (sessionNodes.length > 0) {
      setIsNewNodeAnimation(true);
      const timer = setTimeout(() => setIsNewNodeAnimation(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [sessionNodes.length]);
  
  return (
    <div className="h-full flex flex-col relative" onContextMenu={handleContextMenu} onClick={handleCanvasClick}>
      <div className="flex-1 relative">
        <Tldraw>
          <CanvasWithToolbar sessionId={sessionId} />
        </Tldraw>
        
        {/* Node context menu */}
        {contextMenu && (
          <NodeContextMenu 
            x={contextMenu.x} 
            y={contextMenu.y} 
            nodeId={contextMenu.nodeId}
            onClose={() => setContextMenu(null)}
            onNodeSelect={handleNodeSelect}
            sessionId={sessionId}
          />
        )}
        
        {/* New node animation overlay */}
        {isNewNodeAnimation && (
          <motion.div 
            className="absolute inset-0 pointer-events-none"
            initial={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}
            animate={{ backgroundColor: 'rgba(99, 102, 241, 0)' }}
            transition={{ duration: 1 }}
          />
        )}
        
        {/* Mini Map */}
        <MiniMap 
          sessionId={sessionId} 
          onNodeClick={onNodeSelect}
          className="absolute bottom-4 right-4"
        />
      </div>
      <StatusBar nodeCount={sessionNodes.length} sessionId={sessionId} />
    </div>
  );
};
