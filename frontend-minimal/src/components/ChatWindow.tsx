import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { useSessionWS } from '../hooks/useSessionWS';
import { useGraphStore } from '../store/graph';
import { useHealth } from '../hooks/useHealth';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
}

interface ChatWindowProps {
  sessionId?: string;
  provider?: 'qwen' | 'ollama';
  model?: string;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ sessionId = 'default-session', provider = 'qwen', model = 'llama2' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! How can I help you today?',
      sender: 'ai',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { nodes } = useGraphStore();
  
  // Get the WebSocket connection for this session
  const { sendPrompt, error } = useSessionWS(sessionId, provider, model);
  
  // Get health status
  const { health } = useHealth();
  
  // Check if Ollama is ready
  const isOllamaReady = health?.find((service: any) => service.id === 'ollama')?.status === 'healthy';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add a new AI message when nodes are added to the graph
  useEffect(() => {
    const nodesArray = Object.values(nodes);
    if (nodesArray.length > 0) {
      const lastNode = nodesArray[nodesArray.length - 1];
      // Check if this is a new node for this session
      if (lastNode.sessionId === sessionId) {
        const aiMessage: Message = {
          id: `graph-${lastNode.id}`,
          content: lastNode.label,
          sender: 'ai',
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prev => {
          // Check if this message already exists
          if (prev.some(msg => msg.id === aiMessage.id)) return prev;
          return [...prev, aiMessage];
        });
      }
    }
  }, [nodes, sessionId]);

  const handleSend = () => {
    if (inputValue.trim() === '') return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    // Send prompt to backend via WebSocket
    sendPrompt(inputValue);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle typing end when we receive a response
  useEffect(() => {
    // In a real implementation, you would listen for TYPING_END events
    // from the WebSocket and set isTyping to false
    // For now, we'll just set it to false after a delay
    if (isTyping) {
      const timer = setTimeout(() => {
        setIsTyping(false);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isTyping]);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-200 p-4 bg-white">
        <h2 className="text-lg font-semibold text-gray-800">Session: {sessionId}</h2>
        <div className="text-sm text-gray-500">Provider: {provider}</div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isTyping && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="flex justify-center mb-4">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded max-w-md">
              Error: {error}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t border-gray-200 p-4">
        <div className="flex">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={inputValue.trim() === '' || isTyping || (provider === 'ollama' && (!model || !isOllamaReady))}
            className="bg-blue-500 text-white px-4 py-2 rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Send
          </button>
          {provider === 'ollama' && !model && (
            <div className="text-red-500 text-sm mt-2">
              No Ollama model selected. Please select a model or switch to Qwen provider.
            </div>
          )}
          {provider === 'ollama' && model && !isOllamaReady && (
            <div className="text-yellow-500 text-sm mt-2">
              Model warming up... Please wait.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
