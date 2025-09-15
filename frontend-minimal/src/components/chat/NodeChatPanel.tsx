import { useState, useRef, useEffect } from 'react';
import { Composer } from './Composer.tsx';
import MessageBubble from '../MessageBubble';
import NodeHistoryTab from '../history/NodeHistoryTab';
import axios from 'axios';

interface NodeChatPanelProps {
  nodeId: string;
  onClose: () => void;
  onRequestMerge?: (childId: string) => void;
  isChildNode?: boolean;
}

export function NodeChatPanel({ nodeId, onClose, onRequestMerge, isChildNode = false }: NodeChatPanelProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'history' | 'diff'>('chat');
  const [messages, setMessages] = useState<Array<{
    id: string;
    sender: 'user' | 'ai';
    content: string;
    timestamp: string;
    citations?: Array<{
      id: string;
      nodeId: string;
      nodeLabel: string;
      commitId: string;
      score: number;
      text: string;
      used: boolean;
      metadata?: Record<string, any>;
    }>;
  }>>([
    { id: '1', sender: 'ai', content: 'Node chat initialized. Ask a question about this node.', timestamp: new Date(Date.now() - 300000).toISOString() },
    { id: '2', sender: 'user', content: 'What is this node about?', timestamp: new Date(Date.now() - 240000).toISOString() },
    { id: '3', sender: 'ai', content: 'This is a sample node in the knowledge graph. You can ask questions about its content or request changes.', timestamp: new Date(Date.now() - 180000).toISOString() },
  ]);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleSend = async (content: string) => {
    if (!content.trim() || isSending) return;
    
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      sender: 'user' as const,
      content,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsSending(true);
    
    try {
      // Simulate API call to Router Agent
      // In a real implementation, this would call:
      // POST /api/v1/router/plan_execution
      // POST /api/v1/router/execute_plan
      
      // Simulate delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Add assistant response
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai' as const,
        content: `I've processed your query about the node. Based on my analysis, this node represents a key concept in the knowledge graph. Would you like me to elaborate on any specific aspect?`,
        timestamp: new Date().toISOString()
        // In a real implementation, this would include context citations from the Router Agent
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Add error message
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai' as const,
        content: 'Failed to send message. Please try again.',
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };
  
  const handleRequestMerge = () => {
    // In a real implementation, this would:
    // 1. Mark the node as having a potential hallucination
    // 2. Create a child node for corrections
    // 3. Open the merge preview UI
    console.log('Requesting merge for node:', nodeId);
    alert('Merge request initiated. In a full implementation, this would create a child node for corrections and open the merge preview.');
  };
  
  const handleCreateChildNode = async (parentId: string, content: string) => {
    try {
      // Get auth token
      const token = localStorage.getItem('token');
      
      // Create child node via API
      const response = await axios.post(
        `${process.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/nodes`,
        {
          name: `Correction for message`,
          node_type: 'correction',
          context_window: content,
          parent_node_id: parentId
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('Child node created:', response.data);
      
      // If onRequestMerge is provided, call it with the child node ID
      if (onRequestMerge) {
        onRequestMerge(response.data.node.id);
      }
      
      // Add a system message to indicate the child node was created
      const systemMessage = {
        id: (Date.now() + 2).toString(),
        sender: 'ai' as const,
        content: 'A correction node has been created for this message. You can now make changes to the correction node.',
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error('Error creating child node:', error);
      // Add error message
      const errorMessage = {
        id: (Date.now() + 2).toString(),
        sender: 'ai' as const,
        content: 'Failed to create correction node. Please try again.',
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };
  
  return (
    <div className="flex flex-col h-full bg-white border-l">
      {/* Header */}
      <div className="p-4 border-b flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-gray-900">{isChildNode ? 'Correction Node Chat' : 'Node Chat'}</h3>
          <p className="text-sm text-gray-500 truncate max-w-xs">{nodeId}</p>
        </div>
        <div className="flex space-x-2">
          {!isChildNode && (
            <button 
              className="px-3 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-md hover:bg-yellow-200"
              onClick={handleRequestMerge}
            >
              Request Merge
            </button>
          )}
          <button 
            className="p-2 text-gray-500 hover:text-gray-700"
            onClick={onClose}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b">
        <nav className="flex">
          <button
            className={`px-4 py-2 text-sm font-medium ${activeTab === 'chat' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${activeTab === 'history' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${activeTab === 'diff' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('diff')}
          >
            Diff
          </button>
        </nav>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'chat' && (
          <>
            {messages.map(message => (
              <MessageBubble 
                key={message.id} 
                message={message} 
                onCreateChildNode={handleCreateChildNode}
              />
            ))}
            {isSending && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-xs">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
        
        {activeTab === 'history' && (
          <NodeHistoryTab nodeId={nodeId} />
        )}
        
        {activeTab === 'diff' && (
          <div className="text-center text-gray-500 py-8">
            <p>Diff view would be implemented here</p>
            <p className="text-sm mt-2">This would show differences between versions</p>
          </div>
        )}
      </div>
      
      {/* Composer */}
      {activeTab === 'chat' && (
        <div className="p-4 border-t">
          <Composer onSend={handleSend} isSending={isSending} />
        </div>
      )}
    </div>
  );
}
