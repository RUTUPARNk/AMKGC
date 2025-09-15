import React, { useState, useEffect, useRef } from 'react';
import { useSearchStore } from '../stores/searchStore';

export const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'keyword' | 'semantic'>('keyword');
  const { searchNodes, searchSemantic, loading } = useSearchStore();
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  
  // Debounce search queries
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    if (query.trim()) {
      debounceRef.current = setTimeout(() => {
        if (searchMode === 'keyword') {
          searchNodes(query);
        } else {
          searchSemantic(query);
        }
      }, 300);
    }
    
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, searchMode, searchNodes, searchSemantic]);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };
  
  const handleClear = () => {
    setQuery('');
  };
  
  return (
    <div className="relative w-full mb-4">
      {/* Search mode toggle */}
      <div className="flex mb-2 bg-gray-100 rounded-md p-1">
        <button
          className={`flex-1 py-1 px-2 text-xs rounded-md transition-colors ${searchMode === 'keyword' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          onClick={() => setSearchMode('keyword')}
        >
          Keyword
        </button>
        <button
          className={`flex-1 py-1 px-2 text-xs rounded-md transition-colors ${searchMode === 'semantic' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          onClick={() => setSearchMode('semantic')}
        >
          Semantic
        </button>
      </div>
      
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder="Search nodes and commits..."
          className="w-full px-4 py-2 pl-10 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        {query && (
          <button
            onClick={handleClear}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      
      {loading && (
        <div className="absolute right-0 top-0 bottom-0 flex items-center pr-3">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
        </div>
      )}
    </div>
  );
};
