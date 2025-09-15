import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useGraphStore } from '../../store/graph';
import { ToggleGroup, ToggleGroupItem } from '../ui/toggle-group';
import { NodeFilterBar } from '../navigation/NodeFilterBar';

interface SidebarProps {
  sessionId: string;
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string) => void;
  onSearch?: (query: string) => void;
  onCreateNode?: () => void;
}

export function Sidebar({ sessionId, selectedNodeId, onNodeSelect, onSearch, onCreateNode }: SidebarProps) {
  const nodesObj = useGraphStore(s => s.nodes);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'stale' | 'merge_pending' | 'completed' | 'failed'>('all');
  
  // Filter nodes based on session, search query, and status filter
  const filteredNodes = useMemo(() => {
    return Object.values(nodesObj)
      .filter(node => node.sessionId === sessionId)
      .filter(node => {
        // Apply search filter
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          return (
            node.label.toLowerCase().includes(query) ||
            node.text.toLowerCase().includes(query)
          );
        }
        return true;
      })
      .filter(node => {
        // Apply status filter
        if (filter === 'all') return true;
        return node.status === filter;
      })
      .sort((a, b) => b.createdAt - a.createdAt); // Sort by creation time, newest first
  }, [nodesObj, sessionId, searchQuery, filter]);
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch?.(query);
  };
  
  const getNodeCounts = () => {
    const sessionNodes = Object.values(nodesObj).filter(n => n.sessionId === sessionId);
    return {
      total: sessionNodes.length,
      active: sessionNodes.filter(n => n.status === 'active').length,
      stale: sessionNodes.filter(n => n.status === 'stale').length,
      merge: sessionNodes.filter(n => n.status === 'merge_pending').length
    };
  };
  
  const counts = getNodeCounts();
  
  return (
    <div className="w-80 bg-white shadow-md h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Knowledge Graph</h2>
        
        {/* Search and Filters */}
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="relative mb-4">
            <input
              type="text"
              placeholder="Search nodes..."
              className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              value={searchQuery}
              onChange={handleSearchChange}
            />
            <svg 
              className="absolute right-3 top-2.5 h-4 w-4 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          
          <NodeFilterBar 
            sessionId={sessionId}
            onFilterChange={(filters) => {
              // For now, we'll just update the status filter
              // In a full implementation, we would also handle the hallucination filter
              setFilter(filters.status as any);
            }}
            className="mb-4"
          />
        </motion.div>
      </div>
      
      {/* Node List */}
      <div className="flex-1 overflow-y-auto">
        {filteredNodes.length === 0 ? (
          <motion.div 
            className="p-6 text-center"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="text-gray-500 mb-4">No nodes yet</div>
            <button
              onClick={onCreateNode}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create Node
            </button>
          </motion.div>
        ) : (
          <ul className="divide-y">
            {filteredNodes.map(node => (
              <motion.li 
                key={node.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <button
                  className={`w-full text-left p-4 hover:bg-gray-50 transition-colors duration-150 ${selectedNodeId === node.id ? 'bg-indigo-50 border-l-4 border-indigo-500' : ''}`}
                  onClick={() => onNodeSelect(node.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="font-medium text-gray-900 truncate">{node.label}</div>
                    <motion.span 
                      className="text-xs px-2 py-1 rounded-full whitespace-nowrap flex items-center"
                      style={{ 
                        backgroundColor: getStatusColor(node.status) + '20', 
                        color: getStatusColor(node.status) 
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {getStatusIcon(node.status)}
                      <span className="ml-1">{node.status.replace('_', ' ')}</span>
                    </motion.span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 truncate">
                    {node.text.substring(0, 80)}{node.text.length > 80 ? '...' : ''}
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs text-gray-400">{node.type}</span>
                    <span className="text-xs text-gray-400">
                      {new Date(node.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </button>
              </motion.li>
            ))}
          </ul>
        )}
      </div>
      
      {/* Footer with badge counts */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex justify-between space-x-2">
          <motion.span 
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-800"
            whileHover={{ scale: 1.05 }}
          >
            Nodes: {counts.total}
          </motion.span>
          <motion.span 
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
            whileHover={{ scale: 1.05 }}
          >
            Active: {counts.active}
          </motion.span>
          <motion.span 
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
            whileHover={{ scale: 1.05 }}
          >
            Stale: {counts.stale}
          </motion.span>
          <motion.span 
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
            whileHover={{ scale: 1.05 }}
          >
            Merge: {counts.merge}
          </motion.span>
        </div>
      </div>
    </div>
  );
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return '#22c55e';
    case 'stale': return '#64748b';
    case 'merge_pending': return '#eab308';
    case 'completed': return '#3b82f6';
    case 'failed': return '#ef4444';
    default: return '#334155';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
      return (
        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
          <circle cx="4" cy="4" r="3" />
        </svg>
      );
    case 'stale':
      return (
        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
          <circle cx="4" cy="4" r="3" />
        </svg>
      );
    case 'merge_pending':
      return (
        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 8 8">
          <circle cx="4" cy="4" r="3" />
        </svg>
      );
    default:
      return null;
  }
};
