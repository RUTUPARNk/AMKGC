import React, { useState, useEffect } from 'react';
// HallucinationMarker and ClarificationButton will be used when we implement the full hallucination detection
// import HallucinationMarker from './clarification/HallucinationMarker';
// import ClarificationButton from './clarification/ClarificationButton';
import { useClarificationStore } from '../stores/clarificationStore';
import { ContextCitations } from './router/ContextCitations';

interface MessageBubbleProps {
  message: {
    id: string;
    content: string;
    sender: 'user' | 'ai';
    timestamp: string;
    nodeId?: string; // Added for clarification integration
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
  };
  onCreateChildNode?: (parentId: string, content: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onCreateChildNode }) => {
  const isUser = message.sender === 'user';
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const { analyzeResponse } = useClarificationStore();
  
  // Analyze AI messages for hallucinations when component mounts
  useEffect(() => {
    if (!isUser && message.nodeId && message.content) {
      // In a real implementation, you might want to throttle this or only analyze
      // when certain conditions are met
      analyzeResponse(message.nodeId, message.content).catch(console.error);
    }
  }, [message.nodeId, message.content, isUser, analyzeResponse]);
  
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    if (message.sender === 'ai' && onCreateChildNode) {
      setContextMenuPosition({ x: e.clientX, y: e.clientY });
      setShowContextMenu(true);
    }
  };
  
  const handleCreateChildNode = () => {
    if (onCreateChildNode) {
      onCreateChildNode(message.id, message.content);
      setShowContextMenu(false);
    }
  };
  
  // Close context menu when clicking elsewhere
  React.useEffect(() => {
    const handleClickOutside = () => {
      if (showContextMenu) {
        setShowContextMenu(false);
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showContextMenu]);
  
  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      onContextMenu={handleContextMenu}
    >
      <div
        className={`max-w-xs md:max-w-md px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-blue-500 text-white rounded-br-none'
            : 'bg-gray-200 text-gray-800 rounded-bl-none'
        }`}
      >
        <div className="text-sm">
          {message.content}
          {/* In a real implementation, you would map through detected hallucinations */}
          {/* <HallucinationMarker type="WrongAssumption" snippet="example" confidence={0.8} /> */}
        </div>
        {message.citations && message.citations.length > 0 && (
          <ContextCitations citations={message.citations} className="mt-2" />
        )}
        <div className="flex justify-between items-center mt-1">
          <p className={`text-xs ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
          {!isUser && onCreateChildNode && (
            <button 
              className="text-xs text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded px-2 py-1"
              onClick={() => handleCreateChildNode()}
            >
              Edit
            </button>
          )}
        </div>
      </div>
      
      {/* Context Menu */}
      {showContextMenu && (
        <div 
          className="absolute bg-white shadow-lg rounded-md py-1 z-50"
          style={{ left: contextMenuPosition.x, top: contextMenuPosition.y }}
        >
          <button
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            onClick={handleCreateChildNode}
          >
            Create Correction Node
          </button>
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
