import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CanvasView } from '../components/canvas/CanvasView';
import { GraphView } from '../components/graph/GraphView';
import { Sidebar } from '../components/sidebar/Sidebar';
import { NodeChatPanel } from '../components/chat/NodeChatPanel';
import { MergePreviewModal } from '../components/diff/MergePreviewModal';
import { useWebSocket, WebSocketMessage } from '../services/websocketService';
import { MergeService } from '../services/mergeService';
import { useToast } from '../components/ToastContext';
import { useMergeStore } from '../store/merge';
import { useGraphStore } from '../store/graph';

const EnhancedDashboard: React.FC = () => {
  const [viewMode, setViewMode] = useState<'canvas' | 'graph'>('canvas');
  const [selectedSessionId] = useState<string>('default-session');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isMergePreviewOpen, setIsMergePreviewOpen] = useState(false);
  const [mergeChildId, setMergeChildId] = useState<string | null>(null);
  
  // Merge store
  const { setSelectedMergeChildId } = useMergeStore();
  const { nodes, upsertNode } = useGraphStore();
  const navigate = useNavigate();
  const { showToast } = useToast();
  
  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };
  
  const handleNodeSelect = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);
  
  const handleCreateNode = useCallback(() => {
    // Create a new node
    const newNodeId = upsertNode({
      text: 'New node',
      sessionId: selectedSessionId,
      type: 'atomic',
      status: 'active',
      label: 'New Node'
    });
    
    // Select the new node
    setSelectedNodeId(newNodeId);
  }, [upsertNode, selectedSessionId]);
  
  // Handle when a child node is created and we want to open the merge preview
  const handleChildNodeCreated = useCallback((childId: string) => {
    console.log('Child node created, opening chat panel and merge preview:', childId);
    
    // Set the child node status to merge_pending
    if (nodes[childId]) {
      upsertNode({
        ...nodes[childId],
        status: 'merge_pending'
      });
    }
    
    setSelectedNodeId(childId);
    setMergeChildId(childId);
    setSelectedMergeChildId(childId);
    setIsMergePreviewOpen(true);
  }, [nodes, upsertNode, setSelectedMergeChildId]);
  
  const handleApproveMerge = useCallback(async () => {
    if (!mergeChildId) return;
    
    try {
      const mergeService = MergeService.getInstance();
      const result = await mergeService.applyMerge(mergeChildId, 'Approved by user');
      
      console.log('Merge approved successfully', result);
      showToast('Merge approved successfully!', 'success');
      
      // Update the child node status to completed
      if (nodes[mergeChildId]) {
        upsertNode({
          ...nodes[mergeChildId],
          status: 'completed'
        });
      }
      
      // Close the modal and refresh the UI
      setIsMergePreviewOpen(false);
      setMergeChildId(null);
      setSelectedMergeChildId(null);
      
      // In a real implementation, we would also update the parent node
      // and mark dependent nodes as stale
    } catch (error: any) {
      console.error('Error approving merge:', error);
      showToast(error.message || 'Failed to approve merge', 'error');
    }
  }, [mergeChildId, nodes, upsertNode, setSelectedMergeChildId, showToast]);
  
  const handleRejectMerge = useCallback(() => {
    showToast('Merge rejected. No changes were applied.', 'info');
    
    setIsMergePreviewOpen(false);
    setMergeChildId(null);
  }, [showToast]);
  
  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'router_plan':
        showToast(`Execution plan created with ${message.payload.steps.length} steps`, 'info');
        break;
      case 'router_completion':
        showToast('Query execution completed successfully', 'success');
        break;
      case 'router_error':
        showToast(`Execution error: ${message.payload.error}`, 'error');
        break;
      case 'merge_proposed':
        showToast('New merge proposal available for review', 'warning');
        break;
      default:
        console.log('Unhandled WebSocket message:', message);
    }
  }, [showToast]);
  
  // Setup WebSocket connection
  useWebSocket(selectedSessionId, handleWebSocketMessage);
  
  // Get session nodes for empty state
  const sessionNodes = Object.values(nodes).filter(n => n.sessionId === selectedSessionId);
  
  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Top Navbar */}
      <motion.nav 
        className="bg-gradient-to-r from-indigo-600 to-purple-600 shadow-lg"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <motion.div 
                className="flex-shrink-0 flex items-center"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="h-10 w-10 rounded-lg bg-white flex items-center justify-center text-indigo-600 font-bold text-xl shadow-md">
                  N
                </div>
                <span className="ml-3 text-xl font-bold text-white">Node LLM System</span>
              </motion.div>
            </div>
            <div className="flex items-center">
              <div className="ml-3 relative">
                <div className="flex items-center space-x-4">
                  <motion.div 
                    className="flex-shrink-0"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <div className="h-8 w-8 rounded-full bg-white flex items-center justify-center text-indigo-600 font-medium shadow-sm">
                      U
                    </div>
                  </motion.div>
                  <motion.button
                    onClick={handleLogout}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-700 hover:bg-indigo-800 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-indigo-600"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Logout
                  </motion.button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.nav>
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="flex-shrink-0">
          <Sidebar 
            sessionId={selectedSessionId}
            selectedNodeId={selectedNodeId}
            onNodeSelect={handleNodeSelect}
            onCreateNode={handleCreateNode}
          />
        </div>
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
            {/* View Mode Toggle */}
            <motion.div 
              className="bg-white shadow-sm p-4"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <div className="flex rounded-lg shadow-sm w-fit overflow-hidden">
                <motion.button
                  type="button"
                  onClick={() => setViewMode('canvas')}
                  className={`px-4 py-2 text-sm font-medium ${viewMode === 'canvas' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 400, damping: 17 }}
                >
                  Canvas View
                </motion.button>
                <motion.button
                  type="button"
                  onClick={() => setViewMode('graph')}
                  className={`px-4 py-2 text-sm font-medium ${viewMode === 'graph' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 400, damping: 17 }}
                >
                  Graph View
                </motion.button>
              </div>
            </motion.div>
          
          {/* Canvas/Graph Area */}
          <div className="flex-1 overflow-hidden relative">
            {viewMode === 'canvas' ? (
              sessionNodes.length > 0 ? (
                <CanvasView 
                  sessionId={selectedSessionId} 
                  onNodeSelect={handleNodeSelect} 
                />
              ) : (
                <div className="h-full flex items-center justify-center bg-gray-50">
                  <motion.div 
                    className="text-center p-8 max-w-md border border-gray-200 rounded-lg bg-white shadow-sm"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="text-4xl mb-4">⚡</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No nodes yet</h3>
                    <p className="text-gray-500 mb-6">Right-click anywhere on the canvas to create your first node</p>
                    <button
                      onClick={handleCreateNode}
                      className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      Create Node
                    </button>
                  </motion.div>
                </div>
              )
            ) : (
              <GraphView 
                sessionId={selectedSessionId} 
                onNodeSelect={handleNodeSelect} 
              />
            )}
          </div>
        </div>
        
        {/* Node Chat Panel */}
        {selectedNodeId && (
          <motion.div 
            className="w-96 flex-shrink-0"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
          >
            <NodeChatPanel 
              nodeId={selectedNodeId} 
              onClose={() => setSelectedNodeId(null)}
              onRequestMerge={handleChildNodeCreated}
              isChildNode={mergeChildId === selectedNodeId}
            />
          </motion.div>
        )}
      </div>
      
      {/* Merge Preview Modal */}
      <MergePreviewModal 
        isOpen={isMergePreviewOpen}
        onClose={() => setIsMergePreviewOpen(false)}
        childNodeId={mergeChildId || 'child-123'}
        parentNodeId="parent-456"
        onApprove={handleApproveMerge}
        onReject={handleRejectMerge}
      />
    </div>
  );
};

export default EnhancedDashboard;
